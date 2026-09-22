"""CLI entrypoint: auth | status | serve."""

import argparse
import asyncio
import json
import sys

from discord_mcp import server
from discord_mcp.auth import store
from discord_mcp.auth.store import AuthRequired


def _auth() -> int:
    from discord_mcp.auth.browser import capture

    data = asyncio.run(capture())
    store.save(data)
    print("Auth captured and stored.")
    return 0


def _status() -> int:
    from discord_mcp.tools.status import discord_status

    try:
        print(json.dumps(json.loads(asyncio.run(discord_status())), indent=2))
        return 0
    except AuthRequired as e:
        print(str(e), file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(prog="discord_mcp")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("auth", help="Interactive browser login; captures token into DPAPI")
    sub.add_parser("status", help="Verify connectivity and print authenticated user")
    serve = sub.add_parser("serve", help="Launch the FastMCP server")
    serve.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="stdio (default) or streamable-HTTP on 127.0.0.1",
    )
    serve.add_argument("--port", type=int, default=8000, help="HTTP port (default 8000)")

    args = parser.parse_args()

    if args.command == "auth":
        return _auth()
    if args.command == "status":
        return _status()
    if args.command == "serve":
        server.run(transport=args.transport, port=args.port)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
