import sys

from mcp.server.fastmcp import FastMCP

from discord_mcp.auth import store
from discord_mcp.auth.store import AuthRequired
from discord_mcp.tools import channels as channels_tool
from discord_mcp.tools import dms as dms_tool
from discord_mcp.tools import messages as messages_tool
from discord_mcp.tools import search as search_tool
from discord_mcp.tools import status as status_tool

mcp = FastMCP("discord")


@mcp.tool()
async def discord_status() -> str:
    """Return the authenticated Discord user and count of accessible guilds."""
    return await status_tool.discord_status()


@mcp.tool()
async def discord_channels(guild_id: str | None = None) -> str:
    """List accessible guilds, or the channels of one guild when guild_id is given."""
    return await channels_tool.discord_channels(guild_id)


@mcp.tool()
async def discord_messages(channel_id: str, limit: int = 10) -> str:
    """Fetch recent messages from a channel (secret-scrubbed)."""
    return await messages_tool.discord_messages(channel_id, limit)


@mcp.tool()
async def discord_dms() -> str:
    """List the user's DM and group-DM channels with derived labels."""
    return await dms_tool.discord_dms()


@mcp.tool()
async def discord_search(
    query: str,
    guild_id: str | None = None,
    channel_id: str | None = None,
    limit: int = 10,
) -> str:
    """Search message content in a guild (secret-scrubbed). Requires guild_id."""
    return await search_tool.discord_search(query, guild_id, channel_id, limit)


def run():
    try:
        auth = store.load()
    except AuthRequired:
        print("Auth required. Run: python -m discord_mcp auth", file=sys.stderr)
        sys.exit(1)

    if store.is_expired(auth):
        print("Auth expired. Run: python -m discord_mcp auth", file=sys.stderr)
        sys.exit(1)

    mcp.run(transport="stdio")
