"""discord_channels tool — accessible guilds and channel hierarchy."""

from __future__ import annotations

import json

from discord_mcp.auth import store
from discord_mcp.client import DiscordClient


async def discord_channels(guild_id: str | None = None) -> str:
    auth = store.load()
    async with DiscordClient(auth["token"]) as client:
        if guild_id:
            channels = await client.get_guild_channels(guild_id)
            return json.dumps(
                [
                    {
                        "id": c.get("id"),
                        "type": c.get("type"),
                        "name": c.get("name"),
                        "parent_id": c.get("parent_id"),
                    }
                    for c in channels
                ]
            )
        guilds = await client.get_guilds()
        return json.dumps(
            [
                {
                    "id": g.get("id"),
                    "name": g.get("name"),
                    "owner": g.get("owner"),
                    "permissions": g.get("permissions"),
                }
                for g in guilds
            ]
        )
