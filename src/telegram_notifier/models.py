import socket
import traceback

from django.db.models import (
    BooleanField,
    CharField,
    DateTimeField,
    GenericIPAddressField,
    JSONField,
    Model,
    TextField,
)
from django.http import QueryDict

from telegram_notifier.choices import Level, Severity, Status
from telegram_notifier.utils import (
    _get_client_ip,
    _get_filtered_headers,
    _get_view_name,
)


class ExceptionLog(Model):
    exception_class = CharField(max_length=255, db_index=True)
    message = TextField()
    traceback = TextField()
    level = CharField(max_length=10, choices=Level.choices, default=Level.ERROR)
    severity = CharField(max_length=10, choices=Severity.choices, default=Severity.HIGH)
    status = CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True,
    )

    path = CharField(max_length=500, blank=True)
    method = CharField(max_length=10, blank=True)
    query_params = JSONField(default=dict, blank=True)
    body = TextField(blank=True)
    user_info = CharField(max_length=255, blank=True)
    ip_address = GenericIPAddressField(null=True, blank=True)
    headers = JSONField(default=dict, blank=True)

    view_name = CharField(max_length=255, blank=True)
    hostname = CharField(max_length=255, blank=True)
    environment = CharField(max_length=50, blank=True)
    is_sent = BooleanField(default=False)

    created_at = DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        ts = self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else ""
        return f"{self.exception_class} — {ts}"

    @classmethod
    def create_from_exception(
        cls,
        exc,
        request=None,
        body=None,
        level=Level.ERROR,
        severity=Severity.HIGH,
        is_sent=False,
    ):
        from telegram_notifier.settings import get_setting

        tb_string = "".join(traceback.format_exception(exc))
        environment = get_setting("ENVIRONMENT") or ""

        kwargs = {
            "exception_class": exc.__class__.__name__,
            "message": str(exc),
            "traceback": tb_string,
            "level": level,
            "severity": severity,
            "hostname": socket.gethostname(),
            "environment": environment,
            "is_sent": is_sent,
        }

        if request and hasattr(request, "path"):
            body_str = ""
            if body:
                try:
                    body_str = body.decode("utf-8")
                except (UnicodeDecodeError, AttributeError):
                    body_str = "[binary data]"

            user_info = ""
            if hasattr(request, "user") and request.user.is_authenticated:
                user_info = str(request.user)

            query_params = dict(QueryDict(request.META.get("QUERY_STRING", "")).lists())

            kwargs.update(
                {
                    "path": request.path,
                    "method": request.method,
                    "query_params": query_params,
                    "body": body_str,
                    "user_info": user_info,
                    "ip_address": _get_client_ip(request),
                    "headers": _get_filtered_headers(request),
                    "view_name": _get_view_name(request),
                }
            )

        return cls.objects.create(**kwargs)
