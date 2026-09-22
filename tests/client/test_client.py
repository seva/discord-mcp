import httpx
import pytest
import respx

from discord_mcp.client import AccessDenied, AuthRequired, DiscordClient, NotFound

BASE = "https://discord.com/api/v10"
TOKEN = "test-user-token"


def _make_client() -> DiscordClient:
    return DiscordClient(TOKEN)


@respx.mock
@pytest.mark.asyncio
async def test_client_sends_user_token_header():
    respx.get(f"{BASE}/users/@me").mock(return_value=httpx.Response(200, json={"id": "1"}))
    async with _make_client() as client:
        await client.get_current_user()
    request = respx.calls.last.request
    assert request.headers["authorization"] == TOKEN
    assert "user-agent" in request.headers


@respx.mock
@pytest.mark.asyncio
async def test_get_current_user():
    respx.get(f"{BASE}/users/@me").mock(
        return_value=httpx.Response(200, json={"id": "931228531340496946", "username": "swearlock"})
    )
    async with _make_client() as client:
        result = await client.get_current_user()
    assert result["username"] == "swearlock"


@respx.mock
@pytest.mark.asyncio
async def test_get_guilds():
    respx.get(f"{BASE}/users/@me/guilds").mock(
        return_value=httpx.Response(
            200, json=[{"id": "1551377931866079312", "name": "PlayForKeeps"}]
        )
    )
    async with _make_client() as client:
        result = await client.get_guilds()
    assert result[0]["id"] == "1551377931866079312"


@respx.mock
@pytest.mark.asyncio
async def test_get_guild_channels():
    respx.get(f"{BASE}/guilds/1551377931866079312/channels").mock(
        return_value=httpx.Response(
            200, json=[{"id": "1478480447431376966", "type": 0, "name": "general"}]
        )
    )
    async with _make_client() as client:
        result = await client.get_guild_channels("1551377931866079312")
    assert result[0]["name"] == "general"


@respx.mock
@pytest.mark.asyncio
async def test_get_channel_messages_limit_param():
    respx.get(f"{BASE}/channels/123/messages").mock(return_value=httpx.Response(200, json=[]))
    async with _make_client() as client:
        await client.get_channel_messages("123", limit=25)
    request = respx.calls.last.request
    assert "limit=25" in str(request.url)


@respx.mock
@pytest.mark.asyncio
async def test_search_guild_messages_flattens_nested_results():
    nested = {
        "total_results": 1,
        "messages": [
            [
                {"id": "m1", "content": "hello world", "author": {"username": "a"}},
                {"id": "m2", "content": "context message", "author": {"username": "b"}},
            ]
        ],
    }
    respx.get(f"{BASE}/guilds/1551377931866079312/messages/search").mock(
        return_value=httpx.Response(200, json=nested)
    )
    async with _make_client() as client:
        result = await client.search_guild_messages("1551377931866079312", "hello")
    assert len(result) == 2
    assert result[0]["content"] == "hello world"


@respx.mock
@pytest.mark.asyncio
async def test_401_raises_auth_required():
    respx.get(f"{BASE}/users/@me").mock(return_value=httpx.Response(401))
    with pytest.raises(AuthRequired):
        async with _make_client() as client:
            await client.get_current_user()


@respx.mock
@pytest.mark.asyncio
async def test_403_raises_access_denied():
    respx.get(f"{BASE}/channels/123/messages").mock(return_value=httpx.Response(403))
    with pytest.raises(AccessDenied):
        async with _make_client() as client:
            await client.get_channel_messages("123")


@respx.mock
@pytest.mark.asyncio
async def test_404_raises_not_found():
    respx.get(f"{BASE}/channels/123/messages").mock(return_value=httpx.Response(404))
    with pytest.raises(NotFound):
        async with _make_client() as client:
            await client.get_channel_messages("123")


@respx.mock
@pytest.mark.asyncio
async def test_429_backs_off_then_succeeds():
    route = respx.get(f"{BASE}/channels/123/messages").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}),
            httpx.Response(200, json=[{"id": "m1", "content": "after backoff"}]),
        ]
    )
    async with _make_client() as client:
        result = await client.get_channel_messages("123")
    assert result[0]["content"] == "after backoff"
    assert route.call_count == 2
