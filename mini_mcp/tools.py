"""The tool registry: this is the heart of the 'MCP-style' pattern.

Each tool is described the same way a real MCP/function-calling tool is
described to a model: a stable `name`, a human-readable `description`, and a
JSON Schema for its parameters. `dispatch()` is the single place that turns a
tool-call request (name + arguments) into a real function call against our
local database — the model never touches the database directly.

This mirrors the shape used in the real codebase this training module is
based on: a lightweight, dependency-free tool registry that can later be
re-exposed through an actual MCP server without changing how tools are
defined or dispatched.
"""
from __future__ import annotations

from typing import Any, Callable

from mini_mcp.db import get_connection

# --- Tool implementations -------------------------------------------------


def list_genres(**_: Any) -> dict:
    conn = get_connection()
    rows = conn.execute("SELECT DISTINCT genre FROM books ORDER BY genre").fetchall()
    conn.close()
    return {"genres": [r["genre"] for r in rows]}


def search_books(genre: str | None = None, author: str | None = None, **_: Any) -> dict:
    conn = get_connection()
    query = "SELECT title, author, genre, year, copies_available FROM books WHERE 1=1"
    params: list[str] = []
    if genre:
        query += " AND genre = ?"
        params.append(genre)
    if author:
        query += " AND author LIKE ?"
        params.append(f"%{author}%")
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return {"books": [dict(r) for r in rows]}


def get_book_availability(title: str, **_: Any) -> dict:
    conn = get_connection()
    row = conn.execute(
        "SELECT title, copies_available FROM books WHERE title LIKE ?",
        (f"%{title}%",),
    ).fetchone()
    conn.close()
    if row is None:
        return {"found": False, "title": title}
    return {
        "found": True,
        "title": row["title"],
        "copies_available": row["copies_available"],
        "can_borrow": row["copies_available"] > 0,
    }


def recommend_books(genre: str, limit: int = 3, **_: Any) -> dict:
    conn = get_connection()
    rows = conn.execute(
        "SELECT title, author, year FROM books WHERE genre = ? "
        "ORDER BY year DESC LIMIT ?",
        (genre, limit),
    ).fetchall()
    conn.close()
    return {"genre": genre, "recommendations": [dict(r) for r in rows]}


# --- Registry --------------------------------------------------------------

# Each entry: name -> (description, JSON schema for parameters, callable)
TOOLS: dict[str, dict[str, Any]] = {
    "list_genres": {
        "description": "List every genre currently in the library catalog.",
        "parameters": {"type": "object", "properties": {}, "required": []},
        "handler": list_genres,
    },
    "search_books": {
        "description": "Search the catalog by genre and/or author (partial match).",
        "parameters": {
            "type": "object",
            "properties": {
                "genre": {"type": "string", "description": "Exact genre, e.g. 'fantasy'"},
                "author": {"type": "string", "description": "Partial author name"},
            },
            "required": [],
        },
        "handler": search_books,
    },
    "get_book_availability": {
        "description": "Check how many copies of a specific book (by title, partial match) are available to borrow.",
        "parameters": {
            "type": "object",
            "properties": {"title": {"type": "string", "description": "Partial or full book title"}},
            "required": ["title"],
        },
        "handler": get_book_availability,
    },
    "recommend_books": {
        "description": "Recommend the newest books in a given genre.",
        "parameters": {
            "type": "object",
            "properties": {
                "genre": {"type": "string"},
                "limit": {"type": "integer", "description": "Max number of results", "default": 3},
            },
            "required": ["genre"],
        },
        "handler": recommend_books,
    },
}


def tool_schemas() -> list[dict[str, Any]]:
    """The part of the registry a model actually sees (no handlers)."""
    return [
        {"name": name, "description": spec["description"], "parameters": spec["parameters"]}
        for name, spec in TOOLS.items()
    ]


def dispatch(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Run a tool by name. Raises KeyError for unknown tools."""
    if name not in TOOLS:
        raise KeyError(f"Unknown tool: {name}")
    handler: Callable[..., dict] = TOOLS[name]["handler"]
    return handler(**arguments)
