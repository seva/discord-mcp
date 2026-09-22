import json
import os
from pathlib import Path

import win32crypt


class AuthRequired(Exception):
    pass


def _auth_path() -> Path:
    return Path(os.environ.get("DISCORD_MCP_DIR", Path.home() / ".discord-mcp")) / "auth.dpapi"


def save(data: dict) -> None:
    path = _auth_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(data).encode()
    encrypted = win32crypt.CryptProtectData(blob, None, None, None, None, 0)
    path.write_bytes(encrypted)


def load() -> dict:
    path = _auth_path()
    if not path.exists():
        raise AuthRequired("No auth file found. Run: python -m discord_mcp auth")
    try:
        encrypted = path.read_bytes()
        _, blob = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)
        return json.loads(blob.decode())
    except AuthRequired:
        raise
    except Exception as e:
        raise AuthRequired(
            f"Auth file corrupt or unreadable: {e}. Run: python -m discord_mcp auth"
        ) from e


def is_expired(data: dict) -> bool:
    if not data.get("token"):
        return True
    if data.get("expired"):
        return True
    return False
