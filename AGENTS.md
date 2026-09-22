# discord-mcp — Discord FastMCP Context Server

FastMCP server exposing Discord context (guilds, channels, DMs, threads, messages, search) to MCP clients via Playwright web authentication and Windows DPAPI credential protection.

## Session Start

1. Read `METHODOLOGY.md`
2. Read `ARCHITECTURE.md` — verify component descriptions match current code before acting
3. Scan `IMPLEMENTATION.md` checkboxes — first unchecked task is current state
4. Check open GitHub issues / records for failures and decisions
5. Search memory for relevant prior knowledge
6. Locate the project in the operating cycle (`CYCLE.md`) — which step is current?
7. Identify your role (`ROLES.md`; default Steward) and declared role instances — no role grades its own work

## Conventions

- **Scope position** (`docs/scope.md`): L1 (Local standalone FastMCP server over stdio under operator personal user identity, encrypted DPAPI token store, secret-scrub boundary, and core read tools).
- **Compiled terminal-bound constraints** (`docs/scope.md`, Terminal bound):
  - User session tokens never leave the local DPAPI store at `~/.discord-mcp/auth.dpapi`; plaintext tokens are never written to disk.
  - Secret-scrub boundary (`discord_mcp/scrub.py`) filters all message content before returning across MCP tool boundaries, redacting private keys, GitHub tokens, API keys, bot tokens, URL credentials, and OTPs.
  - Zero desktop application dependency: authentication runs through interactive Chromium via Playwright directly to `https://discord.com/login`.
  - Read-only context operations under personal user account respecting Discord rate limits and platform constraints.
- **Language/runtime**: Python ≥3.11 (`mcp>=1.0`, `playwright>=1.40`, `httpx>=0.27`, `pywin32>=306`).
- **Test runner**: `python -m pytest` (`pytest-asyncio`, auto mode).
- **Formatting/linting**: `ruff check` and `ruff format --check` must pass before commit.
- **Role instances** (`ROLES.md`): Steward = the executing agent session on this repository. Critic = a distinct subagent/session spawned at step completion seeing claim and evidence without the Steward's reasoning. Auditor = separate instance verifying against constitution and success criterion. Owner = project owner (@swearlock).
- **Declared deviation** (ARCHITECTURE.md banned pattern 2): the CLI serve-dispatch test patches the FastMCP stdio transport entry (`mcp.run`) — the process's external boundary — rather than launching a blocking transport in-process; no tool or client logic is mocked anywhere in the suite (tool/client tests run through respx at the HTTP layer and the real DPAPI store path).
- **Dependency direction** (2026-09-22, Owner-accepted): this server is an independent execution-plane **leaf**. It has no runtime or constitutional dependency on any gateway, consumer, or aggregation layer — consumers depend on it, never vice versa, and consumer/origin identities are never recorded in this server's documents (the topology verdict is recorded on the consumer's side and in the operator's meta-store). Consolidation of MCP servers onto one shared process is rejected ("compose in the control plane, isolate in the execution plane"). HTTP `/mcp` stays localhost-bound until consumer auth exists (`docs/scope.md` terminal bound).
- **CLI Commands**:
  - `python -m discord_mcp auth`: Interactive Playwright Chromium login, capturing user token into DPAPI.
  - `python -m discord_mcp status`: Test connectivity and print authenticated user details.
  - `python -m discord_mcp serve [--transport {stdio,http}] [--port N]`: Launch FastMCP server (stdio default; `--transport http` serves streamable-HTTP at `http://127.0.0.1:{port}/mcp`, localhost-bound by default).
