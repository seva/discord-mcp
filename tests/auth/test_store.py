import time

import pytest

from discord_mcp.auth.store import AuthRequired, is_expired, load, save

SAMPLE = {"token": "sample-user-token", "captured_at": time.time()}


def test_save_writes_to_expected_path(tmp_path, monkeypatch):
    monkeypatch.setenv("DISCORD_MCP_DIR", str(tmp_path))
    save(SAMPLE)
    assert (tmp_path / "auth.dpapi").exists()


def test_saved_blob_is_not_plaintext(tmp_path, monkeypatch):
    monkeypatch.setenv("DISCORD_MCP_DIR", str(tmp_path))
    save(SAMPLE)
    blob = (tmp_path / "auth.dpapi").read_bytes()
    assert b"sample-user-token" not in blob


def test_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("DISCORD_MCP_DIR", str(tmp_path))
    save(SAMPLE)
    result = load()
    assert result["token"] == "sample-user-token"
    assert result["captured_at"] == SAMPLE["captured_at"]


def test_load_raises_when_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("DISCORD_MCP_DIR", str(tmp_path))
    with pytest.raises(AuthRequired):
        load()


def test_load_raises_on_corrupt_blob(tmp_path, monkeypatch):
    monkeypatch.setenv("DISCORD_MCP_DIR", str(tmp_path))
    (tmp_path / "auth.dpapi").write_bytes(b"not-a-valid-dpapi-blob")
    with pytest.raises(AuthRequired):
        load()


def test_is_expired_true_when_token_missing():
    assert is_expired({}) is True


def test_is_expired_true_when_token_empty():
    assert is_expired({"token": ""}) is True


def test_is_expired_false_when_token_present():
    assert is_expired({"token": "abc"}) is False


def test_is_expired_true_when_expired_flag_set():
    assert is_expired({"token": "abc", "expired": True}) is True
