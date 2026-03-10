"""
AttackBot shared exception hierarchy.
All custom exceptions are rooted at AttackBotError.
"""


class AttackBotError(Exception):
    """Root exception for all AttackBot errors."""


# ── Scan errors ────────────────────────────────────────────────────────

class ScanError(AttackBotError):
    """A recoverable error during scan execution."""


class ScanTimeoutError(ScanError):
    """A CLI tool or async operation timed out."""


class ScanInternalError(ScanError):
    """An unrecoverable internal error during a scan stage."""


class ScopeFatalError(AttackBotError):
    """
    Scope resolution failed fatally.
    The scan cannot continue without a valid scope definition.
    Always stops the pipeline.
    """


# ── Queue errors ───────────────────────────────────────────────────────

class QueueError(AttackBotError):
    """Base class for all queue-related errors."""


class QueueConnectionError(QueueError):
    """Failed to connect or reconnect to the message broker."""


class QueuePublishError(QueueError):
    """Failed to publish a message to a queue."""


# ── Storage errors ─────────────────────────────────────────────────────

class StorageError(AttackBotError):
    """Failed to read from or write to object storage."""


# ── Collector errors ───────────────────────────────────────────────────

class CollectorError(AttackBotError):
    """Base class for platform collector errors."""


class CollectorRateLimitError(CollectorError):
    """
    Platform API rate limit exhausted after all retries.
    The collector should be retried after a delay.
    """


class CollectorAuthError(CollectorError):
    """
    Platform API authentication failed (401/403).
    Credentials should be checked — retrying will not help.
    """


# ── Schema errors ──────────────────────────────────────────────────────

class MessageSchemaError(AttackBotError):
    """A message payload does not match the expected schema."""
