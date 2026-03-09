import html
import traceback

from django.http import RawPostDataException
from django.utils.timezone import now

from telegram_notifier.settings import get_setting


def build_exception_message(exc, request=None, body=None):
    timestamp = now().strftime("%Y-%m-%d %H:%M:%S")
    tb_string = "".join(traceback.format_exception(exc))
    exc_class = html.escape(exc.__class__.__name__)
    exc_message = html.escape(str(exc))
    max_length = get_setting("MESSAGE_MAX_LENGTH")
    environment = get_setting("ENVIRONMENT")

    parts = [
        f"<b>Timestamp:</b> {timestamp}",
        f"<b>Error Class:</b> {exc_class}",
        f"<b>Message:</b> {exc_message}",
    ]

    if environment:
        parts.insert(0, f"<b>Environment:</b> {environment}")

    parts.append(f"<b>Traceback:</b>\n<pre>{html.escape(tb_string)[:600]}</pre>")

    if request and hasattr(request, "path"):
        body_str = _decode_body(body)
        parts.append(f"<b>Path:</b> {request.path}")
        parts.append(f"<b>Method:</b> {request.method}")
        parts.append(f"<b>Body:</b> <pre>{body_str}</pre>")

        if hasattr(request, "user") and request.user.is_authenticated:
            parts.append(f"<b>User:</b> {html.escape(str(request.user))}")

    return "\n".join(parts)[:max_length]


def _decode_body(body):
    if not body:
        return "{}"
    try:
        return html.escape(body.decode("utf-8"))
    except RawPostDataException:
        return "RawPostDataException: Unable to decode request body"
    except (UnicodeDecodeError, AttributeError):
        return "[binary data omitted]"
