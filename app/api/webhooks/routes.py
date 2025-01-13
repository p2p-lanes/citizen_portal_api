from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.applications.models import Application
from app.api.citizens.crud import create_spice
from app.api.email_logs.models import EmailLog
from app.api.email_logs.schemas import EmailStatus
from app.api.payments.crud import payment as payment_crud
from app.api.payments.schemas import PaymentFilter, PaymentUpdate
from app.api.popup_city.models import EmailTemplate
from app.api.webhooks import schemas
from app.core.config import settings
from app.core.database import get_db
from app.core.logger import logger
from app.core.mail import send_application_accepted_with_ticketing_url, send_mail
from app.core.security import TokenData

router = APIRouter()


@router.post('/send_email', status_code=status.HTTP_200_OK)
async def send_email_webhook(
    webhook_payload: schemas.WebhookPayload,
    template: str = Query(..., description='Email template name'),
    fields: str = Query(..., description='Template fields'),
    unique: bool = Query(True, description='Verify if the email is unique'),
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

        application = db.get(Application, row['id'])
        email_template = (
            db.query(EmailTemplate)
            .filter(
                EmailTemplate.popup_city_id == application.popup_city_id,
                EmailTemplate.event == template,
            )
            .first()
        )
        if email_template:
            logger.info('Email template found %s', email_template.template)
            _template = email_template.template

        if unique:
            email_log = (
                db.query(EmailLog)
                .filter(
                    EmailLog.receiver_email == row['email'],
                    EmailLog.template == _template,
                    EmailLog.status == EmailStatus.SUCCESS,
                )
                .first()
            )
            if email_log:
                logger.info('Email already sent')
                continue

        application_approved = template.startswith('application-approved')
        if application_approved:
            citizen = application.citizen
            logger.info('Citizen %s', citizen.id)
            if not citizen.spice:
                citizen.spice = create_spice()
                db.commit()

            send_application_accepted_with_ticketing_url(
                receiver_mail=row['email'],
                spice=citizen.spice,
                citizen_id=citizen.id,
                first_name=citizen.first_name,
                popup_slug=application.popup_city.slug,
                template=_template,
            )
        else:
            send_mail(
                receiver_mail=row['email'],
                template=_template,
                params=params,
            )

        processed_ids.append(row['id'])

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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Event type is not new_payment or new_card_payment',
        )

    payments = payment_crud.find(
        db, filters=PaymentFilter(external_id=payment_request_id)
    )
    if not payments:
        logger.info('Payment not found')
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Payment not found',
        )

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
        payment_crud.update(db, payment.id, PaymentUpdate(status='expired'), user)

    return {'message': 'Payment status updated successfully'}
