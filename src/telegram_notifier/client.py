import logging

import httpx

from telegram_notifier.settings import get_setting

logger = logging.getLogger("telegram_notifier")

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def notify_error_via_telegram(message):
    token = get_setting("BOT_TOKEN")
    chat_ids = get_setting("CHAT_IDS")
    proxy = get_setting("PROXY")
    max_length = get_setting("MESSAGE_MAX_LENGTH")

    url = TELEGRAM_API_URL.format(token=token)
    payload = {"text": message[:max_length], "parse_mode": "html"}
    success = True

    for chat_id in chat_ids:
        try:
            payload["chat_id"] = chat_id
            if proxy:
                with httpx.Client(proxy=proxy) as client:
                    response = client.post(url, data=payload, timeout=3)
            else:
                response = httpx.post(url, data=payload, timeout=3)
            response.raise_for_status()
            logger.info("Telegram notification sent to %s", chat_id)
        except Exception as e:
            logger.error("Telegram error for chat %s: %s", chat_id, e)
            success = False

    return success
