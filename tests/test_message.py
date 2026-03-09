from django.test import RequestFactory

from telegram_notifier.message import build_exception_message


def test_builds_message_without_request():
    try:
        raise ValueError("something broke")
    except ValueError as exc:
        message = build_exception_message(exc)

    assert "ValueError" in message
    assert "something broke" in message
    assert "<b>Traceback:</b>" in message


def test_builds_message_with_request():
    factory = RequestFactory()
    request = factory.get("/api/test?page=2")

    try:
        raise RuntimeError("fail")
    except RuntimeError as exc:
        message = build_exception_message(exc, request=request, body=b'{"key": "val"}')

    assert "/api/test" in message
    assert "GET" in message
    assert "key" in message


def test_escapes_html_in_exception():
    try:
        raise ValueError("<script>alert('xss')</script>")
    except ValueError as exc:
        message = build_exception_message(exc)

    assert "<script>" not in message
    assert "&lt;script&gt;" in message


def test_handles_binary_body():
    factory = RequestFactory()
    request = factory.post("/api/upload")

    try:
        raise ValueError("fail")
    except ValueError as exc:
        message = build_exception_message(exc, request=request, body=b'\x89PNG\r\n')

    assert "[binary data omitted]" in message


def test_includes_environment_when_set(settings):
    settings.TELEGRAM_NOTIFIER = {
        "BOT_TOKEN": "x",
        "CHAT_IDS": ["1"],
        "ENVIRONMENT": "production",
    }
    try:
        raise ValueError("fail")
    except ValueError as exc:
        message = build_exception_message(exc)

    assert "production" in message


def test_includes_user_info_when_authenticated():
    factory = RequestFactory()
    request = factory.get("/test")

    class FakeUser:
        is_authenticated = True
        def __str__(self):
            return "john@example.com"

    request.user = FakeUser()

    try:
        raise ValueError("fail")
    except ValueError as exc:
        message = build_exception_message(exc, request=request)

    assert "john@example.com" in message
