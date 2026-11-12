"""SQLite state for resumable Shorts discovery, clipping, uploads, and metrics."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.getenv("JARVIS_DB_PATH", os.path.join(HERE, "jarvis.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    video_id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL,
    channel_name TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    published_at TEXT NOT NULL,
    duration_seconds REAL NOT NULL,
    views INTEGER NOT NULL DEFAULT 0,
    likes INTEGER NOT NULL DEFAULT 0,
    discovered_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS clips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_video_id TEXT NOT NULL,
    start_seconds REAL NOT NULL,
    end_seconds REAL NOT NULL,
    hook_text TEXT NOT NULL DEFAULT '',
    score REAL NOT NULL DEFAULT 0,
    reason TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'queued',
    UNIQUE(source_video_id, start_seconds, end_seconds),
    FOREIGN KEY(source_video_id) REFERENCES sources(video_id)
);
CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT,
    clip_id INTEGER,
    title TEXT NOT NULL,
    hook TEXT NOT NULL DEFAULT '',
    score REAL NOT NULL DEFAULT 0,
    publish_time TEXT,
    source_channel TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'queued',
    UNIQUE(clip_id),
    FOREIGN KEY(clip_id) REFERENCES clips(id)
);
CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    views INTEGER NOT NULL DEFAULT 0,
    average_view_duration REAL,
    likes INTEGER NOT NULL DEFAULT 0,
    window TEXT NOT NULL,
    FOREIGN KEY(video_id) REFERENCES uploads(video_id)
);
CREATE TABLE IF NOT EXISTS quota_usage (
    usage_date TEXT PRIMARY KEY,
    units INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_sources_published ON sources(published_at);
CREATE INDEX IF NOT EXISTS idx_clips_source ON clips(source_video_id);
CREATE INDEX IF NOT EXISTS idx_uploads_publish ON uploads(publish_time);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connect(path: str | None = None) -> Iterator[sqlite3.Connection]:
    """Open a foreign-key-enabled database connection and commit safely."""
    connection = sqlite3.connect(path or DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db(path: str | None = None) -> str:
    """Create the database schema and return its path."""
    db_path = path or DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    with connect(db_path) as connection:
        connection.executescript(SCHEMA)
    return db_path


def source_seen(video_id: str, path: str | None = None) -> bool:
    init_db(path)
    with connect(path) as connection:
        return connection.execute(
            "SELECT 1 FROM sources WHERE video_id = ?", (video_id,)
        ).fetchone() is not None


def save_source(source: dict, path: str | None = None) -> None:
    init_db(path)
    with connect(path) as connection:
        connection.execute(
            """INSERT INTO sources
               (video_id, channel_id, channel_name, title, url, published_at,
                duration_seconds, views, likes, discovered_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(video_id) DO UPDATE SET
                 views=excluded.views, likes=excluded.likes""",
            (
                source["video_id"], source["channel_id"], source["channel_name"],
                source["title"], source["url"], source["published_at"],
                source["duration_seconds"], source.get("views", 0),
                source.get("likes", 0), utc_now(),
            ),
        )


def clip_overlaps(source_video_id: str, start: float, end: float,
                  path: str | None = None) -> bool:
    """Return true when a proposed range overlaps a queued or completed clip."""
    init_db(path)
    with connect(path) as connection:
        row = connection.execute(
            """SELECT 1 FROM clips
               WHERE source_video_id = ? AND start_seconds < ? AND end_seconds > ?
               LIMIT 1""",
            (source_video_id, end, start),
        ).fetchone()
        return row is not None


def save_clip(source_video_id: str, start: float, end: float, hook_text: str = "",
              score: float = 0, reason: str = "", path: str | None = None) -> int | None:
    """Insert a non-overlapping clip and return its id, or None when duplicated."""
    if clip_overlaps(source_video_id, start, end, path):
        return None
    init_db(path)
    with connect(path) as connection:
        cursor = connection.execute(
            """INSERT INTO clips
               (source_video_id, start_seconds, end_seconds, hook_text, score, reason)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (source_video_id, start, end, hook_text, score, reason),
        )
        return int(cursor.lastrowid)


def queued_uploads(path: str | None = None) -> list[sqlite3.Row]:
    init_db(path)
    with connect(path) as connection:
        return connection.execute(
            "SELECT * FROM uploads WHERE status = 'queued' ORDER BY publish_time"
        ).fetchall()


def consume_quota(units: int, daily_limit: int, path: str | None = None) -> bool:
    """Reserve API quota for today, returning false when the limit is reached."""
    init_db(path)
    usage_date = datetime.now(timezone.utc).date().isoformat()
    with connect(path) as connection:
        row = connection.execute(
            "SELECT units FROM quota_usage WHERE usage_date = ?", (usage_date,)
        ).fetchone()
        used = int(row["units"]) if row else 0
        if used + units > daily_limit:
            return False
        connection.execute(
            "INSERT INTO quota_usage (usage_date, units) VALUES (?, ?) "
            "ON CONFLICT(usage_date) DO UPDATE SET units = excluded.units",
            (usage_date, used + units),
        )
        return True
