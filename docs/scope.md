# Scope — Maximal Imaginable

Established 2026-09-22. Strategy artifact: the ladder this project climbs. Orient (CYCLE.md, step 1) measures the status quo against this document.

**Maximal mission:** Universal read and context federation across the operator's digital communities, servers, threads, and communications with cryptographic credential boundaries and zero secret leakage.

---

## Scope ladder

| Level | Scope | Current system's contribution |
|---|---|---|
| L1 | Local standalone FastMCP server over stdio under operator personal user identity, encrypted DPAPI token store, secret-scrub boundary, and core read tools | as-is — complete and live-verified: `discord_status`, `discord_channels`, `discord_dms`, `discord_threads`, `discord_messages`, `discord_search` (6 tools) |
| L2 | Multi-guild caching, proactive rate-limit budgeting, thread hierarchy traversal (archived listing built — `discord_threads`, 2026-09-22; active-thread listing bot-only, structural), DM and group DM resolution (complete — pulled forward into L1 as `discord_dms`) | client architecture & schema; DM resolution + archived-thread listing built |
| L3 | Cross-channel CCE integration (Ichnos consumer reading from standalone discord-mcp over stdio / HTTP) | MCP server protocol compliance |
| L4 | Real-time event subscription, reaction analysis, and thread watcher hooks | webhook & event model |
| L5 | Multi-platform unified comms context (Discord, Telegram, WhatsApp, Slack, Matrix) under uniform secret-scrub boundary | scrub boundary & adapter pattern |
| L6–L14 | Institutional context fabric, decentralized consensus verification, autonomous multi-agent operational telemetry | federation interface |
| L15 | Galactic civilizational cross-surface consciousness federation | universal context ground |

---

## Functional depth

- **Cryptographic Credential Seclusion:** User authentication tokens remain exclusively protected by Windows DPAPI; memory extraction is bounded to runtime invocations.
- **Secret-Scrub Boundary Defense:** High-precision regex pattern sanitization redacting private keys, tokens, OTPs, and URL credentials before exposing data to MCP clients.
- **Personal Identity Emulation:** Operates through standard user HTTP REST v10 channels matching browser fingerprints, bypassing administrative bot invite requirements.
- **Rate-Limit Resilience:** 429 `Retry-After` backoff (current — the ONLY live signal: user tokens receive no `X-RateLimit-*` headers, verified live 2026-09-22, so header budgeting is structurally impossible); TTL caching (60s per-key) is the primary request-volume defense.

---

## Survivability

- **Platform Invalidation Risk:** Discord user API changes or aggressive token revocation; defended by interactive Playwright refresh CLI (`python -m discord_mcp auth`).
- **Secret Exfiltration Risk:** Accidental leakage of auth tokens or channel secrets; defended by DPAPI encryption at rest, `.gitignore` terminal patterns, and in-flight boundary scrubbing.
- **Rate-Limit Throttling:** 429 Too Many Requests; defended by proactive backoff parsing response headers before queuing further requests.

---

## Terminal bound

| Compiled constraint | Irrecoverable margin it protects |
|---|---|
| User session tokens never leave local DPAPI store at `~/.discord-mcp/auth.dpapi`; plaintext tokens are never written to disk | Operator account credential integrity |
| Secret-scrub boundary (`discord_mcp/scrub.py`) filters all message content before returning across MCP tool boundaries | Zero secret leakage to external models / contexts |
| Zero desktop application dependency; authentication executed through interactive Chromium via Playwright | Host independence and resilience against client app locks |
| Read-only context operations under personal user account | Account standing and abuse prevention |

| Commitment class | Refinement level (PRAROC-n, HORIZONS.md) | Terms below the cut, registered non-drifting |
|---|---|---|
| FastMCP Server Core | 1 | Protocol serialization |
| Auth & DPAPI Storage | 5 | Windows CryptProtectData API stability |
| REST Client & Rate Limits | 3 | Discord API v10 endpoint schema |
| Secret-Scrub Boundary | 2 | Regex engine performance |

---

## Terminal form

When the mission completes, manual copy-pasting of community discussions, operational announcements, and cross-channel decisions into LLM prompts becomes obsolete. Agents possess real-time, privacy-preserving contextual awareness across all operator digital spheres.

---

## Constraint analysis

- **Level 1 (Current):** Standalone FastMCP server running locally via stdio. Constrained by Windows DPAPI availability and manual Playwright login.
- **Level 2–3:** Local caching and multi-client multiplexing. Constrained by Discord user API rate limits (typically 50 requests/sec with burst buckets).
- **Level 4–5:** Real-time event gateway / websockets. Constrained by Discord Gateway connection policies for user accounts (self-bot detection heuristics; REST-only polling is safest).
- **Nearest concrete anchors:** Discord REST API v10, OpenCode MCP configuration (`~/.config/opencode/opencode.json`), Ichnos CCE MCP client.
