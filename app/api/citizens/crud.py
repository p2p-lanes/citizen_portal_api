import random
from datetime import timedelta
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.base_crud import CRUDBase
from app.api.citizens import models, schemas
from app.api.email_logs.crud import email_log
from app.api.email_logs.schemas import EmailEvent
from app.core.security import TokenData
from app.core.utils import create_spice, current_time


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

    def get_or_create(
        self, db: Session, citizen: schemas.CitizenCreate
    ) -> models.Citizen:
        existing_citizen = self.get_by_email(db, citizen.primary_email)
        if existing_citizen:
            return existing_citizen
        return self.create(db, citizen)

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
        use_code: bool = False,
    ) -> models.Citizen:
        citizen = self.get_by_email(db, email)
        code = random.randint(100000, 999999) if use_code else None
        if not citizen:
            to_create = schemas.CitizenCreate(primary_email=email)
            citizen = self.create(db, to_create)
        else:
            citizen.spice = create_spice()
            if code:
                citizen.code = code
                citizen.code_expiration = current_time() + timedelta(minutes=10)
            db.commit()
            db.refresh(citizen)

        if code:
            email_log.send_mail(
                email,
                event=EmailEvent.AUTH_CITIZEN_BY_CODE.value,
                popup_slug=popup_slug,
                params={'code': code, 'email': email},
                spice=citizen.spice,
                entity_type='citizen',
                entity_id=citizen.id,
                citizen_id=citizen.id,
            )
        else:
            email_log.send_login_mail(email, citizen.spice, citizen.id, popup_slug)

        return {'message': 'Mail sent successfully'}

    def login(
        self,
        db: Session,
        *,
        email: str,
        spice: Optional[str] = None,
        code: Optional[int] = None,
    ) -> models.Citizen:
        if not spice and not code:
            raise HTTPException(
                status_code=400, detail='Either spice or code must be provided'
            )

        citizen = self.get_by_email(db, email)
        if not citizen:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Citizen not found',
            )
        if spice and citizen.spice != spice:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid spice',
            )
        if code:
            if citizen.code != code:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Invalid code',
                )
            if citizen.code_expiration < current_time():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Code expired',
                )

        citizen.email_validated = True
        db.commit()
        db.refresh(citizen)
        return citizen


citizen = CRUDCitizen(models.Citizen)
