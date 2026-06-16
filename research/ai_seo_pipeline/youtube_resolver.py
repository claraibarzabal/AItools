import requests
from ai_seo_pipeline.config import YOUTUBE_API_KEY
from ai_seo_pipeline.cache_store import load_cache, save_cache

CHANNEL_CACHE = load_cache("channels")


def resolve_channel_id(handle: str) -> str:
    """
    Robust YouTube channel resolver:
    1. cache
    2. forHandle
    3. search fallback (IMPORTANT)
    """

    # 1. CACHE
    if handle in CHANNEL_CACHE:
        return CHANNEL_CACHE[handle]

    # 2. TRY FORHANDLE API
    channel_id = _try_forhandle(handle)
    if channel_id:
        return _save(handle, channel_id)

    # 3. FALLBACK: SEARCH API (REAL FIX)
    channel_id = _search_channel(handle)
    if channel_id:
        return _save(handle, channel_id)

    raise ValueError(f"Channel not found for handle={handle}")


def _try_forhandle(handle: str):
    url = "https://www.googleapis.com/youtube/v3/channels"

    r = requests.get(url, params={
        "part": "id",
        "forHandle": handle.replace("@", ""),
        "key": YOUTUBE_API_KEY
    })

    data = r.json()
    items = data.get("items")

    if items:
        return items[0]["id"]

    return None


def _search_channel(handle: str):
    url = "https://www.googleapis.com/youtube/v3/search"

    r = requests.get(url, params={
        "part": "snippet",
        "q": handle,
        "type": "channel",
        "maxResults": 1,
        "key": YOUTUBE_API_KEY
    })

    data = r.json()
    items = data.get("items")

    if items:
        return items[0]["snippet"]["channelId"]

    return None


def _save(handle, channel_id):
    CHANNEL_CACHE[handle] = channel_id
    save_cache("channels", CHANNEL_CACHE)
    return channel_id