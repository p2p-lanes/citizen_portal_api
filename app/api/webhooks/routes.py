from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.applications.schemas import Application
from app.api.webhooks import schemas
from app.core.database import get_db
from app.core.logger import logger
from app.core.mail import send_mail

router = APIRouter()


@router.post('/send_email', status_code=status.HTTP_201_CREATED)
async def send_email_webhook(
    webhook_payload: schemas.WebhookPayload,
    template: str = Query(..., description='Email template name'),
    fields: str = Query(..., description='Template fields'),
    db: Session = Depends(get_db),
):
    if not webhook_payload.data.rows:
        logger.info('No rows to send email')
        return {'message': 'No rows to send email'}

    fields = [f.strip() for f in fields.split(',')]
    processed_ids = []

    logger.info('Sending email %s to %s rows', template, len(webhook_payload.data.rows))
    logger.info('Fields: %s', fields)

    for row in webhook_payload.data.rows:
        row = row.model_dump()
        if not row.get('email'):
            logger.info('No email to send email. Skipping...')
            continue

        params = {k: v for k, v in row.items() if k in fields}

        send_mail(
            receiver_mail=row['email'],
            template=template,
            params=params,
        )
        processed_ids.append(row['id'])

    if processed_ids:
        if webhook_payload.data.table_name == 'applications':
            db.query(Application).filter(Application.id.in_(processed_ids)).update(
                {Application.sent_mails: Application.sent_mails + [template]},
                synchronize_session=False,
            )
            db.commit()

    return {'message': 'Email sent successfully'}
