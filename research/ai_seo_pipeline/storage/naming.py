import re

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:80]


def build_filename(video) -> str:
    date = video.published_at or "unknown-date"
    title = slugify(video.title)
    return f"{date}__{title}__{video.video_id}.json"