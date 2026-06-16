"""Collect recent video metadata from YouTube channels."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, List

import requests

from ai_seo_pipeline.cache_store import load_cache, save_cache
from ai_seo_pipeline.config import YOUTUBE_API_KEY

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


def get_uploads_playlist_id(channel_id: str) -> str:
    url = "https://www.googleapis.com/youtube/v3/channels"

    r = requests.get(url, params={
        "part": "contentDetails",
        "id": channel_id,
        "key": YOUTUBE_API_KEY
    })

    r.raise_for_status()
    data = r.json()

    items = data.get("items")

    if not items:
        raise ValueError(f"No channel contentDetails for {channel_id}. Response={data}")

    try:
        return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    except KeyError:
        raise ValueError(f"No uploads playlist for channel {channel_id}")


def fetch_recent_videos(
    channel_id: str,
    expert_name: str,
    limit: int = 20,
) -> List[VideoInfo]:

    cache_key = f"{channel_id}_{limit}"

    # 🧠 CACHE FIRST
    if cache_key in VIDEO_CACHE:
        logger.info("Video cache hit for %s", expert_name)

        cached = VIDEO_CACHE[cache_key]
        return [
            VideoInfo(**v) if isinstance(v, dict) else v
            for v in cached
        ]

    playlist_id = get_uploads_playlist_id(channel_id)

    url = "https://www.googleapis.com/youtube/v3/playlistItems"

    videos: List[VideoInfo] = []
    page_token = None

    try:
        while len(videos) < limit:

            r = requests.get(url, params={
                "part": "snippet",
                "playlistId": playlist_id,
                "maxResults": 50,
                "pageToken": page_token,
                "key": YOUTUBE_API_KEY
            })

            r.raise_for_status()
            data = r.json()

            for item in data.get("items", []):
                snippet = item["snippet"]
                video_id = snippet["resourceId"]["videoId"]

                videos.append(
                    VideoInfo(
                        video_id=video_id,
                        channel_id=channel_id,   # ✅ FIX IMPORTANTE
                        expert_name=expert_name,
                        title=snippet.get("title", ""),
                        published_at=snippet.get("publishedAt", ""),
                        url=f"https://www.youtube.com/watch?v={video_id}",
                        description="",
                        view_count=None,
                    )
                )

                if len(videos) >= limit:
                    break

            page_token = data.get("nextPageToken")
            if not page_token:
                break

    except Exception as exc:
        logger.error("Failed to fetch videos for %s: %s", expert_name, exc)
        return []

    # 🧠 SAVE CACHE
    VIDEO_CACHE[cache_key] = [v.__dict__ for v in videos]
    save_cache("videos", VIDEO_CACHE)

    return videos


def videos_to_dataframe(videos: list[VideoInfo]):
    import pandas as pd

    return pd.DataFrame([
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
    ])