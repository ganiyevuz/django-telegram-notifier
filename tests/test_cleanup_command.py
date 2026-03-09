from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils.timezone import now

from telegram_notifier.models import ExceptionLog


@pytest.mark.django_db
def test_cleanup_deletes_old_exceptions(settings):
    settings.TELEGRAM_NOTIFIER = {
        "BOT_TOKEN": "fake",
        "CHAT_IDS": ["1"],
        "CLEANUP_DAYS": 30,
    }
    old = ExceptionLog.objects.create(
        exception_class="OldError",
        message="old",
        traceback="...",
    )
    ExceptionLog.objects.filter(pk=old.pk).update(
        created_at=now() - timedelta(days=31)
    )
    new = ExceptionLog.objects.create(
        exception_class="NewError",
        message="new",
        traceback="...",
    )

    call_command("cleanup_exceptions")

    assert ExceptionLog.objects.count() == 1
    assert ExceptionLog.objects.first().pk == new.pk


@pytest.mark.django_db
def test_cleanup_respects_days_argument(settings):
    settings.TELEGRAM_NOTIFIER = {
        "BOT_TOKEN": "fake",
        "CHAT_IDS": ["1"],
        "CLEANUP_DAYS": 30,
    }
    log = ExceptionLog.objects.create(
        exception_class="Error",
        message="test",
        traceback="...",
    )
    ExceptionLog.objects.filter(pk=log.pk).update(
        created_at=now() - timedelta(days=8)
    )

    call_command("cleanup_exceptions", "--days=7")

    assert ExceptionLog.objects.count() == 0
