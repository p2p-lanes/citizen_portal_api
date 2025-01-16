from datetime import timedelta
from functools import lru_cache

from app.core.cache import WebhookCache


@lru_cache()
def get_webhook_cache() -> WebhookCache:
    return WebhookCache(expiry=timedelta(seconds=2))
