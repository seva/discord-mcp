"""Shared helpers for MCP tool modules."""

from __future__ import annotations

from typing import Any

from discord_mcp.scrub import scrub_text


def scrub_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply the secret-scrub boundary to every message's content field."""
    scrubbed: list[dict[str, Any]] = []
    for message in messages:
        entry = dict(message)
        content = entry.get("content")
        if content:
            entry["content"], _ = scrub_text(content)
        scrubbed.append(entry)
    return scrubbed
