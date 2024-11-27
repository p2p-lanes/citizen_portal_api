import json
from datetime import datetime

import jwt

from .config import settings


class Encoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime)):
            return str(o)
        return super().default(o)


def encode(payload: dict) -> str:
    payload['iat'] = datetime.now()
    return jwt.encode(
        payload, settings.SECRET_KEY, algorithm='HS256', json_encoder=Encoder
    )
