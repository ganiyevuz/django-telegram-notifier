from unittest.mock import patch, MagicMock

from telegram_notifier.client import notify_error_via_telegram


def test_sends_message_to_all_chat_ids(settings):
    settings.TELEGRAM_NOTIFIER = {
        "BOT_TOKEN": "fake-token",
        "CHAT_IDS": ["111", "222"],
    }
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("telegram_notifier.client.httpx.post", return_value=mock_response) as mock_post:
        result = notify_error_via_telegram("test error")

    assert mock_post.call_count == 2
    assert result is True


def test_returns_false_on_failure(settings):
    settings.TELEGRAM_NOTIFIER = {
        "BOT_TOKEN": "fake-token",
        "CHAT_IDS": ["111"],
    }
    with patch("telegram_notifier.client.httpx.post", side_effect=Exception("network error")):
        result = notify_error_via_telegram("test error")

    assert result is False


def test_uses_proxy_when_configured(settings):
    settings.TELEGRAM_NOTIFIER = {
        "BOT_TOKEN": "fake-token",
        "CHAT_IDS": ["111"],
        "PROXY": "http://proxy:8080",
    }
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("telegram_notifier.client.httpx") as mock_httpx:
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_httpx.Client.return_value = mock_client

        notify_error_via_telegram("test error")

    mock_httpx.Client.assert_called_once_with(proxy="http://proxy:8080")
