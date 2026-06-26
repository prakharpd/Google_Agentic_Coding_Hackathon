"""Utility logger for the project.

This module provides a simple wrapper around the standard :mod:`logging` module that
writes log messages to ``audit.log`` in the project root.  Each log entry is
prefixed with an ISO‑8601 timestamp so that the audit trail is human‑readable
and easy to parse.

The logger is configured as a singleton – calling :func:`get_logger` multiple
times will return the same logger instance.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

# Determine the project root (two levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_FILE = PROJECT_ROOT / "audit.log"

# Configure the root logger only once
_logger: logging.Logger | None = None


def get_logger(name: str = "business-analyst-agent") -> logging.Logger:
    """Return a configured logger.

    Parameters
    ----------
    name:
        Name of the logger.  All modules should use the same name so that
        messages are routed to the same file.
    """
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    # Avoid duplicate handlers if called multiple times
    if not logger.handlers:
        handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    _logger = logger
    return logger


def log_info(message: str) -> None:
    """Convenience wrapper that logs an ``INFO`` level message."""
    get_logger().info(message)


def log_error(message: str) -> None:
    """Convenience wrapper that logs an ``ERROR`` level message."""
    get_logger().error(message)

# If this module is executed directly, write a simple test log.
if __name__ == "__main__":
    log_info("Logger initialized.")
    log_error("This is a test error.")
