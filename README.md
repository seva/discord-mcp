# discord-mcp

FastMCP server exposing Discord context (guilds, channels, messages, search) to MCP clients via Playwright web authentication and Windows DPAPI credential protection.

## Overview

`discord-mcp` connects LLMs and MCP clients (such as OpenCode, OpenClaw, and Claude Desktop) to Discord. It operates under a user session, providing read access to joined servers, channels, and direct messages without requiring bot administrative invitations.

### Key Features
- **Zero Desktop App Dependency:** Authenticates directly via interactive Chromium (Playwright) supporting QR-code login and credentials.
- **DPAPI Credential Security:** Session tokens are encrypted at rest using the Windows Data Protection API (`CryptProtectData`). Plaintext tokens are never stored on disk.
- **Secret-Scrub Boundary:** Automatically sanitizes private keys, GitHub tokens, API keys, bot tokens, URL credentials, and OTPs from message content before exposing them to the MCP client.
- **FastMCP Protocol:** Standard stdio transport compatible with any MCP client.

---

## MCP Tools

1. **`discord_status`**
   - Returns the authenticated user profile (username, user ID) and count of accessible guilds.
2. **`discord_channels`**
   - Lists accessible guilds and their channels (optionally filtered by `guild_id`).
3. **`discord_dms`**
   - Lists the user's DM and group-DM channels with derived labels; returned channel IDs work with `discord_messages`.
4. **`discord_threads`**
   - Lists a channel's archived threads (public always, private where permissions allow); thread IDs work with `discord_messages`.
5. **`discord_messages`**
   - Retrieves recent messages from a specified channel, DM, or thread (with secret scrubbing applied).
6. **`discord_search`**
   - Searches message content across a guild or channel with keyword filtering and secret scrubbing.

---

## Installation & Setup

### Requirements
- Python >= 3.11
- Windows (for DPAPI encryption)
- Chrome / Chromium (Playwright installed)

### Install
```bash
pip install -e .
playwright install chromium
```

### Authentication
Launch interactive login to capture and encrypt the user token into DPAPI:
```bash
python -m discord_mcp auth
```
Log in using QR code scan via your Discord mobile app or username/password. Once logged in, the browser closes automatically and the encrypted token is stored at `~/.discord-mcp/auth.dpapi`.

### Verify Status
```bash
python -m discord_mcp status
```

---

## Client Configuration

### OpenCode / Claude Desktop
Add to your client configuration:
```json
{
  "mcp": {
    "discord": {
      "type": "local",
      "command": [
        "python",
        "-m",
        "discord_mcp",
        "serve"
      ]
    }
  }
}
```

---

## Development & Testing

```bash
# Run tests
python -m pytest

# Run linter
ruff check .
```
