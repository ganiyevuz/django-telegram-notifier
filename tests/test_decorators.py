import asyncio
from unittest.mock import patch

import pytest

from telegram_notifier.decorators import telegram_exception_notifier


def test_decorator_reports_and_reraises():
    @telegram_exception_notifier
    def failing_function():
        raise ValueError("boom")

    with (
        patch("telegram_notifier.decorators.report_exception") as mock_report,
        pytest.raises(ValueError, match="boom"),
    ):
        failing_function()

    mock_report.assert_called_once()


def test_decorator_returns_value_on_success():
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


@pytest.mark.asyncio
async def test_async_decorator_reports_and_reraises():
    @telegram_exception_notifier
    async def async_failing():
        raise ValueError("async boom")

    with (
        patch("telegram_notifier.decorators.report_exception") as mock_report,
        pytest.raises(ValueError, match="async boom"),
    ):
        await async_failing()

    mock_report.assert_called_once()


@pytest.mark.asyncio
async def test_async_decorator_returns_value():
    @telegram_exception_notifier
    async def async_good():
        return 99

    assert await async_good() == 99


def test_async_decorator_preserves_coroutine_nature():
    @telegram_exception_notifier
    async def async_func():
        pass

    assert asyncio.iscoroutinefunction(async_func)
    assert async_func.__name__ == "async_func"
