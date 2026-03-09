from django.conf import settings

DEFAULTS = {
    "PROXY": None,
    "MESSAGE_MAX_LENGTH": 4000,
    "ENVIRONMENT": None,
    "STORE_EXCEPTIONS": False,
    "CLEANUP_DAYS": 30,
}

REQUIRED = {"BOT_TOKEN", "CHAT_IDS"}


def get_setting(key):
    user_settings = getattr(settings, "TELEGRAM_NOTIFIER", {})
    if key in user_settings:
        return user_settings[key]
    if key in DEFAULTS:
        return DEFAULTS[key]
    raise KeyError(
        f"'{key}' is required in TELEGRAM_NOTIFIER settings"
    )
