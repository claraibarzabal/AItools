from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from ai_seo_pipeline.config import SUPADATA_API_KEY


SUPADATA_URL = "https://api.supadata.ai/v1/youtube/transcript"


def _fetch_one(video_url: str) -> tuple[str, str | None]:
    try:
        response = requests.get(
            SUPADATA_URL,
            params={"url": video_url},
            headers={"Authorization": f"Bearer {SUPADATA_API_KEY}"},
            timeout=30
        )

        response.raise_for_status()
        data = response.json()

        transcript = (
            data.get("transcript")
            or data.get("data", {}).get("transcript")
        )

        return video_url, transcript

    except Exception:
        return video_url, None


def fetch_transcripts_batch(video_urls: list[str], max_workers: int = 10) -> dict[str, str]:
    results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_fetch_one, url): url
            for url in video_urls
        }

        for future in as_completed(futures):
            video_url, transcript = future.result()

            if transcript:
                results[video_url] = transcript

    return results