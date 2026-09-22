"""discord_dms tool — DM and group-DM channel listing with derived labels.

Plain DMs (type 1) carry no name; identity lives in recipients (endpoints.md 2.6).
"""

from __future__ import annotations

import json

from discord_mcp.auth import store
from discord_mcp.client import DiscordClient


async def discord_dms() -> str:
    auth = store.load()
    async with DiscordClient(auth["token"]) as client:
        channels = await client.get_dm_channels()
    entries: list[dict] = []
    for channel in channels:
        recipients = [r.get("username") for r in channel.get("recipients", [])]
        name = channel.get("name")
        label = name if name else ", ".join(filter(None, recipients)) or "unknown"
        entries.append(
            {
                "id": channel.get("id"),
                "type": channel.get("type"),
                "label": label,
                "recipients": recipients,
            }
        )
    return json.dumps(entries)
