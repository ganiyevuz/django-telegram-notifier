from unittest.mock import patch

import pytest

from telegram_notifier.models import ExceptionLog
from telegram_notifier.report import report_exception


@pytest.mark.django_db
def test_report_sends_telegram_and_stores_when_enabled(settings):
    settings.TELEGRAM_NOTIFIER = {**settings.TELEGRAM_NOTIFIER, "STORE_EXCEPTIONS": True}

    with patch("telegram_notifier.report.notify_error_via_telegram", return_value=True):
        try:
            raise ValueError("test")
        except ValueError as exc:
            report_exception(exc)

    assert ExceptionLog.objects.count() == 1
    log = ExceptionLog.objects.first()
    assert log.is_sent is True


@pytest.mark.django_db
def test_report_sends_telegram_without_storing():
    with patch("telegram_notifier.report.notify_error_via_telegram", return_value=True):
        try:
            raise ValueError("test")
        except ValueError as exc:
            report_exception(exc)

    assert ExceptionLog.objects.count() == 0


@pytest.mark.django_db
def test_report_marks_is_sent_false_on_failure(settings):
    settings.TELEGRAM_NOTIFIER = {**settings.TELEGRAM_NOTIFIER, "STORE_EXCEPTIONS": True}

    with patch(
        "telegram_notifier.report.notify_error_via_telegram", return_value=False,
    ):
        try:
            raise ValueError("test")
        except ValueError as exc:
            report_exception(exc)

    log = ExceptionLog.objects.first()
    assert log.is_sent is False


@pytest.mark.django_db
def test_report_passes_traceback_content():
    with patch("telegram_notifier.report.notify_error_via_telegram", return_value=True) as mock_notify:
        try:
            raise ValueError("test")
        except ValueError as exc:
            report_exception(exc)

    call_kwargs = mock_notify.call_args
    traceback_content = call_kwargs[1].get("traceback_content") or call_kwargs[0][1]
    assert "ValueError: test" in traceback_content
    assert "Traceback (most recent call last)" in traceback_content
