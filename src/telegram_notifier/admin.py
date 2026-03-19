from __future__ import annotations

import json

from django.contrib import admin
from django.db.models import Count, Q, QuerySet
from django.db.models.functions import TruncHour
from django.http import HttpRequest, JsonResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from .choices import Level, Status
from .models import ExceptionLog

BADGE = (
    '<span style="background:{bg};color:{fg};padding:2px 8px;'
    'border-radius:4px;font-size:11px;font-weight:600;white-space:nowrap">'
    "{label}</span>"
)

LEVEL_COLORS: dict[str, tuple[str, str]] = {
    "critical": ("#dc2626", "#fff"),
    "error": ("#fecaca", "#991b1b"),
    "warning": ("#fef3c7", "#92400e"),
    "info": ("#dbeafe", "#1e40af"),
    "debug": ("#f3f4f6", "#4b5563"),
}

SEVERITY_COLORS: dict[str, tuple[str, str]] = {
    "critical": ("#dc2626", "#fff"),
    "high": ("#fed7aa", "#9a3412"),
    "moderate": ("#fef3c7", "#92400e"),
    "low": ("#f3f4f6", "#4b5563"),
}

STATUS_COLORS: dict[str, tuple[str, str]] = {
    "new": ("#dbeafe", "#1e40af"),
    "seen": ("#e9d5ff", "#6b21a8"),
    "resolved": ("#dcfce7", "#166534"),
    "ignored": ("#f3f4f6", "#4b5563"),
}

METHOD_COLORS: dict[str, tuple[str, str]] = {
    "GET": ("#dcfce7", "#166534"),
    "POST": ("#dbeafe", "#1e40af"),
    "PUT": ("#fef3c7", "#92400e"),
    "PATCH": ("#fef3c7", "#92400e"),
    "DELETE": ("#fecaca", "#991b1b"),
}


def _badge(label: str, colors: dict[str, tuple[str, str]]) -> str:
    bg, fg = colors.get(label, ("#f3f4f6", "#4b5563"))
    return format_html(BADGE, bg=bg, fg=fg, label=label.upper())


def _time_ago(dt: timezone.datetime) -> str:
    delta = timezone.now() - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return f"{seconds}s ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    if days < 30:
        return f"{days}d ago"
    return dt.strftime("%Y-%m-%d")


# --- Admin Actions ---


@admin.action(description="Mark as Resolved")
def mark_resolved(
    modeladmin: admin.ModelAdmin,
    request: HttpRequest,
    queryset: QuerySet,
) -> None:
    queryset.update(status=Status.RESOLVED)


@admin.action(description="Mark as Ignored")
def mark_ignored(
    modeladmin: admin.ModelAdmin,
    request: HttpRequest,
    queryset: QuerySet,
) -> None:
    queryset.update(status=Status.IGNORED)


@admin.action(description="Mark as Seen")
def mark_seen(
    modeladmin: admin.ModelAdmin,
    request: HttpRequest,
    queryset: QuerySet,
) -> None:
    queryset.update(status=Status.SEEN)


@admin.action(description="Resend to Telegram")
def resend_telegram(
    modeladmin: admin.ModelAdmin,
    request: HttpRequest,
    queryset: QuerySet,
) -> None:
    from .client import notify_error_via_telegram

    for log in queryset:
        try:
            exc_data = {
                "exception_class": log.exception_class,
                "message": log.message,
                "path": log.path,
                "method": log.method,
                "user_info": log.user_info,
                "ip_address": log.ip_address or "",
                "view_name": log.view_name,
                "hostname": log.hostname,
                "environment": log.environment,
            }
            message = (
                f"<b>{exc_data['exception_class']}</b>\n"
                f"{exc_data['message'][:200]}\n\n"
                f"<b>Path:</b> {exc_data['method']} {exc_data['path']}\n"
                f"<b>User:</b> {exc_data['user_info'] or 'anonymous'}\n"
                f"<b>Host:</b> {exc_data['hostname']}\n"
                f"<b>Env:</b> {exc_data['environment']}"
            )
            sent = notify_error_via_telegram(message, log.traceback)
            if sent:
                log.is_sent = True
                log.save(update_fields=["is_sent"])
        except Exception:
            pass

    count = queryset.count()
    modeladmin.message_user(
        request, f"Resent {count} exception(s) to Telegram.",
    )


# --- Admin ---


@admin.register(ExceptionLog)
class ExceptionLogAdmin(admin.ModelAdmin):
    change_form_template = "admin/telegram_notifier/exceptionlog/change_form.html"
    change_list_template = "admin/telegram_notifier/exceptionlog/change_list.html"

    list_display = (
        "exception_class",
        "short_message",
        "level_badge",
        "severity_badge",
        "status",
        "method_badge",
        "path",
        "user_info_display",
        "environment_badge",
        "sent_icon",
        "ago",
    )
    list_filter = (
        "level",
        "severity",
        "status",
        "is_sent",
        "environment",
        "method",
        "created_at",
    )
    search_fields = ("exception_class", "message", "path", "user_info", "ip_address")
    readonly_fields = (
        "exception_class",
        "message",
        "traceback",
        "level",
        "severity",
        "path",
        "method",
        "query_params",
        "body",
        "user_info",
        "ip_address",
        "headers",
        "view_name",
        "hostname",
        "environment",
        "is_sent",
        "created_at",
    )
    list_editable = ("status",)
    list_per_page = 50
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    actions = [mark_resolved, mark_ignored, mark_seen, resend_telegram]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def get_urls(self) -> list:
        custom = [
            path(
                "<path:object_id>/action/",
                self.admin_site.admin_view(self.detail_action_view),
                name="telegram_notifier_exceptionlog_action",
            ),
        ]
        return custom + super().get_urls()

    def detail_action_view(
        self, request: HttpRequest, object_id: str,
    ) -> JsonResponse:
        """AJAX endpoint for detail-page actions."""
        if request.method != "POST":
            return JsonResponse({"error": "POST required"}, status=405)

        obj = self.get_object(request, object_id)
        if not obj:
            return JsonResponse({"error": "Not found"}, status=404)

        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        action = data.get("action")

        if action in ("new", "seen", "resolved", "ignored"):
            obj.status = action
            obj.save(update_fields=["status"])
            return JsonResponse({"ok": True, "status": action})

        if action == "resend":
            from .client import notify_error_via_telegram

            message = (
                f"<b>{obj.exception_class}</b>\n"
                f"{obj.message[:200]}\n\n"
                f"<b>Path:</b> {obj.method} {obj.path}\n"
                f"<b>User:</b> {obj.user_info or 'anonymous'}\n"
                f"<b>Host:</b> {obj.hostname}\n"
                f"<b>Env:</b> {obj.environment}"
            )
            sent = notify_error_via_telegram(
                message, obj.traceback,
            )
            if sent:
                obj.is_sent = True
                obj.save(update_fields=["is_sent"])
            return JsonResponse({"ok": sent, "is_sent": obj.is_sent})

        return JsonResponse({"error": "Unknown action"}, status=400)

    # --- List display columns ---

    @admin.display(description="Message")
    def short_message(self, obj: ExceptionLog) -> str:
        msg = obj.message or ""
        return msg[:80] + "..." if len(msg) > 80 else msg

    @admin.display(description="Level", ordering="level")
    def level_badge(self, obj: ExceptionLog) -> str:
        return _badge(obj.level, LEVEL_COLORS)

    @admin.display(description="Severity", ordering="severity")
    def severity_badge(self, obj: ExceptionLog) -> str:
        return _badge(obj.severity, SEVERITY_COLORS)

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj: ExceptionLog) -> str:
        return _badge(obj.status, STATUS_COLORS)

    @admin.display(description="Method", ordering="method")
    def method_badge(self, obj: ExceptionLog) -> str:
        if not obj.method:
            return "-"
        return _badge(obj.method, METHOD_COLORS)

    @admin.display(description="User", ordering="user_info")
    def user_info_display(self, obj: ExceptionLog) -> str:
        return obj.user_info or format_html(
            '<span style="color:#9ca3af">anonymous</span>'
        )

    @admin.display(description="Env", ordering="environment")
    def environment_badge(self, obj: ExceptionLog) -> str:
        if not obj.environment:
            return "-"
        env = obj.environment.lower()
        if env in ("production", "prod"):
            colors = {env: ("#dc2626", "#fff")}
        else:
            colors = {env: ("#dcfce7", "#166534")}
        return _badge(env, colors)

    @admin.display(description="Sent", ordering="is_sent", boolean=True)
    def sent_icon(self, obj: ExceptionLog) -> bool:
        return obj.is_sent

    @admin.display(description="When", ordering="created_at")
    def ago(self, obj: ExceptionLog) -> str:
        return format_html(
            '<span title="{}">{}</span>',
            obj.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            _time_ago(obj.created_at),
        )

    # --- Detail view context ---

    def change_view(
        self,
        request: HttpRequest,
        object_id: str,
        form_url: str = "",
        extra_context: dict | None = None,
    ) -> object:
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)

        if obj:
            now = timezone.now()
            last_24h = now - timezone.timedelta(hours=24)
            last_7d = now - timezone.timedelta(days=7)
            same_class = ExceptionLog.objects.filter(
                exception_class=obj.exception_class,
            )

            extra_context["occurrence_24h"] = same_class.filter(
                created_at__gte=last_24h,
            ).count()
            extra_context["occurrence_7d"] = same_class.filter(
                created_at__gte=last_7d,
            ).count()
            extra_context["occurrence_total"] = same_class.count()
            extra_context["time_ago"] = _time_ago(obj.created_at)

            # Prev/Next navigation
            app = self.opts.app_label
            model = self.opts.model_name
            prev_pk = (
                ExceptionLog.objects
                .filter(created_at__gt=obj.created_at)
                .order_by("created_at")
                .values_list("pk", flat=True)
                .first()
            )
            next_pk = (
                ExceptionLog.objects
                .filter(created_at__lt=obj.created_at)
                .order_by("-created_at")
                .values_list("pk", flat=True)
                .first()
            )
            extra_context["list_url"] = reverse(
                f"admin:{app}_{model}_changelist",
            )
            extra_context["action_url"] = reverse(
                f"admin:{app}_{model}_action",
                args=[object_id],
            )
            if prev_pk is not None:
                extra_context["prev_url"] = reverse(
                    f"admin:{app}_{model}_change",
                    args=[prev_pk],
                )
            if next_pk is not None:
                extra_context["next_url"] = reverse(
                    f"admin:{app}_{model}_change",
                    args=[next_pk],
                )

        return super().change_view(
            request, object_id, form_url, extra_context,
        )

    # --- Changelist context for summary stats ---

    def changelist_view(
        self,
        request: HttpRequest,
        extra_context: dict | None = None,
    ) -> object:
        extra_context = extra_context or {}
        now = timezone.now()
        last_24h = now - timezone.timedelta(hours=24)
        last_7d = now - timezone.timedelta(days=7)

        qs = self.get_queryset(request)

        stats_24h = qs.filter(created_at__gte=last_24h).aggregate(
            total=Count("id"),
            critical=Count("id", filter=Q(level=Level.CRITICAL)),
            error=Count("id", filter=Q(level=Level.ERROR)),
            warning=Count("id", filter=Q(level=Level.WARNING)),
            unresolved=Count("id", filter=Q(status__in=[Status.NEW, Status.SEEN])),
            unsent=Count("id", filter=Q(is_sent=False)),
        )
        stats_7d = qs.filter(created_at__gte=last_7d).aggregate(
            total=Count("id"),
        )

        extra_context["stats_24h"] = stats_24h
        extra_context["stats_7d_total"] = stats_7d["total"]
        extra_context["total_unresolved"] = qs.filter(
            status__in=[Status.NEW, Status.SEEN]
        ).count()

        # --- Chart data ---

        # Timeline: exceptions per hour (last 24h)
        hourly_qs = (
            qs.filter(created_at__gte=last_24h)
            .annotate(hour=TruncHour("created_at"))
            .values("hour")
            .annotate(count=Count("id"))
            .order_by("hour")
        )
        hourly_map = {
            row["hour"]: row["count"] for row in hourly_qs
        }
        timeline_labels = []
        timeline_data = []
        for i in range(24):
            h = (last_24h + timezone.timedelta(hours=i)).replace(
                minute=0, second=0, microsecond=0,
            )
            timeline_labels.append(h.strftime("%H:00"))
            timeline_data.append(hourly_map.get(h, 0))

        extra_context["chart_timeline_labels"] = json.dumps(
            timeline_labels,
        )
        extra_context["chart_timeline_data"] = json.dumps(
            timeline_data,
        )

        # By level: doughnut (last 7d)
        level_qs = (
            qs.filter(created_at__gte=last_7d)
            .values("level")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        level_labels = []
        level_data = []
        for row in level_qs:
            level_labels.append(row["level"].capitalize())
            level_data.append(row["count"])

        extra_context["chart_level_labels"] = json.dumps(
            level_labels,
        )
        extra_context["chart_level_data"] = json.dumps(level_data)

        return super().changelist_view(request, extra_context)
