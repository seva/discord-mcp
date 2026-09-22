import json

import httpx
import pytest
import respx

from discord_mcp.auth import store
from discord_mcp.auth.store import AuthRequired
from discord_mcp.client import BASE_URL

BASE = BASE_URL
TOKEN = "test-user-token"

GUILD = {"id": "1551377931866079312", "name": "PlayForKeeps"}
USER = {"id": "931228531340496946", "username": "swearlock"}
SECRET_MSG = {
    "id": "m1",
    "content": "my key sk-ant-1234567890abcdef1234567890abcdef12345678",
    "author": {"username": "someone"},
}
CLEAN_MSG = {"id": "m2", "content": "lunch at noon", "author": {"username": "someone"}}


@pytest.fixture
def auth(tmp_path, monkeypatch):
    monkeypatch.setenv("DISCORD_MCP_DIR", str(tmp_path))
    store.save({"token": TOKEN})


@respx.mock
@pytest.mark.asyncio
async def test_status_returns_user_and_guild_count(auth):
    respx.get(f"{BASE}/users/@me").mock(return_value=httpx.Response(200, json=USER))
    respx.get(f"{BASE}/users/@me/guilds").mock(return_value=httpx.Response(200, json=[GUILD]))

    from discord_mcp.tools.status import discord_status

    result = json.loads(await discord_status())
    assert result["username"] == "swearlock"
    assert result["guild_count"] == 1


@pytest.mark.asyncio
async def test_status_raises_auth_required_without_token(tmp_path, monkeypatch):
    monkeypatch.setenv("DISCORD_MCP_DIR", str(tmp_path))

    from discord_mcp.tools.status import discord_status

    with pytest.raises(AuthRequired):
        await discord_status()


@respx.mock
@pytest.mark.asyncio
async def test_channels_lists_guilds(auth):
    respx.get(f"{BASE}/users/@me/guilds").mock(return_value=httpx.Response(200, json=[GUILD]))

    from discord_mcp.tools.channels import discord_channels

    result = json.loads(await discord_channels())
    assert result[0]["name"] == "PlayForKeeps"


@respx.mock
@pytest.mark.asyncio
async def test_channels_with_guild_id_returns_channels(auth):
    channels = [{"id": "1478480447431376966", "type": 0, "name": "general"}]
    route = respx.get(f"{BASE}/guilds/1551377931866079312/channels").mock(
        return_value=httpx.Response(200, json=channels)
    )

    from discord_mcp.tools.channels import discord_channels

    result = json.loads(await discord_channels(guild_id="1551377931866079312"))
    assert result[0]["id"] == "1478480447431376966"
    assert route.called
    assert "guilds/1551377931866079312/channels" in str(respx.calls.last.request.url)


@respx.mock
@pytest.mark.asyncio
async def test_messages_scrubs_secret_content(auth):
    respx.get(f"{BASE}/channels/123/messages").mock(
        return_value=httpx.Response(200, json=[SECRET_MSG, CLEAN_MSG])
    )

    from discord_mcp.tools.messages import discord_messages

    result = json.loads(await discord_messages("123", limit=2))
    assert "sk-ant-" not in result[0]["content"]
    assert "[REDACTED:API_KEY]" in result[0]["content"]
    assert result[1]["content"] == "lunch at noon"


@respx.mock
@pytest.mark.asyncio
async def test_search_scrubs_and_flattens(auth):
    route = respx.get(f"{BASE}/guilds/1551377931866079312/messages/search").mock(
        return_value=httpx.Response(
            200, json={"total_results": 2, "messages": [[SECRET_MSG, CLEAN_MSG]]}
        )
    )

    from discord_mcp.tools.search import discord_search

    result = json.loads(await discord_search("key", guild_id="1551377931866079312"))
    assert "[REDACTED:API_KEY]" in result[0]["content"]
    assert route.called
    url = str(respx.calls.last.request.url)
    assert "content=key" in url


@pytest.mark.asyncio
async def test_search_without_guild_id_raises(auth):
    from discord_mcp.tools.search import discord_search

    with pytest.raises(ValueError):
        await discord_search("key")


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
