from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable
from typing import TypeVar

from telegram_notifier.report import report_exception

F = TypeVar("F", bound=Callable)


def telegram_exception_notifier(func: F) -> F:
    if asyncio.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                request = args[0] if args else None
                report_exception(exc, request)
                raise

        return async_wrapper  # type: ignore[return-value]

    @functools.wraps(func)
    def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            request = args[0] if args else None
            report_exception(exc, request)
            raise

    return wrapper  # type: ignore[return-value]
