"""Cost tracking utilities for control sessions."""
from __future__ import annotations

import os
import threading
from datetime import datetime, timezone
from typing import Any


class CostTracker:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._session_costs: dict[str, float] = {}
        self._session_warned: set[str] = set()
        self._current_day: str | None = None
        self._daily_cost: float = 0.0
        self._daily_warned: bool = False

    def _get_limits(self) -> tuple[float, float, float, float]:
        daily_limit = float(os.getenv("VIBEFORGE_DAILY_COST_LIMIT_USD", "10"))
        session_limit = float(os.getenv("VIBEFORGE_SESSION_COST_LIMIT_USD", "5"))
        warning_threshold = float(os.getenv("VIBEFORGE_COST_WARNING_THRESHOLD", "0.8"))
        cost_per_1k = float(os.getenv("VIBEFORGE_COST_PER_1K_TOKENS_USD", "0"))
        return daily_limit, session_limit, warning_threshold, cost_per_1k

    def _today(self) -> str:
        return datetime.now(timezone.utc).date().isoformat()

    def _reset_daily_if_needed(self) -> None:
        today = self._today()
        if self._current_day != today:
            self._current_day = today
            self._daily_cost = 0.0
            self._daily_warned = False

    def _extract_cost(self, usage: dict[str, Any], cost_per_1k: float) -> float:
        for key in ("cost_usd", "total_cost_usd", "usd_cost", "cost"):
            if key in usage:
                try:
                    return float(usage[key])
                except (TypeError, ValueError):
                    return 0.0

        total_tokens = usage.get("total_tokens")
        if total_tokens is None:
            prompt_tokens = usage.get("prompt_tokens") or 0
            completion_tokens = usage.get("completion_tokens") or 0
            total_tokens = prompt_tokens + completion_tokens

        try:
            total_tokens = float(total_tokens)
        except (TypeError, ValueError):
            return 0.0

        if cost_per_1k <= 0:
            return 0.0

        return (total_tokens / 1000.0) * cost_per_1k

    def record_usage(self, session_id: str, usage: dict[str, Any] | None) -> dict[str, Any]:
        if not usage:
            return {"cost_added": 0.0, "session_warning": False, "daily_warning": False}

        daily_limit, session_limit, warning_threshold, cost_per_1k = self._get_limits()
        cost_added = self._extract_cost(usage, cost_per_1k)
        if cost_added <= 0:
            return {"cost_added": 0.0, "session_warning": False, "daily_warning": False}

        with self._lock:
            self._reset_daily_if_needed()
            session_total = self._session_costs.get(session_id, 0.0) + cost_added
            self._session_costs[session_id] = session_total
            self._daily_cost += cost_added

            session_warning = False
            daily_warning = False

            if session_limit > 0 and session_id not in self._session_warned:
                if session_total >= session_limit * warning_threshold:
                    session_warning = True
                    self._session_warned.add(session_id)

            if daily_limit > 0 and not self._daily_warned:
                if self._daily_cost >= daily_limit * warning_threshold:
                    daily_warning = True
                    self._daily_warned = True

        return {
            "cost_added": cost_added,
            "session_total": session_total,
            "daily_total": self._daily_cost,
            "session_warning": session_warning,
            "daily_warning": daily_warning,
        }

    def get_status(self, session_id: str) -> dict[str, Any]:
        daily_limit, session_limit, warning_threshold, _ = self._get_limits()
        with self._lock:
            self._reset_daily_if_needed()
            session_total = self._session_costs.get(session_id, 0.0)
            daily_total = self._daily_cost

        session_remaining = max(0.0, session_limit - session_total) if session_limit > 0 else None
        daily_remaining = max(0.0, daily_limit - daily_total) if daily_limit > 0 else None

        return {
            "session_cost_usd": session_total,
            "session_limit_usd": session_limit,
            "session_remaining_usd": session_remaining,
            "daily_cost_usd": daily_total,
            "daily_limit_usd": daily_limit,
            "daily_remaining_usd": daily_remaining,
            "session_warning": session_limit > 0 and session_total >= session_limit * warning_threshold,
            "daily_warning": daily_limit > 0 and daily_total >= daily_limit * warning_threshold,
        }

    def is_within_limits(self, session_id: str) -> tuple[bool, dict[str, Any]]:
        status = self.get_status(session_id)
        session_limit = status.get("session_limit_usd", 0.0) or 0.0
        daily_limit = status.get("daily_limit_usd", 0.0) or 0.0

        session_exceeded = session_limit > 0 and status["session_cost_usd"] >= session_limit
        daily_exceeded = daily_limit > 0 and status["daily_cost_usd"] >= daily_limit
        return not (session_exceeded or daily_exceeded), status


_cost_tracker: CostTracker | None = None


def get_cost_tracker() -> CostTracker:
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker


def reset_cost_tracker() -> None:
    global _cost_tracker
    _cost_tracker = CostTracker()
