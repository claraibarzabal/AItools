"""Fetch YouTube transcripts with primary and fallback strategies."""

from __future__ import annotations

import json
import logging
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

from ai_seo_pipeline.global_rate_limiter import throttle
from ai_seo_pipeline.cache_store import load_cache, save_cache
from ai_seo_pipeline.global_rate_limiter import throttle

TRANSCRIPT_CACHE = load_cache("transcripts")

logger = logging.getLogger(__name__)


@dataclass
class TranscriptResult:
    video_id: str
    expert_name: str
    language: str
    transcript_text: str
    source: str
    success: bool
    error_message: str = ""


def _join_transcript_segments(segments: list[dict]) -> str:
    return " ".join(segment.get("text", "").strip() for segment in segments if segment.get("text"))


def _fetch_via_transcript_api(video_id: str) -> tuple[str, str] | None:
    throttle()

    for lang in ("en", "en-US", "en-GB"):
        for attempt in range(3):
            try:
                throttle()

                fetched = YouTubeTranscriptApi.get_transcript(
                    video_id,
                    languages=[lang],
                )

                text = _join_transcript_segments(fetched)

                if text.strip():
                    return text, lang

                break  # no retry si vino vacío

            except (TranscriptsDisabled, VideoUnavailable, NoTranscriptFound):
                break  # no tiene sentido reintentar este idioma

            except Exception as exc:
                logger.debug(
                    "Transcript attempt %s failed for %s (%s): %s",
                    attempt + 1,
                    video_id,
                    lang,
                    exc,
                )
                time.sleep((2 ** attempt) + random.uniform(0, 1.5))

    # fallback: list_transcripts
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    except (TranscriptsDisabled, VideoUnavailable, NoTranscriptFound):
        return None
    except Exception as exc:
        logger.debug("Transcript API list failed for %s: %s", video_id, exc)
        return None

    preferred = []
    for lang in ("en", "en-US", "en-GB"):
        try:
            preferred.append(transcript_list.find_transcript([lang]))
        except NoTranscriptFound:
            continue

    candidates = preferred or list(transcript_list)

    for transcript in candidates:
        try:
            fetched = transcript.fetch()
            text = _join_transcript_segments(fetched)

            if text.strip():
                return text, transcript.language

        except Exception:
            continue

    return None

def _parse_vtt_content(content: str) -> str:
    lines = []
    seen: set[str] = set()
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("WEBVTT") or "-->" in line or line.isdigit():
            continue
        line = re.sub(r"<[^>]+>", "", line)
        line = re.sub(r"\s+", " ", line).strip()
        if line and line not in seen:
            seen.add(line)
            lines.append(line)
    return " ".join(lines)


def _fetch_via_ytdlp_subtitles(video_id: str) -> tuple[str, str] | None:
    throttle() 
    url = f"https://www.youtube.com/watch?v={video_id}"
    with tempfile.TemporaryDirectory() as tmpdir:
        outtmpl = str(Path(tmpdir) / "%(id)s")
        opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,

                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "web"]
                    }
                },

            "sleep_interval": 5,
            "max_sleep_interval": 12,
        }

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
        except Exception as exc:
            logger.debug("yt-dlp subtitle download failed for %s: %s", video_id, exc)
            return None

        vtt_files = sorted(Path(tmpdir).glob("*.vtt"))
        if not vtt_files:
            json_files = sorted(Path(tmpdir).glob("*.json3"))
            if json_files:
                try:
                    data = json.loads(json_files[0].read_text(encoding="utf-8"))
                    events = data.get("events", [])
                    text_parts = []
                    for event in events:
                        for seg in event.get("segs", []):
                            if seg.get("utf8"):
                                text_parts.append(seg["utf8"].strip())
                    text = " ".join(part for part in text_parts if part)
                    if text.strip():
                        return text, "en (auto-json3)"
                except Exception:
                    return None
            return None

        content = vtt_files[0].read_text(encoding="utf-8", errors="ignore")
        text = _parse_vtt_content(content)
        if text.strip():
            return text, "en (auto-vtt)"

    return None


def fetch_transcript(video_id, expert_name):

    # 1. CACHE FIRST (reduce 90%)
    if video_id in TRANSCRIPT_CACHE:
        return TRANSCRIPT_CACHE[video_id]

    # 2. RETRY INTELIGENTE
    for attempt in range(3):
        try:
            throttle()

            result = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=["en", "en-US", "en-GB"]
            )

            text = " ".join(x["text"] for x in result if x.get("text"))

            if text.strip():
                data = {
                    "video_id": video_id,
                    "text": text,
                    "success": True
                }

                TRANSCRIPT_CACHE[video_id] = data
                save_cache("transcripts", TRANSCRIPT_CACHE)

                return data

        except Exception as e:

            msg = str(e).lower()

            # 🔥 rate limit handling real
            if "rate" in msg or "data blocks" in msg:
                time.sleep((attempt + 1) * 25)  # backoff fuerte
            else:
                break  # no reintentar errores inútiles

    return None


def transcripts_to_dataframe(results: list[TranscriptResult]):
    import pandas as pd

    rows = [
        {
            "video_id": r.video_id,
            "expert_name": r.expert_name,
            "language": r.language,
            "transcript_text": r.transcript_text,
            "source": r.source,
            "success": r.success,
            "error_message": r.error_message,
        }
        for r in results
    ]
    return pd.DataFrame(rows)
