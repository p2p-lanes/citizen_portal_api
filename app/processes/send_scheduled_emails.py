import time

from app.api.email_logs.crud import email_log
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
