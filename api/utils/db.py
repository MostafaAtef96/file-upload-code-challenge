"""SQLite metadata store (file-level only)."""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY,
                filename TEXT UNIQUE NOT NULL,
                object_key TEXT NOT NULL,
                idx_key TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                uploaded_at TEXT NOT NULL,
                num_lines INTEGER NOT NULL,
                lines_per_chunk INTEGER NOT NULL
            )
            """
        )