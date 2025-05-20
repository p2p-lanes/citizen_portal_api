import base64
import json
import re
import time
from datetime import datetime, timedelta
from enum import Enum
from io import BytesIO
from typing import List
from urllib.parse import urlencode, urljoin

import qrcode
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.applications.models import Application
from app.api.attendees.models import Attendee
from app.api.check_in.models import CheckIn
from app.api.email_logs.crud import email_log as email_log_crud
from app.api.email_logs.models import EmailLog
from app.api.email_logs.schemas import EmailAttachment, EmailEvent
from app.api.popup_city.models import PopUpCity
from app.api.products.models import Product
from app.core import models
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logger import logger
from app.core.utils import current_time

POPUP_CITY_SLUG = 'edge-esmeralda'


class EmailTemplate(str, Enum):
    WEEK1 = 'checkin-ee25-week1'
    WEEK2 = 'checkin-ee25-week2'
    WEEK3 = 'checkin-ee25-week3'
    WEEK4 = 'checkin-ee25-week4'
    DAY = 'checkin-ee25-day'

    @classmethod
    def all(cls):
        return [t.value for t in cls]

    @classmethod
    def from_week_number(cls, week_number: int):
        return cls[f'WEEK{week_number}']


def extract_week_number_from_slug(slug: str) -> int:
    match = re.search(r'-?(\d+)', slug)
    if match:
        return int(match.group(1))
    raise ValueError(f'Invalid slug: {slug}')


def generate_qr_base64(data: str) -> str:
    """
    Generate a QR code from the given string and return
    the image as a Base64-encoded PNG.

    :param data: The string to encode in the QR code
    :return: Base64 string of the PNG image
    """
    # 1. Create QR code object
    qr = qrcode.QRCode(
        version=1,  # 1–40, controls size; or use fit=True to auto size
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,  # size of each "box" in pixels
        border=4,  # thickness of the border (in boxes)
    )
    qr.add_data(data)
    qr.make(fit=True)

    # 2. Render to PIL image
    img = qr.make_image(fill_color='black', back_color='white')

    # 3. Save image to memory buffer as PNG
    buffered = BytesIO()
    img.save(buffered, format='PNG')
    img_bytes = buffered.getvalue()

    # 4. Encode to Base64 and return as UTF-8 string
    base64_str = base64.b64encode(img_bytes).decode('utf-8')
    return base64_str


def generate_qr_attachment(check_in_code: str, attendee_name: str):
    logger.info('Generating QR code for %s %s', check_in_code, attendee_name)
    data = json.dumps({'code': check_in_code})
    return EmailAttachment(
        name=f'{attendee_name}.png',
        content_id='cid:qr.png',
        content=generate_qr_base64(data),
        content_type='image/png',
    )


def generate_qr_attachments(attendees: List[Attendee]):
    attachments = []
    for attendee in attendees:
        if attendee.products:
            qr = generate_qr_attachment(attendee.check_in_code, attendee.name)
            attachments.append(qr)
    return attachments


def get_check_in_template(application: Application):
    first_product = None
    for attendee in application.attendees:
        for product in attendee.products:
            if not product.start_date:
                continue
            if not first_product:
                first_product = product
            elif product.start_date < first_product.start_date:
                first_product = product

    if not first_product or first_product.category in ['month', 'patreon']:
        return EmailTemplate.WEEK1
    if first_product.category == 'week':
        week_number = extract_week_number_from_slug(first_product.slug)
        return EmailTemplate.from_week_number(week_number)
    if first_product.category == 'day':
        return EmailTemplate.DAY

    raise ValueError(f'Invalid product category: {first_product.category}')


def _get_virtual_checkin_url(application: Application):
    main_attendee = next(a for a in application.attendees if a.category == 'main')
    params = {
        'application_id': application.id,
        'code': main_attendee.check_in_code,
        'email': application.email,
    }
    url = urljoin(settings.FRONTEND_URL, '/online-checkin') + '?' + urlencode(params)
    logger.info('Virtual checkin URL: %s', url)
    return url


def process_application_for_check_in(application: Application):
    logger.info('Processing application %s %s', application.id, application.email)
    attachments = generate_qr_attachments(application.attendees)

    event = get_check_in_template(application)

    virtual_checkin_url = _get_virtual_checkin_url(application)
    params = {
        'virtual_checkin_url': virtual_checkin_url,
        'first_name': application.first_name,
    }

    logger.info('Sending email %s to %s', event, application.email)

    email_log_crud.send_mail(
        receiver_mail=application.email,
        event=event,
        params=params,
        entity_type='application',
        entity_id=application.id,
        attachments=attachments,
    )

    spouse_attendee = next(
        (a for a in application.attendees if a.category == 'spouse'), None
    )
    if spouse_attendee:
        receiver_mail = spouse_attendee.email
        params['first_name'] = spouse_attendee.name
        logger.info('Sending email %s to spouse %s', event, receiver_mail)
        try:
            email_log_crud.send_mail(
                receiver_mail=receiver_mail,
                event=event,
                params=params,
                entity_type='application',
                entity_id=application.id,
                attachments=attachments,
            )
        except Exception as e:
            logger.error('Error sending email to spouse %s', receiver_mail)
            logger.error(e)


def process_application_for_check_in_reminder(application: Application):
    logger.info('Processing application %s %s', application.id, application.email)
    attachments = generate_qr_attachments(application.attendees)

    virtual_checkin_url = _get_virtual_checkin_url(application)
    params = {'virtual_checkin_url': virtual_checkin_url}

    logger.info('Sending email to %s', application.email)
    email_log_crud.send_mail(
        receiver_mail=application.email,
        event=get_check_in_template(application),
        params=params,
        entity_type='application',
        entity_id=application.id,
        attachments=attachments,
    )


def get_sent_checkin_emails(db: Session):
    logs = (
        db.query(EmailLog.entity_id.distinct())
        .filter(
            EmailLog.template.in_(EmailTemplate.all()),
            EmailLog.entity_type == 'application',
        )
        .all()
    )
    return [log[0] for log in logs]


def has_recent_payment(application: Application):
    return any(
        p.created_at > current_time() - timedelta(hours=1) and p.status == 'approved'
        for p in application.payments
    )


def get_applications_for_check_in(db: Session):
    popup = db.query(PopUpCity).filter(PopUpCity.slug == POPUP_CITY_SLUG).first()
    if not popup:
        raise ValueError('Popup not found')

    popup_id = popup.id
    excluded_application_ids = get_sent_checkin_emails(db)
    logger.info('Excluded application IDs: %s', excluded_application_ids)

    today = current_time()
    five_days_from_now = today + timedelta(days=5)

    applications = (
        db.query(Application)
        .join(Application.attendees)
        .join(Attendee.products)
        .filter(
            Application.popup_city_id == popup_id,
            Application.id.notin_(excluded_application_ids),
            Product.start_date <= five_days_from_now,
        )
        .distinct()
        .all()
    )
    logger.info('Total applications found: %s', len(applications))

    applications = [a for a in applications if not has_recent_payment(a)]

    logger.info('Total applications to process: %s', len(applications))
    logger.info('Applications ids to process: %s', [a.id for a in applications])

    return applications


def check_in_info_and_qr(db: Session):
    logger.info('Starting check in info and QR code generation')
    applications = get_applications_for_check_in(db)
    logger.info('Total applications to process: %s', len(applications))
    for application in applications:
        process_application_for_check_in(application)
    logger.info('Finished check in info and QR code generation')


def get_applications_for_check_in_reminder(db: Session):
    popup = db.query(PopUpCity).filter(PopUpCity.slug == POPUP_CITY_SLUG).first()
    if not popup:
        raise ValueError('Popup not found')

    popup_id = popup.id

    check_in_sent_once = (
        db.query(EmailLog.receiver_email)
        .filter(
            EmailLog.template.in_(EmailTemplate.all()),
            EmailLog.entity_type == 'application',
        )
        .group_by(EmailLog.receiver_email)
        .having(func.count() == 1)
        .all()
    )
    check_in_sent_once = [row[0] for row in check_in_sent_once]

    check_in_completed = (
        db.query(Attendee.application_id)
        .join(CheckIn, Attendee.id == CheckIn.attendee_id)
        .filter(CheckIn.virtual_check_in)
        .distinct()
        .all()
    )
    check_in_completed = [row[0] for row in check_in_completed]

    one_day_from_now = current_time() + timedelta(days=1)

    return (
        db.query(Application)
        .join(Application.attendees)
        .join(Attendee.products)
        .filter(
            Application.popup_city_id == popup_id,
            Application.id.notin_(check_in_completed),
            Application.email.in_(check_in_sent_once),
            Product.start_date <= one_day_from_now,
        )
        .distinct()
        .all()
    )


def check_in_reminder(db: Session):
    logger.info('Starting check in reminder')
    applications = get_applications_for_check_in_reminder(db)
    logger.info('Total applications to process: %s', len(applications))
    for application in applications:
        process_application_for_check_in_reminder(application)
    logger.info('Finished check in reminder')


def main():
    with SessionLocal() as db:
        check_in_info_and_qr(db)
        logger.info('Finished check in info and QR code generation')
        check_in_reminder(db)
        logger.info('Finished check in reminder. Sleeping for 1 hour...')
        time.sleep(1 * 60 * 60)


if __name__ == '__main__':
    main()
