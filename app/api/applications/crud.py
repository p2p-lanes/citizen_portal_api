from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.applications import models, schemas
from app.api.base_crud import CRUDBase
from app.api.citizens.models import Citizen as CitizenModel
from app.core.mail import send_mail

class CRUDApplication(
    CRUDBase[models.Application, schemas.ApplicationCreate, schemas.ApplicationCreate]
):
    def get_by_email(self, db: Session, email: str) -> Optional[models.Application]:
        return db.query(self.model).filter(self.model.email == email).first()

    def create(self, db: Session, obj: schemas.ApplicationCreate) -> models.Application:
        citizen = (
            db.query(CitizenModel).filter(CitizenModel.id == obj.citizen_id).first()
        )
        if not citizen:
            raise HTTPException(status_code=404, detail='Citizen not found')
        email = citizen.primary_email
        obj = schemas.InternalApplicationCreate(**obj.model_dump(), email=email)

        params = {
            "submission_form_url": "https://citizen-portal-ten.vercel.app/portal",
            "first_name": obj.first_name
        }
        send_mail(
            receiver_mail=email,
            template="application-recieved",
            params=params,
        )

        return super().create(db, obj)


application = CRUDApplication(models.Application)
