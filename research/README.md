# AI-Powered SEO Content Production — YouTube Research Pipeline

A modular Python research pipeline that collects, analyzes, and visualizes YouTube content from leading SEO, AI Search, and Content Marketing experts.

## Overview

This project automates a full research workflow:

1. **Channel discovery** — Finds expert YouTube channels via configured handles with search fallback
2. **Video metadata collection** — Downloads the 20 most recent videos per creator
3. **Transcript extraction** — Uses `youtube-transcript-api` with yt-dlp subtitle fallback
4. **Data storage** — Saves raw artifacts to structured CSV files
5. **Transcript cleaning** — Removes timestamps, deduplicates text, normalizes whitespace
6. **NLP analysis** — Topic extraction, keyword frequency, n-grams, theme clustering
7. **Reporting** — Generates markdown summaries, comparison tables, and charts

## Project Structure

```
research/
├── ai_seo_pipeline/          # Core Python package
│   ├── channel_finder.py     # YouTube channel discovery
│   ├── video_collector.py    # Video metadata collection
│   ├── transcript_fetcher.py # Transcript download (primary + fallback)
│   ├── transcript_cleaner.py # Transcript preprocessing
│   ├── nlp_analyzer.py       # NLP analysis and clustering
│   ├── report_generator.py   # Markdown + CSV report exports
│   ├── visualizer.py         # Matplotlib charts
│   ├── data_storage.py       # CSV helpers
│   ├── config.py             # Paths and domain lexicons
│   └── pipeline.py           # Pipeline orchestrator
├── config/
│   └── experts.yaml          # Expert list and settings
├── data/
│   └── youtube/
│       ├── channels.csv
│       ├── videos.csv
│       ├── transcripts.csv
│       └── transcripts_cleaned.csv
├── output/
│   ├── summary_report.md
│   ├── ai_seo_themes.csv
│   ├── top_keywords.csv
│   ├── creator_comparison.csv
│   └── visualizations/
├── requirements.txt
└── run_pipeline.py           # CLI entry point
```

## Experts Analyzed

- Aleyda Solís
- Lily Ray
- Kevin Indig
- Matt Diggity
- Nathan Gotch
- Julian Goldie
- Koray Tuğberk GÜBÜR
- Neil Patel
- Rand Fishkin
- Ross Simmonds
- Britney Muller
- Patrick Stox
- Crystal Carter
- Chris Long
- Tom Niezgoda
- Amanda Natividad
- Gael Breton
- Mark Webster
- Grace Leung
- Charlie Marchant

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/claraibarzabal/AItools.git
cd AItools/research
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the pipeline

```bash
python run_pipeline.py
```

### Optional flags

```bash
# Re-run analysis only (skip YouTube collection)
python run_pipeline.py --skip-collection

# Collect fewer videos per channel (faster testing)
python run_pipeline.py --videos-per-channel 5

# Use a custom expert config
python run_pipeline.py --config config/experts.yaml
```

## Output Files

| File | Description |
|------|-------------|
| `data/youtube/channels.csv` | Discovered channel metadata |
| `data/youtube/videos.csv` | Video titles, dates, URLs, descriptions, view counts |
| `data/youtube/transcripts.csv` | Raw transcripts with source metadata |
| `data/youtube/transcripts_cleaned.csv` | Preprocessed transcripts |
| `output/summary_report.md` | Final research summary |
| `output/ai_seo_themes.csv` | Theme clusters per video |
| `output/top_keywords.csv` | Keyword and n-gram frequencies |
| `output/creator_comparison.csv` | Per-creator analysis metrics |
| `output/visualizations/*.png` | Topic, tool, and concept charts |

## Research Questions Answered

The pipeline generates a final summary addressing:

- **What AI SEO topics are discussed most frequently?**
- **Which AI tools are mentioned most often?**
- **What content production workflows are repeatedly recommended?**
- **What differences exist between creators?**

## Methodology

### Channel Discovery
Experts are matched to YouTube channels using configured `@handles` first. If a handle fails, the pipeline searches YouTube and scores candidates by name and SEO-related signals.

### Transcript Fetching
1. **Primary:** `youtube-transcript-api` (manual and auto-generated captions)
2. **Fallback:** yt-dlp subtitle download (VTT/JSON3 auto-captions)

### NLP Analysis
- Tokenization and lemmatization with NLTK
- TF-IDF + NMF for topic extraction
- KMeans clustering for theme grouping
- Domain lexicon matching for AI tools, SEO concepts, and workflow phrases

## Configuration

Edit `config/experts.yaml` to add experts or override channel handles:

```yaml
experts:
  - name: Aleyda Solís
    channel_handle: aleyda
  - name: Custom Expert
    channel_url: https://www.youtube.com/@channelname

settings:
  videos_per_channel: 20
  max_search_results: 5
```

## Requirements

- Python 3.10+
- Internet access for YouTube data collection
- Dependencies listed in `requirements.txt`

## Notes

- YouTube rate limits may apply during large collection runs. The pipeline includes short delays between requests.
- Not all videos have transcripts available; the pipeline logs failures and continues.
- Channel handles in the config are best-effort starting points — verify and update handles in `experts.yaml` for higher accuracy.
- This project is intended as a portfolio demonstration of data collection, NLP, and research automation.

## License

See the repository root `LICENSE` file.
