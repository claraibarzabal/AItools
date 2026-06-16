"""Matplotlib visualizations for AI SEO research outputs."""

from __future__ import annotations

import logging

import matplotlib.pyplot as plt
import pandas as pd

from .config import VIZ_DIR
from .nlp_analyzer import NLPAnalysisResult

logger = logging.getLogger(__name__)

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")


def _save_bar_chart(
    labels: list[str],
    values: list[int | float],
    title: str,
    xlabel: str,
    filename: str,
    top_n: int = 15,
) -> None:
    if not labels:
        logger.warning("Skipping chart '%s' — no data.", title)
        return

    pairs = sorted(zip(labels, values), key=lambda x: x[1], reverse=True)[:top_n]
    chart_labels, chart_values = zip(*pairs)

    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.barh(range(len(chart_labels)), chart_values, color="#2563eb")
    ax.set_yticks(range(len(chart_labels)))
    ax.set_yticklabels(chart_labels)
    ax.invert_yaxis()
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel(xlabel)

    for bar, value in zip(bars, chart_values):
        ax.text(bar.get_width() + max(chart_values) * 0.01, bar.get_y() + bar.get_height() / 2, str(value), va="center")

    fig.tight_layout()
    VIZ_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(VIZ_DIR / filename, dpi=150, bbox_inches="tight")
    plt.close(fig)


def create_visualizations(analysis: NLPAnalysisResult) -> None:
    if not analysis.top_keywords.empty:
        _save_bar_chart(
            labels=analysis.top_keywords["keyword"].tolist(),
            values=analysis.top_keywords["frequency"].tolist(),
            title="Most Common Topics (Keywords)",
            xlabel="Frequency",
            filename="most_common_topics.png",
        )

    if not analysis.ai_tools_mentions.empty:
        _save_bar_chart(
            labels=analysis.ai_tools_mentions["phrase"].tolist(),
            values=analysis.ai_tools_mentions["mentions"].tolist(),
            title="Most Common AI Tools Mentioned",
            xlabel="Mentions",
            filename="most_common_ai_tools.png",
        )

    if not analysis.seo_concepts_mentions.empty:
        _save_bar_chart(
            labels=analysis.seo_concepts_mentions["phrase"].tolist(),
            values=analysis.seo_concepts_mentions["mentions"].tolist(),
            title="Most Common SEO Concepts Mentioned",
            xlabel="Mentions",
            filename="most_common_seo_concepts.png",
        )

    if not analysis.creator_comparison.empty:
        creators = analysis.creator_comparison["expert_name"].tolist()
        ai_counts = analysis.creator_comparison["ai_tool_mentions"].tolist()
        seo_counts = analysis.creator_comparison["seo_concept_mentions"].tolist()

        fig, ax = plt.subplots(figsize=(12, 7))
        x = range(len(creators))
        width = 0.35
        ax.bar([i - width / 2 for i in x], ai_counts, width, label="AI Tools", color="#2563eb")
        ax.bar([i + width / 2 for i in x], seo_counts, width, label="SEO Concepts", color="#16a34a")
        ax.set_xticks(list(x))
        ax.set_xticklabels(creators, rotation=45, ha="right")
        ax.set_title("Creator Comparison: AI Tools vs SEO Concepts", fontweight="bold")
        ax.set_ylabel("Mentions")
        ax.legend()
        fig.tight_layout()
        VIZ_DIR.mkdir(parents=True, exist_ok=True)
        fig.savefig(VIZ_DIR / "creator_comparison.png", dpi=150, bbox_inches="tight")
        plt.close(fig)

    logger.info("Visualizations saved to %s", VIZ_DIR)
