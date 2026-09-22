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
- [ ] Tests for MCP tools (`tests/tools/test_tools.py`)
- [ ] Implement MCP tools (`discord_mcp/tools/`)
- [ ] Tests for FastMCP stdio server (`tests/server/test_server.py`)
- [ ] Implement FastMCP server (`discord_mcp/server.py`)

## Phase 4: CLI Interface & Verification
- [ ] Tests for CLI entrypoint (`tests/test_main.py`)
- [ ] Implement CLI entrypoint (`discord_mcp/__main__.py`)
- [ ] Verify test suite passes with coverage and ruff linting clean

## Phase 5: Post-Phase Audit & WaLRuS-DATA
- [ ] Execute 6-step Epistegrity Post-Phase Audit
- [ ] Commit WaLRuS session summary (`docs/walrus-YYYY-MM-DD.md`)
