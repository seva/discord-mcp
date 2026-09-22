import asyncio
import re
import time

from playwright.async_api import BrowserContext, async_playwright

DISCORD_URL = "https://discord.com/login"
POLL_INTERVAL = 2  # seconds
CAPTURE_TIMEOUT = 300  # seconds

_BEARER_RE = re.compile(r"^Bearer\s+(.+)$", re.IGNORECASE)
_BOT_PREFIX_RE = re.compile(r"^Bot\s+", re.IGNORECASE)


def _extract_token(headers: dict) -> str | None:
    value = headers.get("authorization") or headers.get("Authorization")
    if not value:
        return None
    if _BOT_PREFIX_RE.match(value):
        return None
    match = _BEARER_RE.match(value)
    if match:
        return match.group(1)
    return value


async def capture(timeout: int = CAPTURE_TIMEOUT) -> dict:
    token: str | None = None

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
        )
        context: BrowserContext = await browser.new_context()
        page = await context.new_page()

        def _on_request(request):
            nonlocal token
            if token:
                return
            if "discord.com/api/" in request.url:
                candidate = _extract_token(dict(request.headers))
                if candidate:
                    token = candidate

        page.on("request", _on_request)

        await page.goto(DISCORD_URL)

        start = time.monotonic()
        while True:
            if token:
                break
            if time.monotonic() - start >= timeout:
                await browser.close()
                raise TimeoutError(
                    f"Auth capture timed out after {timeout}s. "
                    "Log in within the browser window before the timeout expires."
                )
            await asyncio.sleep(POLL_INTERVAL)

        await browser.close()

        return {"token": token, "captured_at": time.time()}
