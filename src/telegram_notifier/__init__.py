from telegram_notifier.client import notify_error_via_telegram
from telegram_notifier.decorators import telegram_exception_notifier
from telegram_notifier.message import build_exception_message
from telegram_notifier.middleware import GlobalExceptionReporterMiddleware
from telegram_notifier.report import report_exception


def __getattr__(name):
    if name in ("ExceptionLog", "Level", "Severity", "Status"):
        from telegram_notifier.models import ExceptionLog, Level, Severity, Status

        _lazy = {
            "ExceptionLog": ExceptionLog,
            "Level": Level,
            "Severity": Severity,
            "Status": Status,
        }
        globals().update(_lazy)
        return _lazy[name]
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
