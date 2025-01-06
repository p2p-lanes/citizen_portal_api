from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.applications import models, schemas
from app.api.applications.attendees import schemas as attendees_schemas
from app.api.applications.attendees.crud import attendee as attendees_crud
from app.api.base_crud import CRUDBase
from app.api.citizens.models import Citizen as CitizenModel
from app.core.mail import send_application_received_mail
from app.core.security import TokenData


class CRUDApplication(
    CRUDBase[models.Application, schemas.ApplicationCreate, schemas.ApplicationCreate]
):
    def _check_permission(self, db_obj: models.Application, user: TokenData) -> bool:
        return db_obj.citizen_id == user.citizen_id

    def get_by_email(self, db: Session, email: str) -> Optional[models.Application]:
        return db.query(self.model).filter(self.model.email == email).first()

    def create(
        self,
        db: Session,
        obj: schemas.ApplicationCreate,
        user: TokenData,
    ) -> models.Application:
        if obj.citizen_id != user.citizen_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Not authorized to create application for another citizen',
            )
        citizen = (
            db.query(CitizenModel).filter(CitizenModel.id == obj.citizen_id).first()
        )
        if not citizen:
            raise HTTPException(status_code=404, detail='Citizen not found')
        email = citizen.primary_email
        obj = schemas.InternalApplicationCreate(**obj.model_dump(), email=email)

        if obj.status and obj.status != schemas.ApplicationStatus.DRAFT:
            send_application_received_mail(receiver_mail=email)

        application = super().create(db, obj)
        attendee = attendees_schemas.AttendeeCreate(
            name=f'{obj.first_name} {obj.last_name}'.strip(),
            category='main',
            email=email,
        )
        self.create_attendee(db, application.id, attendee, user)
        return application

    def update(
        self,
        db: Session,
        id: int,
        obj: schemas.ApplicationUpdate,
        user: TokenData,
    ) -> models.Application:
        application = super().update(db, id, obj, user)

        if obj.status != schemas.ApplicationStatus.DRAFT:
            send_application_received_mail(receiver_mail=application.email)

        return application

    def find(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[schemas.ApplicationFilter] = None,
        user: Optional[TokenData] = None,
    ) -> List[models.Application]:
        if user:
            filters = filters or schemas.ApplicationFilter()
            filters.citizen_id = user.citizen_id
        return super().find(db, skip, limit, filters, user)

    def create_attendee(
        self,
        db: Session,
        application_id: int,
        attendee: attendees_schemas.AttendeeCreate,
        user: TokenData,
    ) -> models.Application:
        application = self.get(db, application_id, user)
        existing_categories = {a.category for a in application.attendees}
        if (
            attendee.category in ['main', 'spouse']
            and attendee.category in existing_categories
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Attendee {attendee.category} already exists',
            )
        existing_emails = [a.email for a in application.attendees if a.email]
        if attendee.email and attendee.email in existing_emails:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Attendee {attendee.email} already exists',
            )
        attendee = attendees_schemas.InternalAttendeeCreate(
            **attendee.model_dump(), application_id=application_id
        )
        attendee = attendees_crud.create(db, attendee, user)
        return application

    def update_attendee(
        self,
        db: Session,
        application_id: int,
        attendee_id: int,
        attendee: attendees_schemas.AttendeeUpdate,
        user: TokenData,
    ) -> models.Application:
        application = self.get(db, application_id, user)
        existing_emails = [a.email for a in application.attendees if a.email]
        if attendee.email and attendee.email in existing_emails:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Attendee {attendee.email} already exists',
            )
        _ = attendees_crud.update(db, attendee_id, attendee, user)
        return application

    def delete_attendee(
        self,
        db: Session,
        application_id: int,
        attendee_id: int,
        user: TokenData,
    ) -> models.Application:
        application = self.get(db, application_id, user)
        if attendee_id not in [a.id for a in application.attendees]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Attendee not found',
            )
        attendee = attendees_crud.get(db, attendee_id, user)
        if attendee.category == 'main':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Cannot delete main attendee',
            )
        attendees_crud.delete(db, attendee_id, user)
        return application


application = CRUDApplication(models.Application)
