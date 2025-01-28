import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from .config import settings


class Encoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime, UUID)):
            return str(o)
        return super().default(o)


def encode(payload: dict, *, expires_delta: timedelta = None) -> str:
    payload['iat'] = current_time()
    if expires_delta:
        payload['exp'] = current_time() + expires_delta
    return jwt.encode(
        payload, settings.SECRET_KEY, algorithm='HS256', json_encoder=Encoder
    )


def current_time() -> datetime:
    return datetime.now(timezone.utc)
