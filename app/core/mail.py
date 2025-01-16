import urllib.parse
from datetime import datetime, timedelta
from typing import Optional

from app.api.email_logs.crud import email_log

from .config import settings
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
        auth_url += f'&popup={popup_slug}'
    return auth_url


def send_mail(
    receiver_mail: str,
    *,
    template: str,
    params: dict,
    send_at: Optional[datetime] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
):
    logger.info('sending %s email to %s', template, receiver_mail)
    return email_log.send_mail(
        receiver_mail,
        template=template,
        params=params,
        send_at=send_at,
        entity_type=entity_type,
        entity_id=entity_id,
    )


def send_login_mail(
    receiver_mail: str,
    spice: str,
    citizen_id: int,
    popup_slug: Optional[str] = None,
):
    authenticate_url = _generate_authenticate_url(
        receiver_mail, spice, citizen_id, popup_slug
    )
    params = {
        'the_url': authenticate_url,
        'email': receiver_mail,
    }
    template = 'auth-citizen-portal'
    return send_mail(
        receiver_mail=receiver_mail,
        template=template,
        params=params,
        entity_type='citizen',
        entity_id=citizen_id,
    )


def send_application_accepted_with_ticketing_url(
    receiver_mail: str,
    spice: str,
    citizen_id: int,
    first_name: str,
    popup_slug: str,
    template: str,
    *,
    send_at: Optional[datetime] = None,
    application_id: Optional[int] = None,
):
    ticketing_url = _generate_authenticate_url(
        receiver_mail, spice, citizen_id, popup_slug=popup_slug
    )
    params = {
        'first_name': first_name,
        'ticketing_url': ticketing_url,
    }
    return send_mail(
        receiver_mail,
        template=template,
        params=params,
        send_at=send_at,
        entity_type='application',
        entity_id=application_id,
    )


def send_application_received_mail(
    receiver_mail: str,
    *,
    send_at: Optional[datetime] = None,
    application_id: Optional[int] = None,
):
    submission_form_url = urllib.parse.urljoin(settings.FRONTEND_URL, 'portal')
    params = {
        'submission_form_url': submission_form_url,
        'email': receiver_mail,
    }
    return send_mail(
        receiver_mail,
        template='application-received',
        params=params,
        send_at=send_at,
        entity_type='application',
        entity_id=application_id,
    )


def send_payment_confirmed_mail(
    receiver_mail: str,
    first_name: str,
    ticket_list: list[str],
    template: Optional[str] = None,
    *,
    send_at: Optional[datetime] = None,
    application_id: Optional[int] = None,
):
    params = {
        'first_name': first_name,
        'ticket_list': ' - '.join(ticket_list),
    }
    if not template:
        template = 'payment-confirmed'
    return send_mail(
        receiver_mail,
        template=template,
        params=params,
        send_at=send_at,
        entity_type='application',
        entity_id=application_id,
    )
