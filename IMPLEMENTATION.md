# discord-mcp — Implementation State

Task state machine tracked under Epistegrity methodology.
WIP Limit = 1. Done means tests pass, invariants hold, and evidence is recorded.

---

## Phase 0: Discovery & Grounding
- [x] Document Discord API v10 user-facing endpoints in `docs/endpoints.md`
- [x] Define maximal scope ladder and terminal bounds in `docs/scope.md`

## Phase 1: Authentication & DPAPI Storage
- [x] Tests for DPAPI storage (`tests/auth/test_store.py`)
- [x] Implement DPAPI store (`discord_mcp/auth/store.py`)
- [x] Tests for Playwright browser capture (`tests/auth/test_browser.py`)
- [x] Implement Playwright browser capture (`discord_mcp/auth/browser.py`)

## Phase 2: Secret-Scrub Boundary & Discord Client
- [x] Tests for secret-scrub boundary (`tests/client/test_scrub.py`)
- [x] Implement secret-scrub filter (`discord_mcp/scrub.py`)
- [x] Tests for Discord REST client (`tests/client/test_client.py`)
- [x] Implement Discord REST client (`discord_mcp/client.py`)

## Phase 3: FastMCP Tools & Server
- [x] Tests for MCP tools (`tests/tools/test_tools.py`)
- [x] Implement MCP tools (`discord_mcp/tools/`)
- [x] Tests for FastMCP stdio server (`tests/server/test_server.py`)
- [x] Implement FastMCP server (`discord_mcp/server.py`)

## Phase 4: CLI Interface & Verification
- [x] Tests for CLI entrypoint (`tests/test_main.py`)
- [x] Implement CLI entrypoint (`discord_mcp/__main__.py`)
- [x] Verify test suite passes with coverage and ruff linting clean

## Phase 5: Post-Phase Audit & WaLRuS-DATA
- [x] Execute 6-step Epistegrity Post-Phase Audit
- [x] Commit WaLRuS session summary (`docs/walrus-YYYY-MM-DD.md`)

## L2 Rung — Resilience & Depth (complete, externally audited)
- [x] Post-L2 self-scan repair: search `limit` contract was silently ignored — client-side truncation (endpoint has no server-side limit param, endpoints.md 2.5); tests-first + live re-probe (limit=3 → 3)
- [ ] L3 rung: HTTP transport (`serve` over streamable-HTTP) — this repo's L3 contribution; Ichnos-side consumer is Ichnos's cycle
- [x] DM resolution discovery: live `GET /users/@me/channels` probe (commitment record: Activation = live 200 with parseable channel array — held; Continuation = shapes matching endpoints.md entry — recorded in §2.6; Exit = endpoint unusable for user tokens — did not fire). 27 channels observed (25 DM, 2 group DM); `discord_messages` verified reading a DM channel ID.
- [x] DM listing surface (tests-first): expose DM channels to MCP clients (tool or channels extension) — implemented as new `discord_dms` tool (Owner-approved option A); client `get_dm_channels()`; labels derived from recipients (type-1) / name (type-3); live probe: 27 channels over MCP boundary, isError=False
- [x] TTL cache layer (tests-first): per-key TTL for `/users/@me/guilds`, `/guilds/{id}/channels`, `/channels/{id}/messages` — implemented transparently in `DiscordClient._request` (GET-only, 60s default, 200-only, 256-entry bound, params-distinguished keys). 4 new tests. Live: two identical `discord_channels` MCP calls produced one HTTP request (second = cache hit, identical payload). Commitment record: Activation held; Continuation = cache-hit live observation held; Invalidation watch = stale claims / rate-limit violations; Exit = cache is process-local and dies with the client context.
- [x] `X-RateLimit-*` budgeting attempt — FALSIFIED by live probe: user tokens receive NO `X-RateLimit-*` headers on 200s (verified live across `/users/@me`, `/users/@me/guilds`, `/channels/{id}/messages`); only `Retry-After` on 429 exists as a signal. Code was written against a bot-API assumption before live-verifying the header surface — Phase-Gate violation, caught by the probe, reverted same-step. endpoints.md §3 corrected. Cache dir complete: cache (primary volume defense) + reactive backoff (fallback) are the only available levers for user tokens.
- [x] L2 completion: external audit round (Critic on accumulated state since seed audit) — Critic: 2 MATERIAL + 5 MINOR, all closed (fce2b39); Auditor verdict after G1 repair: PASS — role-separated gate complete
- [x] Thread traversal discovery: `GET /guilds/{id}/threads/active` + `GET /channels/{id}/threads/archived/public` live probes (commitment record: Activation — archived endpoint live 200, held; active-threads Exit FIRED — 403 code 20002, bot-only, structural platform constraint). Traversal for user tokens = archived lists + ID-based reads (search surfaces thread IDs). Shape recorded in endpoints.md §2.7.
- [x] Thread listing surface (tests-first): expose archived-thread listing per channel to MCP clients — new `discord_threads(channel_id)` tool; client `get_archived_threads()` (public + private best-effort, AccessDenied degrades to public-only); Phase-Gate probe of private archived = 403 permission-gated (not bot-only); live probe: 2 archived threads over MCP boundary, isError=False
- [x] Live probe `discord_threads` over the MCP boundary — isError=False, 2 archived threads (AutoGPT channel); private-archived 403 degraded to public-only as designed

## Live Verification (L1 rung)
- [x] Substrate: `pip install -e .` — package importable from any cwd
- [x] Operator live auth: `python -m discord_mcp auth` → token captured, DPAPI-encrypted at `~/.discord-mcp/auth.dpapi`
- [x] `python -m discord_mcp status` → 200 OK, `swearlock`, 11 guilds
- [x] Registered in `~/.config/opencode/opencode.json` (mcp/discord)
- [x] Live MCP tool-call round trip: `discord_status` + `discord_channels` over FastMCP against real Discord API — PlayForKeeps (1551377931866079312) visible; live 429 absorbed by Retry-After backoff and retried to 200 OK
- [x] Live `discord_search` probe: discovered async `202 Accepted` behavior, implemented 202-poll in client (tests-first), re-verified end-to-end — 9 scrubbed results returned over the MCP boundary
