from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import case, or_
from sqlalchemy.orm import Session

from app.api.applications.models import Application
from app.api.payments.crud import payment as payment_crud
from app.api.payments.schemas import PaymentFilter
from app.api.webhooks import schemas
from app.core.config import settings
from app.core.database import get_db
from app.core.logger import logger
from app.core.mail import send_mail
from app.core.security import TokenData

router = APIRouter()


@router.post('/send_email', status_code=status.HTTP_200_OK)
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
        if 'ticketing_url' not in params:
            params['ticketing_url'] = settings.FRONTEND_URL

        send_mail(
            receiver_mail=row['email'],
            template=template,
            params=params,
        )
        processed_ids.append(row['id'])

    if processed_ids:
        if webhook_payload.data.table_name == 'applications':
            db.query(Application).filter(Application.id.in_(processed_ids)).update(
                {
                    Application.sent_mails: case(
                        (
                            or_(
                                Application.sent_mails.is_(None),
                                Application.sent_mails == '',
                            ),
                            template,
                        ),
                        else_=Application.sent_mails + ',' + template,
                    )
                },
                synchronize_session=False,
            )
            db.commit()

    return {'message': 'Email sent successfully'}


@router.post('/simplefi', status_code=status.HTTP_200_OK)
async def simplefi_webhook(
    webhook_payload: schemas.SimplefiWebhookPayload,
    db: Session = Depends(get_db),
):
    payment_request_id = webhook_payload.data.payment_request.id
    event_type = webhook_payload.event_type
    logger.info(
        'Payment request id: %s, event type: %s', payment_request_id, event_type
    )
    if event_type not in ['new_payment', 'new_card_payment']:
        logger.info('Event type is not new_payment or new_card_payment. Skipping...')
        return {'message': 'Event type is not new_payment or new_card_payment'}

    payments = payment_crud.find(
        db, filters=PaymentFilter(external_id=payment_request_id)
    )
    if not payments:
        logger.info('Payment not found')
        return {'message': 'Payment not found'}

    payment = payments[0]
    payment_request_status = webhook_payload.data.payment_request.status

    if payment.status == payment_request_status:
        logger.info('Payment status is the same as payment request status. Skipping...')
        return {'message': 'Payment status is the same as payment request status'}

    currency = 'USD'
    if webhook_payload.data.new_payment:
        currency = webhook_payload.data.new_payment.coin
    user = TokenData(citizen_id=payment.application.citizen_id, email='')

    if payment_request_status == 'approved':
        payment_crud.approve_payment(db, payment, currency=currency, user=user)
    else:
        logger.info('Payment status is not approved. Skipping...')
        return {'message': 'Payment status is not approved'}

    return {'message': 'Payment status updated successfully'}
