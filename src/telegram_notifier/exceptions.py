import html
import traceback

import httpx
from django.conf import settings
from django.http import RawPostDataException
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now
from loguru import logger


def notify_error_via_telegram(message, proxies=None):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    for chat_id in settings.TELEGRAM_CHAT_IDS:
        try:
            response = httpx.post(
                url,
                data={"chat_id": chat_id, "text": message, "parse_mode": "html"},
                timeout=3,
                proxies=proxies,
            )
            response.raise_for_status()
            if response.status_code == 200:
                logger.success(f"Telegram notification sent successfully to {chat_id}")
        except Exception as e:
            logger.error(f"Telegram error: {e}")


def build_exception_message(exc, request=None, body=None):
    timestamp = now().strftime("%Y-%m-%d %H:%M:%S")
    tb_string = "".join(traceback.format_exception(exc))
    exc_class = html.escape(exc.__class__.__name__)
    exc_message = html.escape(str(exc))

    request_info, user_info = "", ""
    if request and hasattr(request, "path"):
        try:
            body = html.escape(body.decode("utf-8")) if body else "{}"
        except RawPostDataException:
            body = "RawPostDataException: Unable to decode request body"
        except (UnicodeDecodeError, AttributeError):
            # Binary payload or nobody
            body = "[binary data omitted]"

        if hasattr(request, "user") and request.user.is_authenticated:
            user_info += f"<b>User:</b> {request.user.get_user_info()}\n"

        request_info = (
            f"<b>Path:</b> {request.path}\n<b>Method:</b> {request.method}\n"
            f"<b>Body:</b> <pre>{body}</pre>"
        )
    return (
        f"<b>Timestamp:</b> {timestamp}\n"
        f"<b>Error Class:</b> {exc_class}\n"
        f"<b>Message:</b> {exc_message}\n"
        f"<b>Traceback:</b>\n<pre>{html.escape(tb_string)[:600]}</pre>\n"
        f"{user_info}{request_info}"
    )


def report_exception(exc, request=None, body=None):
    message = build_exception_message(exc, request, body)
    notify_error_via_telegram(message)


def telegram_exception_notifier(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            request = args[0] if args and len(args) else None
            report_exception(e, request)
            raise e

    return wrapper


class GlobalExceptionReporterMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)
        self._body = None

    def process_request(self, request):
        self._body = getattr(request, "body", b"")

    def process_exception(self, request, exception):
        report_exception(exception, request, self._body)
