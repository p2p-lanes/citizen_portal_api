from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, Tuple


class WebhookCache:
    def __init__(self, expiry: timedelta = timedelta(hours=24)):
        self._cache: Dict[str, Tuple[datetime, str]] = {}
        self._expiry = expiry
        self._lock = Lock()

    def exists(self, fingerprint: str) -> bool:
        """Check if fingerprint exists and is not expired in a thread-safe manner"""
        with self._lock:
            self._clean_expired()
            return fingerprint in self._cache

    def add(self, fingerprint: str) -> bool:
        """
        Add fingerprint to cache if it doesn't exist.
        Returns True if fingerprint was added, False if it already existed.
        """
        with self._lock:
            self._clean_expired()
            if fingerprint in self._cache:
                return False
            self._cache[fingerprint] = datetime.utcnow()
            return True

    def _clean_expired(self) -> None:
        """Remove expired fingerprints - already protected by lock in public methods"""
        current_time = datetime.utcnow()
        expired = [
            k
            for k, timestamp in self._cache.items()
            if current_time - timestamp > self._expiry
        ]
        for key in expired:
            del self._cache[key]
