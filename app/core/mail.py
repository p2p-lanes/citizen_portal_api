import urllib.parse
from datetime import timedelta

import requests

from .config import settings
from .logger import logger
from .utils import encode


def _generate_authenticate_url(receiver_mail: str, spice: str, citizen_id: int):
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
    return urllib.parse.urljoin(settings.FRONTEND_URL, f'/auth?token_url={token_url}')


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


def send_application_received_mail(receiver_mail: str):
    submission_form_url = urllib.parse.urljoin(settings.FRONTEND_URL, 'portal')
    params = {
        'submission_form_url': submission_form_url,
        'email': receiver_mail,
    }
    return send_mail(receiver_mail, template='application-received', params=params)


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
        'From': 'Edge City <no-reply@edgecity.live>',
        'To': receiver_mail,
        'TemplateAlias': template,
        'TemplateModel': params,
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()
