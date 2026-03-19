from unittest.mock import patch

import pytest

from telegram_notifier.models import ExceptionLog
from telegram_notifier.report import report_exception


def _report_and_wait(exc, **kwargs):
    """Call report_exception and wait for the background thread to finish."""
    with patch("telegram_notifier.report.threading") as mock_threading:

        class FakeThread:
            def __init__(self, target, kwargs, daemon=True):
                self.target = target
                self.kwargs = kwargs

            def start(self):
                self.target(**self.kwargs)

        mock_threading.Thread = FakeThread
        return report_exception(exc, **kwargs)


@pytest.mark.django_db
def test_report_sends_telegram_and_stores_when_enabled(settings):
    settings.TELEGRAM_NOTIFIER = {
        **settings.TELEGRAM_NOTIFIER,
        "STORE_EXCEPTIONS": True,
    }

    with patch(
        "telegram_notifier.report.notify_error_via_telegram",
        return_value=True,
    ):
        try:
            raise ValueError("test")
        except ValueError as exc:
            _report_and_wait(exc)

    assert ExceptionLog.objects.count() == 1
    log = ExceptionLog.objects.first()
    assert log.is_sent is True


@pytest.mark.django_db
def test_report_sends_telegram_without_storing():
    with patch(
        "telegram_notifier.report.notify_error_via_telegram",
        return_value=True,
    ):
        try:
            raise ValueError("test")
        except ValueError as exc:
            _report_and_wait(exc)

    assert ExceptionLog.objects.count() == 0


@pytest.mark.django_db
def test_report_marks_is_sent_false_on_failure(settings):
    settings.TELEGRAM_NOTIFIER = {
        **settings.TELEGRAM_NOTIFIER,
        "STORE_EXCEPTIONS": True,
    }

    with patch(
        "telegram_notifier.report.notify_error_via_telegram",
        return_value=False,
    ):
        try:
            raise ValueError("test")
        except ValueError as exc:
            _report_and_wait(exc)

    log = ExceptionLog.objects.first()
    assert log.is_sent is False


@pytest.mark.django_db
def test_report_passes_traceback_content():
    with patch(
        "telegram_notifier.report.notify_error_via_telegram",
        return_value=True,
    ) as mock_notify:
        try:
            raise ValueError("test")
        except ValueError as exc:
            _report_and_wait(exc)

    traceback_content = mock_notify.call_args.kwargs["traceback_content"]
    assert "ValueError: test" in traceback_content
    assert "Traceback (most recent call last)" in traceback_content


@pytest.mark.django_db
def test_report_skips_filtered_exception(settings):
    settings.TELEGRAM_NOTIFIER = {
        **settings.TELEGRAM_NOTIFIER,
        "IGNORE_EXCEPTIONS": ["ValueError"],
    }

    with patch(
        "telegram_notifier.report.notify_error_via_telegram",
    ) as mock_notify:
        try:
            raise ValueError("filtered")
        except ValueError as exc:
            result = report_exception(exc)

    assert result is False
    mock_notify.assert_not_called()
