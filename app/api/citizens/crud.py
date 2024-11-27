import random
import string
from typing import Optional

from sqlalchemy.orm import Session

from app.api.base_crud import CRUDBase
from app.api.citizens import models, schemas
from app.core.mail import send_login_mail


def create_spice() -> str:
    alla = string.ascii_letters + string.digits
    return ''.join(random.sample(alla, 12))


class CRUDCitizen(
    CRUDBase[models.Citizen, schemas.CitizenCreate, schemas.CitizenCreate]
):
    def get_by_email(self, db: Session, email: str) -> Optional[models.Citizen]:
        return db.query(self.model).filter(self.model.email == email).first()

    def signup(self, db: Session, *, obj: schemas.CitizenCreate) -> models.Citizen:
        to_create = schemas.InternalCitizenCreate(
            **obj.model_dump(), spice=create_spice()
        )
        citizen = self.create(db, to_create)
        send_login_mail(obj.email, to_create.spice)
        return citizen


citizen = CRUDCitizen(models.Citizen)
