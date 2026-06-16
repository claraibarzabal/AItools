"""Main orchestration pipeline for AI SEO YouTube research (Supadata version)."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import yaml

from .config import (
    CHANNELS_CSV,
    DATA_DIR,
    EXPERTS_CONFIG,
    VIDEOS_CSV,
)
from .data_storage import load_csv, save_csv
from .nlp_analyzer import NLPAnalyzer
from .report_generator import export_analysis_outputs, generate_summary_report
from .video_collector import fetch_recent_videos, videos_to_dataframe
from .visualizer import create_visualizations

# NEW (Supadata + file storage)
from .transcript_client import fetch_transcripts_batch
from .storage.naming import build_filename
from .storage.local_store import save_transcript_file
import hashlib
from ai_seo_pipeline.cache_store import load_cache, save_cache
import pandas as pd
from ai_seo_pipeline.youtube_resolver import resolve_channel_id

TRANSCRIPT_CACHE = load_cache("transcripts")

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def load_experts_config(path: Path | None = None) -> dict[str, Any]:
    config_path = path or EXPERTS_CONFIG
    with config_path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def ensure_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def collect_channels(config):
    import pandas as pd

    rows = []

    for expert in config["experts"]:
        rows.append({
            "expert_name": expert["name"],
            "handle": expert["handle"],
        })

    df = pd.DataFrame(rows)
    save_csv(df, CHANNELS_CSV)
    return df

def collect_videos(channels_df, videos_per_channel=20):
    all_videos = []

    for _, row in channels_df.iterrows():

        logger.info("Collecting videos for %s", row["expert_name"])

        channel_id = resolve_channel_id(row["handle"])

        videos = fetch_recent_videos(
            channel_id=channel_id,
            expert_name=row["expert_name"],
            limit=videos_per_channel,
        )

        all_videos.extend(videos)

        time.sleep(0.5)

    df = videos_to_dataframe(all_videos)
    save_csv(df, VIDEOS_CSV)
    return df

def build_transcripts_dataset(videos_df: Any) -> None:

    logger.info("Building transcripts dataset with Supadata (BATCH MODE)...")

    base_dir = Path("research/youtube-transcripts/data/transcripts")
    base_dir.mkdir(parents=True, exist_ok=True)

    videos = list(videos_df.to_dict("records"))

    logger.info(
        "Total videos in transcript stage: %s",
        len(videos)
    )

    video_urls = [v["url"] for v in videos]

    logger.info(
        "Video URLs sent: %s",
        len(video_urls)
    )

    # 🚀 BATCH CALL (10x faster)
    transcripts_map = fetch_transcripts_batch(
        video_urls,
        max_workers=1
    )

    logger.info(
        "Transcripts returned: %s",
        len(transcripts_map)
    )

    logger.info(
        "Transcript keys sample: %s",
        list(transcripts_map.keys())[:5]
    )

    for video in videos:

        video_url = video["url"]
        transcript = transcripts_map.get(video_url)

        print(
            "PIPELINE:",
            video["video_id"],
            len(transcript) if transcript else 0
        )

        if not transcript:
            logger.warning(
                "No transcript for video %s",
                video["video_id"]
            )
            transcript = ""

        filename = build_filename(video)

        data = {
            "video_id": video["video_id"],
            "title": video["title"],
            "published_at": video["published_at"],
            "url": video_url,
            "expert_name": video["expert_name"],
            "transcript": transcript,
            "has_transcript": bool(transcript),
        }

        save_transcript_file(filename, data)

def run_analysis_from_files() -> tuple[Any, Any]:
    """
    OPTIONAL:
    aquí puedes leer los JSON generados si quieres NLP posterior
    """
    analyzer = NLPAnalyzer()

    # Si ya tienes loader de JSON → conviertes a DF aquí
    # cleaned_df = load_transcripts_from_files()

    # analysis = analyzer.analyze(cleaned_df)

    # return cleaned_df, analysis

    raise NotImplementedError("Implement file-based loader if needed")


def run_pipeline(
    config_path: Path | None = None,
    skip_collection: bool = False,
    videos_per_channel: int | None = None,
) -> None:

    setup_logging()
    ensure_directories()

    config = load_experts_config(config_path)

    per_channel = videos_per_channel or config.get("settings", {}).get("videos_per_channel", 20)

    if skip_collection:
        channels_df = load_csv(CHANNELS_CSV)
        videos_df = load_csv(VIDEOS_CSV)
    else:
        channels_df = collect_channels(config)

        if channels_df.empty:
            raise RuntimeError("No channels discovered")

        videos_df = collect_videos(channels_df, videos_per_channel=per_channel)
    
    logger.info("VIDEOS DF SHAPE: %s", videos_df.shape)
    logger.info("VIDEOS DF COLUMNS: %s", list(videos_df.columns))

    # 🔥 NEW STEP: Supadata → files
    build_transcripts_dataset(videos_df)

    logger.info("Pipeline complete (transcripts saved to local repo)")