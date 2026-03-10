import os

import pytest
from django.test import RequestFactory

from telegram_notifier.client import notify_error_via_telegram
from telegram_notifier.message import build_exception_message

requires_telegram = pytest.mark.skipif(
    not os.environ.get("TELEGRAM_BOT_TOKEN"),
    reason="Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_IDS env vars to run",
)


@requires_telegram
def test_send_real_message():
    try:
        raise ValueError("Integration test — this is a test exception")
    except ValueError as exc:
        message = build_exception_message(exc)

    result = notify_error_via_telegram(message)
    assert result is True


@requires_telegram
def test_send_real_message_with_request():
    factory = RequestFactory()
    request = factory.post(
        "/api/orders?status=pending",
        data=b'{"order_id": 123, "amount": 99.99}',
        content_type="application/json",
    )

    try:
        raise RuntimeError("Order processing failed — test exception")
    except RuntimeError as exc:
        message = build_exception_message(exc, request=request, body=request.body)

    result = notify_error_via_telegram(message)
    assert result is True


@requires_telegram
def test_send_real_message_critical():
    try:
        raise ConnectionError("Database connection lost — test exception")
    except ConnectionError as exc:
        message = build_exception_message(exc, level="critical")

    result = notify_error_via_telegram(message)
    assert result is True
