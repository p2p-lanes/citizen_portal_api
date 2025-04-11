import json
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.api.applications.models import Application
from app.api.base_crud import CRUDBase
from app.api.email_logs import models, schemas
from app.api.email_logs.schemas import EmailEvent, EmailLogCreate, EmailStatus
from app.api.popup_city.models import PopUpCity
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logger import logger
from app.core.mail import send_mail
from app.core.utils import create_spice, current_time, encode


def _generate_authenticate_url(
    receiver_mail: str,
    spice: str,
    citizen_id: int,
    popup_slug: Optional[str] = None,
):
    url = urllib.parse.urljoin(
        settings.BACKEND_URL,
        f'citizens/login?email={urllib.parse.quote(receiver_mail)}&spice={spice}',
    )
    token_url = encode(
        {
            'url': url,
            'citizen_email': receiver_mail,
            'citizen_id': citizen_id,
        },
        expires_delta=timedelta(hours=3),
    )
    auth_url = urllib.parse.urljoin(
        settings.FRONTEND_URL, f'/auth?token_url={token_url}'
    )
    if popup_slug:
        auth_url += f'&popup={popup_slug}'
    return auth_url


class CRUDEmailLog(
    CRUDBase[models.EmailLog, schemas.EmailLogCreate, schemas.EmailLogCreate]
):
    def generate_authenticate_url(
        self,
        db: Session,
        application: Application,
    ) -> str:
        citizen = application.citizen
        logger.info('Citizen %s', citizen.id)
        if not citizen.spice:
            citizen.spice = create_spice()
            db.commit()

        email = application.email
        popup_slug = application.popup_city.slug
        return _generate_authenticate_url(email, citizen.spice, citizen.id, popup_slug)

    def get_by_email(self, db: Session, email: str) -> List[models.EmailLog]:
        return db.query(self.model).filter(self.model.receiver_email == email).all()

    def send_mail(
        self,
        receiver_mail: str,
        *,
        event: str,
        popup_city: Optional[PopUpCity] = None,
        params: Optional[dict] = None,
        send_at: Optional[datetime] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        spice: Optional[str] = None,
        citizen_id: Optional[int] = None,
        popup_slug: Optional[str] = None,
    ) -> dict:
        if send_at and not entity_type and not entity_id:
            raise ValueError(
                'entity_type and entity_id are required if send_at is provided'
            )

        if spice and citizen_id and popup_slug:
            params['ticketing_url'] = _generate_authenticate_url(
                receiver_mail, spice, citizen_id, popup_slug
            )

        db = SessionLocal()
        status = EmailStatus.FAILED
        error_message = None
        template = event
        params = params or {}
        if popup_city:
            template = popup_city.get_email_template(event)
            params.update(
                {
                    'popup_name': popup_city.name,
                    'web_url': popup_city.web_url,
                    'email_image': popup_city.email_image,
                    'contact_email': popup_city.contact_email,
                    'blog_url': popup_city.blog_url,
                    'twitter_url': popup_city.twitter_url,
                }
            )

        params['portal_url'] = settings.FRONTEND_URL
        try:
            if send_at is not None:
                logger.info('Scheduled email to be sent at %s', send_at)
                status = EmailStatus.SCHEDULED
                return {'status': status}

            response_data = send_mail(
                receiver_mail,
                template=template,
                params=params,
            )
            status = response_data['status']
            return response_data
        except Exception as e:
            error_message = str(e)
            raise
        finally:
            try:
                email_log_data = EmailLogCreate(
                    receiver_email=receiver_mail,
                    popup_city_id=popup_city.id if popup_city else None,
                    template=template,
                    event=event,
                    params=params,
                    status=status,
                    send_at=send_at,
                    error_message=error_message,
                    entity_type=entity_type,
                    entity_id=entity_id,
                )
                self.create(db, obj=email_log_data)
            except Exception as db_error:
                logger.error('Failed to log email: %s', str(db_error))
            finally:
                db.close()

    def send_login_mail(
        self,
        receiver_mail: str,
        spice: str,
        citizen_id: int,
        popup_slug: Optional[str] = None,
    ):
        authenticate_url = _generate_authenticate_url(
            receiver_mail, spice, citizen_id, popup_slug
        )
        params = {'the_url': authenticate_url}
        return self.send_mail(
            receiver_mail=receiver_mail,
            event=EmailEvent.AUTH_CITIZEN_PORTAL.value,
            params=params,
            entity_type='citizen',
            entity_id=citizen_id,
        )

    def send_scheduled_mails(self, db: Session):
        scheduled_emails = (
            db.query(self.model)
            .filter(self.model.status == EmailStatus.SCHEDULED)
            .all()
        )
        logger.info('Found %s scheduled emails', len(scheduled_emails))

        for email in scheduled_emails:
            logger.info('Processing email %s, send_at: %s', email.id, email.send_at)
            if email.send_at > current_time():
                logger.info('Email is not due to be sent yet. Skipping...')
                continue

            try:
                params = json.loads(email.params)
                send_mail(
                    receiver_mail=email.receiver_email,
                    template=email.template,
                    params=params,
                )
                email.status = EmailStatus.SUCCESS
                email.error_message = None
            except Exception as e:
                logger.error('Failed to send email %s: %s', email.id, str(e))
                email.status = EmailStatus.FAILED
                email.error_message = str(e)
            finally:
                # Commit changes for each email individually
                try:
                    db.commit()
                except Exception as db_error:
                    logger.error(
                        'Failed to update email log %s: %s', email.id, str(db_error)
                    )
                    db.rollback()

    def cancel_scheduled_emails(self, db: Session, entity_type: str, entity_id: int):
        db.query(self.model).filter(
            self.model.entity_type == entity_type,
            self.model.entity_id == entity_id,
            self.model.status == EmailStatus.SCHEDULED,
        ).update({'status': EmailStatus.CANCELLED})
        db.commit()
        return {'message': 'Scheduled emails cancelled successfully'}


email_log = CRUDEmailLog(models.EmailLog)
