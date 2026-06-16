# ai_seo_pipeline/storage/local_store.py

from pathlib import Path
import json

TRANSCRIPTS_DIR = Path("research/youtube-transcripts")

def save_transcript_file(filename: str, data: dict):
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    path = TRANSCRIPTS_DIR / filename

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return path