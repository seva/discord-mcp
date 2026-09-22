import json
import sys
from unittest.mock import AsyncMock, patch

import pytest

from discord_mcp.__main__ import main


def test_cli_auth_captures_and_saves(tmp_path, monkeypatch):
    monkeypatch.setenv("DISCORD_MCP_DIR", str(tmp_path))
    with patch.object(sys, "argv", ["discord_mcp", "auth"]):
        with patch("discord_mcp.auth.browser.capture", return_value={"token": "tok"}) as mock:
            result = main()
    assert result == 0
    mock.assert_called_once()
    assert (tmp_path / "auth.dpapi").exists()


def test_cli_status_prints_user(capsys):
    payload = {"id": "1", "username": "swearlock", "global_name": None, "guild_count": 2}
    with patch.object(sys, "argv", ["discord_mcp", "status"]):
        with patch(
            "discord_mcp.tools.status.discord_status",
            new=AsyncMock(return_value=json.dumps(payload)),
        ):
            result = main()
    assert result == 0
    assert "swearlock" in capsys.readouterr().out


def test_cli_status_exits_on_auth_required(capsys):
    from discord_mcp.auth.store import AuthRequired

    with patch.object(sys, "argv", ["discord_mcp", "status"]):
        with patch(
            "discord_mcp.tools.status.discord_status",
            new=AsyncMock(side_effect=AuthRequired("Auth required")),
        ):
            result = main()
    assert result == 1
    assert "Auth required" in capsys.readouterr().err


def test_cli_serve_invokes_server_run():
    with patch.object(sys, "argv", ["discord_mcp", "serve"]):
        with patch("discord_mcp.server.run", return_value=None) as mock_run:
            result = main()
    assert result == 0
    mock_run.assert_called_once()


def test_cli_requires_subcommand():
    with patch.object(sys, "argv", ["discord_mcp"]):
        with pytest.raises(SystemExit):
            main()


def test_cli_unknown_command_exits():
    with patch.object(sys, "argv", ["discord_mcp", "bogus"]):
        with pytest.raises(SystemExit):
            main()
