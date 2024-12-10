from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.applications import models, schemas
from app.api.base_crud import CRUDBase
from app.api.citizens.models import Citizen as CitizenModel
from app.core.mail import send_application_received_mail
from app.core.security import TokenData


class CRUDApplication(
    CRUDBase[models.Application, schemas.ApplicationCreate, schemas.ApplicationCreate]
):
    def check_permission(self, db_obj: models.Application, user: TokenData) -> bool:
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
            application.sent_mails = application.sent_mails or []
            application.sent_mails.append('application-recieved')
            db.commit()
            db.refresh(application)
        return application

    def find(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: schemas.ApplicationFilter | None = None,
        user: TokenData | None = None,
    ) -> List[models.Application]:
        if user:
            filters = filters or schemas.ApplicationFilter()
            filters.citizen_id = user.citizen_id
        return super().find(db, skip, limit, filters, user)


application = CRUDApplication(models.Application)
