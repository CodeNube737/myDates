from __future__ import annotations

import sqlite3
from pathlib import Path

from src.utils import DB_PATH, ensure_runtime_dirs

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS user_profile (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        name TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS profile_religions (
        profile_id INTEGER NOT NULL,
        religion TEXT NOT NULL,
        UNIQUE(profile_id, religion),
        FOREIGN KEY (profile_id) REFERENCES user_profile(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS profile_countries (
        profile_id INTEGER NOT NULL,
        country TEXT NOT NULL,
        UNIQUE(profile_id, country),
        FOREIGN KEY (profile_id) REFERENCES user_profile(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS profile_astronomy_interests (
        profile_id INTEGER NOT NULL,
        interest TEXT NOT NULL,
        UNIQUE(profile_id, interest),
        FOREIGN KEY (profile_id) REFERENCES user_profile(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS recurring_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        event_type TEXT NOT NULL DEFAULT 'custom',
        month INTEGER NOT NULL,
        day INTEGER NOT NULL,
        contact_info TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS scraped_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_type TEXT NOT NULL,
        category TEXT NOT NULL,
        name TEXT NOT NULL,
        event_date TEXT NOT NULL,
        is_recurring INTEGER NOT NULL DEFAULT 1,
        metadata TEXT,
        UNIQUE(source_type, category, name, event_date)
    );
    """,
    'CREATE INDEX IF NOT EXISTS idx_scraped_events_date ON scraped_events(event_date);',
)


def resolve_db_path(db_path: str | Path | None = None) -> Path:
    return Path(db_path) if db_path else DB_PATH


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = resolve_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA foreign_keys = ON')
    return connection


def init_db(db_path: str | Path | None = None) -> Path:
    ensure_runtime_dirs()
    path = resolve_db_path(db_path)
    with get_connection(path) as connection:
        for statement in SCHEMA:
            connection.execute(statement)
        # Legacy migration guard for databases created before recurring_events
        # included the event_type column.
        columns = {
            row['name']
            for row in connection.execute("PRAGMA table_info(recurring_events)").fetchall()
        }
        if 'event_type' not in columns:
            connection.execute(
                "ALTER TABLE recurring_events ADD COLUMN event_type TEXT NOT NULL DEFAULT 'custom'"
            )
        connection.commit()
    return path
