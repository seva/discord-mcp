import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from discord_mcp.auth.store import AuthRequired

GUILD = {"id": "1551377931866079312", "name": "PlayForKeeps"}
USER = {"id": "931228531340496946", "username": "swearlock"}
SECRET_MSG = {
    "id": "m1",
    "content": "my key sk-ant-1234567890abcdef1234567890abcdef12345678",
    "author": {"username": "someone"},
}
CLEAN_MSG = {"id": "m2", "content": "lunch at noon", "author": {"username": "someone"}}


def _mock_client(return_map: dict):
    client = AsyncMock()
    for name, value in return_map.items():
        setattr(client, name, AsyncMock(return_value=value))
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=client)
    cm.__aexit__ = AsyncMock(return_value=False)
    cm.client = client
    return cm


@pytest.mark.asyncio
async def test_status_returns_user_and_guild_count():
    cm = _mock_client({"get_current_user": USER, "get_guilds": [GUILD]})
    with patch("discord_mcp.auth.store.load", return_value={"token": "t"}):
        with patch("discord_mcp.tools.status.DiscordClient", return_value=cm):
            from discord_mcp.tools.status import discord_status

            result = json.loads(await discord_status())
    assert result["username"] == "swearlock"
    assert result["guild_count"] == 1


@pytest.mark.asyncio
async def test_status_raises_auth_required_without_token():
    with patch("discord_mcp.auth.store.load", side_effect=AuthRequired("no auth")):
        from discord_mcp.tools.status import discord_status

        with pytest.raises(AuthRequired):
            await discord_status()


@pytest.mark.asyncio
async def test_channels_lists_guilds():
    cm = _mock_client({"get_guilds": [GUILD]})
    with patch("discord_mcp.auth.store.load", return_value={"token": "t"}):
        with patch("discord_mcp.tools.channels.DiscordClient", return_value=cm):
            from discord_mcp.tools.channels import discord_channels

            result = json.loads(await discord_channels())
    assert result[0]["name"] == "PlayForKeeps"


@pytest.mark.asyncio
async def test_channels_with_guild_id_returns_channels():
    channels = [{"id": "1478480447431376966", "type": 0, "name": "general"}]
    cm = _mock_client({"get_guild_channels": channels})
    with patch("discord_mcp.auth.store.load", return_value={"token": "t"}):
        with patch("discord_mcp.tools.channels.DiscordClient", return_value=cm):
            from discord_mcp.tools.channels import discord_channels

            result = json.loads(await discord_channels(guild_id="1551377931866079312"))
    assert result[0]["id"] == "1478480447431376966"
    cm.client.get_guild_channels.assert_awaited_once_with("1551377931866079312")


@pytest.mark.asyncio
async def test_messages_scrubs_secret_content():
    cm = _mock_client({"get_channel_messages": [SECRET_MSG, CLEAN_MSG]})
    with patch("discord_mcp.auth.store.load", return_value={"token": "t"}):
        with patch("discord_mcp.tools.messages.DiscordClient", return_value=cm):
            from discord_mcp.tools.messages import discord_messages

            result = json.loads(await discord_messages("123", limit=2))
    assert "sk-ant-" not in result[0]["content"]
    assert "[REDACTED:API_KEY]" in result[0]["content"]
    assert result[1]["content"] == "lunch at noon"


@pytest.mark.asyncio
async def test_search_scrubs_and_flattens():
    cm = _mock_client({"search_guild_messages": [SECRET_MSG, CLEAN_MSG]})
    with patch("discord_mcp.auth.store.load", return_value={"token": "t"}):
        with patch("discord_mcp.tools.search.DiscordClient", return_value=cm):
            from discord_mcp.tools.search import discord_search

            result = json.loads(await discord_search("key", guild_id="1551377931866079312"))
    assert "[REDACTED:API_KEY]" in result[0]["content"]
    cm.client.search_guild_messages.assert_awaited_once_with("1551377931866079312", "key", None, 10)


def test_scrub_messages_reaches_embed_free_text():
    from discord_mcp.tools import scrub_messages

    message = {
        "id": "m3",
        "content": "",
        "embeds": [
            {
                "title": "Deploy ghp_1234567890abcdefghijklmnopqrstuvwxyzAB",
                "description": "Key: sk-ant-1234567890abcdef1234567890abcdef12345678",
                "fields": [{"name": "note", "value": "password: 95172243"}],
                "footer": {"text": "backup token 8597761224:AAFcvCF0ZV_Qh9xzWAgCKG21F3MTR8Iu2pg"},
                "author": {"name": "poster"},
            }
        ],
    }
    result = scrub_messages([message])[0]
    embed = result["embeds"][0]
    assert "ghp_" not in embed["title"]
    assert "[REDACTED:GITHUB_TOKEN]" in embed["title"]
    assert "sk-ant-" not in embed["description"]
    assert "95172243" not in embed["fields"][0]["value"]
    assert "AAFcvCF0ZV" not in embed["footer"]["text"]


def test_scrub_messages_preserves_embed_without_secrets():
    from discord_mcp.tools import scrub_messages

    message = {
        "id": "m4",
        "content": "see embed",
        "embeds": [{"title": "Meeting notes", "description": "All clean here."}],
    }
    result = scrub_messages([message])[0]
    assert result["embeds"][0]["description"] == "All clean here."
