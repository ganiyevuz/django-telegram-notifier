from unittest.mock import MagicMock, patch

from telegram_notifier.client import notify_error_via_telegram


def test_sends_message_to_all_chat_ids(settings):
    settings.TELEGRAM_NOTIFIER = {
        "BOT_TOKEN": "fake-token",
        "CHAT_IDS": ["111", "222"],
    }
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch(
        "telegram_notifier.client.httpx.post",
        return_value=mock_response,
    ) as mock_post:
        result = notify_error_via_telegram("test error")

    assert mock_post.call_count == 2
    assert result is True


def test_returns_false_on_failure():
    with patch(
        "telegram_notifier.client.httpx.post",
        side_effect=Exception("network error"),
    ):
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


def test_sends_document_with_caption(settings):
    settings.TELEGRAM_NOTIFIER = {
        "BOT_TOKEN": "fake-token",
        "CHAT_IDS": ["111"],
    }
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch(
        "telegram_notifier.client.httpx.post",
        return_value=mock_response,
    ) as mock_post:
        notify_error_via_telegram("test error", traceback_content="ValueError: boom")

    assert mock_post.call_count == 1
    call = mock_post.call_args
    assert "sendDocument" in call[0][0]
    assert call[1]["data"]["chat_id"] == "111"
    assert call[1]["data"]["caption"] == "test error"
    assert call[1]["data"]["parse_mode"] == "HTML"
    assert "document" in call[1]["files"]


def test_sends_document_to_all_chats(settings):
    settings.TELEGRAM_NOTIFIER = {
        "BOT_TOKEN": "fake-token",
        "CHAT_IDS": ["111", "222"],
    }
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch(
        "telegram_notifier.client.httpx.post",
        return_value=mock_response,
    ) as mock_post:
        notify_error_via_telegram("test error", traceback_content="ValueError: boom")

    # 2 chats x 1 call each (document with caption)
    assert mock_post.call_count == 2
