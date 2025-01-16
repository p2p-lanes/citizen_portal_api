from typing import Optional

from sqlalchemy.orm import Session

from app.api.base_crud import CRUDBase
from app.api.popup_city import models, schemas
from app.core.logger import logger


class CRUDPopUpCity(
    CRUDBase[models.PopUpCity, schemas.PopUpCityCreate, schemas.PopUpCityCreate]
):
    def get_by_name(self, db: Session, name: str) -> Optional[models.PopUpCity]:
        return db.query(self.model).filter(self.model.name == name).first()

    def get_email_template(
        self, db: Session, popup_city_id: int, template: str
    ) -> Optional[models.EmailTemplate]:
        email_template = (
            db.query(models.EmailTemplate)
            .filter(
                models.EmailTemplate.popup_city_id == popup_city_id,
                models.EmailTemplate.event == template,
            )
            .first()
        )
        _template = template
        if email_template:
            logger.info('Email template found %s', email_template.template)
            _template = email_template.template
        return _template


popup_city = CRUDPopUpCity(models.PopUpCity)
