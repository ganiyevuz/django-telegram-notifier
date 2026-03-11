from __future__ import annotations

import logging

from django.http import HttpRequest

from telegram_notifier.client import notify_error_via_telegram
from telegram_notifier.message import build_exception_message, build_traceback_content
from telegram_notifier.settings import get_setting

logger = logging.getLogger("telegram_notifier")


def report_exception(
    exc: BaseException,
    request: HttpRequest | None = None,
    body: bytes | None = None,
    level: str | None = None,
    severity: str | None = None,
) -> bool:
    message = build_exception_message(
        exc,
        request=request,
        body=body,
        level=level or "error",
    )
    traceback_content = build_traceback_content(exc)
    sent = notify_error_via_telegram(message, traceback_content=traceback_content)

    if get_setting("STORE_EXCEPTIONS"):
        from telegram_notifier.models import ExceptionLog

        kwargs = {}
        if level:
            kwargs["level"] = level
        if severity:
            kwargs["severity"] = severity

        ExceptionLog.create_from_exception(
            exc, request=request, body=body, is_sent=sent, **kwargs
        )

    return sent
