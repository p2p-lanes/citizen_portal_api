import json
from datetime import timedelta

import requests
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.applications.crud import calculate_status
from app.api.applications.models import Application
from app.api.applications.schemas import ApplicationStatus
from app.api.email_logs.crud import email_log
from app.api.email_logs.models import EmailLog
from app.api.email_logs.schemas import EmailStatus
from app.api.payments.crud import payment as payment_crud
from app.api.payments.schemas import PaymentFilter, PaymentUpdate
from app.api.webhooks import schemas
from app.api.webhooks.dependencies import get_webhook_cache
from app.core.cache import WebhookCache
from app.core.config import settings
from app.core.database import get_db
from app.core.logger import logger
from app.core.security import TokenData
from app.core.utils import current_time

router = APIRouter()


@router.post('/update_status', status_code=status.HTTP_200_OK)
async def update_status_webhook(
    webhook_payload: schemas.WebhookPayload,
    secret: str = Header(..., description='Secret'),
    db: Session = Depends(get_db),
    webhook_cache: WebhookCache = Depends(get_webhook_cache),
):
    rows_str = json.dumps([row.model_dump() for row in webhook_payload.data.rows])
    fingerprint = f'update_status:{webhook_payload.data.table_id}:{rows_str}'
    if not webhook_cache.add(fingerprint):
        logger.info('Webhook already processed. Skipping...')
        return {'message': 'Webhook already processed'}

    logger.info('POST /update_status')
    if secret != settings.NOCODB_WEBHOOK_SECRET:
        logger.info('Secret is not valid. Skipping...')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Secret is not valid',
        )

    if webhook_payload.data.table_name != 'applications':
        logger.info('Table name is not applications. Skipping...')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Table name is not applications',
        )

    table_id = webhook_payload.data.table_id
    url = f'{settings.NOCODB_URL}/api/v2/tables/{table_id}/records'
    headers = {
        'accept': 'application/json',
        'xc-token': settings.NOCODB_TOKEN,
        'Content-Type': 'application/json',
    }
    for row in webhook_payload.data.rows:
        application = db.get(Application, row.id)

        row_dict = row.model_dump()
        reviews_status = row_dict.get('calculated_status')
        current_status = row_dict.get('status')

        group = application.citizen.get_group(application.popup_city_id)
        if group:
            calculated_status = ApplicationStatus.ACCEPTED
            if reviews_status == ApplicationStatus.WITHDRAWN.value:
                calculated_status = ApplicationStatus.WITHDRAWN
            requested_discount = False
        else:
            calculated_status, requested_discount = calculate_status(
                application,
                requires_approval=application.popup_city.requires_approval,
                reviews_status=reviews_status,
            )

        if current_status == calculated_status:
            logger.info('Status is the same as calculated status. Skipping...')
            continue

        email_log.cancel_scheduled_emails(
            db,
            entity_type='application',
            entity_id=row.id,
        )

        data = {
            'id': row.id,
            'status': calculated_status,
            'requested_discount': requested_discount,
        }
        if (
            calculated_status == ApplicationStatus.ACCEPTED
            and application.accepted_at is None
        ):
            data['accepted_at'] = current_time().isoformat()

        logger.info('update_status data: %s', data)
        response = requests.patch(url, headers=headers, json=data)
        logger.info('update_status status code: %s', response.status_code)
        logger.info('update_status response: %s', response.json())

    logger.info('update_status finished')
    return {'message': 'Status updated successfully'}


@router.post('/send_email', status_code=status.HTTP_200_OK)
async def send_email_webhook(
    webhook_payload: schemas.WebhookPayload,
    event: str = Query(..., description='Email event'),
    fields: str = Query(..., description='Template fields'),
    unique: bool = Query(True, description='Verify if the email is unique'),
    delay: int = Query(0, description='Delay in minutes'),
    db: Session = Depends(get_db),
):
    if not webhook_payload.data.rows:
        logger.info('No rows to send email')
        return {'message': 'No rows to send email'}

    fields = [f.strip() for f in fields.split(',')]
    processed_ids = []

    logger.info('Sending email %s to %s rows', event, len(webhook_payload.data.rows))
    logger.info('Fields: %s', fields)
    send_at = current_time() + timedelta(minutes=delay) if delay else None

    for row in webhook_payload.data.rows:
        row = row.model_dump()
        if not row.get('email'):
            logger.info('No email to send email. Skipping...')
            continue

        params = {k: v for k, v in row.items() if k in fields}
        if 'ticketing_url' not in params:
            params['ticketing_url'] = settings.FRONTEND_URL

        application = db.get(Application, row['id'])

        if unique:
            exists_email_log = (
                db.query(EmailLog)
                .filter(
                    EmailLog.entity_id == application.id,
                    EmailLog.entity_type == 'application',
                    EmailLog.event == event,
                    EmailLog.status == EmailStatus.SUCCESS,
                )
                .first()
            )
            if exists_email_log:
                logger.info('Email already sent')
                continue

        if send_at:
            # Cancel any existing scheduled emails since only one can be active per application
            logger.info('Cancelling scheduled emails')
            email_log.cancel_scheduled_emails(
                db,
                entity_type='application',
                entity_id=application.id,
            )

        params['ticketing_url'] = email_log.generate_authenticate_url(db, application)
        params['first_name'] = application.first_name
        email_log.send_mail(
            receiver_mail=row['email'],
            event=event,
            popup_city=application.popup_city,
            params=params,
            send_at=send_at,
            entity_type='application',
            entity_id=application.id,
        )

        processed_ids.append(row['id'])

    return {'message': 'Email sent successfully'}


@router.post('/simplefi', status_code=status.HTTP_200_OK)
async def simplefi_webhook(
    webhook_payload: schemas.SimplefiWebhookPayload,
    db: Session = Depends(get_db),
    webhook_cache: WebhookCache = Depends(get_webhook_cache),
):
    payment_request_id = webhook_payload.data.payment_request.id
    event_type = webhook_payload.event_type

    fingerprint = f'simplefi:{payment_request_id}:{event_type}'
    if not webhook_cache.add(fingerprint):
        logger.info('Webhook already processed. Skipping...')
        return {'message': 'Webhook already processed'}

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
    rate = 1
    if webhook_payload.data.new_payment:
        currency = webhook_payload.data.new_payment.coin
        for t in webhook_payload.data.payment_request.transactions:
            if t.coin == currency:
                rate = t.price_details.rate
                break

    user = TokenData(citizen_id=payment.application.citizen_id, email='')

    if payment_request_status == 'approved':
        payment_crud.approve_payment(
            db, payment, currency=currency, rate=rate, user=user
        )
    else:
        payment_crud.update(db, payment.id, PaymentUpdate(status='expired'), user)

    return {'message': 'Payment status updated successfully'}
