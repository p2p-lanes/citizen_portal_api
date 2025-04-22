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
        acquired = False
        original_lock_timeout = None

        try:
            if timeout_seconds is not None:
                # Store original lock_timeout and set the new one
                try:
                    original_lock_timeout_result = db.execute(
                        text('SHOW lock_timeout')
                    ).scalar()
                    # Convert timeout like '10s' to milliseconds '10000ms' if needed, or handle plain integer '0'
                    if isinstance(
                        original_lock_timeout_result, str
                    ) and original_lock_timeout_result.endswith('ms'):
                        original_lock_timeout = original_lock_timeout_result
                    elif isinstance(
                        original_lock_timeout_result, str
                    ) and original_lock_timeout_result.endswith('s'):
                        original_lock_timeout = (
                            f'{int(original_lock_timeout_result[:-1]) * 1000}ms'
                        )
                    else:  # Default or '0' case
                        original_lock_timeout = (
                            '0ms'  # PostgreSQL default is 0 (no timeout)
                        )

                    new_timeout_ms = timeout_seconds * 1000
                    db.execute(text(f"SET LOCAL lock_timeout = '{new_timeout_ms}ms'"))
                    logger.debug(
                        f'Set LOCAL lock_timeout to {new_timeout_ms}ms for lock {self.lock_id}'
                    )

                    # Try to acquire the advisory lock (will respect lock_timeout)
                    result = db.execute(
                        text(f'SELECT pg_try_advisory_lock({self.lock_id})')
                    ).scalar()

                finally:
                    # Always reset lock_timeout to its original value for the session
                    if original_lock_timeout is not None:
                        db.execute(
                            text(f"SET LOCAL lock_timeout = '{original_lock_timeout}'")
                        )
                        logger.debug(
                            f'Reset LOCAL lock_timeout to {original_lock_timeout} for lock {self.lock_id}'
                        )

            else:
                # If no timeout specified, use regular advisory lock which waits indefinitely
                # Ensure no prior lock_timeout is set or reset it explicitly if needed.
                # Setting to 0 ensures it waits indefinitely.
                db.execute(text("SET LOCAL lock_timeout = '0ms'"))
                result = db.execute(
                    text(f'SELECT pg_try_advisory_lock({self.lock_id})')
                ).scalar()

            acquired = bool(result)
            if not acquired:
                # Use a more specific error or log if timeout was expected
                error_message = f'Failed to acquire lock {self.lock_id}'
                if timeout_seconds is not None:
                    error_message += f' within {timeout_seconds} seconds timeout'
                logger.warning(error_message)
                # Raising TimeoutError might still be appropriate,
                # or a custom LockAcquisitionError could be used.
                raise TimeoutError(error_message)

            logger.debug(f'Acquired lock {self.lock_id}')
            yield

        finally:
            if acquired:
                # Release the lock
                db.execute(text(f'SELECT pg_advisory_unlock({self.lock_id})'))
                logger.debug(f'Released lock {self.lock_id}')

            # Ensure timeout is reset if acquisition failed before yield but after setting timeout
            elif original_lock_timeout is not None:
                try:
                    db.execute(
                        text(f"SET LOCAL lock_timeout = '{original_lock_timeout}'")
                    )
                    logger.debug(
                        f'Reset LOCAL lock_timeout to {original_lock_timeout} after failed acquisition for lock {self.lock_id}'
                    )
                except Exception as e:
                    # Log error if resetting timeout fails, but don't overshadow original error
                    logger.error(f'Failed to reset lock_timeout: {e}')
