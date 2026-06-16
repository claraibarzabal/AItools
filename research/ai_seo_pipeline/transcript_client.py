from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from ai_seo_pipeline.config import SUPADATA_API_KEY
import time

SUPADATA_URL = "https://api.supadata.ai/v1/youtube/transcript"


def _fetch_one(video_url: str) -> tuple[str, str | None]:
    print("TRANSCRIPT CLIENT LOADED")
    print("SUPADATA_API_KEY:", SUPADATA_API_KEY)
    try:

        for attempt in range(3):

            response = requests.get(
                SUPADATA_URL,
                params={"url": video_url},
                headers={
                    "x-api-key": SUPADATA_API_KEY
                },
                timeout=30
            )

            print("URL:", video_url)
            print("STATUS:", response.status_code)

            if response.status_code == 429:

                print(
                    f"RATE LIMITED ({attempt + 1}/3): {video_url}"
                )

                time.sleep(5)

                continue

            response.raise_for_status()

            break

        else:
            print(
                "FAILED AFTER 3 RETRIES:",
                video_url
            )
            return video_url, None
        data = response.json()

        print("\n====================")
        print(video_url)
        print(data)
        print("====================\n")

        content = data.get("content", [])

        if content:
            transcript = " ".join(
                chunk["text"]
                for chunk in content
                if chunk.get("text")
            )

            print(
                "TRANSCRIPT LENGTH:",
                len(transcript),
                video_url
            )

        else:
            transcript = None

        print(
            "RETURNING:",
            video_url,
            transcript[:100] if transcript else "EMPTY"
        )

        return video_url, transcript

    except Exception as e:
        print("ERROR:", video_url)
        print(repr(e))
        return video_url, None


def fetch_transcripts_batch(
    video_urls: list[str],
    max_workers: int = 10
) -> dict[str, str]:

    results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:

        futures = {
            executor.submit(_fetch_one, url): url
            for url in video_urls
        }

        for future in as_completed(futures):

            try:
                video_url, transcript = future.result()

                print(
                    "RETURNED:",
                    video_url,
                    len(transcript) if transcript else 0
                )

                results[video_url] = transcript or ""

            except Exception:
                url = futures[future]
                results[url] = ""

    return results