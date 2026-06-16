"""Clean and normalize raw YouTube transcripts."""

from __future__ import annotations

import re

import pandas as pd


TIMESTAMP_PATTERN = re.compile(
    r"\b\d{1,2}:\d{2}(?::\d{2})?\b|\[\d{1,2}:\d{2}(?::\d{2})?\]|\(\d{1,2}:\d{2}(?::\d{2})?\)"
)
WHITESPACE_PATTERN = re.compile(r"\s+")


def remove_timestamps(text: str) -> str:
    return TIMESTAMP_PATTERN.sub(" ", text)


def normalize_whitespace(text: str) -> str:
    return WHITESPACE_PATTERN.sub(" ", text).strip()


def remove_duplicate_sentences(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    seen: set[str] = set()
    unique: list[str] = []
    for sentence in sentences:
        normalized = sentence.strip().lower()
        if not normalized:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(sentence.strip())
    return " ".join(unique)


def remove_duplicate_phrases(text: str, min_phrase_words: int = 4) -> str:
    words = text.split()
    if len(words) < min_phrase_words * 2:
        return text

    i = 0
    cleaned_words: list[str] = []
    while i < len(words):
        cleaned_words.append(words[i])
        # Skip immediate repeated n-grams common in auto-captions.
        for n in range(8, min_phrase_words - 1, -1):
            if i + 2 * n <= len(words) and words[i : i + n] == words[i + n : i + 2 * n]:
                i += n
                break
        i += 1
    return " ".join(cleaned_words)


def clean_transcript(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return ""

    cleaned = text
    cleaned = remove_timestamps(cleaned)
    cleaned = re.sub(r"\[[^\]]+\]", " ", cleaned)
    cleaned = re.sub(r"\([^)]*music[^)]*\)", " ", cleaned, flags=re.IGNORECASE)
    cleaned = remove_duplicate_phrases(cleaned)
    cleaned = remove_duplicate_sentences(cleaned)
    cleaned = normalize_whitespace(cleaned)
    return cleaned


def clean_transcripts_df(transcripts_df: pd.DataFrame) -> pd.DataFrame:
    if transcripts_df.empty:
        return pd.DataFrame(
            columns=[
                "video_id",
                "expert_name",
                "language",
                "transcript_raw",
                "transcript_cleaned",
                "source",
                "word_count",
            ]
        )

    rows = []
    for _, row in transcripts_df.iterrows():
        raw = row.get("transcript_text", "") or ""
        cleaned = clean_transcript(raw)
        rows.append(
            {
                "video_id": row.get("video_id"),
                "expert_name": row.get("expert_name"),
                "language": row.get("language"),
                "transcript_raw": raw,
                "transcript_cleaned": cleaned,
                "source": row.get("source"),
                "word_count": len(cleaned.split()) if cleaned else 0,
            }
        )

    return pd.DataFrame(rows)
