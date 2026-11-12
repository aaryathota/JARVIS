"""One-command daily faceless Shorts pipeline."""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta

import job_status
from clip_automation import create_and_upload_clips_from_video
from discovery import Candidate, discover_candidates

DEFAULT_WINDOWS = ("09:00", "12:00", "15:00", "18:00", "21:00")


def publish_schedule(count: int, now: datetime | None = None) -> list[str]:
    """Return ISO timestamps spread across the configured local peak windows."""
    current = now or datetime.now().astimezone()
    if current.tzinfo is None:
        current = current.astimezone()
    configured = os.getenv("DAILY_PUBLISH_WINDOWS", ",".join(DEFAULT_WINDOWS))
    windows: list[datetime] = []
    for value in configured.split(","):
        try:
            hour, minute = (int(part) for part in value.strip().split(":", 1))
            candidate = current.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if candidate <= current:
                candidate += timedelta(days=1)
            windows.append(candidate)
        except ValueError:
            continue
    if not windows:
        windows = [current + timedelta(hours=1)]
    windows.sort()
    return [(windows[index % len(windows)] + timedelta(days=index // len(windows))).isoformat()
            for index in range(count)]


def _process_candidate(candidate: Candidate, publish_at: str, dry_run: bool, status_index: int) -> list[str]:
    job_status.step(f"Clipping: {candidate.title[:70]}")
    return create_and_upload_clips_from_video(
        candidate.url,
        num_clips=1,
        clip_duration=30,
        privacy_status="public",
        wait_between_uploads=0,
        upload=not dry_run,
        publish_times=[publish_at],
        niche=candidate.niche,
        manage_job_status=False,
        status_index=status_index,
    )


def run_daily_clips(limit: int = 10, dry_run: bool = False) -> list[str]:
    """Discover and process a daily batch without interactive prompts."""
    limit = max(1, min(limit, 10))
    job_status.start(limit, "daily discovery")
    try:
        job_status.step("Discovering permitted videos from the last 48 hours")
        candidates = discover_candidates(limit=limit)
        if not candidates:
            job_status.finish([], "No eligible permitted videos found")
            print("[DAILY] No eligible permitted videos found")
            return []

        schedule = publish_schedule(len(candidates))
        results: list[str] = []
        for index, candidate in enumerate(candidates):
            if index >= limit:
                break
            print(f"[DAILY] {index + 1}/{len(candidates)} {candidate.title}")
            try:
                results.extend(_process_candidate(candidate, schedule[index], dry_run, index + 1))
            except Exception as error:
                print(f"[DAILY] Failed source {candidate.video_id}: {error}")
        job_status.finish(results)
        print(f"[DAILY] Completed: {len(results)} {'local clips' if dry_run else 'uploads'}")
        return results
    except Exception as error:
        job_status.finish([], str(error))
        print(f"[DAILY ERROR] {type(error).__name__}: {error}")
        return []


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the daily JARVIS Shorts batch")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true", help="Create clips without uploading")
    parser.add_argument("--review", action="store_true", help="Create clips for dashboard review without uploading")
    args = parser.parse_args()
    run_daily_clips(limit=args.limit, dry_run=args.dry_run or args.review)


if __name__ == "__main__":
    main()
