"""Simple rate limits (F19): a sliding window per client address and route.

One process only. Production moves this to Redis (M0) with the same calls.
Off with ARCH_RATE_LIMITS=false.
"""
import threading
import time
from collections import defaultdict, deque

from fastapi import Request

from app import config
from app.core.errors import ApiError

_hits = defaultdict(deque)
_lock = threading.Lock()


def limit(name: str, max_calls: int, per_seconds: int):
    def dep(request: Request):
        if not config.RATE_LIMITS_ENABLED:
            return
        client = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip() or \
            (request.client.host if request.client else "unknown")
        key = f"{name}:{client}"
        now = time.time()
        with _lock:
            q = _hits[key]
            while q and q[0] <= now - per_seconds:
                q.popleft()
            if len(q) >= max_calls:
                wait = int(q[0] + per_seconds - now) + 1
                raise ApiError("RATE_LIMITED", "Too many tries. Please wait a moment and try again.", 429,
                               {"retry_after": wait, "route_to": None})
            q.append(now)
    return dep


def reset():
    with _lock:
        _hits.clear()
