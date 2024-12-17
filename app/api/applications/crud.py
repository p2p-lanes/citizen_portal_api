from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.applications import models, schemas
from app.api.applications.attendees import models as attendees_models
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

        if obj.status and obj.status != 'draft':
            send_application_received_mail(receiver_mail=email)

        return super().create(db, obj)

    def update(
        self,
        db: Session,
        id: int,
        obj: schemas.ApplicationUpdate,
        user: TokenData,
    ) -> models.Application:
        application = super().update(db, id, obj, user)

        if obj.status != 'draft':
            send_application_received_mail(receiver_mail=application.email)
            sent_mails = application.sent_mails or ''
            sent_mails = ','.join(sent_mails.split(',') + ['application-recieved'])
            application.sent_mails = sent_mails
            db.commit()
            db.refresh(application)
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
    ) -> attendees_models.Attendee:
        _ = self.get(db, application_id, user)
        attendee = attendees_schemas.InternalAttendeeCreate(
            **attendee.model_dump(), application_id=application_id
        )
        return attendees_crud.create(db, attendee, user)

    def update_attendee(
        self,
        db: Session,
        application_id: int,
        attendee_id: int,
        attendee: attendees_schemas.AttendeeUpdate,
        user: TokenData,
    ) -> attendees_models.Attendee:
        _ = self.get(db, application_id, user)
        return attendees_crud.update(db, attendee_id, attendee, user)


application = CRUDApplication(models.Application)
