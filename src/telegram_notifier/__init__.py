from telegram_notifier.choices import Level, Severity, Status
from telegram_notifier.client import notify_error_via_telegram
from telegram_notifier.decorators import telegram_exception_notifier
from telegram_notifier.message import build_exception_message
from telegram_notifier.middleware import GlobalExceptionReporterMiddleware
from telegram_notifier.report import report_exception


def __getattr__(name):
    if name == "ExceptionLog":
        from telegram_notifier.models import ExceptionLog

        globals()["ExceptionLog"] = ExceptionLog
        return ExceptionLog
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "notify_error_via_telegram",
    "telegram_exception_notifier",
    "build_exception_message",
    "GlobalExceptionReporterMiddleware",
    "ExceptionLog",
    "Level",
    "Severity",
    "Status",
    "report_exception",
]
