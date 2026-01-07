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


def create_phase_transition_event(session_id: str, old_phase: str, new_phase: str) -> Event:
    return Event(
        event_type=EventType.PHASE_TRANSITION,
        timestamp=datetime.now(timezone.utc),
        session_id=session_id,
        message=f"Phase transition: {old_phase} → {new_phase}",
        metadata={"from": old_phase, "to": new_phase},
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

    def get_latest(self, session_id: str, limit: int = 1) -> list[Event]:
        events = self.get_events(session_id)
        return events[-limit:]

    def count(self, session_id: str) -> int:
        return len(self.get_events(session_id))
