import pytest
from unittest.mock import patch

from telegram_notifier.models import ExceptionLog
from telegram_notifier.report import report_exception


@pytest.mark.django_db
def test_report_sends_telegram_and_stores_when_enabled(settings):
    settings.TELEGRAM_NOTIFIER = {
        "BOT_TOKEN": "fake",
        "CHAT_IDS": ["1"],
        "STORE_EXCEPTIONS": True,
    }

    with patch("telegram_notifier.report.notify_error_via_telegram", return_value=True):
        try:
            raise ValueError("test")
        except ValueError as exc:
            report_exception(exc)

    assert ExceptionLog.objects.count() == 1
    log = ExceptionLog.objects.first()
    assert log.is_sent is True


@pytest.mark.django_db
def test_report_sends_telegram_without_storing(settings):
    settings.TELEGRAM_NOTIFIER = {
        "BOT_TOKEN": "fake",
        "CHAT_IDS": ["1"],
        "STORE_EXCEPTIONS": False,
    }

    with patch("telegram_notifier.report.notify_error_via_telegram", return_value=True):
        try:
            raise ValueError("test")
        except ValueError as exc:
            report_exception(exc)

    assert ExceptionLog.objects.count() == 0


@pytest.mark.django_db
def test_report_marks_is_sent_false_on_failure(settings):
    settings.TELEGRAM_NOTIFIER = {
        "BOT_TOKEN": "fake",
        "CHAT_IDS": ["1"],
        "STORE_EXCEPTIONS": True,
    }

    with patch("telegram_notifier.report.notify_error_via_telegram", return_value=False):
        try:
            raise ValueError("test")
        except ValueError as exc:
            report_exception(exc)

    log = ExceptionLog.objects.first()
    assert log.is_sent is False
