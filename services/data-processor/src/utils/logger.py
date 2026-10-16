"""
CRYPTO VIZ - Data Processor Logger
Structured logging configuration using structlog
"""

import sys
import logging
from typing import Any
import structlog
from structlog.stdlib import LoggerFactory


def setup_logger(name: str, log_level: str = "INFO") -> Any:
    """
    Setup structured logger with consistent formatting

    Args:
        name: Logger name (usually __name__)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured structlog logger
    """
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO)
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger(name)


def get_logger(name: str) -> Any:
    """
    Get a configured logger instance

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return structlog.get_logger(name)
