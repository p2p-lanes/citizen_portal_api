import json
from datetime import datetime
from typing import List, Optional

import requests
from sqlalchemy.orm import Session

from app.api.base_crud import CRUDBase
from app.api.email_logs import models, schemas
from app.api.email_logs.schemas import EmailLogCreate, EmailStatus
from app.core.config import Environment, settings
from app.core.database import SessionLocal
from app.core.logger import logger
from app.core.utils import current_time


def _send_mail(
    receiver_mail: str,
    *,
    template: str,
    params: dict,
):
    logger.info('sending %s email to %s', template, receiver_mail)
    url = 'https://api.postmarkapp.com/email/withTemplate'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Postmark-Server-Token': settings.POSTMARK_API_TOKEN,
    }
    data = {
        'From': f'{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>',
        'To': receiver_mail,
        'TemplateAlias': template,
        'TemplateModel': params,
    }
    if settings.EMAIL_REPLY_TO:
        data['ReplyTo'] = settings.EMAIL_REPLY_TO

    if settings.ENVIRONMENT == Environment.TEST:
        return {'status': EmailStatus.SUCCESS}

    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()

    return {'status': EmailStatus.SUCCESS, 'response': response.json()}


class CRUDEmailLog(
    CRUDBase[models.EmailLog, schemas.EmailLogCreate, schemas.EmailLogCreate]
):
    def get_by_email(self, db: Session, email: str) -> List[models.EmailLog]:
        return db.query(self.model).filter(self.model.receiver_email == email).all()

    def send_mail(
        self,
        receiver_mail: str,
        *,
        template: str,
        params: dict,
        send_at: Optional[datetime] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
    ) -> dict:
        if send_at and not entity_type and not entity_id:
            raise ValueError(
                'entity_type and entity_id are required if send_at is provided'
            )

        db = SessionLocal()
        status = EmailStatus.FAILED
        error_message = None

        try:
            if send_at is not None:
                logger.info('Scheduled email to be sent at %s', send_at)
                status = EmailStatus.SCHEDULED
                return {'status': status}

            response_data = _send_mail(
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
                    template=template,
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

    def send_scheduled_mails(self, db: Session):
        scheduled_emails = (
            db.query(self.model)
            .filter(self.model.status == EmailStatus.SCHEDULED)
            .all()
        )
        logger.info('Found %s scheduled emails', len(scheduled_emails))

        for email in scheduled_emails:
            logger.info('Processing email %s, send_at: %s', email.id, email.send_at)
            if email.send_at < current_time():
                try:
                    params = json.loads(email.params)
                    _send_mail(
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
