from unittest.mock import patch

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
