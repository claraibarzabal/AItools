# ai_seo_pipeline/cache_store.py

import json
from pathlib import Path

CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)

def _path(name):
    return CACHE_DIR / f"{name}.json"

def load_cache(name):
    path = _path(name)
    if path.exists():
        return json.loads(path.read_text())
    return {}

def save_cache(name, data):
    path = _path(name)
    path.write_text(json.dumps(data, indent=2))