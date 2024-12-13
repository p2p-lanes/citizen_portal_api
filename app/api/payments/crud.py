from typing import List, Optional

from sqlalchemy.orm import Session

from app.api.base_crud import CRUDBase
from app.api.payments import models, schemas
from app.core import payments_utils
from app.core.security import TokenData


class CRUDPayment(
    CRUDBase[models.Payment, schemas.PaymentCreate, schemas.PaymentUpdate]
):
    def _check_permission(self, db_obj: models.Payment, user: TokenData) -> bool:
        return db_obj.citizen_id == user.citizen_id

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
        p = payments_utils.create_payment(db, obj, user)
        obj = schemas.InternalPaymentCreate(**p)
        return super().create(db, obj, user)


payment = CRUDPayment(models.Payment)
