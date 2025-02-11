from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.base_crud import CRUDBase
from app.api.citizens import models, schemas
from app.api.email_logs.crud import email_log
from app.core.security import TokenData
from app.core.utils import create_spice


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

    def create(
        self,
        db: Session,
        obj: schemas.CitizenCreate,
        user: Optional[TokenData] = None,
    ) -> models.Citizen:
        to_create = schemas.InternalCitizenCreate(
            **obj.model_dump(),
            spice=create_spice(),
        )
        citizen = super().create(db, to_create)
        email_log.send_login_mail(citizen.primary_email, to_create.spice, citizen.id)
        return citizen

    def signup(self, db: Session, *, obj: schemas.CitizenCreate) -> models.Citizen:
        citizen = self.create(db, obj)
        email_log.send_login_mail(citizen.primary_email, citizen.spice, citizen.id)
        return citizen

    def authenticate(
        self,
        db: Session,
        *,
        email: str,
        popup_slug: Optional[str] = None,
    ) -> models.Citizen:
        citizen = self.get_by_email(db, email)
        if not citizen:
            to_create = schemas.CitizenCreate(primary_email=email)
            citizen = self.create(db, to_create)
        else:
            citizen.spice = create_spice()
            db.commit()
            db.refresh(citizen)
        email_log.send_login_mail(email, citizen.spice, citizen.id, popup_slug)
        return {"message": "Mail sent successfully"}

    def login(
        self,
        db: Session,
        *,
        email: str,
        spice: str,
    ) -> models.Citizen:
        citizen = self.get_by_email(db, email)
        if not citizen:
            raise HTTPException(status_code=404, detail="Citizen not found")
        if citizen.spice != spice:
            raise HTTPException(status_code=401, detail="Invalid spice")
        citizen.email_validated = True
        db.commit()
        db.refresh(citizen)
        return citizen


citizen = CRUDCitizen(models.Citizen)
