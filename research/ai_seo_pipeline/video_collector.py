"""Collect recent video metadata from YouTube channels."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import yt_dlp

from ai_seo_pipeline.cache_store import load_cache, save_cache
from ai_seo_pipeline.global_rate_limiter import throttle

VIDEO_CACHE = load_cache("videos")

logger = logging.getLogger(__name__)


@dataclass
class VideoInfo:
    video_id: str
    channel_id: str
    expert_name: str
    title: str
    published_at: str
    url: str
    description: str
    view_count: int | None


def _format_timestamp(timestamp: int | float | None) -> str:
    if not timestamp:
        return ""
    try:
        return datetime.fromtimestamp(int(timestamp), tz=timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OSError):
        return ""


def _entry_timestamp(entry: dict[str, Any]) -> int:
    ts = entry.get("timestamp") or entry.get("release_timestamp") or 0
    try:
        return int(ts)
    except (TypeError, ValueError):
        return 0


def fetch_recent_videos(
    channel_url: str,
    expert_name: str,
    limit: int = 20,
) -> list[VideoInfo]:

    global VIDEO_CACHE

    # 🧠 1. CACHE FIRST (CRÍTICO)
    cache_key = channel_url  # usamos URL como clave estable

    if cache_key in VIDEO_CACHE:
        logger.info("Video cache hit for %s", expert_name)

        cached = VIDEO_CACHE[cache_key]

        return [
            VideoInfo(**v) if isinstance(v, dict) else v
            for v in cached
        ]

    playlist_url = channel_url.rstrip("/")
    if "/videos" not in playlist_url:
        playlist_url = f"{playlist_url}/videos"

    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
    }

    videos: list[VideoInfo] = []

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)

    except Exception as exc:
        logger.error("Failed to fetch videos for %s: %s", expert_name, exc)
        return []

    if not info:
        logger.warning("No channel info returned for %s", expert_name)
        return []

    entries = info.get("entries") or []

    entries = sorted(
        [e for e in entries if e],
        key=lambda x: x.get("timestamp") or x.get("release_timestamp") or 0,
        reverse=True,
    )

    selected_entries = entries[:limit]

    for entry in selected_entries:
        video_id = entry.get("id")
        if not video_id:
            continue

        timestamp = _entry_timestamp(entry)

        videos.append(
            VideoInfo(
                video_id=str(video_id),
                expert_name=expert_name,
                title=entry.get("title") or "",
                published_at=_format_timestamp(timestamp),
                url=entry.get("webpage_url")
                or f"https://www.youtube.com/watch?v={video_id}",
                description=entry.get("description") or "",
                view_count=entry.get("view_count"),
            )
        )

    # 🧠 2. SAVE CACHE (CRÍTICO)
    VIDEO_CACHE[cache_key] = [
        v.__dict__ for v in videos
    ]
    save_cache("videos", VIDEO_CACHE)

    return videos

def videos_to_dataframe(videos: list[VideoInfo]):
    import pandas as pd

    rows = [
        {
            "video_id": v.video_id,
            "channel_id": v.channel_id,
            "expert_name": v.expert_name,
            "title": v.title,
            "published_at": v.published_at,
            "url": v.url,
            "description": v.description,
            "view_count": v.view_count,
        }
        for v in videos
    ]
    return pd.DataFrame(rows)
