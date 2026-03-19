from telegram_notifier.choices import Level, Severity, Status
from telegram_notifier.client import notify_error_via_telegram
from telegram_notifier.decorators import telegram_exception_notifier
from telegram_notifier.message import build_exception_message, build_traceback_content
from telegram_notifier.middleware import GlobalExceptionReporterMiddleware
from telegram_notifier.report import report_exception
from telegram_notifier.utils import classify_exception

__version__ = "0.2.0"


def __getattr__(name: str) -> type:
    if name == "ExceptionLog":
        from telegram_notifier.models import ExceptionLog

        globals()["ExceptionLog"] = ExceptionLog
        return ExceptionLog
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "notify_error_via_telegram",
    "telegram_exception_notifier",
    "build_exception_message",
    "build_traceback_content",
    "GlobalExceptionReporterMiddleware",
    "ExceptionLog",
    "Level",
    "Severity",
    "Status",
    "report_exception",
    "classify_exception",
]
