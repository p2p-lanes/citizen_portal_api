from typing import List, Optional

from sqlalchemy.orm import Session

from app.api.base_crud import CRUDBase
from app.core.security import TokenData

from . import models, schemas


class CRUDAttendees(
    CRUDBase[models.Attendee, schemas.InternalAttendeeCreate, schemas.AttendeeUpdate]
):
    def _check_permission(self, db_obj: models.Attendee, user: TokenData) -> bool:
        return db_obj.application.citizen_id == user.citizen_id

    def get_by_email(self, db: Session, email: str) -> List[models.Attendee]:
        return db.query(self.model).filter(self.model.email == email).all()

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


attendee = CRUDAttendees(models.Attendee)
