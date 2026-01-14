from __future__ import annotations

import json

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class EventType(str, Enum):
    """Enumerates structured event categories for observability."""

    WORKSPACE_INITIALIZED = "workspace_initialized"
    PHASE_TRANSITION = "phase_transition"
    INTENT_PROFILE_CREATED = "intent_profile_created"
    BUILD_SPEC_CREATED = "build_spec_created"
    CONCEPT_CREATED = "concept_created"
    TASK_GRAPH_CREATED = "task_graph_created"
    PLAN_APPROVED = "plan_approved"
    PLAN_REJECTED = "plan_rejected"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    AGENT_INVOKED = "agent_invoked"
    AGENT_COMPLETED = "agent_completed"
    LLM_REQUEST_SENT = "llm_request_sent"
    LLM_RESPONSE_RECEIVED = "llm_response_received"
    VERIFICATION_STARTED = "verification_started"
    VERIFICATION_COMPLETED = "verification_completed"
    MODEL_ROUTED = "model_routed"
    GATE_EVALUATED = "gate_evaluated"
    INFO = "info"
    # VF-163, VF-165: Failure and abort events
    SESSION_FAILED = "session_failed"
    SESSION_ABORTED = "session_aborted"
    # VF-202, VF-203: Tick engine and graph-gated messaging events
    TICK_ADVANCED = "tick_advanced"
    MESSAGE_SENT = "message_sent"
    MESSAGE_BLOCKED_BY_GRAPH = "message_blocked_by_graph"
    # VF-206: Simulation lifecycle events
    SIMULATION_CONFIGURED = "simulation_configured"
    SIMULATION_STARTED = "simulation_started"
    SIMULATION_RESET = "simulation_reset"
    SIMULATION_PAUSED = "simulation_paused"
    TICK_STARTED = "tick_started"
    TICK_COMPLETED = "tick_completed"
    TICK_BLOCKED = "tick_blocked"
    AGENT_MESSAGE_SENT = "agent_message_sent"


@dataclass
class Event:
    """Structured event that can be persisted and queried."""

    event_type: EventType
    timestamp: datetime
    session_id: str
    message: str
    phase: Optional[str] = None
    task_id: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["event_type"] = self.event_type.value
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        return cls(
            event_type=EventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            session_id=data["session_id"],
            message=data.get("message", ""),
            phase=data.get("phase"),
            task_id=data.get("task_id"),
            metadata=data.get("metadata"),
        )


def create_phase_transition_event(
    session_id: str, old_phase: str, new_phase: str, reason: Optional[str] = None
) -> Event:
    return Event(
        event_type=EventType.PHASE_TRANSITION,
        timestamp=datetime.now(timezone.utc),
        session_id=session_id,
        message=f"Phase transition: {old_phase} → {new_phase}",
        phase=new_phase,
        metadata={"from": old_phase, "to": new_phase, "reason": reason},
    )


class EventLog:
    """Append-only event log persisted per session as JSONL."""

    def __init__(self, workspace_root: Path, use_cache: bool = True):
        self.workspace_root = Path(workspace_root)
        self.use_cache = use_cache
        self._cache: dict[str, list[Event]] = {}

    def _event_file(self, session_id: str) -> Path:
        workspace_path = self.workspace_root / session_id
        workspace_path.mkdir(parents=True, exist_ok=True)
        return workspace_path / "events.jsonl"

    def _load_cache(self, session_id: str) -> list[Event]:
        if not self.use_cache:
            return []

        if session_id not in self._cache:
            events: list[Event] = []
            file_path = self._event_file(session_id)
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            events.append(Event.from_dict(json.loads(line)))
            self._cache[session_id] = events
        return self._cache[session_id]

    def append(self, event: Event) -> None:
        """Append an event to disk (and cache)."""

        if self.use_cache:
            cache = self._load_cache(event.session_id)
            cache.append(event)

        file_path = self._event_file(event.session_id)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict()) + "\n")

    def get_events(
        self, session_id: str, event_type: Optional[EventType] = None
    ) -> list[Event]:
        """Return events for a session, optionally filtered by type."""

        events = list(self._load_cache(session_id))
        if not self.use_cache:
            file_path = self._event_file(session_id)
            if file_path.exists():
                events = [Event.from_dict(json.loads(line)) for line in file_path.read_text().splitlines() if line.strip()]

        if event_type:
            return [e for e in events if e.event_type == event_type]
        return events

    def get_events_filtered(
        self,
        session_id: str,
        event_type: Optional[str] = None,
        tick_index: Optional[int] = None,
        tick_min: Optional[int] = None,
        tick_max: Optional[int] = None,
        agent_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[Event]:
        """Return events with multi-criteria filtering (VF-206).

        Args:
            session_id: Session to query
            event_type: Filter by event type string
            tick_index: Filter by exact tick index (from metadata.tick_index)
            tick_min: Filter by minimum tick index (inclusive)
            tick_max: Filter by maximum tick index (inclusive)
            agent_id: Filter by agent ID (from metadata.agent_id or metadata.from_agent)
            limit: Maximum number of events to return (most recent)

        Returns:
            List of matching events, ordered by timestamp ascending.
        """
        events = list(self._load_cache(session_id))
        if not self.use_cache:
            file_path = self._event_file(session_id)
            if file_path.exists():
                events = [
                    Event.from_dict(json.loads(line))
                    for line in file_path.read_text().splitlines()
                    if line.strip()
                ]

        filtered: list[Event] = []
        for e in events:
            # Filter by event type
            if event_type and e.event_type.value != event_type:
                continue

            # Filter by tick_index (exact match)
            if tick_index is not None:
                event_tick = e.metadata.get("tick_index") if e.metadata else None
                if event_tick != tick_index:
                    continue

            # Filter by tick range
            if tick_min is not None or tick_max is not None:
                event_tick = e.metadata.get("tick_index") if e.metadata else None
                if event_tick is None:
                    continue
                if tick_min is not None and event_tick < tick_min:
                    continue
                if tick_max is not None and event_tick > tick_max:
                    continue

            # Filter by agent_id
            if agent_id is not None:
                meta = e.metadata or {}
                event_agent = meta.get("agent_id") or meta.get("from_agent") or meta.get("sender")
                if event_agent != agent_id:
                    continue

            filtered.append(e)

        # Apply limit (return most recent)
        if limit is not None and len(filtered) > limit:
            return filtered[-limit:]

        return filtered

    def get_latest(self, session_id: str, limit: int = 1) -> list[Event]:
        events = self.get_events(session_id)
        return events[-limit:]

    def count(self, session_id: str) -> int:
        return len(self.get_events(session_id))
