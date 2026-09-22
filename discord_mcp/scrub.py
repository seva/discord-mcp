"""Secret-scrub boundary module.

Enforces the terminal bound constraint (secrets never surfaced in tool or API output)
for free-form message bodies (Discord, Telegram, emails).

Applies regex-based pattern redaction at the channel ingestion boundary,
replacing detected secrets with opaque markers `[REDACTED:<KIND>]`.
"""

from __future__ import annotations

import re
from typing import Any

# Private key blocks
_PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----[\s\S]+?-----END (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
    re.MULTILINE,
)

# GitHub personal access tokens
_GITHUB_TOKEN_RE = re.compile(r"\b(gh[pousr]_[A-Za-z0-9_]{36,255})\b")

# General API keys (OpenAI, Anthropic, generic sk- keys)
_API_KEY_RE = re.compile(r"\b(sk-(?:proj-|ant-)?[A-Za-z0-9_-]{32,100})\b")

# Bot tokens (Telegram / Discord bot token patterns)
_BOT_TOKEN_RE = re.compile(r"\b(\d{8,11}:[A-Za-z0-9_-]{35})\b")

# URL secret parameters (token=..., key=..., secret=..., password=...)
_URL_SECRET_RE = re.compile(
    r"((?:https?://[^\s?#]+[?&](?:token|key|secret|password|auth|api_key)=)[^&\s#]{8,})",
    re.IGNORECASE,
)

# OTP code patterns (6 to 8 digits preceded by OTP keywords, to avoid false positives on years/dates)
_OTP_RE = re.compile(
    r"(?i)\b(?:code|otp|verification|pin|password|token|2fa)(?:\s+(?:is|:|=))?\s+([0-9]{6,8})\b"
)


def scrub_text(text: str) -> tuple[str, list[dict[str, Any]]]:
    """Scrub sensitive credentials, tokens, OTPs, and private keys from message text.

    Returns:
        (scrubbed_text, list_of_redactions)
    """
    if not text:
        return text, []

    redactions: list[dict[str, Any]] = []

    # 1. Private key blocks
    def _sub_pk(match: re.Match) -> str:
        redactions.append({"kind": "PRIVATE_KEY"})
        return "[REDACTED:PRIVATE_KEY]"

    scrubbed = _PRIVATE_KEY_RE.sub(_sub_pk, text)

    # 2. GitHub Tokens
    def _sub_gh(match: re.Match) -> str:
        redactions.append({"kind": "GITHUB_TOKEN"})
        return "[REDACTED:GITHUB_TOKEN]"

    scrubbed = _GITHUB_TOKEN_RE.sub(_sub_gh, scrubbed)

    # 3. API Keys
    def _sub_key(match: re.Match) -> str:
        redactions.append({"kind": "API_KEY"})
        return "[REDACTED:API_KEY]"

    scrubbed = _API_KEY_RE.sub(_sub_key, scrubbed)

    # 4. Bot Tokens
    def _sub_bot(match: re.Match) -> str:
        redactions.append({"kind": "BOT_TOKEN"})
        return "[REDACTED:BOT_TOKEN]"

    scrubbed = _BOT_TOKEN_RE.sub(_sub_bot, scrubbed)

    # 5. Tokenized URLs
    def _sub_url(match: re.Match) -> str:
        prefix = match.group(0).split("=")[0] + "="
        redactions.append({"kind": "URL_SECRET"})
        return prefix + "[REDACTED:URL_SECRET]"

    scrubbed = _URL_SECRET_RE.sub(_sub_url, scrubbed)

    # 6. OTPs
    def _sub_otp(match: re.Match) -> str:
        val = match.group(1)
        full = match.group(0)
        redactions.append({"kind": "OTP"})
        return full.replace(val, "[REDACTED:OTP]")

    scrubbed = _OTP_RE.sub(_sub_otp, scrubbed)

    return scrubbed, redactions
