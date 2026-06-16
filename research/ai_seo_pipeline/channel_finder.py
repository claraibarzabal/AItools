"""Discover YouTube channels for SEO/AI content marketing experts."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

import yt_dlp
import time
import random
from ai_seo_pipeline.global_rate_limiter import throttle
from ai_seo_pipeline.cache_store import load_cache, save_cache
from ai_seo_pipeline.global_rate_limiter import throttle

CHANNEL_CACHE = load_cache("channels")

logger = logging.getLogger(__name__)


@dataclass
class ChannelInfo:
    expert_name: str
    channel_id: str
    channel_name: str
    channel_url: str
    subscriber_count: int | None
    discovery_method: str


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _normalize_name(name: str | None) -> str:
    if not name:
        return ""
    return re.sub(r"\s+", " ", str(name).strip().lower())


def _score_channel_candidate(
    expert_name: str,
    title: str | None,
    description: str | None = None,
) -> float:
    expert_tokens = set(_normalize_name(expert_name).split())
    title_norm = _normalize_name(title)
    desc_norm = _normalize_name(description)
    score = 0.0

    for token in expert_tokens:
        if len(token) < 3:
            continue
        if token in title_norm:
            score += 3.0
        if token in desc_norm:
            score += 1.0

    seo_signals = ("seo", "search", "marketing", "content", "digital")
    for signal in seo_signals:
        if signal in title_norm or signal in desc_norm:
            score += 0.5

    return score


def _extract_channel_id(entry: dict[str, Any]) -> str | None:
    if not entry:
        return None
    channel_id = entry.get("channel_id") or entry.get("id")
    if channel_id and str(channel_id).startswith("UC"):
        return str(channel_id)
    url = _safe_str(entry.get("channel_url") or entry.get("url") or entry.get("webpage_url"))
    match = re.search(r"/channel/(UC[\w-]+)", url)
    if match:
        return match.group(1)
    return None


def _fetch_channel_metadata(channel_url: str | None) -> dict[str, Any] | None:
    if not channel_url:
        return None

    throttle()

    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
        "sleep_interval": 3,
        "max_sleep_interval": 8,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
            if info:
                return info
    except Exception as exc:
        logger.warning("Could not fetch channel metadata for %s: %s", channel_url, exc)
    return None


def _channel_from_handle(handle: str | None) -> str | None:
    if not handle:
        return None
    return f"https://www.youtube.com/@{handle.lstrip('@')}/videos"


def _build_channel_info(
    expert_name: str,
    metadata: dict[str, Any],
    discovery_method: str,
    fallback_url: str = "",
    fallback_title: str | None = None,
) -> ChannelInfo | None:
    channel_id = metadata.get("channel_id") or metadata.get("id")
    if not channel_id:
        return None

    return ChannelInfo(
        expert_name=expert_name,
        channel_id=str(channel_id),
        channel_name=_safe_str(
            metadata.get("channel") or metadata.get("title") or fallback_title,
            expert_name,
        ),
        channel_url=_safe_str(
            metadata.get("channel_url") or fallback_url,
            f"https://www.youtube.com/channel/{channel_id}",
        ),
        subscriber_count=metadata.get("channel_follower_count"),
        discovery_method=discovery_method,
    )


def discover_channel_from_handle(expert_name: str, handle: str | None) -> ChannelInfo | None:
    try:
        url = _channel_from_handle(handle)
        if not url:
            return None

        info = _fetch_channel_metadata(url)
        if not info:
            return None

        return _build_channel_info(
            expert_name=expert_name,
            metadata=info,
            discovery_method="handle",
            fallback_url=url.replace("/videos", ""),
        )
    except Exception as exc:
        logger.warning("Handle lookup failed for %s (@%s): %s", expert_name, handle, exc)
        return None


def discover_channel_via_search(expert_name: str, max_results: int = 5) -> ChannelInfo | None:
    query = f"{expert_name} SEO YouTube channel"
    search_url = f"ytsearch{max_results}:{query}"

    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": True,
        "sleep_interval": 3,
        "max_sleep_interval": 8,
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            result = ydl.extract_info(search_url, download=False)

    except Exception as exc:
        logger.warning("Search failed for %s: %s", expert_name, exc)
        return None

    if not result:
        logger.warning("Search returned no results for %s", expert_name)
        return None

    entries = result.get("entries") or []
    best: tuple[float, dict[str, Any]] | None = None

    for entry in entries:
        if not entry:
            continue
        title = entry.get("title")
        description = entry.get("description")
        score = _score_channel_candidate(expert_name, title, description)
        if best is None or score > best[0]:
            best = (score, entry)

    if not best or best[0] < 2.0:
        logger.info("No suitable search match for %s (best score below threshold)", expert_name)
        return None

    entry = best[1]
    channel_id = _extract_channel_id(entry)
    channel_url = _safe_str(entry.get("channel_url") or entry.get("url"))
    fallback_title = _safe_str(entry.get("title"), expert_name)

    if channel_id:
        throttle()
        metadata = _fetch_channel_metadata(f"https://www.youtube.com/channel/{channel_id}")
        if metadata:
            channel = _build_channel_info(
                expert_name=expert_name,
                metadata=metadata,
                discovery_method="search",
                fallback_url=f"https://www.youtube.com/channel/{channel_id}",
                fallback_title=fallback_title,
            )
            if channel:
                return channel

    if channel_url:
        throttle()
        metadata = _fetch_channel_metadata(channel_url)
        if metadata:
            return _build_channel_info(
                expert_name=expert_name,
                metadata=metadata,
                discovery_method="search",
                fallback_url=channel_url,
                fallback_title=fallback_title,
            )

    return None


def discover_channel(
    expert_name: str,
    channel_handle: str | None = None,
    channel_url: str | None = None,
    max_search_results: int = 5,
):
    global CHANNEL_CACHE

    # 1. CACHE FIRST (🔥 clave)
    if expert_name in CHANNEL_CACHE:
        cached = CHANNEL_CACHE[expert_name]
        return ChannelInfo(**cached)

    try:
        # 2. URL FIRST
        if channel_url:
            metadata = _fetch_channel_metadata(channel_url)
            if metadata:
                channel = _build_channel_info(
                    expert_name=expert_name,
                    metadata=metadata,
                    discovery_method="url",
                    fallback_url=channel_url,
                )
                if channel:
                    CHANNEL_CACHE[expert_name] = channel.__dict__
                    save_cache("channels", CHANNEL_CACHE)
                    return channel

        # 3. HANDLE
        if channel_handle:
            channel = discover_channel_from_handle(expert_name, channel_handle)
            if channel:
                CHANNEL_CACHE[expert_name] = channel.__dict__
                save_cache("channels", CHANNEL_CACHE)
                return channel

        # 4. SEARCH (last resort)
        channel = discover_channel_via_search(
            expert_name,
            max_results=max_search_results
        )

        if channel:
            CHANNEL_CACHE[expert_name] = channel.__dict__
            save_cache("channels", CHANNEL_CACHE)
            return channel

        return None

    except Exception as exc:
        logger.warning("Channel discovery failed for %s: %s", expert_name, exc)
        return None


def channels_to_dataframe(channels: list[ChannelInfo]):
    import pandas as pd

    rows = [
        {
            "expert_name": c.expert_name,
            "channel_id": c.channel_id,
            "channel_name": c.channel_name,
            "channel_url": c.channel_url,
            "subscriber_count": c.subscriber_count,
            "discovery_method": c.discovery_method,
        }
        for c in channels
    ]
    return pd.DataFrame(rows)
