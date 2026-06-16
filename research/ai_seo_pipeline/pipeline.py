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

    df = pd.DataFrame(config["experts"]).rename(
        columns={"name": "expert_name"}
    )

    # asegurás solo columnas necesarias
    df = df[["expert_name", "channel_url"]]

    save_csv(df, CHANNELS_CSV)
    return df


def collect_videos(channels_df: Any, videos_per_channel: int = 20) -> Any:
    all_videos = []

    for _, row in channels_df.iterrows():

        logger.info("Collecting videos for %s", row["expert_name"])

        videos = fetch_recent_videos(
            channel_url=row["channel_url"],
            expert_name=row["expert_name"],
            limit=videos_per_channel,
        )

        all_videos.extend(videos)

        logger.info("Collected %d videos for %s", len(videos), row["expert_name"])

        time.sleep(0.5)

    df = videos_to_dataframe(all_videos)
    save_csv(df, VIDEOS_CSV)
    return df


def build_transcripts_dataset(videos_df: Any) -> None:

    logger.info("Building transcripts dataset with Supadata (BATCH MODE)...")

    base_dir = Path("research/youtube-transcripts/data/transcripts")
    base_dir.mkdir(parents=True, exist_ok=True)

    videos = list(videos_df.to_dict("records"))

    video_urls = [v["url"] for v in videos]

    # 🚀 BATCH CALL (10x faster)
    transcripts_map = fetch_transcripts_batch(video_urls, max_workers=10)

    for video in videos:

        video_url = video["url"]
        transcript = transcripts_map.get(video_url)

        if not transcript:
            logger.warning("No transcript for video %s", video["video_id"])
            continue

        filename = build_filename(video)

        data = {
            "video_id": video["video_id"],
            "title": video["title"],
            "published_at": video["published_at"],
            "url": video_url,
            "expert_name": video["expert_name"],
            "transcript": transcript,
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

    # 🔥 NEW STEP: Supadata → files
    build_transcripts_dataset(videos_df)

    logger.info("Pipeline complete (transcripts saved to local repo)")