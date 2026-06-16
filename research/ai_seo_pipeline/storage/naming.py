import re

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:80]


def build_filename(video: dict) -> str:

    date = video.get("published_at") or "unknown-date"

    title = slugify(
        str(video.get("title", "untitled"))
    )

    video_id = video.get("video_id", "unknown")

    return f"{date}__{title}__{video_id}.json"