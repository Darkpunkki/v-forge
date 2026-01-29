"""Rate limiting middleware for control dispatch endpoints."""
from __future__ import annotations

import asyncio
import os
import re
import time
from collections import deque
from typing import Deque, Dict, Tuple

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

_DISPATCH_PATH = re.compile(r"^/control/agents/([^/]+)/dispatch$")


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


class RateLimiterState:
    def __init__(self, window_seconds: int = 60) -> None:
        self._window_seconds = window_seconds
        self._agent_buckets: Dict[str, Deque[float]] = {}
        self._ip_buckets: Dict[str, Deque[float]] = {}
        self._lock = asyncio.Lock()
    
    def reset(self) -> None:
        self._agent_buckets.clear()
        self._ip_buckets.clear()

    def _prune(self, bucket: Deque[float], now: float) -> None:
        cutoff = now - self._window_seconds
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

    def _allow(self, bucket: Deque[float], now: float, limit: int) -> Tuple[bool, int, int]:
        self._prune(bucket, now)
        if limit <= 0:
            return True, -1, 0
        if len(bucket) >= limit:
            reset = int(max(0.0, self._window_seconds - (now - bucket[0])))
            return False, 0, reset
        bucket.append(now)
        remaining = max(0, limit - len(bucket))
        reset = int(max(0.0, self._window_seconds - (now - bucket[0])))
        return True, remaining, reset

    async def check(self, agent_id: str, ip: str, agent_limit: int, ip_limit: int) -> Tuple[bool, dict[str, str]]:
        now = time.monotonic()
        async with self._lock:
            agent_bucket = self._agent_buckets.setdefault(agent_id, deque())
            ip_bucket = self._ip_buckets.setdefault(ip, deque())

            agent_allowed, agent_remaining, agent_reset = self._allow(agent_bucket, now, agent_limit)
            ip_allowed, ip_remaining, ip_reset = self._allow(ip_bucket, now, ip_limit)

        headers = {
            "X-RateLimit-Limit-Agent": str(agent_limit),
            "X-RateLimit-Remaining-Agent": str(agent_remaining),
            "X-RateLimit-Reset-Agent": str(agent_reset),
            "X-RateLimit-Limit-Ip": str(ip_limit),
            "X-RateLimit-Remaining-Ip": str(ip_remaining),
            "X-RateLimit-Reset-Ip": str(ip_reset),
        }

        return agent_allowed and ip_allowed, headers


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Apply rate limits to dispatch endpoints."""

    def __init__(self, app: Response) -> None:
        super().__init__(app)
        self._state = _rate_limiter_state

    async def dispatch(self, request: Request, call_next):
        if request.method.upper() != "POST":
            return await call_next(request)

        match = _DISPATCH_PATH.match(request.url.path)
        if not match:
            return await call_next(request)

        agent_id = match.group(1)
        ip = request.client.host if request.client else "unknown"
        agent_limit = _env_int("VIBEFORGE_RATE_LIMIT_AGENT_PER_MIN", 10)
        ip_limit = _env_int("VIBEFORGE_RATE_LIMIT_IP_PER_MIN", 50)

        allowed, headers = await self._state.check(agent_id, ip, agent_limit, ip_limit)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers=headers,
            )

        response = await call_next(request)
        for key, value in headers.items():
            response.headers[key] = value
        return response


_rate_limiter_state = RateLimiterState()


def reset_rate_limiter_state() -> None:
    _rate_limiter_state.reset()
