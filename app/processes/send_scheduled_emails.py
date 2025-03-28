import time

from app.api.attendees.models import Attendee
from app.api.applications.models import Application
from app.api.citizens.models import Citizen
from app.api.email_logs.crud import email_log
from app.api.organizations.models import Organization
from app.api.payments.models import Payment, PaymentProduct
from app.api.popup_city.models import PopUpCity
from app.api.products.models import Product
from app.core.database import SessionLocal
from app.core.logger import logger


def send_scheduled_emails():
    logger.info('Sending scheduled emails')
    with SessionLocal() as db:
        email_log.send_scheduled_mails(db)
    logger.info('Scheduled emails sent successfully')


if __name__ == '__main__':
    send_scheduled_emails()
    time.sleep(30)
