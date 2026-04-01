# backend/shared/logging.py
import logging
import sys

import structlog


def configure_logging(service_name: str, log_level: str = "INFO") -> None:
    """
    Call once at service startup in main.py lifespan.
    Configures structlog for structured JSON output.
    All subsequent get_logger() calls return a pre-configured bound logger.
    """
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

    # Bind service name to all log calls from this process.
    structlog.contextvars.bind_contextvars(service=service_name)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Usage:
        log = get_logger(__name__)
        log.info("event_name", key=value, ...)
    """
    return structlog.get_logger(name)  # type: ignore[return-value]