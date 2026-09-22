"""Discord REST API v10 user-authenticated client.

Endpoints per docs/endpoints.md. All responses are returned as parsed JSON;
message-content scrubbing happens at the tools boundary, not here.
"""

from __future__ import annotations

import asyncio

import httpx

BASE_URL = "https://discord.com/api/v10"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
)
MAX_RETRIES = 3
# Discord's search endpoint returns 202 while results are computed asynchronously.
SEARCH_RETRY_INTERVAL = 2.0  # seconds


class AuthRequired(Exception):
    pass


class AccessDenied(Exception):
    pass


class NotFound(Exception):
    pass


class DiscordClient:
    """Async Discord REST client operating under a captured user token."""

    def __init__(self, token: str, base_url: str = BASE_URL):
        self._token = token
        self._base_url = base_url
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> DiscordClient:
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": self._token,
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            },
            timeout=10.0,
        )
        return self

    async def __aexit__(self, *exc) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(self, method: str, path: str, params: dict | None = None) -> object:
        assert self._client is not None, "Use 'async with DiscordClient(...)'"
        for _attempt in range(MAX_RETRIES):
            response = await self._client.request(method, path, params=params)
            if response.status_code == 429:
                retry_after = float(response.headers.get("Retry-After", 1))
                await asyncio.sleep(retry_after)
                continue
            if response.status_code == 202:
                # Search still computing; poll after a short interval.
                await asyncio.sleep(SEARCH_RETRY_INTERVAL)
                continue
            if response.status_code == 401:
                raise AuthRequired("Token invalid or expired. Run: python -m discord_mcp auth")
            if response.status_code == 403:
                raise AccessDenied(f"Missing permission for {path}")
            if response.status_code == 404:
                raise NotFound(f"Not found: {path}")
            response.raise_for_status()
            return response.json()
        raise RuntimeError(
            f"Rate limited or search incomplete after {MAX_RETRIES} retries on {path}"
        )

    async def get_current_user(self) -> dict:
        return await self._request("GET", "/users/@me")  # type: ignore[return-value]

    async def get_guilds(self) -> list[dict]:
        return await self._request("GET", "/users/@me/guilds")  # type: ignore[return-value]

    async def get_dm_channels(self) -> list[dict]:
        return await self._request("GET", "/users/@me/channels")  # type: ignore[return-value]

    async def get_guild_channels(self, guild_id: str) -> list[dict]:
        return await self._request("GET", f"/guilds/{guild_id}/channels")  # type: ignore[return-value]

    async def get_channel_messages(self, channel_id: str, limit: int = 10) -> list[dict]:
        return await self._request(
            "GET", f"/channels/{channel_id}/messages", params={"limit": limit}
        )  # type: ignore[return-value]

    async def get_archived_threads(self, channel_id: str) -> list[dict]:
        """Archived threads of a channel: public always; private best-effort.

        Private archived listing is permission-gated (MANAGE_THREADS / thread
        membership); AccessDenied there degrades to public-only, not an error.
        """
        threads: list[dict] = []
        for visibility in ("public", "private"):
            try:
                data = await self._request(
                    "GET", f"/channels/{channel_id}/threads/archived/{visibility}"
                )
                threads.extend(data["threads"])  # type: ignore[index]
            except AccessDenied:
                continue
        return threads

    async def search_guild_messages(
        self,
        guild_id: str,
        query: str,
        channel_id: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        params: dict = {"content": query}
        if channel_id:
            params["channel_id"] = channel_id
        data = await self._request("GET", f"/guilds/{guild_id}/messages/search", params=params)
        # Discord search returns nested arrays (match + context). Flatten.
        return [msg for block in data["messages"] for msg in block]  # type: ignore[index,return-value]
