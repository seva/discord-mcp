"""Tests for the secret-scrub boundary module.

Enforces the terminal bound constraint (secrets never surfaced in tool output)
across free-form Discord message content.
"""

from __future__ import annotations

from discord_mcp.scrub import scrub_text


def test_scrub_clean_text_unchanged():
    text = "Hello world! Meeting at 2pm in general."
    cleaned, redactions = scrub_text(text)
    assert cleaned == text
    assert redactions == []


def test_scrub_empty_text():
    cleaned, redactions = scrub_text("")
    assert cleaned == ""
    assert redactions == []


def test_scrub_github_token():
    text = "Here is my token: ghp_1234567890abcdefghijklmnopqrstuvwxyzAB"
    cleaned, redactions = scrub_text(text)
    assert "ghp_1234567890" not in cleaned
    assert "[REDACTED:GITHUB_TOKEN]" in cleaned
    assert len(redactions) == 1
    assert redactions[0]["kind"] == "GITHUB_TOKEN"


def test_scrub_openai_style_key():
    text = "OpenAI key sk-proj-1234567890abcdef1234567890abcdef12345678"
    cleaned, redactions = scrub_text(text)
    assert "sk-proj-" not in cleaned
    assert "[REDACTED:API_KEY]" in cleaned
    assert len(redactions) == 1


def test_scrub_bot_token():
    text = "Telegram bot token 8597761224:AAFcvCF0ZV_Qh9xzWAgCKG21F3MTR8Iu2pg"
    cleaned, _ = scrub_text(text)
    assert "AAFcvCF0ZV" not in cleaned
    assert "[REDACTED:BOT_TOKEN]" in cleaned


def test_scrub_otp_code():
    text = "Your verification code is 849201. Do not share it."
    cleaned, redactions = scrub_text(text)
    assert "849201" not in cleaned
    assert "[REDACTED:OTP]" in cleaned
    assert len(redactions) == 1


def test_spare_normal_numbers_and_dates():
    text = "Met on 2026-09-22 with 5 participants in room 402."
    cleaned, redactions = scrub_text(text)
    assert cleaned == text
    assert redactions == []


def test_scrub_private_key_block():
    text = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQD...
-----END PRIVATE KEY-----"""
    cleaned, redactions = scrub_text(text)
    assert "MIIEvg" not in cleaned
    assert "[REDACTED:PRIVATE_KEY]" in cleaned
    assert len(redactions) == 1


def test_scrub_tokenized_url():
    text = "Click to confirm: https://example.com/verify?token=secret1234567890abcdef&user=seva"
    cleaned, _ = scrub_text(text)
    assert "token=secret1234567890abcdef" not in cleaned
    assert "token=[REDACTED:URL_SECRET]" in cleaned


def test_scrub_multiple_secrets_in_one_message():
    text = (
        "Use ghp_1234567890abcdefghijklmnopqrstuvwxyzAB "
        "and key sk-ant-1234567890abcdef1234567890abcdef12345678"
    )
    cleaned, redactions = scrub_text(text)
    assert "[REDACTED:GITHUB_TOKEN]" in cleaned
    assert "[REDACTED:API_KEY]" in cleaned
    assert len(redactions) == 2
