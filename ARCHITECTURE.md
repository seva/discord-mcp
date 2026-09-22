# discord-mcp — System Architecture

FastMCP server exposing Discord context to MCP clients via Playwright web authentication and Windows DPAPI credential protection.

---

## 1. System Overview

```
 MCP Client (OpenCode / OpenClaw / Claude)
                   │
                   │ stdio (JSON-RPC)
                   ▼
     ┌───────────────────────────┐
     │  discord_mcp.server       │ ◄── FastMCP
     └─────────────┬─────────────┘
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
┌──────────────┐       ┌──────────────┐
│ Tools Layer  │       │ Scrub Layer  │ ◄── Redacts tokens, keys, OTPs
└──────┬───────┘       └──────────────┘
       │
       ▼
┌──────────────┐
│ Client Layer │ ◄── Discord REST API v10 (User Bearer Auth)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Auth Layer  │ ◄── Windows DPAPI (~/.discord-mcp/auth.dpapi) & Playwright
└──────────────┘
```

---

## 2. Component Specifications

### 2.1 Auth Module (`discord_mcp.auth`)
- **`discord_mcp.auth.store`**:
  - `_auth_path() -> Path`: Default `~/.discord-mcp/auth.dpapi`, overridable via `DISCORD_MCP_DIR`.
  - `save(data: dict) -> None`: Serializes token metadata to JSON, encrypts with `win32crypt.CryptProtectData`, writes binary ciphertext to disk.
  - `load() -> dict`: Reads binary ciphertext, decrypts with `win32crypt.CryptUnprotectData`, deserializes JSON. Raises `AuthRequired` on missing or corrupt file.
  - `is_expired(data: dict) -> bool`: True when the token string is missing/empty or an explicit `expired` flag is set.
- **`discord_mcp.auth.browser`**:
  - `capture(timeout: int = 300) -> dict`: Launches interactive Chromium via `playwright.async_api.async_playwright()`.
  - Intercepts requests to `discord.com/api/`, extracting the `Authorization` header (Bot-prefixed tokens rejected).
  - Returns `{"token": token_str, "captured_at": timestamp}`.

### 2.2 Secret-Scrub Boundary (`discord_mcp.scrub`)
- **`scrub_text(text: str) -> tuple[str, list[dict[str, Any]]]`**:
  - Boundary filter applied to all Discord message content before exposing it across the MCP interface.
  - Redacts:
    - Private key blocks (`[REDACTED:PRIVATE_KEY]`)
    - GitHub personal access tokens (`[REDACTED:GITHUB_TOKEN]`)
    - API keys (`sk-...`) (`[REDACTED:API_KEY]`)
    - Bot tokens (`\d{8,11}:[A-Za-z0-9_-]{35}`) (`[REDACTED:BOT_TOKEN]`)
    - URL secret parameters (`token=...`, `key=...`, `api_key=...`) (`[REDACTED:URL_SECRET]`)
    - 6-to-8 digit OTPs preceded by OTP keywords (`[REDACTED:OTP]`)
  - **`discord_mcp.tools.scrub_messages(messages) -> list[dict]`**: applies `scrub_text` to every free-text surface of each message — `content` plus embeds (`title`, `description`, `fields[].value`, `footer.text`, `author.name`).

### 2.3 Discord API Client (`discord_mcp.client`)
- **`DiscordClient`**:
  - Uses `httpx.AsyncClient` with standard Discord user headers:
    - `Authorization`: Captured user bearer token (without `Bot ` prefix).
    - `User-Agent`: Chrome browser user agent matching browser capture.
  - Methods:
    - `get_current_user() -> dict`: `GET /users/@me`
    - `get_guilds() -> list[dict]`: `GET /users/@me/guilds`
    - `get_guild_channels(guild_id: str) -> list[dict]`: `GET /guilds/{guild_id}/channels`
    - `get_channel_messages(channel_id: str, limit: int = 10) -> list[dict]`: `GET /channels/{channel_id}/messages?limit={limit}`
    - `search_guild_messages(guild_id: str, query: str, channel_id: str | None = None, limit: int = 10) -> list[dict]`: `GET /guilds/{guild_id}/messages/search?content={query}`
  - Rate limit handling: On HTTP 429, reads `Retry-After` header and sleeps before retrying (max 3 retries). Proactive `X-RateLimit-*` budgeting is an L2 ladder rung, not current behavior.
  - Error types: `AuthRequired` (401 — token invalid/expired, distinct from the store's `AuthRequired`), `AccessDenied` (403), `NotFound` (404), `RuntimeError` (rate-limit retries exhausted).

### 2.4 FastMCP Server & Tools (`discord_mcp.server`, `discord_mcp.tools`)
- Server exposes 4 tools:
  - `discord_status()`: Authenticated user handle, user ID, guild count.
  - `discord_channels(guild_id: str | None = None)`: Accessible guilds and channel hierarchy.
  - `discord_messages(channel_id: str, limit: int = 10)`: Recent channel messages (scrubbed).
  - `discord_search(query: str, guild_id: str | None = None, channel_id: str | None = None, limit: int = 10)`: Guild message search results (scrubbed).

### 2.5 CLI Interface (`discord_mcp.__main__`)
- Commands:
  - `python -m discord_mcp auth`: Launches browser login and DPAPI storage.
  - `python -m discord_mcp status`: Verifies connectivity and prints authenticated user.
  - `python -m discord_mcp serve`: Runs FastMCP server over stdio.

---

## 3. Engineering Invariants & Banned Patterns

### Invariants
1. **Boundary Defense:** All external message content passes through `scrub_text` before returning from any tool.
2. **DPAPI Security at Rest:** No plaintext session tokens are ever written to disk or logged. All credentials pass through `win32crypt`.
3. **No Desktop App Hooking:** Zero runtime dependency on desktop Discord client files, locks, or databases.
4. **Indirection Cap:** Maximum call chain depth of 3 hops (Server -> Tool -> Client). No superfluous abstraction layers.

### Banned Patterns
1. **Plaintext Secret Caching:** Never save auth tokens to `.env`, json config, or sqlite without encryption.
2. **Mocking Internal Boundaries in System Tests:** Internal boundaries use real function calls; mocks are reserved strictly for external Discord HTTP endpoints (`respx`) and Playwright browser UI.
3. **Premature Multi-process Orchestration:** Standalone stdio service; no background daemons or multi-worker clustering.
