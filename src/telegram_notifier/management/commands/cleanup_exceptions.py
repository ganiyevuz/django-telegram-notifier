from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils.timezone import now

from telegram_notifier.models import ExceptionLog
from telegram_notifier.settings import get_setting


class Command(BaseCommand):
    help = "Delete ExceptionLog entries older than N days"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=None,
            help="Number of days to keep (overrides CLEANUP_DAYS setting)",
        )

    def handle(self, *args, **options):
        days = options["days"]
        if days is None:
            days = get_setting("CLEANUP_DAYS")
        cutoff = now() - timedelta(days=days)
        count, _ = ExceptionLog.objects.filter(created_at__lt=cutoff).delete()
        self.stdout.write(
            self.style.SUCCESS(f"Deleted {count} exception(s) older than {days} days")
        )
