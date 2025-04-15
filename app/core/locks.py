import hashlib
from contextlib import contextmanager
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.logger import logger


def _calculate_lock_id(name: str) -> int:
    return int.from_bytes(hashlib.md5(name.encode()).digest()[:4], 'big')


class DistributedLock:
    """
    A distributed lock implementation using PostgreSQL advisory locks.
    This ensures that only one process across all FastAPI workers can acquire the lock.
    """

    def __init__(self, name: str):
        # Convert lock name to a 32-bit integer using hash
        self.lock_id = _calculate_lock_id(name)
        logger.info('Created lock %s with ID %s', name, self.lock_id)

    @contextmanager
    def acquire(self, db: Session, timeout_seconds: Optional[int] = 10):
        """
        Acquire a distributed lock using PostgreSQL advisory locks.
        If timeout_seconds is None, it will wait indefinitely.
        """
        timeout_clause = (
            f'TIMEOUT {timeout_seconds * 1000}' if timeout_seconds is not None else ''
        )
        acquired = False

        try:
            # Try to acquire the advisory lock
            result = db.execute(
                text(f'SELECT pg_try_advisory_lock({self.lock_id}) {timeout_clause}')
            ).scalar()

            acquired = bool(result)
            if not acquired:
                logger.warning(
                    f'Failed to acquire lock {self.lock_id} after {timeout_seconds}s'
                )
                raise TimeoutError(
                    f'Could not acquire lock within {timeout_seconds} seconds'
                )

            logger.debug(f'Acquired lock {self.lock_id}')
            yield

        finally:
            if acquired:
                # Release the lock
                db.execute(text(f'SELECT pg_advisory_unlock({self.lock_id})'))
                logger.debug(f'Released lock {self.lock_id}')
