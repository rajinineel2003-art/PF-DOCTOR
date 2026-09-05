import asyncio
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


_hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_lock = asyncio.Lock()


async def enforce_rate_limit(request: Request, bucket: str, limit: int, window_seconds: int = 60) -> None:
    """Small in-process MVP limiter; production can replace it with Redis."""
    forwarded = request.headers.get("x-forwarded-for", "")
    client_id = forwarded.split(",", 1)[0].strip() or (request.client.host if request.client else "unknown")
    key = (bucket, client_id)
    now = time.monotonic()
    async with _lock:
        hits = _hits[key]
        while hits and now - hits[0] >= window_seconds:
            hits.popleft()
        if len(hits) >= limit:
            raise HTTPException(status_code=429, detail={"status": "ERROR", "message": "Too many requests. Please wait before trying again."})
        hits.append(now)