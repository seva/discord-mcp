"""discord_search tool — guild message search behind the scrub boundary."""

from __future__ import annotations

import json

from discord_mcp.auth import store
from discord_mcp.client import DiscordClient
from discord_mcp.tools import scrub_messages


async def discord_search(
    query: str,
    guild_id: str | None = None,
    channel_id: str | None = None,
    limit: int = 10,
) -> str:
    if not guild_id:
        raise ValueError("guild_id is required for message search")
    auth = store.load()
    async with DiscordClient(auth["token"]) as client:
        messages = await client.search_guild_messages(guild_id, query, channel_id, limit)
    return json.dumps(scrub_messages(messages))
