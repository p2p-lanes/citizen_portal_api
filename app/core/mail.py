import base64
import re
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Optional

import mailchimp_transactional
from mailchimp_transactional.api_client import ApiClientError

from .config import settings
from .exceptions.mail_exceptions import ErrorMail, InvalidMail, RejectedMail
from .logger import logger
from .utils import encode

mailchimp = mailchimp_transactional.Client(settings.MAILCHIMP_KEY)


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
        'festival_name': 'Citizen Portal',
    }
    template = 'auth_citizen_portal'
    return send_mail(
        receiver_mail=receiver_mail,
        template=template,
        params=params,
    )


def send_mail(
    receiver_mail: str,
    *,
    template: str,
    params: dict,
    subject: Optional[str] = None,
    files_attachments: Optional[List[str]] = None,
    from_name: Optional[str] = None,
    send_at: Optional[datetime] = None,
    cc: Optional[List[str]] = None,
):
    logger.info('sending %s email to %s', template, receiver_mail)
    global_merge_vars = [{'name': k, 'content': v} for k, v in params.items()]

    attachment = []
    if files_attachments is not None:
        for file in files_attachments:
            with open(file['path'], 'rb') as f:
                file_content = base64.b64encode(f.read()).decode('utf-8')

            attachment.append(
                {
                    'content': file_content,
                    'name': re.split(r'[\\/]', file['name']).pop(),
                    'type': file.get('type', 'application/pdf'),
                }
            )

    cc = cc if cc else []
    send_to = [{'email': receiver_mail, 'type': 'cc'}] + [
        {'email': email, 'type': 'cc'} for email in cc
    ]

    msg = {
        'from_email': 'no-reply@edgecity.live',
        'from_name': from_name,
        'to': send_to,
        'preserve_recipients': True,
        'global_merge_vars': global_merge_vars,
        'attachments': attachment,
    }
    if subject:
        msg['subject'] = subject
    body = {'template_name': template, 'template_content': [], 'message': msg}
    if send_at:
        body['send_at'] = send_at.strftime('%Y-%m-%d %H:%M:%S')

    try:
        response = mailchimp.messages.send_template(body)
    except ApiClientError as error:
        raise ErrorMail(detail=error.text) from error
    except Exception as e:
        raise ErrorMail() from e

    assert isinstance(response, list)

    if response[0]['status'] == 'invalid':
        raise InvalidMail()
    if response[0]['status'] == 'rejected':
        raise RejectedMail(reason=response[0]['reject_reason'])

    return response[0]
