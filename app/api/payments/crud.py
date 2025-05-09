from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Query, Session

from app.api.applications.models import Application
from app.api.attendees.models import Attendee, AttendeeProduct
from app.api.base_crud import CRUDBase
from app.api.coupon_codes.crud import coupon_code as coupon_code_crud
from app.api.email_logs.crud import email_log
from app.api.email_logs.schemas import EmailEvent
from app.api.payments import models, schemas
from app.api.payments.schemas import PaymentSource
from app.api.products.models import Product
from app.core import payments_utils
from app.core.logger import logger
from app.core.security import TokenData


class CRUDPayment(
    CRUDBase[models.Payment, schemas.PaymentCreate, schemas.PaymentUpdate]
):
    def _check_permission(self, db_obj: models.Payment, user: TokenData) -> bool:
        return db_obj.application.citizen_id == user.citizen_id

    def _apply_filters(
        self, query: Query, filters: Optional[schemas.BaseModel] = None
    ) -> Query:
        query = super()._apply_filters(query, filters)

        filter_data = filters.model_dump(exclude_none=True)

        if 'citizen_id' in filter_data:
            citizen_id = filter_data.pop('citizen_id')
            query = query.join(models.Payment.application).filter(
                Application.citizen_id == citizen_id
            )
        return query

    def find(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[schemas.PaymentFilter] = None,
        user: Optional[TokenData] = None,
    ) -> List[models.Payment]:
        if user:
            filters = filters or schemas.PaymentFilter()
            filters.citizen_id = user.citizen_id
        return super().find(db, skip, limit, filters)

    def preview(
        self,
        db: Session,
        obj: schemas.PaymentCreate,
        user: Optional[TokenData] = None,
    ) -> schemas.PaymentPreview:
        return payments_utils.preview_payment(db, obj, user)

    def create(
        self,
        db: Session,
        obj: schemas.PaymentCreate,
        user: Optional[TokenData] = None,
    ) -> models.Payment:
        payment_data = payments_utils.create_payment(db, obj, user)

        payment_dict = payment_data.model_dump(exclude={'products', 'original_amount'})
        payment_dict['edit_passes'] = obj.edit_passes
        db_payment = self.model(**payment_dict)

        # First save the payment to get its ID
        db.add(db_payment)
        db.flush()  # This assigns an ID to db_payment without committing

        if obj.products:
            # validate that the attendees correspond to the application
            attendees_ids = {p.attendee_id for p in obj.products}
            attendees = db.query(Attendee).filter(Attendee.id.in_(attendees_ids)).all()
            if len(attendees) != len(attendees_ids):
                raise HTTPException(status_code=400, detail='Invalid attendees')
            for attendee in attendees:
                if attendee.application_id != obj.application_id:
                    raise HTTPException(status_code=400, detail='Invalid attendees')

            product_ids = [p.product_id for p in obj.products]
            products_data = {
                p.id: p
                for p in db.query(Product).filter(Product.id.in_(product_ids)).all()
            }

            for product in obj.products:
                product_id = product.product_id
                payment_product = models.PaymentProduct(
                    payment_id=db_payment.id,
                    product_id=product_id,
                    attendee_id=product.attendee_id,
                    quantity=product.quantity,
                    product_name=products_data[product_id].name,
                    product_description=products_data[product_id].description,
                    product_price=products_data[product_id].price,
                    product_category=products_data[product_id].category,
                )
                db.add(payment_product)

            db.flush()
            db.refresh(db_payment)

        if db_payment.status == 'approved':
            if db_payment.edit_passes:
                self._clear_application_products(db, db_payment)

            if db_payment.coupon_code_id is not None:
                coupon_code_crud.use_coupon_code(db, db_payment.coupon_code_id)

            self._add_products_to_attendees(db_payment)
            self._send_payment_confirmed_email(db_payment)

        db.commit()
        db.refresh(db_payment)
        return db_payment

    def _add_products_to_attendees(self, payment: models.Payment) -> None:
        if not payment.products_snapshot:
            return

        logger.info('Adding products to attendees')
        for product_snapshot in payment.products_snapshot:
            attendee = product_snapshot.attendee
            product_id = product_snapshot.product_id
            if product_id not in [p.id for p in attendee.products]:
                attendee.attendee_products.append(
                    AttendeeProduct(
                        attendee_id=attendee.id,
                        product_id=product_id,
                        quantity=product_snapshot.quantity,
                    )
                )

    def _clear_application_products(self, db: Session, payment: models.Payment) -> None:
        logger.info('Removing products from attendees')
        application = payment.application
        attendees_ids = {a.id for a in application.attendees}
        query = AttendeeProduct.attendee_id.in_(attendees_ids)
        db.query(AttendeeProduct).filter(query).delete(synchronize_session=False)

    def _send_payment_confirmed_email(self, payment: models.Payment) -> None:
        ticket_list = []
        if payment.products_snapshot:
            for product_snapshot in payment.products_snapshot:
                attendee = product_snapshot.attendee
                ticket_list.append(f'{product_snapshot.product_name} ({attendee.name})')

        params = {
            'ticket_list': ', '.join(ticket_list),
            'first_name': payment.application.first_name,
        }
        email_log.send_mail(
            receiver_mail=payment.application.citizen.primary_email,
            event=EmailEvent.PAYMENT_CONFIRMED.value,
            params=params,
            popup_city=payment.application.popup_city,
            entity_type='payment',
            entity_id=payment.id,
        )

    def approve_payment(
        self,
        db: Session,
        payment: models.Payment,
        *,
        user: TokenData,
        currency: Optional[str] = None,
        rate: Optional[float] = None,
    ) -> models.Payment:
        """Handle payment approval and related operations."""
        if payment.status == 'approved':
            logger.info('Payment %s already approved', payment.id)
            return payment

        source = PaymentSource.STRIPE if currency == 'USD' else PaymentSource.SIMPLEFI
        payment_update = schemas.PaymentUpdate(
            status='approved',
            currency=currency,
            rate=rate,
            source=source,
        )
        updated_payment = self.update(db, payment.id, payment_update, user)

        if payment.edit_passes:
            self._clear_application_products(db, payment)
            payment.application.credit = 0
            db.flush()
            db.refresh(payment.application)

        if payment.coupon_code_id is not None:
            coupon_code_crud.use_coupon_code(db, payment.coupon_code_id)

        self._add_products_to_attendees(payment)
        self._send_payment_confirmed_email(payment)

        logger.info('Payment %s approved', payment.id)
        return updated_payment


payment = CRUDPayment(models.Payment)
