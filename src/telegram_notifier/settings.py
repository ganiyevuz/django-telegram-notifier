from __future__ import annotations

import logging
from typing import Any

from django.conf import settings

DEFAULTS: dict[str, Any] = {
    "PROXY": None,
    "MESSAGE_MAX_LENGTH": 4000,
    "ENVIRONMENT": None,
    "STORE_EXCEPTIONS": False,
    "CLEANUP_DAYS": 30,
    "IGNORE_EXCEPTIONS": [],
    "IGNORE_PATHS": [],
    "FILTER": None,
    "CELERY_TASK": None,
}

REQUIRED: set[str] = {"BOT_TOKEN", "CHAT_IDS"}

_default_logger = logging.getLogger("telegram_notifier")


def get_setting(key: str) -> Any:
    user_settings = getattr(settings, "TELEGRAM_NOTIFIER", {})
    if key in user_settings:
        return user_settings[key]
    if key in DEFAULTS:
        return DEFAULTS[key]
    raise KeyError(f"'{key}' is required in TELEGRAM_NOTIFIER settings")


def get_logger() -> Any:
    """Return the configured logger.

    Accepts any object with .debug(), .info(), .warning(), .error()
    methods — stdlib logging, loguru, structlog, or a custom logger.

    Usage in settings.py::

        # stdlib (default)
        TELEGRAM_NOTIFIER = { ... }

        # loguru
        from loguru import logger
        TELEGRAM_NOTIFIER = { ..., "LOGGER": logger }

        # structlog
        import structlog
        TELEGRAM_NOTIFIER = { ..., "LOGGER": structlog.get_logger() }

        # silent (disable logging)
        TELEGRAM_NOTIFIER = { ..., "LOGGER": None }
    """
    user_settings = getattr(settings, "TELEGRAM_NOTIFIER", {})
    if "LOGGER" not in user_settings:
        return _default_logger

    logger = user_settings["LOGGER"]
    if logger is None:
        return _NullLogger()
    return logger


class _NullLogger:
    """No-op logger for when users want to silence all output."""

    def debug(self, *args: Any, **kwargs: Any) -> None:
        pass

    def info(self, *args: Any, **kwargs: Any) -> None:
        pass

    def warning(self, *args: Any, **kwargs: Any) -> None:
        pass

    def error(self, *args: Any, **kwargs: Any) -> None:
        pass

    def critical(self, *args: Any, **kwargs: Any) -> None:
        pass
