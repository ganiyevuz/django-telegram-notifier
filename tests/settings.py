SECRET_KEY = "test-secret-key-do-not-use-in-production"
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "telegram_notifier",
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
TELEGRAM_NOTIFIER = {
    "BOT_TOKEN": "fake-bot-token",
    "CHAT_IDS": ["123456"],
}
