from typing import Optional

from sqlalchemy.orm import Session

from app.api.access_tokens import models, schemas
from app.api.base_crud import CRUDBase


class CRUDAccessToken(
    CRUDBase[models.AccessToken, schemas.AccessTokenCreate, schemas.AccessTokenUpdate]
):
    def get_by_name(self, db: Session, name: str) -> Optional[models.AccessToken]:
        """Get an access token by its name"""
        return db.query(self.model).filter(self.model.name == name).first()

    def update_by_name(
        self, db: Session, name: str, obj: schemas.AccessTokenUpdate
    ) -> Optional[models.AccessToken]:
        """Update an access token by its name"""
        db_obj = self.get_by_name(db, name)
        if not db_obj:
            return None

        obj_data = obj.model_dump(exclude_unset=True)
        for field, value in obj_data.items():
            setattr(db_obj, field, value)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete_by_name(self, db: Session, name: str) -> bool:
        """Delete an access token by its name"""
        db_obj = self.get_by_name(db, name)
        if not db_obj:
            return False

        db.delete(db_obj)
        db.commit()
        return True


access_token = CRUDAccessToken(models.AccessToken)
