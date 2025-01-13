from typing import Optional

import requests

from app.core.config import settings
from app.core.logger import logger


def create_payment(
    amount: float,
    *,
    simplefi_api_key: str,
    reference: Optional[dict] = None,
) -> dict:
    logger.info(f'Creating payment for amount: {amount}')
    body = {
        'amount': amount,
        'currency': 'USD',
        'reference': reference if reference else {},
        'memo': 'Citizen Portal Payment',
    }
    response = requests.post(
        f'{settings.SIMPLEFI_API_URL}/payment_requests',
        json=body,
        headers={'Authorization': f'Bearer {simplefi_api_key}'},
    )
    response.raise_for_status()
    return response.json()
