import json
import os
import subprocess
import sys

import anyio
import httpx
import pytest
import respx
from mcp.client.session import ClientSession
from mcp.shared.message import SessionMessage
from mcp.types import TextContent

from discord_mcp.auth.store import save
from discord_mcp.client import BASE_URL
from discord_mcp.server import mcp


def test_run_exits_when_auth_missing(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "discord_mcp", "serve"],
        capture_output=True,
        text=True,
        env={**os.environ, "DISCORD_MCP_DIR": str(tmp_path)},
    )
    assert result.returncode == 1
    assert "Auth required" in result.stderr


def test_run_exits_when_auth_expired(tmp_path):
    os.environ["DISCORD_MCP_DIR"] = str(tmp_path)
    try:
        save({"token": "", "expired": True})
    finally:
        os.environ.pop("DISCORD_MCP_DIR")

    result = subprocess.run(
        [sys.executable, "-m", "discord_mcp", "serve"],
        capture_output=True,
        text=True,
        env={**os.environ, "DISCORD_MCP_DIR": str(tmp_path)},
    )
    assert result.returncode == 1
    assert "Auth expired" in result.stderr


def test_tool_registration():
    tools = {t.name: t for t in mcp._tool_manager.list_tools()}

    expected = {
        "discord_status",
        "discord_channels",
        "discord_messages",
        "discord_search",
        "discord_dms",
    }
    assert expected == set(tools.keys())

    props = tools["discord_messages"].parameters.get("properties", {})
    assert "channel_id" in props and props["channel_id"].get("type") == "string"

    props = tools["discord_search"].parameters.get("properties", {})
    assert "query" in props and props["query"].get("type") == "string"


@respx.mock
@pytest.mark.asyncio
async def test_call_tool_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("DISCORD_MCP_DIR", str(tmp_path))
    save({"token": "test-user-token"})
    respx.get(f"{BASE_URL}/users/@me").mock(
        return_value=httpx.Response(200, json={"id": "1", "username": "swearlock"})
    )
    respx.get(f"{BASE_URL}/users/@me/guilds").mock(
        return_value=httpx.Response(200, json=[{"id": "2", "name": "PlayForKeeps"}])
    )

    client_to_server_send, client_to_server_recv = anyio.create_memory_object_stream[
        SessionMessage | Exception
    ](16)
    server_to_client_send, server_to_client_recv = anyio.create_memory_object_stream[
        SessionMessage
    ](16)

    async def _run_server():
        await mcp._mcp_server.run(
            client_to_server_recv,
            server_to_client_send,
            mcp._mcp_server.create_initialization_options(),
            raise_exceptions=True,
        )

    async with anyio.create_task_group() as tg:
        tg.start_soon(_run_server)

        async with ClientSession(
            server_to_client_recv,
            client_to_server_send,
        ) as client:
            await client.initialize()

            result = await client.call_tool("discord_status", {})

            tg.cancel_scope.cancel()

    assert not result.isError
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert json.loads(result.content[0].text) == {
        "id": "1",
        "username": "swearlock",
        "global_name": None,
        "guild_count": 1,
    }
