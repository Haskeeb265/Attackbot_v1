"""
Idempotency service for message processing.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Callable
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.models.idempotency import IdempotencyKey
from backend.shared.logging import get_logger

logger = get_logger(__name__)


class IdempotencyService:
    """
    Service for ensuring idempotent message processing.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def check_and_record(
        self,
        event_id: str,
        service: str,
        operation: str,
        entity_id: Optional[UUID] = None
    ) -> Optional[IdempotencyKey]:
        """
        Check if message has already been processed.
        
        Args:
            event_id: Unique event ID from MessageEnvelope
            service: Service name (e.g., "core_engine", "reporter")
            operation: Operation name (e.g., "scan.start", "report.generate")
            entity_id: Optional related entity ID
        
        Returns:
            Existing IdempotencyKey if message already processed, None otherwise
        """
        # Check for existing key
        result = await self.session.execute(
            select(IdempotencyKey)
            .where(IdempotencyKey.key == event_id)
            .where(IdempotencyKey.service == service)
            .where(IdempotencyKey.operation == operation)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            logger.info(
                "Idempotent message detected - returning cached response",
                event_id=event_id,
                service=service,
                operation=operation,
                original_processed_at=existing.created_at.isoformat()
            )
            return existing
        
        # Record new key
        key = IdempotencyKey(
            key=event_id,
            service=service,
            operation=operation,
            entity_id=entity_id,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            response=None  # Will be updated after processing
        )
        
        self.session.add(key)
        await self.session.commit()
        
        logger.info(
            "Recorded idempotency key",
            event_id=event_id,
            service=service,
            operation=operation
        )
        
        return None
    
    async def store_response(
        self,
        event_id: str,
        response: Dict[str, Any]
    ):
        """
        Store response for cached replay.
        
        Args:
            event_id: Unique event ID
            response: Response data to cache
        """
        result = await self.session.execute(
            select(IdempotencyKey)
            .where(IdempotencyKey.key == event_id)
        )
        key = result.scalar_one_or_none()
        
        if key:
            key.response = response
            await self.session.commit()
            
            logger.info(
                "Stored idempotent response",
                event_id=event_id,
                response_keys=list(response.keys())
            )
    
    async def cleanup_expired(self):
        """
        Remove expired idempotency keys.
        Called periodically by scheduler.
        """
        cutoff = datetime.now(timezone.utc)
        
        result = await self.session.execute(
            delete(IdempotencyKey)
            .where(IdempotencyKey.expires_at < cutoff)
        )
        
        deleted_count = result.rowcount
        await self.session.commit()
        
        if deleted_count > 0:
            logger.info(
                "Cleaned up expired idempotency keys",
                count=deleted_count,
                cutoff=cutoff.isoformat()
            )


async def with_idempotency(
    event_id: str,
    service: str,
    operation: str,
    handler: Callable,
    session: AsyncSession,
    entity_id: Optional[UUID] = None
) -> Any:
    """
    Decorator-style wrapper for idempotent message processing.
    
    Usage:
        async def process_scan_message(envelope):
            async with get_session() as session:
                result = await with_idempotency(
                    event_id=envelope.event_id,
                    service="core_engine",
                    operation="scan.execute",
                    handler=lambda: _do_scan(envelope),
                    session=session
                )
                return result
    
    Args:
        event_id: Unique event ID
        service: Service name
        operation: Operation name
        handler: Async function to execute if message not yet processed
        session: Database session
        entity_id: Optional related entity ID
    
    Returns:
        Handler result or cached response
    """
    idempotency = IdempotencyService(session)
    
    # Check for duplicate
    cached = await idempotency.check_and_record(
        event_id=event_id,
        service=service,
        operation=operation,
        entity_id=entity_id
    )
    
    if cached is not None:
        return cached.response if cached.response else None
    
    # Process message
    result = await handler()
    
    # Cache response
    if isinstance(result, dict):
        await idempotency.store_response(event_id, result)
    
    return result
