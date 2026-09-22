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
        "discord_dms",
        "discord_messages",
        "discord_search",
        "discord_threads",
    }
    assert expected == set(tools.keys())

    props = tools["discord_messages"].parameters.get("properties", {})
    assert "channel_id" in props and props["channel_id"].get("type") == "string"

    props = tools["discord_search"].parameters.get("properties", {})
    assert "query" in props and props["query"].get("type") == "string"


def test_build_mcp_factory_pins_tools_and_settings():
    from discord_mcp.server import build_mcp

    instance = build_mcp(port=9123)
    tools = {t.name for t in instance._tool_manager.list_tools()}
    assert tools == {
        "discord_status",
        "discord_channels",
        "discord_dms",
        "discord_messages",
        "discord_search",
        "discord_threads",
    }
    assert instance.settings.port == 9123
    assert instance.settings.host == "127.0.0.1"


def _free_port() -> int:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_http_transport_end_to_end(tmp_path):
    """Real streamable-HTTP round trip over a live subprocess (initialize + list_tools only — no Discord calls)."""
    import time

    import httpx as _httpx

    os.environ["DISCORD_MCP_DIR"] = str(tmp_path)
    try:
        save({"token": "test-user-token"})
    finally:
        os.environ.pop("DISCORD_MCP_DIR")

    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "discord_mcp", "serve", "--transport", "http", "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        # Poll until uvicorn accepts connections (any HTTP response proves it is up).
        ready = False
        for _ in range(60):
            if proc.poll() is not None:
                break
            try:
                _httpx.get(f"http://127.0.0.1:{port}/mcp", timeout=1)
                ready = True
                break
            except _httpx.HTTPError:
                time.sleep(0.5)
        assert ready, (
            f"HTTP server did not come up; stderr={proc.stderr.read() if proc.stderr else ''}"
        )

        from mcp.client.session import ClientSession
        from mcp.client.streamable_http import streamablehttp_client

        async def _call():
            async with streamablehttp_client(f"http://127.0.0.1:{port}/mcp") as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    listed = await session.list_tools()
                    return {t.name for t in listed.tools}

        tools = anyio.run(_call)
        assert tools == {
            "discord_status",
            "discord_channels",
            "discord_dms",
            "discord_messages",
            "discord_search",
            "discord_threads",
        }
    finally:
        proc.kill()


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
