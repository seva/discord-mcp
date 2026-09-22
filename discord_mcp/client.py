"""Discord REST API v10 user-authenticated client.

Endpoints per docs/endpoints.md. All responses are returned as parsed JSON;
message-content scrubbing happens at the tools boundary, not here.
"""

from __future__ import annotations

import asyncio
import time

import httpx

BASE_URL = "https://discord.com/api/v10"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
)
MAX_RETRIES = 3
# Discord's search endpoint returns 202 while results are computed asynchronously.
SEARCH_RETRY_INTERVAL = 2.0  # seconds
# Per-process GET cache: 60s per Ichnos channel-matrix precedent.
DEFAULT_CACHE_TTL = 60.0  # seconds
CACHE_MAX_ENTRIES = 256


class AuthRequired(Exception):
    pass


class AccessDenied(Exception):
    pass


class NotFound(Exception):
    pass


class DiscordClient:
    """Async Discord REST client operating under a captured user token."""

    def __init__(self, token: str, base_url: str = BASE_URL, cache_ttl: float = DEFAULT_CACHE_TTL):
        self._token = token
        self._base_url = base_url
        self._client: httpx.AsyncClient | None = None
        self._cache: dict[tuple, tuple[float, object]] = {}
        self._cache_ttl = cache_ttl

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

    def _cache_key(self, method: str, path: str, params: dict | None) -> tuple:
        return (method, path, tuple(sorted((params or {}).items())))

    async def _request(self, method: str, path: str, params: dict | None = None) -> object:
        assert self._client is not None, "Use 'async with DiscordClient(...)'"
        key: tuple | None = None
        if method == "GET":
            key = self._cache_key(method, path, params)
            entry = self._cache.get(key)
            if entry and time.monotonic() - entry[0] < self._cache_ttl:
                return entry[1]
            if entry is None and len(self._cache) >= CACHE_MAX_ENTRIES:
                oldest = min(self._cache, key=lambda k: self._cache[k][0])
                del self._cache[oldest]
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
            data = response.json()
            if key is not None:
                self._cache[key] = (time.monotonic(), data)
            return data
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
        # Discord search returns nested arrays (match + context). Flatten; the
        # endpoint has no server-side limit param, so `limit` truncates client-side.
        return [msg for block in data["messages"] for msg in block][:limit]  # type: ignore[index,return-value]
