from typing import List, Optional

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
        if not email_template:
            error_message = (
                f'Email template not found for {template} in popup city {popup_city_id}'
            )
            logger.error(error_message)
            raise ValueError(error_message)

        logger.info('Email template found %s', email_template.template)
        return email_template.template

    def get_reminder_templates(self, db: Session) -> List[models.EmailTemplate]:
        return (
            db.query(models.EmailTemplate)
            .filter(
                models.EmailTemplate.frequency.isnot(None),
                models.EmailTemplate.frequency != '',
            )
            .all()
        )


popup_city = CRUDPopUpCity(models.PopUpCity)
