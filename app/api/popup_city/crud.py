from typing import Optional

from sqlalchemy.orm import Session

from app.api.base_crud import CRUDBase
from app.api.popup_city import models, schemas


class CRUDPopUpCity(
    CRUDBase[models.PopUpCity, schemas.PopUpCityCreate, schemas.PopUpCityCreate]
):
    def get_by_name(self, db: Session, name: str) -> Optional[models.PopUpCity]:
        return db.query(self.model).filter(self.model.name == name).first()


popup_city = CRUDPopUpCity(models.PopUpCity)
