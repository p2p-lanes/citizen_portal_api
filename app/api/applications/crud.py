from typing import Optional

from sqlalchemy.orm import Session

from app.api.applications import models, schemas
from app.api.base_crud import CRUDBase


class CRUDApplication(
    CRUDBase[models.Application, schemas.ApplicationCreate, schemas.ApplicationCreate]
):
    def get_by_email(self, db: Session, email: str) -> Optional[models.Application]:
        return db.query(self.model).filter(self.model.email == email).first()


application = CRUDApplication(models.Application)
