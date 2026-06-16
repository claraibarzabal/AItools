# ai_seo_pipeline/request_guard.py

import time
import random

GLOBAL_LAST_CALL = 0
MIN_INTERVAL = 18  # sube a 18–25s para estabilidad real

def throttle():
    global GLOBAL_LAST_CALL

    jitter = random.uniform(0.5, 2.0)
    now = time.time()

    wait = MIN_INTERVAL - (now - GLOBAL_LAST_CALL) + jitter

    if wait > 0:
        time.sleep(wait)

    GLOBAL_LAST_CALL = time.time()