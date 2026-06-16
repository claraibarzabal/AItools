import os
import requests

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


def get_uploads_playlist_id(channel_id: str) -> str:
    url = "https://www.googleapis.com/youtube/v3/channels"

    r = requests.get(url, params={
        "part": "contentDetails",
        "id": channel_id,
        "key": YOUTUBE_API_KEY
    })

    r.raise_for_status()
    data = r.json()

    return data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]