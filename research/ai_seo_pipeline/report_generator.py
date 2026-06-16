"""Generate markdown reports and analysis CSV exports."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from .config import (
    AI_SEO_THEMES_CSV,
    CREATOR_COMPARISON_CSV,
    SUMMARY_REPORT,
    TOP_KEYWORDS_CSV,
)
from .data_storage import save_csv
from .nlp_analyzer import NLPAnalysisResult


def _df_stats(df: pd.DataFrame, label: str) -> str:
    if df.empty:
        return f"- **{label}:** 0 records"
    return f"- **{label}:** {len(df)} records"


def generate_summary_report(
    channels_df: pd.DataFrame,
    videos_df: pd.DataFrame,
    transcripts_df: pd.DataFrame,
    cleaned_df: pd.DataFrame,
    analysis: NLPAnalysisResult,
) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    answers = analysis.research_answers

    successful_transcripts = (
        int(transcripts_df["success"].sum()) if "success" in transcripts_df.columns else 0
    )

    lines = [
        "# AI-Powered SEO Content Production — Research Summary",
        "",
        f"*Generated: {timestamp}*",
        "",
        "## Dataset Overview",
        "",
        _df_stats(channels_df, "Channels discovered"),
        _df_stats(videos_df, "Videos collected"),
        f"- **Transcripts retrieved:** {successful_transcripts}",
        _df_stats(cleaned_df, "Cleaned transcripts"),
        "",
        "## Research Questions",
        "",
        "### What AI SEO topics are discussed most frequently?",
        "",
        answers.get("most_discussed_ai_seo_topics", "N/A"),
        "",
        "**Top SEO concepts:**",
        "",
        answers.get("top_seo_concepts", "N/A"),
        "",
        "### Which AI tools are mentioned most often?",
        "",
        answers.get("most_mentioned_ai_tools", "N/A"),
        "",
        "### What content production workflows are repeatedly recommended?",
        "",
        answers.get("recommended_workflows", "N/A"),
        "",
        "### What differences exist between creators?",
        "",
        answers.get("creator_differences", "N/A"),
        "",
        "## Topic Modeling Highlights",
        "",
        answers.get("topic_model_summary", "N/A"),
        "",
        "## Top Keywords",
        "",
    ]

    if not analysis.top_keywords.empty:
        for _, row in analysis.top_keywords.head(20).iterrows():
            lines.append(f"- {row['keyword']} ({row['frequency']})")
    else:
        lines.append("- No keyword data available.")

    lines.extend(
        [
            "",
            "## Creator Comparison Snapshot",
            "",
        ]
    )

    if not analysis.creator_comparison.empty:
        lines.append("| Creator | Videos | AI Tool Mentions | SEO Concept Mentions | Dominant Theme |")
        lines.append("|---------|--------|------------------|----------------------|----------------|")
        for _, row in analysis.creator_comparison.iterrows():
            lines.append(
                f"| {row['expert_name']} | {row['videos_analyzed']} | "
                f"{row['ai_tool_mentions']} | {row['seo_concept_mentions']} | "
                f"{row['dominant_theme']} |"
            )
    else:
        lines.append("No creator comparison data available.")

    lines.extend(
        [
            "",
            "## Methodology",
            "",
            "1. Expert YouTube channels were discovered via configured handles with search fallback.",
            "2. The 20 most recent videos per channel were collected with metadata.",
            "3. Transcripts were fetched using `youtube-transcript-api` with yt-dlp subtitle fallback.",
            "4. Transcripts were cleaned (timestamps removed, duplicates deduplicated, whitespace normalized).",
            "5. NLP analysis included keyword frequency, n-grams, NMF topic extraction, and KMeans clustering.",
            "",
            "## Output Files",
            "",
            "- `data/youtube/channels.csv`",
            "- `data/youtube/videos.csv`",
            "- `data/youtube/transcripts.csv`",
            "- `data/youtube/transcripts_cleaned.csv`",
            "- `output/ai_seo_themes.csv`",
            "- `output/top_keywords.csv`",
            "- `output/creator_comparison.csv`",
            "- `output/visualizations/`",
        ]
    )

    SUMMARY_REPORT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_analysis_outputs(analysis: NLPAnalysisResult) -> None:
    keywords_export = analysis.top_keywords.copy()
    if not analysis.top_ngrams.empty:
        keywords_export = pd.concat(
            [
                keywords_export.assign(type="keyword"),
                analysis.top_ngrams.rename(columns={"ngram": "keyword"}).assign(type="ngram"),
            ],
            ignore_index=True,
        )

    save_csv(keywords_export, TOP_KEYWORDS_CSV)
    save_csv(analysis.ai_seo_themes, AI_SEO_THEMES_CSV)
    save_csv(analysis.creator_comparison, CREATOR_COMPARISON_CSV)
