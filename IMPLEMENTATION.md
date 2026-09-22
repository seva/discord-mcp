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

## L2 Rung — Resilience & Depth (current)
- [x] DM resolution discovery: live `GET /users/@me/channels` probe (commitment record: Activation = live 200 with parseable channel array — held; Continuation = shapes matching endpoints.md entry — recorded in §2.6; Exit = endpoint unusable for user tokens — did not fire). 27 channels observed (25 DM, 2 group DM); `discord_messages` verified reading a DM channel ID.
- [ ] DM listing surface (tests-first): expose DM channels to MCP clients (tool or channels extension)
- [ ] TTL cache layer (tests-first): per-key TTL for `/users/@me/guilds`, `/guilds/{id}/channels`, `/channels/{id}/messages`
- [ ] Thread traversal discovery: `GET /channels/{id}/threads/archived` live probe

## Live Verification (L1 rung)
- [x] Substrate: `pip install -e .` — package importable from any cwd
- [x] Operator live auth: `python -m discord_mcp auth` → token captured, DPAPI-encrypted at `~/.discord-mcp/auth.dpapi`
- [x] `python -m discord_mcp status` → 200 OK, `swearlock`, 11 guilds
- [x] Registered in `~/.config/opencode/opencode.json` (mcp/discord)
- [x] Live MCP tool-call round trip: `discord_status` + `discord_channels` over FastMCP against real Discord API — PlayForKeeps (1551377931866079312) visible; live 429 absorbed by Retry-After backoff and retried to 200 OK
- [x] Live `discord_search` probe: discovered async `202 Accepted` behavior, implemented 202-poll in client (tests-first), re-verified end-to-end — 9 scrubbed results returned over the MCP boundary
