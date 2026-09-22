"""discord_threads tool — archived-thread listing for a channel.

Active-thread listing is bot-only (endpoints.md 2.7); archived public works
for user tokens, private is permission-gated best-effort.
"""

from __future__ import annotations

import json

from discord_mcp.auth import store
from discord_mcp.client import DiscordClient


async def discord_threads(channel_id: str) -> str:
    auth = store.load()
    async with DiscordClient(auth["token"]) as client:
        threads = await client.get_archived_threads(channel_id)
    entries: list[dict] = []
    for thread in threads:
        metadata = thread.get("thread_metadata", {})
        entries.append(
            {
                "id": thread.get("id"),
                "name": thread.get("name"),
                "type": thread.get("type"),
                "parent_id": thread.get("parent_id"),
                "archived_at": metadata.get("archive_timestamp"),
                "locked": metadata.get("locked"),
                "message_count": thread.get("message_count"),
                "member_count": thread.get("member_count"),
            }
        )
    return json.dumps(entries)
