import logging

from telegram_notifier.client import notify_error_via_telegram
from telegram_notifier.message import build_exception_message
from telegram_notifier.settings import get_setting

logger = logging.getLogger("telegram_notifier")


def report_exception(exc, request=None, body=None, level=None, severity=None):
    message = build_exception_message(exc, request=request, body=body)
    sent = notify_error_via_telegram(message)

    if get_setting("STORE_EXCEPTIONS"):
        from telegram_notifier.models import ExceptionLog

        kwargs = {}
        if level:
            kwargs["level"] = level
        if severity:
            kwargs["severity"] = severity

        log = ExceptionLog.create_from_exception(
            exc, request=request, body=body, **kwargs
        )
        log.is_sent = sent
        log.save(update_fields=["is_sent"])

    return sent
