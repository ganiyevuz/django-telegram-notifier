import functools

from telegram_notifier.report import report_exception


def telegram_exception_notifier(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            request = args[0] if args else None
            report_exception(exc, request)
            raise

    return wrapper
