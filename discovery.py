"""Allowlisted YouTube source discovery and popularity ranking."""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from db import init_db, save_source, source_seen

HERE = os.path.dirname(os.path.abspath(__file__))
CHANNELS_FILE = os.path.join(HERE, "channels.json")
MIN_DURATION = 5 * 60
MAX_DURATION = 90 * 60
MAX_AGE = timedelta(hours=48)


@dataclass(frozen=True)
class Channel:
    channel_id: str
    name: str
    niche: str
    clipping_permitted: bool
    credit_text: str


@dataclass(frozen=True)
class Candidate:
    video_id: str
    channel_id: str
    channel_name: str
    title: str
    url: str
    published_at: str
    duration_seconds: float
    views: int
    likes: int
    score: float
    niche: str = "entertainment"
    max_clips: int = 3


def load_channels(path: str = CHANNELS_FILE) -> list[Channel]:
    with open(path, "r", encoding="utf-8") as file:
        raw = json.load(file)
    if not isinstance(raw, list):
        raise ValueError("channels.json must contain a list")
    return [Channel(
        channel_id=str(item["channel_id"]),
        name=str(item.get("name", item["channel_id"])),
        niche=str(item.get("niche", "entertainment")),
        clipping_permitted=bool(item.get("clipping_permitted", False)),
        credit_text=str(item.get("credit_text", "")),
    ) for item in raw]


def save_channels(channels: list[Channel], path: str = CHANNELS_FILE) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump([channel.__dict__ for channel in channels], file, indent=2)
        file.write("\n")


def add_channel(channel_id: str, name: str, niche: str, credit_text: str,
                path: str = CHANNELS_FILE) -> None:
    channels = load_channels(path)
    if any(channel.channel_id == channel_id for channel in channels):
        raise ValueError(f"Channel already exists: {channel_id}")
    channels.append(Channel(channel_id, name, niche, True, credit_text))
    save_channels(channels, path)


def remove_channel(channel_id: str, path: str = CHANNELS_FILE) -> bool:
    channels = load_channels(path)
    kept = [channel for channel in channels if channel.channel_id != channel_id]
    if len(kept) == len(channels):
        return False
    save_channels(kept, path)
    return True


def _parse_duration(value: str) -> float:
    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?", value or "")
    if not match:
        return 0.0
    hours, minutes, seconds = match.groups(default="0")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def _published_at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _score(views: int, likes: int, published: datetime, now: datetime) -> float:
    hours = max((now - published).total_seconds() / 3600, 1 / 60)
    views_per_hour = views / hours
    like_ratio = likes / max(views, 1)
    return views_per_hour * (1 + min(like_ratio * 100, 1))


def _service(api_key: str | None = None):
    from googleapiclient.discovery import build
    key = api_key or os.getenv("YOUTUBE_API_KEY")
    if not key:
        raise RuntimeError("YOUTUBE_API_KEY is required for discovery")
    return build("youtube", "v3", developerKey=key, cache_discovery=False)


def discover_candidates(limit: int = 10, db_path: str | None = None,
                        channels_path: str = CHANNELS_FILE,
                        service: Any | None = None) -> list[Candidate]:
    """Fetch and rank permitted videos from the last 48 hours."""
    init_db(db_path)
    permitted_channels = [channel for channel in load_channels(channels_path)
                          if channel.clipping_permitted]
    if not permitted_channels:
        return []
    youtube = service or _service()
    now = datetime.now(timezone.utc)
    candidates: list[Candidate] = []

    for channel in permitted_channels:
        channel_response = youtube.channels().list(
            part="contentDetails", id=channel.channel_id
        ).execute()
        items = channel_response.get("items", [])
        if not items:
            continue
        uploads_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
        playlist_response = youtube.playlistItems().list(
            part="contentDetails,snippet", playlistId=uploads_id, maxResults=50
        ).execute()
        video_ids = [item["contentDetails"]["videoId"] for item in playlist_response.get("items", [])]
        if not video_ids:
            continue
        video_response = youtube.videos().list(
            part="snippet,contentDetails,statistics,liveStreamingDetails",
            id=",".join(video_ids),
        ).execute()
        for item in video_response.get("items", []):
            video_id = item["id"]
            snippet = item.get("snippet", {})
            published = _published_at(snippet.get("publishedAt", ""))
            duration = _parse_duration(item.get("contentDetails", {}).get("duration", ""))
            live = item.get("snippet", {}).get("liveBroadcastContent") == "live"
            if live or now - published > MAX_AGE or not MIN_DURATION <= duration <= MAX_DURATION:
                continue
            if source_seen(video_id, db_path):
                continue
            stats = item.get("statistics", {})
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))
            candidate = Candidate(
                video_id=video_id,
                channel_id=channel.channel_id,
                channel_name=channel.name,
                title=snippet.get("title", "Untitled"),
                url=f"https://www.youtube.com/watch?v={video_id}",
                published_at=published.isoformat(),
                duration_seconds=duration,
                views=views,
                likes=likes,
                score=_score(views, likes, published, now),
                niche=channel.niche,
            )
            save_source(candidate.__dict__, db_path)
            candidates.append(candidate)

    candidates.sort(key=lambda candidate: candidate.score, reverse=True)
    selected: list[Candidate] = []
    source_counts: dict[str, int] = {}
    for candidate in candidates:
        count = source_counts.get(candidate.video_id, 0)
        if count >= 3:
            continue
        selected.append(candidate)
        source_counts[candidate.video_id] = count + 1
        if len(selected) >= limit:
            break
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage the JARVIS Shorts channel allowlist")
    subparsers = parser.add_subparsers(dest="action", required=True)
    add = subparsers.add_parser("add")
    add.add_argument("channel_id")
    add.add_argument("name")
    add.add_argument("--niche", default="entertainment")
    add.add_argument("--credit", default="")
    remove = subparsers.add_parser("remove")
    remove.add_argument("channel_id")
    subparsers.add_parser("list")
    args = parser.parse_args()
    if args.action == "add":
        add_channel(args.channel_id, args.name, args.niche, args.credit)
    elif args.action == "remove":
        print("removed" if remove_channel(args.channel_id) else "not found")
    else:
        for channel in load_channels():
            print(f"{channel.channel_id}\t{channel.name}\t{channel.niche}\t{channel.clipping_permitted}")


if __name__ == "__main__":
    main()
