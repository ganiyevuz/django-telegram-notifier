import html
import traceback

from django.http import RawPostDataException
from django.utils.timezone import now

from telegram_notifier.settings import get_setting

TRACEBACK_PREVIEW_LINES = 5

LEVEL_EMOJI = {
    "debug": "⚪",
    "info": "🔵",
    "warning": "🟡",
    "error": "🔴",
    "critical": "⛔",
}


def build_traceback_content(exc):
    return "".join(traceback.format_exception(exc))


def build_exception_message(exc, request=None, body=None, level="error"):
    timestamp = now().strftime("%Y-%m-%d %H:%M:%S")
    tb_string = "".join(traceback.format_exception(exc))
    exc_class = html.escape(exc.__class__.__name__)
    exc_message = html.escape(str(exc))
    max_length = get_setting("MESSAGE_MAX_LENGTH")
    environment = get_setting("ENVIRONMENT")

    emoji = LEVEL_EMOJI.get(level, "🔴")
    env_tag = f" in <b>{html.escape(str(environment))}</b>" if environment else ""

    parts = [
        f"{emoji} <b>{exc_class}</b>{env_tag}",
        "",
        f"<b>Message:</b> {exc_message}",
        f"<b>Timestamp:</b> <i>{timestamp}</i>",
    ]

    tb_lines = tb_string.strip().splitlines()
    preview_lines = tb_lines[-TRACEBACK_PREVIEW_LINES:]
    tb_preview = html.escape("\n".join(preview_lines))
    parts.append(f"\n▸ <b>Traceback (preview)</b>\n<pre>{tb_preview}</pre>")

    if request and hasattr(request, "path"):
        body_str = _decode_body(body)
        request_lines = [
            "\n▸ <b>Request</b>",
            f"<blockquote><b>Path:</b> <code>{html.escape(request.path)}</code>",
            f"<b>Method:</b> <code>{html.escape(request.method)}</code>",
        ]

        if body_str != "{}":
            request_lines.append(f"<b>Body:</b>\n<pre>{body_str}</pre>")

        try:
            if hasattr(request, "user") and request.user.is_authenticated:
                request_lines.append(
                    f"<b>User:</b> <code>{html.escape(str(request.user))}</code>",
                )
        except Exception:
            pass

        request_lines.append("</blockquote>")
        parts.extend(request_lines)

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
