import time
import urllib.parse
from typing import Optional

import requests

from app.core.config import settings
from app.core.logger import logger


def _create_payment_request(body: dict, simplefi_api_key: str):
    def post_request():
        return requests.post(
            f'{settings.SIMPLEFI_API_URL}/payment_requests',
            json=body,
            headers={'Authorization': f'Bearer {simplefi_api_key}'},
            timeout=10,
        )

    response = post_request()
    logger.info('Simplefi response status: %s', response.status_code)

    if response.status_code >= 400:
        logger.error('Simplefi error, retrying...')
        time.sleep(5)
        response = post_request()
        logger.info('Simplefi response status (retry): %s', response.status_code)

    response.raise_for_status()
    return response.json()


def create_payment(
    amount: float,
    *,
    simplefi_api_key: str,
    reference: Optional[dict] = None,
) -> dict:
    logger.info(f'Creating payment for amount: {amount}')
    notification_url = urllib.parse.urljoin(settings.BACKEND_URL, 'webhooks/simplefi')
    body = {
        'amount': amount,
        'currency': 'USD',
        'reference': reference if reference else {},
        'memo': 'Citizen Portal Payment',
        'notification_url': notification_url,
    }
    return _create_payment_request(body, simplefi_api_key)
