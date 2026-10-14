"""Interactive CLI for the mini MCP library assistant.

Run with:  python -m mini_mcp.cli
"""
from __future__ import annotations

from mini_mcp.server import run_turn


def main() -> None:
    print("Mini MCP Library Assistant — ask about books, genres, authors, or availability.")
    print("Examples: 'recommend some fantasy', 'who wrote Dune?', 'is Clean Code available?'")
    print("Type 'quit' to exit.\n")
    while True:
        try:
            user_message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_message:
            continue
        if user_message.lower() in {"quit", "exit"}:
            break
        print(f"Assistant: {run_turn(user_message)}\n")


if __name__ == "__main__":
    main()
