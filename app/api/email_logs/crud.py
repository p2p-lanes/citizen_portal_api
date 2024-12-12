from typing import List

from sqlalchemy.orm import Session

from app.api.base_crud import CRUDBase
from app.api.email_logs import models, schemas


class CRUDEmailLog(
    CRUDBase[models.EmailLog, schemas.EmailLogCreate, schemas.EmailLogCreate]
):
    def get_by_email(self, db: Session, email: str) -> List[models.EmailLog]:
        return db.query(self.model).filter(self.model.receiver_email == email).all()


email_log = CRUDEmailLog(models.EmailLog)
