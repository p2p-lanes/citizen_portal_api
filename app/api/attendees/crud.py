import random
import string
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.base_crud import CRUDBase
from app.core.security import SYSTEM_TOKEN, TokenData

from . import models, schemas


class CRUDAttendees(
    CRUDBase[models.Attendee, schemas.InternalAttendeeCreate, schemas.AttendeeUpdate]
):
    def _check_permission(self, db_obj: models.Attendee, user: TokenData) -> bool:
        return db_obj.application.citizen_id == user.citizen_id or user == SYSTEM_TOKEN

    def get_by_email(self, db: Session, email: str) -> List[models.Attendee]:
        return db.query(self.model).filter(self.model.email == email).all()

    def get_by_code(self, db: Session, code: str) -> models.Attendee:
        """Get a single record by code with permission check."""
        return db.query(self.model).filter(self.model.check_in_code == code).first()

    def find(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[schemas.AttendeeFilter] = None,
        user: Optional[TokenData] = None,
    ) -> List[models.Attendee]:
        if user:
            filters = filters or schemas.AttendeeFilter()
            filters.citizen_id = user.citizen_id
        return super().find(db, skip, limit, filters)

    def create(
        self,
        db: Session,
        obj: schemas.AttendeeCreate,
        user: TokenData,
    ) -> models.Attendee:
        code = ''.join(random.choices(string.ascii_uppercase, k=4))
        obj.check_in_code = 'EE25' + code
        return super().create(db, obj, user)

    def update(
        self,
        db: Session,
        id: int,
        obj: schemas.AttendeeUpdate,
        user: TokenData,
    ) -> models.Attendee:
        attendee = self.get(db, id, user)
        if attendee.products:
            # if attendee has products, we cannot change the category
            obj.category = attendee.category

        return super().update(db, id, obj, user)

    def delete(self, db: Session, id: int, user: TokenData) -> models.Attendee:
        """Delete an attendee and its related payment products."""
        try:
            attendee = self.get(db, id, user)  # This will raise 404 if not found

            if attendee.products:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Attendee has products',
                )

            if attendee.payment_products:
                for payment_product in attendee.payment_products:
                    db.delete(payment_product)

            db.delete(attendee)
            db.commit()
            return attendee
        except Exception as e:
            db.rollback()
            raise e


attendee = CRUDAttendees(models.Attendee)
