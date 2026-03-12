"""
AttackBot shared exception hierarchy.

All exceptions root at AttackBotError.
New exception types must be added here and nowhere else.
"""


class AttackBotError(Exception):
    """Root exception for all AttackBot errors."""


# ---------------------------------------------------------------------------
# Infrastructure errors
# ---------------------------------------------------------------------------

class DatabaseError(AttackBotError):
    """Raised when a database operation fails unexpectedly."""


class QueueError(AttackBotError):
    """Raised when a message queue operation fails."""

class QueueConnectionError(QueueError):
    """Raised when a connection to the message queue cannot be established."""


class StorageError(AttackBotError):
    """Raised when an object storage operation fails."""


class VaultError(AttackBotError):
    """Raised when a secrets vault operation fails."""


# ---------------------------------------------------------------------------
# Scraper / Collector errors
# ---------------------------------------------------------------------------

class CollectorError(AttackBotError):
    """Base class for all collector errors."""


class CollectorRateLimitError(CollectorError):
    """
    Raised when a platform API returns 429 Too Many Requests and all
    retry attempts have been exhausted.
    """


class CollectorAuthError(CollectorError):
    """
    Raised when a platform API returns 401 or 403.
    Indicates bad credentials — will not be retried.
    """


class CollectorNotFoundError(CollectorError):
    """Raised when a requested program handle does not exist on the platform."""


# ---------------------------------------------------------------------------
# Scan / Pipeline errors
# ---------------------------------------------------------------------------

class ScanError(AttackBotError):
    """Raised when a scan pipeline stage fails."""


class ScanTimeoutError(ScanError):
    """Raised when a scan pipeline stage exceeds its timeout."""


class ScopeViolationError(ScanError):
    """
    Raised when an asset or operation would go out of scope.
    This is a hard failure — never demoted to a warning.
    """


class StageError(ScanError):
    """Raised when a specific pipeline stage encounters a fatal error."""


# ---------------------------------------------------------------------------
# Reporting errors
# ---------------------------------------------------------------------------

class ReportError(AttackBotError):
    """Raised when report generation fails."""


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

class ValidationError(AttackBotError):
    """Raised when input data fails validation."""


class SchemaError(AttackBotError):
    """Raised when a message envelope or schema is malformed."""