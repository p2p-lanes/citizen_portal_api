import urllib.parse
from datetime import timedelta
from functools import wraps
from typing import Any, Callable, Optional

import requests

from app.api.email_logs.crud import email_log
from app.api.email_logs.schemas import EmailLogCreate, EmailStatus
from app.core.database import SessionLocal

from .config import Environment, settings
from .logger import logger
from .utils import encode


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
        auth_url += f'&popup_slug={popup_slug}'
    return auth_url


def send_login_mail(receiver_mail: str, spice: str, citizen_id: int):
    params = {
        'the_url': _generate_authenticate_url(receiver_mail, spice, citizen_id),
        'email': receiver_mail,
    }
    template = 'auth-citizen-portal'
    return send_mail(
        receiver_mail=receiver_mail,
        template=template,
        params=params,
    )


def send_application_accepted_with_ticketing_url(
    receiver_mail: str,
    spice: str,
    citizen_id: int,
    first_name: str,
    popup_slug: str,
    template: str,
):
    ticketing_url = _generate_authenticate_url(
        receiver_mail, spice, citizen_id, popup_slug=popup_slug
    )
    params = {
        'first_name': first_name,
        'ticketing_url': ticketing_url,
    }
    return send_mail(receiver_mail, template=template, params=params)


def send_application_received_mail(receiver_mail: str):
    submission_form_url = urllib.parse.urljoin(settings.FRONTEND_URL, 'portal')
    params = {
        'submission_form_url': submission_form_url,
        'email': receiver_mail,
    }
    return send_mail(receiver_mail, template='application-received', params=params)


def send_payment_confirmed_mail(
    receiver_mail: str,
    first_name: str,
    ticket_list: list[str],
    template: Optional[str] = None,
):
    params = {
        'first_name': first_name,
        'ticket_list': ' - '.join(ticket_list),
    }
    if not template:
        template = 'payment-confirmed'
    return send_mail(receiver_mail, template=template, params=params)


def log_email_send(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(
        receiver_mail: str,
        *,
        template: str,
        params: dict,
        **kwargs: Any,
    ) -> Any:
        db = SessionLocal()
        status = EmailStatus.FAILED
        error_message = None

        try:
            # Execute the original send_mail function
            response_data = func(
                receiver_mail=receiver_mail,
                template=template,
                params=params,
                **kwargs,
            )
            status = EmailStatus.SUCCESS
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
                    error_message=error_message,
                )
                email_log.create(db, obj=email_log_data)
            except Exception as db_error:
                logger.error('Failed to log email: %s', str(db_error))
            finally:
                db.close()

    return wrapper


@log_email_send
def send_mail(
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
        'From': 'Edge City <edgeportal@edgecity.live>',
        'To': receiver_mail,
        'TemplateAlias': template,
        'TemplateModel': params,
    }
    if settings.ENVIRONMENT == Environment.TEST:
        return {}

    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()

    return response.json()
