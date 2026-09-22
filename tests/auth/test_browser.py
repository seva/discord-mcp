import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from discord_mcp.auth.browser import capture


def test_extract_token_from_authorization_header():
    from discord_mcp.auth.browser import _extract_token

    headers = {"authorization": "Bearer my-user-token"}
    assert _extract_token(headers) == "my-user-token"


def test_extract_token_returns_none_when_absent():
    from discord_mcp.auth.browser import _extract_token

    assert _extract_token({}) is None


def test_extract_token_ignores_bot_prefixed_tokens():
    from discord_mcp.auth.browser import _extract_token

    assert _extract_token({"authorization": "Bot abc"}) is None


@pytest.mark.asyncio
async def test_capture_timeout_closes_browser():
    mock_page = AsyncMock()
    mock_page.on = MagicMock()

    mock_context = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)

    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_browser.close = AsyncMock()

    mock_p = MagicMock()
    mock_p.chromium.launch = AsyncMock(return_value=mock_browser)

    mock_playwright_cm = AsyncMock()
    mock_playwright_cm.__aenter__ = AsyncMock(return_value=mock_p)
    mock_playwright_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("discord_mcp.auth.browser.async_playwright", return_value=mock_playwright_cm):
        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(TimeoutError):
                await capture(timeout=2)

    mock_browser.close.assert_called_once()


@pytest.mark.asyncio
async def test_capture_returns_token_once_intercepted():
    token_holder = {"value": None}
    on_request_handlers = []

    def fake_on(event, handler):
        on_request_handlers.append(handler)

    mock_page = AsyncMock()
    mock_page.on = fake_on

    mock_context = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    mock_context.cookies = AsyncMock(return_value=[])

    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_browser.close = AsyncMock()

    mock_p = MagicMock()
    mock_p.chromium.launch = AsyncMock(return_value=mock_browser)

    mock_playwright_cm = AsyncMock()
    mock_playwright_cm.__aenter__ = AsyncMock(return_value=mock_p)
    mock_playwright_cm.__aexit__ = AsyncMock(return_value=False)

    class FakeRequest:
        def __init__(self, url, headers):
            self.url = url
            self.headers = headers

    async def fake_sleep(_):
        if token_holder["value"] is None:
            # Simulate the login completing on first poll
            req = FakeRequest(
                "https://discord.com/api/v10/users/@me",
                {"authorization": "my-user-token"},
            )
            for handler in on_request_handlers:
                handler(req)

    with patch("discord_mcp.auth.browser.async_playwright", return_value=mock_playwright_cm):
        with patch("discord_mcp.auth.browser.asyncio.sleep", side_effect=fake_sleep):
            with patch("time.time", side_effect=[0, 0, time.time() + 999]):
                result = await capture(timeout=10)

    assert result["token"] == "my-user-token"
    mock_browser.close.assert_called_once()
