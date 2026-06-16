"""Central configuration for paths, lexicons, and runtime settings."""

from __future__ import annotations

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

SUPADATA_API_KEY = os.getenv("SUPADATA_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data" / "youtube"
OUTPUT_DIR = PROJECT_ROOT / "output"
VIZ_DIR = OUTPUT_DIR / "visualizations"

CHANNELS_CSV = DATA_DIR / "channels.csv"
VIDEOS_CSV = DATA_DIR / "videos.csv"
TRANSCRIPTS_CSV = DATA_DIR / "transcripts.csv"
TRANSCRIPTS_CLEANED_CSV = DATA_DIR / "transcripts_cleaned.csv"

SUMMARY_REPORT = OUTPUT_DIR / "summary_report.md"
AI_SEO_THEMES_CSV = OUTPUT_DIR / "ai_seo_themes.csv"
TOP_KEYWORDS_CSV = OUTPUT_DIR / "top_keywords.csv"
CREATOR_COMPARISON_CSV = OUTPUT_DIR / "creator_comparison.csv"

EXPERTS_CONFIG = CONFIG_DIR / "experts.yaml"

# Domain lexicons used for entity/concept frequency analysis.
AI_TOOLS = [
    "chatgpt",
    "gpt-4",
    "gpt4",
    "claude",
    "gemini",
    "bard",
    "copilot",
    "perplexity",
    "jasper",
    "copy.ai",
    "surfer seo",
    "surfer",
    "clearscope",
    "marketmuse",
    "frase",
    "semrush",
    "ahrefs",
    "moz",
    "screaming frog",
    "google search console",
    "search console",
    "google analytics",
    "looker studio",
    "rankmath",
    "yoast",
    "wordpress",
    "webflow",
    "notion",
    "zapier",
    "make.com",
    "midjourney",
    "dall-e",
    "stable diffusion",
    "sora",
    "notebooklm",
    "llm",
    "large language model",
    "openai",
    "anthropic",
    "google ai",
    "bing chat",
    "searchgpt",
    "ai overviews",
    "ai mode",
]

SEO_CONCEPTS = [
    "seo",
    "search engine optimization",
    "keyword research",
    "backlinks",
    "link building",
    "technical seo",
    "on-page seo",
    "off-page seo",
    "content strategy",
    "content marketing",
    "eeat",
    "e-e-a-t",
    "core web vitals",
    "page speed",
    "schema markup",
    "structured data",
    "serp",
    "featured snippet",
    "ai search",
    "generative engine optimization",
    "geo",
    "aeo",
    "answer engine optimization",
    "zero-click search",
    "topical authority",
    "topical map",
    "entity seo",
    "semantic seo",
    "internal linking",
    "site architecture",
    "crawl budget",
    "indexing",
    "canonical",
    "hreflang",
    "local seo",
    "programmatic seo",
    "content cluster",
    "pillar page",
    "search intent",
    "ctr",
    "click-through rate",
    "conversion rate",
    "organic traffic",
    "rankings",
    "algorithm update",
    "helpful content",
    "ai content",
    "content production",
    "content workflow",
    "editorial calendar",
    "brief",
    "content brief",
]

WORKFLOW_PHRASES = [
    "content workflow",
    "content production",
    "editorial process",
    "research phase",
    "outline",
    "first draft",
    "human review",
    "fact check",
    "edit and refine",
    "publish",
    "optimize",
    "repurpose",
    "update content",
    "content brief",
    "keyword mapping",
    "topic research",
    "competitor analysis",
    "serp analysis",
    "ai assisted writing",
    "ai assisted research",
    "human in the loop",
    "quality control",
    "brand voice",
    "style guide",
]

NLP_SETTINGS = {
    "min_df": 2,
    "max_df": 0.85,
    "max_features": 5000,
    "ngram_range": (1, 3),
    "n_clusters": 8,
    "top_n_keywords": 50,
    "top_n_topics": 15,
}
