"""A tiny vector-search knowledge base backed by SQLite.

This mirrors the real pattern this training module is based on: a table of
entries, each with an embedding, a flag for whether it's been accepted, and a
similarity search that only considers accepted entries by default — so the
knowledge base's quality is driven entirely by what real users approved.
"""
from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from mini_rag.embeddings import cosine_similarity, embed_text

DB_PATH = Path(__file__).parent / "knowledge_base.db"


@dataclass
class Entry:
    id: int
    question: str
    answer: str
    accepted: bool
    similarity: float | None = None


def get_connection() -> sqlite3.Connection:
    is_new = not DB_PATH.exists()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if is_new:
        _create_tables(conn)
    return conn


def reset_database() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()


def _create_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            embedding TEXT NOT NULL,
            accepted INTEGER NOT NULL DEFAULT 0,
            created_at REAL NOT NULL
        )
        """
    )
    conn.commit()


def add_entry(question: str, answer: str, accepted: bool = False) -> int:
    """Embed and store a question/answer pair. This is the 'embed-on-accept'
    step: called the moment a human approves an answer, not before.
    """
    conn = get_connection()
    vector = embed_text(f"{question}\n{answer}")
    cursor = conn.execute(
        "INSERT INTO entries (question, answer, embedding, accepted, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (question, answer, json.dumps(vector), int(accepted), time.time()),
    )
    conn.commit()
    entry_id = cursor.lastrowid
    conn.close()
    return entry_id


def set_accepted(entry_id: int, accepted: bool = True) -> None:
    conn = get_connection()
    conn.execute("UPDATE entries SET accepted = ? WHERE id = ?", (int(accepted), entry_id))
    conn.commit()
    conn.close()


def find_similar(query: str, top_k: int = 3, accepted_only: bool = True) -> list[Entry]:
    """Return the most similar stored entries to `query`, best first.

    By default only *accepted* entries are searched — this is what keeps the
    knowledge base's answers grounded in human-approved output instead of
    every unreviewed draft that was ever generated.
    """
    conn = get_connection()
    sql = "SELECT id, question, answer, embedding, accepted FROM entries"
    if accepted_only:
        sql += " WHERE accepted = 1"
    rows = conn.execute(sql).fetchall()
    conn.close()

    query_vector = embed_text(query)
    scored: list[Entry] = []
    for row in rows:
        vector = json.loads(row["embedding"])
        similarity = cosine_similarity(query_vector, vector)
        scored.append(
            Entry(
                id=row["id"],
                question=row["question"],
                answer=row["answer"],
                accepted=bool(row["accepted"]),
                similarity=similarity,
            )
        )
    scored.sort(key=lambda e: e.similarity or 0.0, reverse=True)
    return scored[:top_k]


def count_entries(accepted_only: bool = False) -> int:
    conn = get_connection()
    sql = "SELECT COUNT(*) AS n FROM entries"
    if accepted_only:
        sql += " WHERE accepted = 1"
    row = conn.execute(sql).fetchone()
    conn.close()
    return row["n"]
