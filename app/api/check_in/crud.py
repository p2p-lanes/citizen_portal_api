from sqlalchemy.orm import Session

from app.api.attendees.crud import attendee as attendee_crud
from app.api.base_crud import CRUDBase
from app.core.logger import logger
from app.core.security import SYSTEM_TOKEN
from app.core.utils import current_time

from . import models, schemas


class CRUDCheckIn(
    CRUDBase[
        models.CheckIn, schemas.InternalCheckInCreate, schemas.InternalCheckInCreate
    ]
):
    def _validate_attendee(self, db: Session, attendee_id: int, code: str) -> bool:
        attendee = attendee_crud.get(db, attendee_id, user=SYSTEM_TOKEN)
        return bool(attendee.products) and attendee.check_in_code == code

    def get_check_in_by_attendee_id(
        self,
        db: Session,
        attendee_id: int,
    ) -> models.CheckIn:
        return (
            db.query(models.CheckIn)
            .filter(models.CheckIn.attendee_id == attendee_id)
            .first()
        )

    def new_qr_check_in(
        self,
        db: Session,
        code: str,
    ) -> schemas.CheckInResponse:
        attendee = attendee_crud.get_by_code(db, code)
        logger.info('Attendee with code %s found: %s', code, attendee is not None)
        if not attendee or not attendee.products:
            logger.error('Attendee with code %s not found or has no products', code)
            return schemas.CheckInResponse(success=False, first_check_in=False)

        existing_check_in = self.get_check_in_by_attendee_id(db, attendee.id)
        if existing_check_in:
            logger.info('Existing check-in for attendee %s', attendee.id)
            existing_check_in.code = code
            existing_check_in.qr_check_in = True
            if not existing_check_in.qr_scan_timestamp:
                existing_check_in.qr_scan_timestamp = current_time()

            return schemas.CheckInResponse(success=True, first_check_in=False)

        logger.info('Creating new check-in for attendee %s', attendee.id)
        new_check_in = schemas.InternalCheckInCreate(
            code=code,
            attendee_id=attendee.id,
            qr_check_in=True,
            qr_scan_timestamp=current_time(),
        )
        super().create(db, new_check_in, SYSTEM_TOKEN)
        return schemas.CheckInResponse(success=True, first_check_in=True)

    def new_virtual_check_in(
        self,
        db: Session,
        obj: schemas.NewVirtualCheckIn,
    ) -> schemas.CheckInResponse:
        logger.info('Validating attendee %s with code %s', obj.attendee_id, obj.code)
        if not self._validate_attendee(db, obj.attendee_id, obj.code):
            return schemas.CheckInResponse(success=False, first_check_in=False)

        existing_check_in = self.get_check_in_by_attendee_id(db, obj.attendee_id)
        if existing_check_in:
            logger.info('Existing check-in for attendee %s', obj.attendee_id)
            existing_check_in.code = obj.code
            existing_check_in.virtual_check_in = True
            if not existing_check_in.virtual_check_in_timestamp:
                existing_check_in.virtual_check_in_timestamp = current_time()

            existing_check_in.arrival_date = obj.arrival_date
            existing_check_in.departure_date = obj.departure_date

            return schemas.CheckInResponse(success=True, first_check_in=False)

        logger.info('Creating new check-in for attendee %s', obj.attendee_id)
        new_check_in = schemas.InternalCheckInCreate(
            code=obj.code,
            attendee_id=obj.attendee_id,
            arrival_date=obj.arrival_date,
            departure_date=obj.departure_date,
            virtual_check_in=True,
            virtual_check_in_timestamp=current_time(),
        )
        super().create(db, new_check_in, SYSTEM_TOKEN)
        return schemas.CheckInResponse(success=True, first_check_in=True)


check_in = CRUDCheckIn(models.CheckIn)
