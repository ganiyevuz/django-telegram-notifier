from django.db.models import TextChoices


class Level(TextChoices):
    DEBUG = "debug", "Debug"
    INFO = "info", "Info"
    WARNING = "warning", "Warning"
    ERROR = "error", "Error"
    CRITICAL = "critical", "Critical"


class Severity(TextChoices):
    LOW = "low", "Low"
    MODERATE = "moderate", "Moderate"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class Status(TextChoices):
    NEW = "new", "New"
    SEEN = "seen", "Seen"
    RESOLVED = "resolved", "Resolved"
    IGNORED = "ignored", "Ignored"
