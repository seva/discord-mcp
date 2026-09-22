"""discord_status tool — authenticated user identity and guild count."""

from __future__ import annotations

import json

from discord_mcp.auth import store
from discord_mcp.client import DiscordClient


async def discord_status() -> str:
    auth = store.load()
    async with DiscordClient(auth["token"]) as client:
        user = await client.get_current_user()
        guilds = await client.get_guilds()
    return json.dumps(
        {
            "id": user.get("id"),
            "username": user.get("username"),
            "global_name": user.get("global_name"),
            "guild_count": len(guilds),
        }
    )
