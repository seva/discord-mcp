# Discord API v10 — User Endpoint Specification (Phase 0 Discovery)

Base URL: `https://discord.com/api/v10`

---

## 1. Authentication & Request Headers

User tokens operate without the `Bot ` prefix in the `Authorization` header. User requests must include browser-like headers to avoid anti-bot edge fingerprinting.

```http
Authorization: <captured_user_bearer_token>
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36
Content-Type: application/json
Accept: application/json
```

---

## 2. Core Endpoints

### 2.1 Get Current User (`GET /users/@me`)
- **Path:** `/users/@me`
- **Purpose:** Verifies token validity and retrieves authenticated user identity.
- **Response Schema:**
  ```json
  {
    "id": "931228531340496946",
    "username": "swearlock",
    "discriminator": "0",
    "global_name": "Seva Lapsha",
    "avatar": "a1b2c3d4...",
    "email": "user@example.com"
  }
  ```

### 2.2 Get User Guilds (`GET /users/@me/guilds`)
- **Path:** `/users/@me/guilds`
- **Purpose:** Lists all servers the authenticated user is currently a member of.
- **Response Schema:**
  ```json
  [
    {
      "id": "1551377931866079312",
      "name": "PlayForKeeps",
      "icon": "icon_hash",
      "owner": false,
      "permissions": "1071698660929"
    }
  ]
  ```

### 2.3 Get Guild Channels (`GET /guilds/{guild_id}/channels`)
- **Path:** `/guilds/{guild_id}/channels`
- **Purpose:** Lists text channels, categories, and voice channels within a guild.
- **Channel Types:**
  - `0`: `GUILD_TEXT`
  - `2`: `GUILD_VOICE`
  - `4`: `GUILD_CATEGORY`
  - `5`: `GUILD_ANNOUNCEMENT`
  - `11`: `PUBLIC_THREAD`
  - `12`: `PRIVATE_THREAD`
- **Response Schema:**
  ```json
  [
    {
      "id": "1478480447431376966",
      "type": 0,
      "name": "general",
      "position": 1,
      "parent_id": null
    }
  ]
  ```

### 2.4 Get Channel Messages (`GET /channels/{channel_id}/messages`)
- **Path:** `/channels/{channel_id}/messages`
- **Query Parameters:**
  - `limit`: Integer (1–100, default 10)
  - `before`: Snowflake ID (optional, pagination)
  - `after`: Snowflake ID (optional, pagination)
- **Response Schema:**
  ```json
  [
    {
      "id": "123456789012345678",
      "channel_id": "1478480447431376966",
      "author": {
        "id": "931228531340496946",
        "username": "swearlock",
        "global_name": "Seva Lapsha"
      },
      "content": "Meeting scheduled for 2pm.",
      "timestamp": "2026-09-22T14:00:00.000000+00:00",
      "attachments": []
    }
  ]
  ```

### 2.5 Search Guild Messages (`GET /guilds/{guild_id}/messages/search`)
- **Path:** `/guilds/{guild_id}/messages/search`
- **Query Parameters:**
  - `content`: String query term
  - `channel_id`: Snowflake ID (optional filter)
  - `author_id`: Snowflake ID (optional filter)
- **Async behavior (verified live 2026-09-22):** The first call may return `202 Accepted` while results are computed; the response body has no `messages` key. Poll the same request until `200 OK` (observed ready within ~2s). The client implements this poll (`SEARCH_RETRY_INTERVAL = 2.0`, bounded by `MAX_RETRIES`).
- **Response Schema:**
  Note: Discord message search returns an array of message arrays (where each inner array contains the matched message plus contextual neighboring messages).
  ```json
  {
    "total_results": 1,
    "messages": [
      [
        {
          "id": "123456789012345678",
          "channel_id": "1478480447431376966",
          "author": {
            "id": "931228531340496946",
            "username": "swearlock"
          },
          "content": "Secret key sk-proj-12345678901234567890123456789012"
        }
      ]
    ]
  }
  ```

---

## 3. Rate Limits & Error Handling

- **Rate Limit Headers:**
  - `X-RateLimit-Limit`: Maximum requests allowed in current window.
  - `X-RateLimit-Remaining`: Remaining requests.
  - `X-RateLimit-Reset-After`: Seconds until quota reset.
  - `Retry-After`: Returned on HTTP 429 responses.
- **Error Status Codes:**
  - `401 Unauthorized`: Token invalid, expired, or rejected. Triggers `AuthRequired`.
  - `403 Forbidden`: User lacks permission to read channel / guild.
  - `404 Not Found`: Channel or guild ID does not exist.
  - `429 Too Many Requests`: Rate limited. Back off by `retry_after` seconds.
