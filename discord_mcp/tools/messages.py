"""discord_messages tool — recent channel messages behind the scrub boundary."""

from __future__ import annotations

import json

from discord_mcp.auth import store
from discord_mcp.client import DiscordClient
from discord_mcp.tools import scrub_messages


async def discord_messages(channel_id: str, limit: int = 10) -> str:
    auth = store.load()
    async with DiscordClient(auth["token"]) as client:
        messages = await client.get_channel_messages(channel_id, limit=limit)
    return json.dumps(scrub_messages(messages))
