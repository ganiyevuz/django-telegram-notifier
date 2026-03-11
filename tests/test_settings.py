import pytest

from telegram_notifier.settings import DEFAULTS, get_setting


def test_get_setting_returns_configured_value(settings):
    settings.TELEGRAM_NOTIFIER = {"BOT_TOKEN": "my-token", "CHAT_IDS": ["1"]}
    assert get_setting("BOT_TOKEN") == "my-token"


def test_get_setting_returns_default_when_not_configured(settings):
    settings.TELEGRAM_NOTIFIER = {"BOT_TOKEN": "x", "CHAT_IDS": ["1"]}
    assert get_setting("MESSAGE_MAX_LENGTH") == DEFAULTS["MESSAGE_MAX_LENGTH"]


def test_get_setting_raises_for_missing_required(settings):
    settings.TELEGRAM_NOTIFIER = {}
    with pytest.raises(KeyError):
        get_setting("BOT_TOKEN")


def test_defaults_contains_expected_keys():
    expected = {
        "PROXY",
        "MESSAGE_MAX_LENGTH",
        "ENVIRONMENT",
        "STORE_EXCEPTIONS",
        "CLEANUP_DAYS",
    }
    assert expected.issubset(set(DEFAULTS.keys()))
