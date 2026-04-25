"""
Scheduled job to clean up expired idempotency keys.
"""

from backend.shared.db import get_session
from backend.shared.idempotency import IdempotencyService


async def cleanup_expired_idempotency_keys_job():
    """
    Scheduled job to remove expired idempotency keys.
    Runs daily.
    """
    async with get_session() as session:
        service = IdempotencyService(session)
        await service.cleanup_expired()
