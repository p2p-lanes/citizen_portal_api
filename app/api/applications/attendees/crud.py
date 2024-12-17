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


attendee = CRUDAttendees(models.Attendee)
