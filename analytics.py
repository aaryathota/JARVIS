"""Optional YouTube Analytics pull and compact picker-learning summaries."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from db import connect, init_db, utc_now


def pull_video_metrics(video_ids: list[str], analytics_service: Any,
                       start: date | None = None, end: date | None = None,
                       db_path: str | None = None) -> int:
    """Pull daily views/likes/watch duration for uploaded clips.

    The caller supplies an Analytics API service because its OAuth scope is
    optional and should not force existing upload credentials to reauthorize.
    """
    if not video_ids:
        return 0
    init_db(db_path)
    start = start or (date.today() - timedelta(days=1))
    end = end or date.today()
    response = analytics_service.reports().query(
        ids="channel==MINE",
        startDate=start.isoformat(),
        endDate=end.isoformat(),
        metrics="views,averageViewDuration,likes",
        dimensions="video",
        filters="video==" + ",".join(video_ids),
    ).execute()
    rows = response.get("rows", [])
    with connect(db_path) as connection:
        for video_id, views, average_duration, likes in rows:
            connection.execute(
                """INSERT INTO metrics
                   (video_id, captured_at, views, average_view_duration, likes, window)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (video_id, utc_now(), int(views), float(average_duration), int(likes),
                 f"{start.isoformat()}:{end.isoformat()}"),
            )
    return len(rows)


def performance_summary(db_path: str | None = None) -> dict[str, dict[str, float]]:
    """Return average performance grouped by clip length and hook presence."""
    init_db(db_path)
    with connect(db_path) as connection:
        rows = connection.execute(
            """SELECT c.end_seconds - c.start_seconds AS length,
                      CASE WHEN c.hook_text != '' THEN 'hook' ELSE 'no_hook' END AS hook,
                      AVG(m.views) AS views, AVG(m.likes) AS likes
               FROM metrics m
               JOIN uploads u ON u.video_id = m.video_id
               JOIN clips c ON c.id = u.clip_id
               GROUP BY length, hook"""
        ).fetchall()
    return {
        f"{row['length']:.0f}s_{row['hook']}": {
            "views": float(row["views"] or 0),
            "likes": float(row["likes"] or 0),
        }
        for row in rows
    }
