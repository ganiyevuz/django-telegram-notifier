import io
import logging
from datetime import datetime

import httpx

from telegram_notifier.settings import get_setting

logger = logging.getLogger("telegram_notifier")

TELEGRAM_SEND_MESSAGE_URL = "https://api.telegram.org/bot{token}/sendMessage"
TELEGRAM_SEND_DOCUMENT_URL = "https://api.telegram.org/bot{token}/sendDocument"

CAPTION_MAX_LENGTH = 1024


def notify_error_via_telegram(message, traceback_content=None):
    token = get_setting("BOT_TOKEN")
    chat_ids = get_setting("CHAT_IDS")
    proxy = get_setting("PROXY")
    max_length = get_setting("MESSAGE_MAX_LENGTH")
    success = True

    for chat_id in chat_ids:
        try:
            if traceback_content:
                _send_document_with_caption(
                    token, chat_id, message, traceback_content, proxy,
                )
            else:
                url = TELEGRAM_SEND_MESSAGE_URL.format(token=token)
                payload = {
                    "chat_id": chat_id,
                    "text": message[:max_length],
                    "parse_mode": "HTML",
                }
                _post(url, data=payload, proxy=proxy)
            logger.info("Telegram notification sent to %s", chat_id)
        except Exception as e:
            logger.error("Telegram error for chat %s: %s", chat_id, e)
            success = False

    return success


def _send_document_with_caption(token, chat_id, message, traceback_content, proxy):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    last_line = traceback_content.strip().splitlines()[-1]
    exc_class = last_line.split(":")[0].split(".")[-1]
    filename = f"traceback_{exc_class}_{timestamp}.py"

    file_bytes = io.BytesIO(traceback_content.encode("utf-8"))
    url = TELEGRAM_SEND_DOCUMENT_URL.format(token=token)
    data = {
        "chat_id": chat_id,
        "caption": message[:CAPTION_MAX_LENGTH],
        "parse_mode": "HTML",
    }
    files = {"document": (filename, file_bytes, "text/x-python")}

    _post(url, data=data, files=files, proxy=proxy)


def _post(url, *, data, files=None, proxy=None):
    if proxy:
        with httpx.Client(proxy=proxy) as client:
            response = client.post(url, data=data, files=files, timeout=3)
    else:
        response = httpx.post(url, data=data, files=files, timeout=3)
    response.raise_for_status()
