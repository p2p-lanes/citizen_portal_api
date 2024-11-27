from typing import Optional

from sqlalchemy.orm import Session

from app.api.base_crud import CRUDBase
from app.api.products import models, schemas


class CRUDProduct(
    CRUDBase[models.Product, schemas.ProductCreate, schemas.ProductCreate]
):
    def get_by_name(self, db: Session, name: str) -> Optional[models.Product]:
        return db.query(self.model).filter(self.model.name == name).first()


product = CRUDProduct(models.Product)
