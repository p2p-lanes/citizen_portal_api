import random
import string
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.base_crud import CRUDBase
from app.api.citizens import models, schemas
from app.core.mail import send_login_mail
from app.core.security import TokenData


def create_spice() -> str:
    alla = string.ascii_letters + string.digits
    return ''.join(random.sample(alla, 12))


class CRUDCitizen(
    CRUDBase[models.Citizen, schemas.CitizenCreate, schemas.CitizenCreate]
):
    def _check_permission(self, db_obj: models.Citizen, user: TokenData) -> bool:
        return db_obj.id == user.citizen_id

    def find(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[schemas.CitizenFilter] = None,
        user: Optional[TokenData] = None,
    ) -> List[models.Citizen]:
        if user:
            filters = filters or schemas.CitizenFilter()
            filters.id = user.citizen_id
        return super().find(db, skip, limit, filters)

    def get_by_email(self, db: Session, email: str) -> Optional[models.Citizen]:
        return db.query(self.model).filter(self.model.primary_email == email).first()

    def signup(self, db: Session, *, obj: schemas.CitizenCreate) -> models.Citizen:
        to_create = schemas.InternalCitizenCreate(
            **obj.model_dump(), spice=create_spice()
        )
        citizen = self.create(db, to_create)
        send_login_mail(citizen.primary_email, to_create.spice, citizen.id)
        return citizen

    def authenticate(self, db: Session, *, email: str) -> models.Citizen:
        citizen = self.get_by_email(db, email)
        spice = create_spice()
        if not citizen:
            to_create = schemas.InternalCitizenCreate(
                primary_email=email,
                spice=spice,
            )
            citizen = self.create(db, to_create)
        citizen.spice = spice
        db.commit()
        db.refresh(citizen)
        send_login_mail(email, citizen.spice, citizen.id)
        return {'message': 'Mail sent successfully'}

    def login(
        self,
        db: Session,
        *,
        email: str,
        spice: str,
    ) -> models.Citizen:
        citizen = self.get_by_email(db, email)
        if not citizen:
            raise HTTPException(status_code=404, detail='Citizen not found')
        if citizen.spice != spice:
            raise HTTPException(status_code=401, detail='Invalid spice')
        citizen.email_validated = True
        db.commit()
        db.refresh(citizen)
        return citizen


citizen = CRUDCitizen(models.Citizen)
