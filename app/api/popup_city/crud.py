from datetime import timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.api.base_crud import CRUDBase
from app.api.popup_city import models, schemas
from app.core.logger import logger
from app.core.utils import current_time


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
        week_from_now = current_time() + timedelta(days=7)
        return (
            db.query(models.EmailTemplate)
            .join(models.PopUpCity)
            .filter(
                models.EmailTemplate.frequency.isnot(None),
                models.EmailTemplate.frequency != '',
                models.PopUpCity.end_date.isnot(None),
                models.PopUpCity.end_date > week_from_now,
            )
            .all()
        )


popup_city = CRUDPopUpCity(models.PopUpCity)
