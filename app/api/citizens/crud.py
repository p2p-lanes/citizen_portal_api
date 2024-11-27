from typing import Optional

from sqlalchemy.orm import Session

from app.api.base_crud import CRUDBase
from app.api.citizens import models, schemas


class CRUDCitizen(
    CRUDBase[models.Citizen, schemas.CitizenCreate, schemas.CitizenCreate]
):
    def get_by_email(self, db: Session, email: str) -> Optional[models.Citizen]:
        return db.query(self.model).filter(self.model.email == email).first()


citizen = CRUDCitizen(models.Citizen)
