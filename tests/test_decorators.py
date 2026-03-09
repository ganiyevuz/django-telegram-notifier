from unittest.mock import patch

import pytest

from telegram_notifier.decorators import telegram_exception_notifier


def test_decorator_reports_and_reraises(settings):
    settings.TELEGRAM_NOTIFIER = {
        "BOT_TOKEN": "fake",
        "CHAT_IDS": ["1"],
    }

    @telegram_exception_notifier
    def failing_function():
        raise ValueError("boom")

    with (
        patch("telegram_notifier.decorators.report_exception") as mock_report,
        pytest.raises(ValueError, match="boom"),
    ):
        failing_function()

    mock_report.assert_called_once()


def test_decorator_returns_value_on_success(settings):
    settings.TELEGRAM_NOTIFIER = {
        "BOT_TOKEN": "fake",
        "CHAT_IDS": ["1"],
    }

    @telegram_exception_notifier
    def good_function():
        return 42

    assert good_function() == 42


def test_decorator_preserves_function_metadata():
    @telegram_exception_notifier
    def my_func():
        """My docstring."""
        pass

    assert my_func.__name__ == "my_func"
    assert my_func.__doc__ == "My docstring."
