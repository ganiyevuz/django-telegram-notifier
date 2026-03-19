from __future__ import annotations

import threading

from django.http import HttpRequest

from telegram_notifier.client import notify_error_via_telegram
from telegram_notifier.message import build_exception_message, build_traceback_content
from telegram_notifier.settings import get_logger, get_setting
from telegram_notifier.utils import classify_exception


def _should_report(
    exc: BaseException,
    request: HttpRequest | None,
) -> bool:
    """Check ignore rules. Returns False if the exception should be skipped."""
    # Check IGNORE_EXCEPTIONS
    ignore_classes: list[str] = get_setting("IGNORE_EXCEPTIONS")
    if ignore_classes:
        exc_names = {cls.__name__ for cls in type(exc).__mro__}
        if exc_names & set(ignore_classes):
            return False

    # Check IGNORE_PATHS
    ignore_paths: list[str] = get_setting("IGNORE_PATHS")
    if ignore_paths and request and hasattr(request, "path"):
        for prefix in ignore_paths:
            if request.path.startswith(prefix):
                return False

    # Check custom FILTER callable
    custom_filter = get_setting("FILTER")
    if custom_filter is not None:
        return bool(custom_filter(exc, request))

    return True


def _do_report(
    exc_class_name: str,
    exc_message: str,
    message: str,
    traceback_content: str,
    effective_level: str,
    effective_severity: str,
    request_data: dict | None,
    body: bytes | None,
) -> None:
    """Actual reporting work — runs in a background thread."""
    logger = get_logger()

    try:
        sent = notify_error_via_telegram(
            message, traceback_content=traceback_content,
        )
    except Exception as e:
        logger.error(
            "telegram_notifier: failed to send: %s", e,
        )
        sent = False

    if get_setting("STORE_EXCEPTIONS"):
        try:
            from telegram_notifier.models import ExceptionLog

            kwargs = {
                "exception_class": exc_class_name,
                "message": exc_message,
                "traceback": traceback_content,
                "level": effective_level,
                "severity": effective_severity,
                "is_sent": sent,
            }
            if request_data:
                kwargs.update(request_data)

            import socket

            kwargs["hostname"] = socket.gethostname()
            kwargs["environment"] = get_setting("ENVIRONMENT") or ""

            ExceptionLog.objects.create(**kwargs)
        except Exception as e:
            logger.error(
                "telegram_notifier: failed to store: %s", e,
            )


def _extract_request_data(
    request: HttpRequest | None,
    body: bytes | None,
) -> dict | None:
    """Extract serializable request data before the request object is recycled."""
    if not request or not hasattr(request, "path"):
        return None

    from django.http import QueryDict

    from telegram_notifier.utils import (
        _get_client_ip,
        _get_filtered_headers,
        _get_view_name,
    )

    body_str = ""
    if body:
        try:
            body_str = body.decode("utf-8")
        except (UnicodeDecodeError, AttributeError):
            body_str = "[binary data]"

    user_info = ""
    try:
        if hasattr(request, "user") and request.user.is_authenticated:
            user_info = str(request.user)
    except Exception:
        pass

    return {
        "path": request.path,
        "method": request.method,
        "query_params": dict(
            QueryDict(request.META.get("QUERY_STRING", "")).lists(),
        ),
        "body": body_str,
        "user_info": user_info,
        "ip_address": _get_client_ip(request),
        "headers": _get_filtered_headers(request),
        "view_name": _get_view_name(request),
    }


def report_exception(
    exc: BaseException,
    request: HttpRequest | None = None,
    body: bytes | None = None,
    level: str | None = None,
    severity: str | None = None,
) -> bool:
    logger = get_logger()

    if not _should_report(exc, request):
        logger.debug(
            "Skipped reporting %s (filtered)",
            type(exc).__name__,
        )
        return False

    auto_level, auto_severity = classify_exception(exc)
    effective_level = level or auto_level
    effective_severity = severity or auto_severity

    # Build message and extract request data while request is still alive
    message = build_exception_message(
        exc,
        request=request,
        body=body,
        level=effective_level,
    )
    traceback_content = build_traceback_content(exc)
    request_data = _extract_request_data(request, body)

    # Check for custom Celery task
    celery_task = get_setting("CELERY_TASK")
    if celery_task is not None:
        celery_task.delay(
            type(exc).__name__,
            str(exc),
            message,
            traceback_content,
            effective_level,
            effective_severity,
            request_data,
        )
        return True

    # Fire and forget in a daemon thread
    thread = threading.Thread(
        target=_do_report,
        kwargs={
            "exc_class_name": type(exc).__name__,
            "exc_message": str(exc),
            "message": message,
            "traceback_content": traceback_content,
            "effective_level": effective_level,
            "effective_severity": effective_severity,
            "request_data": request_data,
            "body": body,
        },
        daemon=True,
    )
    thread.start()

    return True
