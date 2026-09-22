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


DM_CHANNELS = [
    {
        "id": "552672738930851851",
        "type": 1,
        "flags": 0,
        "recipient_flags": 0,
        "recipients": [
            {"id": "540654797414465581", "username": "mathslap", "global_name": "mathslap"}
        ],
    },
    {
        "id": "552672738930851852",
        "type": 3,
        "name": "the boys",
        "flags": 0,
        "recipient_flags": 0,
        "recipients": [{"id": "1", "username": "a", "global_name": "A"}],
    },
]


@respx.mock
@pytest.mark.asyncio
async def test_dms_derives_labels_from_recipients(auth):
    respx.get(f"{BASE}/users/@me/channels").mock(return_value=httpx.Response(200, json=DM_CHANNELS))

    from discord_mcp.tools.dms import discord_dms

    result = json.loads(await discord_dms())
    # type-1 DM: label from recipients (no name field)
    assert result[0]["id"] == "552672738930851851"
    assert result[0]["label"] == "mathslap"
    assert result[0]["type"] == 1
    # type-3 group DM: label from name
    assert result[1]["label"] == "the boys"
    assert result[1]["type"] == 3
    # channel ids are usable by discord_messages
    assert all("id" in entry and "type" in entry and "label" in entry for entry in result)


ARCHIVED_PUBLIC = {
    "has_more": False,
    "members": [],
    "threads": [
        {
            "id": "1288145052110946468",
            "type": 10,
            "name": "Exciting News",
            "parent_id": "1092243196798582928",
            "guild_id": "1092243196446249134",
            "member_count": 50,
            "message_count": 12,
            "thread_metadata": {
                "archived": True,
                "archive_timestamp": "2024-10-24T19:15:09.980000+00:00",
                "locked": False,
            },
        }
    ],
}
ARCHIVED_PRIVATE = {"has_more": False, "members": [], "threads": []}


@respx.mock
@pytest.mark.asyncio
async def test_threads_returns_archived_thread_entries(auth):
    respx.get(f"{BASE}/channels/123/threads/archived/public").mock(
        return_value=httpx.Response(200, json=ARCHIVED_PUBLIC)
    )
    respx.get(f"{BASE}/channels/123/threads/archived/private").mock(
        return_value=httpx.Response(200, json=ARCHIVED_PRIVATE)
    )

    from discord_mcp.tools.threads import discord_threads

    result = json.loads(await discord_threads("123"))
    assert len(result) == 1
    entry = result[0]
    assert entry["id"] == "1288145052110946468"
    assert entry["name"] == "Exciting News"
    assert entry["parent_id"] == "1092243196798582928"
    assert entry["archived_at"] == "2024-10-24T19:15:09.980000+00:00"
    assert entry["locked"] is False
    assert entry["message_count"] == 12


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
