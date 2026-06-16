#!/usr/bin/env python3
"""CLI entry point for the AI SEO YouTube research pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from ai_seo_pipeline.pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect and analyze YouTube content from AI SEO experts.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to experts YAML config (default: config/experts.yaml)",
    )
    parser.add_argument(
        "--skip-collection",
        action="store_true",
        help="Skip data collection and re-run analysis on existing CSV files",
    )
    parser.add_argument(
        "--videos-per-channel",
        type=int,
        default=None,
        help="Override number of recent videos to collect per channel",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_pipeline(
        config_path=args.config,
        skip_collection=args.skip_collection,
        videos_per_channel=args.videos_per_channel,
    )


if __name__ == "__main__":
    main()
