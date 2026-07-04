"""
jarvis_core/memory.py
~~~~~~~~~~~~~~~~~~~~~
Lightweight SQLite-backed conversation history store.

Schema
------
  sessions(id INTEGER PK, session_id TEXT, role TEXT, content TEXT, ts INTEGER)

Each session is capped at MAX_HISTORY messages (oldest trimmed on insert) to
mirror the in-memory list behaviour that existed before this module.
"""

import sqlite3
import time
import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# DB lives at project root alongside server.py / requirements.txt
_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "jarvis_memory.db")
MAX_HISTORY = 10  # per session, same cap as the old in-memory list


def _get_conn() -> sqlite3.Connection:
    """Return a thread-local-safe connection with WAL mode for concurrent reads."""
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _init_db() -> None:
    """Create the sessions table if it doesn't already exist."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT    NOT NULL,
                role       TEXT    NOT NULL,
                content    TEXT    NOT NULL,
                ts         INTEGER NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON sessions(session_id, ts)")
    logger.info("Memory DB initialised at %s", _DB_PATH)


# Initialise on import
_init_db()


def load_history(session_id: str) -> List[Dict[str, str]]:
    """
    Return the last MAX_HISTORY messages for *session_id* as a list of
    {"role": str, "content": str} dicts, oldest first.
    """
    with _get_conn() as conn:
        rows = conn.execute(
            """
            SELECT role, content
            FROM   sessions
            WHERE  session_id = ?
            ORDER  BY ts ASC
            LIMIT  ?
            """,
            (session_id, MAX_HISTORY),
        ).fetchall()
    return [{"role": r, "content": c} for r, c in rows]


def append_turn(session_id: str, role: str, content: str) -> None:
    """
    Append one turn to persistent storage and prune so the session stays
    within MAX_HISTORY messages.

    *role* should be "User" or "Jarvis" (matching the in-memory convention).
    """
    now = int(time.time() * 1000)  # ms timestamp for ordering
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO sessions (session_id, role, content, ts) VALUES (?, ?, ?, ?)",
            (session_id, role, content, now),
        )
        # Trim: delete oldest rows beyond the cap for this session
        conn.execute(
            """
            DELETE FROM sessions
            WHERE session_id = ?
              AND id NOT IN (
                  SELECT id FROM sessions
                  WHERE  session_id = ?
                  ORDER  BY ts DESC
                  LIMIT  ?
              )
            """,
            (session_id, session_id, MAX_HISTORY),
        )


def clear_session(session_id: str) -> None:
    """Remove all history for *session_id* (useful for 'New Chat')."""
    with _get_conn() as conn:
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
