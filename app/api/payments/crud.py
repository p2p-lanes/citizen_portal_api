from typing import List, Optional

from sqlalchemy.orm import Query, Session
from sqlalchemy import insert

from app.api.base_crud import CRUDBase
from app.api.payments import models, schemas
from app.api.applications.models import Application
from app.api.products.models import Product
from app.core import payments_utils
from app.core.security import TokenData


class CRUDPayment(
    CRUDBase[models.Payment, schemas.PaymentCreate, schemas.PaymentUpdate]
):
    def _check_permission(self, db_obj: models.Payment, user: TokenData) -> bool:
        return db_obj.application.citizen_id == user.citizen_id

    def _apply_filters(
        self, query: Query, filters: schemas.BaseModel | None = None
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

        payment_dict = payment_data.model_dump(exclude={'product_ids'})
        db_payment = self.model(**payment_dict)

        # First save the payment to get its ID
        db.add(db_payment)
        db.flush()  # This assigns an ID to db_payment without committing

        if hasattr(obj, 'product_ids'):
            products = db.query(Product).filter(Product.id.in_(obj.product_ids)).all()
            # Insert directly into the association table
            for product in products:
                stmt = insert(models.payment_products).values(
                    payment_id=db_payment.id,
                    product_id=product.id,
                    product_name=product.name,
                    product_description=product.description,
                    product_price=product.price,
                    product_category=product.category,
                    quantity=1,
                )
                db.execute(stmt)

        db.commit()
        db.refresh(db_payment)
        return db_payment


payment = CRUDPayment(models.Payment)
