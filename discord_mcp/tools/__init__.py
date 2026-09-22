"""Shared helpers for MCP tool modules."""

from __future__ import annotations

from typing import Any

from discord_mcp.scrub import scrub_text

_EMBED_TEXT_KEYS = ("title", "description")


def _scrub_embed(embed: dict[str, Any]) -> dict[str, Any]:
    scrubbed = dict(embed)
    for key in _EMBED_TEXT_KEYS:
        if scrubbed.get(key):
            scrubbed[key], _ = scrub_text(scrubbed[key])
    if scrubbed.get("fields"):
        scrubbed["fields"] = [
            {**field, "value": scrub_text(field.get("value", ""))[0]}
            if field.get("value")
            else field
            for field in scrubbed["fields"]
        ]
    if scrubbed.get("footer", {}).get("text"):
        scrubbed["footer"] = {
            **scrubbed["footer"],
            "text": scrub_text(scrubbed["footer"]["text"])[0],
        }
    if scrubbed.get("author", {}).get("name"):
        scrubbed["author"] = {
            **scrubbed["author"],
            "name": scrub_text(scrubbed["author"]["name"])[0],
        }
    return scrubbed


def scrub_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply the secret-scrub boundary to all free-text surfaces of a message.

    Covers content, embeds (title, description, fields, footer, author).
    """
    scrubbed: list[dict[str, Any]] = []
    for message in messages:
        entry = dict(message)
        content = entry.get("content")
        if content:
            entry["content"], _ = scrub_text(content)
        if entry.get("embeds"):
            entry["embeds"] = [_scrub_embed(embed) for embed in entry["embeds"]]
        scrubbed.append(entry)
    return scrubbed
