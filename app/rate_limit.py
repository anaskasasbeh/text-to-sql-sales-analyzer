"""A small in-memory rate limiter: at most N requests per IP per time window."""

from __future__ import annotations

import threading
import time
from collections import deque


class SlidingWindowLimiter:
    """Allow `limit` requests per `window_seconds` for each key (e.g. an IP address).

    State lives in memory, which is fine for a single small server: it resets
    when the server restarts.
    """

    def __init__(self, limit: int, window_seconds: float = 60.0) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str, now: float | None = None) -> float:
        """Record a request. Returns 0 if allowed, else seconds until the next slot."""
        now = time.monotonic() if now is None else now
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and now - hits[0] >= self.window_seconds:
                hits.popleft()
            if len(hits) >= self.limit:
                return self.window_seconds - (now - hits[0])
            hits.append(now)
            if len(self._hits) > 10_000:
                self._forget_idle(now)
            return 0.0

    def _forget_idle(self, now: float) -> None:
        idle = [k for k, v in self._hits.items() if not v or now - v[-1] >= self.window_seconds]
        for key in idle:
            del self._hits[key]
