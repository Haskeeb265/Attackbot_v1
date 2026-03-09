# backend/shared/exceptions.py


class AttackBotError(Exception):
    """Base exception for all AttackBot errors."""


# ── Scan lifecycle ─────────────────────────────────────────────────────────

class ScanError(AttackBotError):
    """Non-fatal scan stage failure. Scan continues as partial."""


class ScanTimeoutError(ScanError):
    """A CLI tool or external request exceeded its timeout."""


class ScopeFatalError(AttackBotError):
    """Stage 0 fatal: scope cannot be resolved. Scan must abort."""


class ScanInternalError(AttackBotError):
    """Stage 10 fatal: aggregation failed. Data integrity at risk."""


class ScanAuthError(AttackBotError):
    """Browser session bootstrap failed critically."""


# ── Infrastructure ─────────────────────────────────────────────────────────

class QueueError(AttackBotError):
    """RabbitMQ publish/consume failure."""


class QueueConnectionError(QueueError):
    """Cannot establish RabbitMQ connection."""


class StorageError(AttackBotError):
    """MinIO read/write failure."""


# ── Platform collectors ────────────────────────────────────────────────────

class CollectorError(AttackBotError):
    """Generic platform scraping failure."""


class CollectorRateLimitError(CollectorError):
    """Platform returned HTTP 429 after all retries."""


class CollectorAuthError(CollectorError):
    """Platform API credentials rejected."""


# ── Schema ─────────────────────────────────────────────────────────────────

class MessageSchemaError(AttackBotError):
    """Incoming queue message failed schema validation."""