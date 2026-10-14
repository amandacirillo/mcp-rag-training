"""Seeds and provides access to a tiny local SQLite 'library' database.

This stands in for 'the app's own database' that a real MCP tool server would
query. Everything lives in a single file, created on first use.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "library.db"

_SEED_BOOKS = [
    # (title, author, genre, year, copies_available)
    ("The Hobbit", "J.R.R. Tolkien", "fantasy", 1937, 3),
    ("Dune", "Frank Herbert", "sci-fi", 1965, 2),
    ("A Brief History of Time", "Stephen Hawking", "science", 1988, 1),
    ("The Pragmatic Programmer", "Andrew Hunt", "software", 1999, 4),
    ("Clean Code", "Robert C. Martin", "software", 2008, 0),
    ("Project Hail Mary", "Andy Weir", "sci-fi", 2021, 2),
    ("Sapiens", "Yuval Noah Harari", "history", 2011, 1),
    ("The Name of the Wind", "Patrick Rothfuss", "fantasy", 2007, 0),
]


def get_connection() -> sqlite3.Connection:
    """Open (and lazily seed) the library database."""
    is_new = not DB_PATH.exists()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if is_new:
        _create_and_seed(conn)
    return conn


def reset_database() -> None:
    """Delete and re-seed the database. Handy for tests and demos."""
    if DB_PATH.exists():
        DB_PATH.unlink()


def _create_and_seed(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            genre TEXT NOT NULL,
            year INTEGER NOT NULL,
            copies_available INTEGER NOT NULL
        )
        """
    )
    conn.executemany(
        "INSERT INTO books (title, author, genre, year, copies_available) "
        "VALUES (?, ?, ?, ?, ?)",
        _SEED_BOOKS,
    )
    conn.commit()
