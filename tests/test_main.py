import sys
from unittest.mock import patch

import httpx
import pytest
import respx

from discord_mcp.__main__ import main
from discord_mcp.auth import store
from discord_mcp.client import BASE_URL


def test_cli_auth_captures_and_saves(tmp_path, monkeypatch):
    monkeypatch.setenv("DISCORD_MCP_DIR", str(tmp_path))
    with patch.object(sys, "argv", ["discord_mcp", "auth"]):
        with patch("discord_mcp.auth.browser.capture", return_value={"token": "tok"}) as mock:
            result = main()
    assert result == 0
    mock.assert_called_once()
    assert (tmp_path / "auth.dpapi").exists()


@respx.mock
def test_cli_status_prints_user(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DISCORD_MCP_DIR", str(tmp_path))
    store.save({"token": "test-user-token"})
    respx.get(f"{BASE_URL}/users/@me").mock(
        return_value=httpx.Response(200, json={"id": "1", "username": "swearlock"})
    )
    respx.get(f"{BASE_URL}/users/@me/guilds").mock(return_value=httpx.Response(200, json=[]))

    with patch.object(sys, "argv", ["discord_mcp", "status"]):
        result = main()
    assert result == 0
    assert "swearlock" in capsys.readouterr().out


def test_cli_status_exits_on_auth_required(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DISCORD_MCP_DIR", str(tmp_path))

    with patch.object(sys, "argv", ["discord_mcp", "status"]):
        result = main()
    assert result == 1
    assert "No auth file found" in capsys.readouterr().err


def test_cli_serve_invokes_transport_run(tmp_path, monkeypatch):
    monkeypatch.setenv("DISCORD_MCP_DIR", str(tmp_path))
    store.save({"token": "test-user-token"})
    with patch.object(sys, "argv", ["discord_mcp", "serve"]):
        with patch("discord_mcp.server.mcp.run", return_value=None) as mock_run:
            result = main()
    assert result == 0
    mock_run.assert_called_once_with(transport="stdio")


def test_cli_serve_http_transport_builds_configured_instance():
    with patch.object(
        sys, "argv", ["discord_mcp", "serve", "--transport", "http", "--port", "9123"]
    ):
        with patch("discord_mcp.server.build_mcp") as mock_build:
            instance = mock_build.return_value
            result = main()
    assert result == 0
    mock_build.assert_called_once_with(port=9123)
    instance.run.assert_called_once_with("streamable-http")


def test_cli_requires_subcommand():
    with patch.object(sys, "argv", ["discord_mcp"]):
        with pytest.raises(SystemExit):
            main()


def test_cli_unknown_command_exits():
    with patch.object(sys, "argv", ["discord_mcp", "bogus"]):
        with pytest.raises(SystemExit):
            main()
