import json
from datetime import datetime, timedelta
from uuid import UUID

import jwt

from .config import settings


class Encoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime, UUID)):
            return str(o)
        return super().default(o)


def encode(payload: dict, *, expires_delta: timedelta = None) -> str:
    payload['iat'] = datetime.now()
    if expires_delta:
        payload['exp'] = datetime.now() + expires_delta
    return jwt.encode(
        payload, settings.SECRET_KEY, algorithm='HS256', json_encoder=Encoder
    )
