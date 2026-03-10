from unittest.mock import patch

import pytest
from django.test import RequestFactory

from telegram_notifier.middleware import GlobalExceptionReporterMiddleware


def test_middleware_calls_report_on_exception(settings):
    settings.TELEGRAM_NOTIFIER = {
        "BOT_TOKEN": "fake",
        "CHAT_IDS": ["1"],
    }
    factory = RequestFactory()
    request = factory.get("/test")

    middleware = GlobalExceptionReporterMiddleware(lambda r: None)
    middleware(request)

    exc = ValueError("boom")

    with patch("telegram_notifier.middleware.report_exception") as mock_report:
        middleware.process_exception(request, exc)

    mock_report.assert_called_once()
    args = mock_report.call_args
    assert args[0][0] is exc
    assert args[0][1] is request


def test_middleware_captures_request_body(settings):
    settings.TELEGRAM_NOTIFIER = {
        "BOT_TOKEN": "fake",
        "CHAT_IDS": ["1"],
    }
    factory = RequestFactory()
    request = factory.post(
        "/test", data=b'{"key": "value"}', content_type="application/json",
    )

    middleware = GlobalExceptionReporterMiddleware(lambda r: None)
    middleware(request)

    with patch("telegram_notifier.middleware.report_exception") as mock_report:
        middleware.process_exception(request, ValueError("fail"))

    body_arg = mock_report.call_args[0][2]
    assert body_arg is not None


def test_middleware_body_is_per_request(settings):
    settings.TELEGRAM_NOTIFIER = {
        "BOT_TOKEN": "fake",
        "CHAT_IDS": ["1"],
    }
    factory = RequestFactory()
    request_a = factory.post(
        "/a", data=b'{"a": 1}', content_type="application/json",
    )
    request_b = factory.post(
        "/b", data=b'{"b": 2}', content_type="application/json",
    )

    middleware = GlobalExceptionReporterMiddleware(lambda r: None)
    middleware(request_a)
    middleware(request_b)

    with patch("telegram_notifier.middleware.report_exception") as mock_report:
        middleware.process_exception(request_a, ValueError("fail"))

    body_arg = mock_report.call_args[0][2]
    assert b"a" in body_arg


@pytest.mark.asyncio
async def test_middleware_async(settings):
    settings.TELEGRAM_NOTIFIER = {
        "BOT_TOKEN": "fake",
        "CHAT_IDS": ["1"],
    }
    factory = RequestFactory()
    request = factory.get("/test")

    async def async_get_response(req):
        return None

    middleware = GlobalExceptionReporterMiddleware(async_get_response)
    await middleware.__acall__(request)

    with patch("telegram_notifier.middleware.report_exception") as mock_report:
        middleware.process_exception(request, ValueError("async boom"))

    mock_report.assert_called_once()
    assert mock_report.call_args[0][2] is not None
