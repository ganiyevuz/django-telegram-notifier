import pytest
from django.test import RequestFactory

from telegram_notifier.choices import Level, Severity, Status
from telegram_notifier.models import ExceptionLog


@pytest.mark.django_db
def test_create_exception_log():
    log = ExceptionLog.objects.create(
        exception_class="ValueError",
        message="something broke",
        traceback="Traceback ...",
    )
    assert log.pk is not None
    assert log.level == Level.ERROR
    assert log.severity == Severity.HIGH
    assert log.status == Status.NEW
    assert log.is_sent is False


@pytest.mark.django_db
def test_exception_log_str():
    log = ExceptionLog(
        exception_class="ValueError",
        message="something broke",
    )
    assert "ValueError" in str(log)


@pytest.mark.django_db
def test_create_from_exception():
    factory = RequestFactory()
    request = factory.get("/api/test?page=2")

    try:
        raise ValueError("test error")
    except ValueError as exc:
        log = ExceptionLog.create_from_exception(exc, request=request, body=b'{"a":1}')

    assert log.pk is not None
    assert log.exception_class == "ValueError"
    assert log.message == "test error"
    assert log.path == "/api/test"
    assert log.method == "GET"
    assert log.query_params == {"page": ["2"]}
    assert log.hostname != ""


@pytest.mark.django_db
def test_create_from_exception_filters_sensitive_headers():
    factory = RequestFactory()
    request = factory.get(
        "/test",
        HTTP_AUTHORIZATION="Bearer secret",
        HTTP_USER_AGENT="TestAgent/1.0",
    )

    try:
        raise ValueError("test")
    except ValueError as exc:
        log = ExceptionLog.create_from_exception(exc, request=request)

    assert "Authorization" not in log.headers
    assert "User-Agent" in log.headers
