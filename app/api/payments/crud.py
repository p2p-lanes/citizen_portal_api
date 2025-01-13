from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Query, Session

from app.api.applications.attendees.models import Attendee, AttendeeProduct
from app.api.applications.models import Application
from app.api.base_crud import CRUDBase
from app.api.payments import models, schemas
from app.api.payments.schemas import PaymentSource
from app.api.popup_city.models import EmailTemplate
from app.api.products.models import Product
from app.core import payments_utils
from app.core.logger import logger
from app.core.mail import send_payment_confirmed_mail
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

    def create(
        self,
        db: Session,
        obj: schemas.PaymentCreate,
        user: Optional[TokenData] = None,
    ) -> models.Payment:
        payment_data = payments_utils.create_payment(db, obj, user)

        payment_dict = payment_data.model_dump(exclude={'products'})
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
            self._add_products_to_attendees(db_payment)

        db.commit()
        db.refresh(db_payment)
        return db_payment

    def _add_products_to_attendees(self, payment: models.Payment) -> None:
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

    def approve_payment(
        self,
        db: Session,
        payment: models.Payment,
        *,
        user: TokenData,
        currency: Optional[str] = None,
    ) -> models.Payment:
        """Handle payment approval and related operations."""
        if payment.status == 'approved':
            logger.info('Payment %s already approved', payment.id)
            return payment

        payment_update = schemas.PaymentUpdate(
            status='approved',
            currency=currency,
            source=PaymentSource.STRIPE
            if currency == 'USD'
            else PaymentSource.SIMPLEFI,
        )
        updated_payment = self.update(db, payment.id, payment_update, user)

        ticket_list = []
        if payment.products_snapshot:
            logger.info(
                'Processing %s products for payment %s',
                len(payment.products_snapshot),
                payment.id,
            )
            self._add_products_to_attendees(payment)
            for product_snapshot in payment.products_snapshot:
                attendee = product_snapshot.attendee
                ticket_list.append(f'{product_snapshot.product_name} ({attendee.name})')
            db.commit()

        template = 'payment-confirmed'
        email_template = (
            db.query(EmailTemplate)
            .filter(
                EmailTemplate.popup_city_id == payment.application.popup_city_id,
                EmailTemplate.event == template,
            )
            .first()
        )
        if email_template:
            template = email_template.template
        send_payment_confirmed_mail(
            receiver_mail=payment.application.citizen.primary_email,
            first_name=payment.application.citizen.first_name,
            ticket_list=ticket_list,
            template=template,
        )

        logger.info('Payment %s approved', payment.id)
        return updated_payment


payment = CRUDPayment(models.Payment)
