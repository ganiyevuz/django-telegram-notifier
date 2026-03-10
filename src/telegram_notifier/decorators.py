import asyncio
import functools

from telegram_notifier.report import report_exception


def telegram_exception_notifier(func):
    if asyncio.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                request = args[0] if args else None
                report_exception(exc, request)
                raise

        return async_wrapper

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            request = args[0] if args else None
            report_exception(exc, request)
            raise

    return wrapper
