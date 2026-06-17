# AI-Powered SEO Research Pipeline

A modular Python pipeline that automatically collects YouTube videos and transcripts from leading SEO and AI Search experts for research and content analysis.

## Overview

This project automates the data collection stage of an AI-powered SEO research workflow.

The pipeline:

1. Discovers YouTube channels from a curated list of experts
2. Collects recent videos from each channel using the YouTube Data API
3. Retrieves transcripts through the Supadata API
4. Saves structured JSON files for downstream analysis

The project is designed as the data collection layer for future NLP, semantic analysis, and AI content generation workflows.

---

## Sources

### YouTube Experts (used in the AI-Powered SEO Research Pipeline)

The following YouTube channels were selected as primary sources for collecting SEO and AI Search Optimization content:

* Neil Patel
* Nathan Gotch
* Julian Goldie
* Matt Diggity
* Ahrefs
* Authority Hacker
* Exposure Ninja
* Nico | AI Ranking
* Vendasta
* Asier López Ruiz

### LinkedIn Experts (added manually)

The following professionals were selected as additional sources of insights and industry updates:

* Aleyda Solís
* Britney Muller
* Crystal Carter
* Kevin Indig
* Koray Tuğberk GÜBÜR
* Lily Ray
* Matt Diggity
* Nathan Gotch
* Olaf Kopp
* Rand Fishkin

## Why These Experts?

These experts were selected because they are well-recognized professionals in SEO, AI Search, and digital marketing. Many of them run successful agencies, SEO software companies, or consulting businesses, giving them extensive hands-on experience in the field.

Their content consistently focuses on practical strategies, real-world case studies, and current industry trends rather than purely theoretical concepts. This makes them reliable sources for collecting high-quality transcripts and insights that reflect modern SEO and AI search best practices.


## Project Structure

```
research/
├── ai_seo_pipeline/
│   ├── channel_client.py         # YouTube channel discovery
│   ├── video_client.py           # Video metadata collection
│   ├── transcript_client.py      # Transcript retrieval via Supadata
│   ├── storage.py                # JSON storage utilities
│   ├── config.py                 # Environment variables and paths
│   └── pipeline.py               # Pipeline orchestration
├── config/
│   └── experts.yaml              # Expert configuration
├── data/
│   └── transcripts/
│       ├── expert_name/
│       │   ├── video_1.json
│       │   ├── video_2.json
│       │   └── ...
├── run_pipeline.py               # CLI entry point
├── requirements.txt
└── README.md
```

---

## Features

* YouTube channel lookup
* Recent video collection
* Transcript extraction using Supadata
* Parallel transcript downloads
* Automatic retry for API rate limits
* Structured JSON output
* Modular architecture for future NLP processing

---

## Setup

### Clone the repository

```bash
git clone https://github.com/claraibarzabal/AItools.git
cd AItools/research
```

### Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment variables

Create a `.env` file containing:

```text
YOUTUBE_API_KEY=your_youtube_api_key
SUPADATA_API_KEY=your_supadata_api_key
```

---

## Run the Pipeline

Collect one recent video per expert:

```bash
python run_pipeline.py --videos-per-channel 1
```

Collect five videos:

```bash
python run_pipeline.py --videos-per-channel 5
```

---

## Output

Each transcript is stored as an individual JSON document.

Example:

```json
{
  "video_id": "B3iK_CZLq64",
  "title": "...",
  "url": "...",
  "published_at": "...",
  "channel": "...",
  "transcript": "..."
}
```

The directory structure is organized by expert:

```
data/
└── transcripts/
    ├── Aleyda Solis/
    ├── Lily Ray/
    ├── Kevin Indig/
    └── ...
```

---

## Experts Included

The list of experts is maintained in `config/experts.yaml` and can be extended without changing the application code.

---

## Technologies

* Python 3.11+
* YouTube Data API v3
* Supadata API
* requests
* PyYAML
* concurrent.futures

---

## Future Work

Planned additions include:

* Transcript preprocessing
* Topic extraction
* Keyword frequency analysis
* Semantic clustering
* LLM-powered summaries
* SEO insight generation
* Markdown and CSV reports

---

## License

See the repository `LICENSE` file.


