"""Simple in-memory rate limiter for sensitive endpoints."""
from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request, status

_lock = Lock()
_buckets: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(
    request: Request,
    *,
    key_prefix: str,
    max_attempts: int = 10,
    window_seconds: int = 60,
) -> None:
    client = request.client.host if request.client else "unknown"
    bucket_key = f"{key_prefix}:{client}"
    now = time.monotonic()
    cutoff = now - window_seconds

    with _lock:
        hits = [t for t in _buckets[bucket_key] if t > cutoff]
        if len(hits) >= max_attempts:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="محاولات كثيرة. انتظر دقيقة ثم حاول مجدداً.",
            )
        hits.append(now)
        _buckets[bucket_key] = hits
