# WP-0021 — Observability Foundations (EventLog + Structured Events)

## VF Tasks Included
- [ ] VF-130 — Formalize ArtifactStore with query APIs
  - **Files:** `apps/api/vibeforge_api/core/artifacts.py` (add query methods)
  - **Tests:** `apps/api/tests/test_artifact_store.py` (extend with query tests)
  - **Verify:** `cd apps/api && pytest tests/test_artifact_store.py -v`
- [ ] VF-131 — Implement EventLog (append-only event stream)
  - **Files:** `apps/api/vibeforge_api/core/event_log.py` (EventLog, Event dataclasses)
  - **Tests:** `apps/api/tests/test_event_log.py` (15+ tests)
  - **Verify:** `cd apps/api && pytest tests/test_event_log.py -v`
- [ ] VF-142 — Upgrade to structured progress events
  - **Files:** `orchestration/coordinator/session_coordinator.py` (emit events instead of logs)
  - **Tests:** `apps/api/tests/test_session_coordinator.py` (verify event emission)
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py -k event -v`

## Goal
Implement structured observability foundation to enable real-time monitoring, cost tracking, and control UI development. Replace unstructured session.logs with typed events that can be queried, filtered, and streamed to dashboards.

## Dependencies
- ✅ None (foundational layer, no dependencies)

## Why Critical for Control UI
The control UI (VF-170 through VF-180) requires:
1. **Historical query** - ArtifactStore needs query APIs to retrieve past sessions for comparison
2. **Real-time monitoring** - EventLog provides live stream of structured events for dashboards
3. **Cost tracking** - Events must include token usage metadata for VF-172 (token visualization)
4. **Debug visibility** - Events capture prompts, gate decisions, model routing for VF-176, VF-179

Without these foundations, the control UI cannot access historical data or monitor live execution.

## Execution Steps

### 1. VF-130: Formalize ArtifactStore with Query APIs

**Intent:** Add query methods to ArtifactStore for historical session retrieval and artifact inspection.

**Current State:**
- `apps/api/vibeforge_api/core/artifacts.py` exists with basic save/load methods
- Used informally in SessionCoordinator for persisting BuildSpec, Concept, TaskGraph, etc.
- No query APIs for listing sessions, filtering by date, or aggregating metadata

**Implementation:**

Add methods to ArtifactStore class:
```python
class ArtifactStore:
    """Enhanced with query APIs for control UI."""

    def __init__(self, artifacts_path: str):
        self.artifacts_path = Path(artifacts_path)
        self.artifacts_path.mkdir(parents=True, exist_ok=True)

    # Existing methods (keep as-is)
    def save_artifact(self, key: str, data: dict | list) -> None: ...
    def load_artifact(self, key: str) -> dict | list | None: ...

    # NEW: Query APIs
    def list_artifacts(self) -> list[str]:
        """List all artifact keys in this store."""
        return [f.stem for f in self.artifacts_path.glob("*.json")]

    def artifact_exists(self, key: str) -> bool:
        """Check if artifact exists."""
        return (self.artifacts_path / f"{key}.json").exists()

    def get_artifact_metadata(self, key: str) -> dict:
        """Get metadata for artifact (size, modified time, etc.)."""
        path = self.artifacts_path / f"{key}.json"
        if not path.exists():
            return {}
        stat = path.stat()
        return {
            "key": key,
            "size_bytes": stat.st_size,
            "modified_at": stat.st_mtime,
            "path": str(path),
        }

    def delete_artifact(self, key: str) -> bool:
        """Delete artifact by key. Returns True if deleted."""
        path = self.artifacts_path / f"{key}.json"
        if path.exists():
            path.unlink()
            return True
        return False
```

Add session-level query utilities (new class or module-level functions):
```python
class SessionArtifactQuery:
    """Query artifacts across multiple sessions."""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root

    def list_sessions(self) -> list[str]:
        """List all session IDs with artifacts."""
        return [d.name for d in self.workspace_root.iterdir() if d.is_dir()]

    def get_session_artifacts(self, session_id: str) -> list[str]:
        """Get all artifacts for a session."""
        artifacts_path = self.workspace_root / session_id / "artifacts"
        if not artifacts_path.exists():
            return []
        return [f.stem for f in artifacts_path.glob("*.json")]

    def query_sessions_by_date(
        self, start_date: float | None = None, end_date: float | None = None
    ) -> list[dict]:
        """Query sessions by creation date range.

        Returns list of session metadata dicts with session_id, created_at, artifacts.
        """
        sessions = []
        for session_id in self.list_sessions():
            store = ArtifactStore(str(self.workspace_root / session_id / "artifacts"))

            # Try to get creation time from build_spec or earliest artifact
            metadata = store.get_artifact_metadata("build_spec")
            if not metadata:
                continue

            created_at = metadata["modified_at"]

            # Filter by date range
            if start_date and created_at < start_date:
                continue
            if end_date and created_at > end_date:
                continue

            sessions.append({
                "session_id": session_id,
                "created_at": created_at,
                "artifacts": store.list_artifacts(),
            })

        return sorted(sessions, key=lambda s: s["created_at"], reverse=True)

    def get_session_summary(self, session_id: str) -> dict:
        """Get high-level summary of a session's artifacts."""
        store = ArtifactStore(str(self.workspace_root / session_id / "artifacts"))

        summary = {
            "session_id": session_id,
            "has_build_spec": store.artifact_exists("build_spec"),
            "has_concept": store.artifact_exists("concept"),
            "has_task_graph": store.artifact_exists("task_graph"),
            "has_run_summary": store.artifact_exists("run_summary"),
            "artifacts": store.list_artifacts(),
        }

        # Load key metrics if run_summary exists
        if summary["has_run_summary"]:
            run_summary = store.load_artifact("run_summary")
            if run_summary:
                summary["status"] = run_summary.get("status")
                summary["files_generated"] = len(run_summary.get("files_generated", []))

        return summary
```

**Tests:**
- `test_list_artifacts()` - verify list_artifacts returns all keys
- `test_artifact_exists()` - check existence checks work
- `test_get_artifact_metadata()` - verify metadata extraction
- `test_delete_artifact()` - verify deletion works
- `test_list_sessions()` - verify session ID listing
- `test_get_session_artifacts()` - verify per-session artifact listing
- `test_query_sessions_by_date()` - verify date range filtering
- `test_get_session_summary()` - verify summary generation

**Done means:**
- ✅ ArtifactStore has list_artifacts(), artifact_exists(), get_artifact_metadata(), delete_artifact()
- ✅ SessionArtifactQuery provides list_sessions(), get_session_artifacts(), query_sessions_by_date(), get_session_summary()
- ✅ All 8+ query tests pass
- ✅ Control UI can query historical sessions and artifacts

---

### 2. VF-131: Implement EventLog (Append-Only Event Stream)

**Intent:** Create structured event logging to replace unstructured session.logs. Events are typed, timestamped, and queryable.

**Current State:**
- `session.add_log(message: str)` appends unstructured strings
- No event types, no structured metadata, no filtering capability
- Logs stored in Session.logs list (in-memory only)

**Implementation:**

Create Event dataclass with strong typing:
```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

class EventType(str, Enum):
    """Event type enumeration."""
    # Phase transitions
    PHASE_TRANSITION = "phase_transition"

    # Session lifecycle
    SESSION_STARTED = "session_started"
    SESSION_COMPLETED = "session_completed"
    SESSION_FAILED = "session_failed"
    SESSION_ABORTED = "session_aborted"

    # Task execution
    TASK_SCHEDULED = "task_scheduled"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_RETRYING = "task_retrying"
    TASK_SKIPPED = "task_skipped"

    # Agent operations
    AGENT_INVOKED = "agent_invoked"
    AGENT_RESPONSE = "agent_response"
    LLM_REQUEST_SENT = "llm_request_sent"
    LLM_RESPONSE_RECEIVED = "llm_response_received"
    MODEL_ROUTED = "model_routed"

    # Gates and policies
    GATE_EVALUATED = "gate_evaluated"
    GATE_BLOCKED = "gate_blocked"
    GATE_WARNED = "gate_warned"

    # Workspace operations
    DIFF_APPLIED = "diff_applied"
    DIFF_FAILED = "diff_failed"
    COMMAND_EXECUTED = "command_executed"

    # Verification
    VERIFICATION_STARTED = "verification_started"
    VERIFICATION_PASSED = "verification_passed"
    VERIFICATION_FAILED = "verification_failed"

    # Artifacts
    ARTIFACT_CREATED = "artifact_created"
    ARTIFACT_UPDATED = "artifact_updated"

    # Clarifications
    CLARIFICATION_REQUESTED = "clarification_requested"
    CLARIFICATION_ANSWERED = "clarification_answered"

    # Generic
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class Event:
    """Structured event with metadata."""

    event_type: EventType
    timestamp: datetime
    session_id: str
    message: str

    # Optional context fields
    phase: Optional[str] = None
    task_id: Optional[str] = None
    agent_role: Optional[str] = None
    model: Optional[str] = None

    # Structured metadata (JSON-serializable)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "message": self.message,
            "phase": self.phase,
            "task_id": self.task_id,
            "agent_role": self.agent_role,
            "model": self.model,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        """Create Event from dictionary."""
        return cls(
            event_type=EventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            session_id=data["session_id"],
            message=data["message"],
            phase=data.get("phase"),
            task_id=data.get("task_id"),
            agent_role=data.get("agent_role"),
            model=data.get("model"),
            metadata=data.get("metadata", {}),
        )
```

Create EventLog class for append-only storage:
```python
class EventLog:
    """Append-only event log with query capabilities."""

    def __init__(self, log_path: str):
        """Initialize event log.

        Args:
            log_path: Path to JSONL file for event storage
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # In-memory cache for fast queries (optional, can disable for large logs)
        self._events: list[Event] = []
        self._load_events()

    def _load_events(self) -> None:
        """Load existing events from file."""
        if not self.log_path.exists():
            return

        with open(self.log_path, "r") as f:
            for line in f:
                if line.strip():
                    event = Event.from_dict(json.loads(line))
                    self._events.append(event)

    def append(self, event: Event) -> None:
        """Append event to log (append-only)."""
        # Write to file immediately (append mode)
        with open(self.log_path, "a") as f:
            f.write(json.dumps(event.to_dict()) + "\n")

        # Add to in-memory cache
        self._events.append(event)

    def get_events(
        self,
        event_type: Optional[EventType | list[EventType]] = None,
        phase: Optional[str] = None,
        task_id: Optional[str] = None,
        agent_role: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[Event]:
        """Query events with filters."""
        events = self._events

        # Filter by event type
        if event_type:
            if isinstance(event_type, EventType):
                event_type = [event_type]
            events = [e for e in events if e.event_type in event_type]

        # Filter by phase
        if phase:
            events = [e for e in events if e.phase == phase]

        # Filter by task
        if task_id:
            events = [e for e in events if e.task_id == task_id]

        # Filter by agent role
        if agent_role:
            events = [e for e in events if e.agent_role == agent_role]

        # Filter by time range
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        return events

    def get_latest(self, n: int = 100) -> list[Event]:
        """Get the N most recent events."""
        return self._events[-n:]

    def count(
        self, event_type: Optional[EventType | list[EventType]] = None
    ) -> int:
        """Count events, optionally filtered by type."""
        if not event_type:
            return len(self._events)
        return len(self.get_events(event_type=event_type))

    def clear(self) -> None:
        """Clear all events (use with caution!)."""
        self.log_path.unlink(missing_ok=True)
        self._events = []
```

**Helper functions for common event creation:**
```python
def create_phase_transition_event(
    session_id: str, old_phase: str, new_phase: str
) -> Event:
    """Create phase transition event."""
    return Event(
        event_type=EventType.PHASE_TRANSITION,
        timestamp=datetime.utcnow(),
        session_id=session_id,
        message=f"Phase transition: {old_phase} → {new_phase}",
        phase=new_phase,
        metadata={"old_phase": old_phase, "new_phase": new_phase},
    )

def create_llm_request_event(
    session_id: str,
    model: str,
    role: str,
    prompt_tokens: int,
    task_id: Optional[str] = None,
) -> Event:
    """Create LLM request event."""
    return Event(
        event_type=EventType.LLM_REQUEST_SENT,
        timestamp=datetime.utcnow(),
        session_id=session_id,
        message=f"LLM request to {model} for {role}",
        task_id=task_id,
        agent_role=role,
        model=model,
        metadata={"prompt_tokens": prompt_tokens},
    )

# ... more helper functions for common events
```

**Tests:**
- `test_event_to_dict_from_dict()` - verify serialization
- `test_event_log_append()` - verify appending works
- `test_event_log_persistence()` - verify JSONL file format
- `test_get_events_by_type()` - verify filtering by event type
- `test_get_events_by_phase()` - verify filtering by phase
- `test_get_events_by_task()` - verify filtering by task_id
- `test_get_events_by_time_range()` - verify time range queries
- `test_get_latest()` - verify latest N events
- `test_count()` - verify counting with filters
- `test_event_log_reload()` - verify events reload from disk
- `test_create_helper_functions()` - verify helper event creation

**Done means:**
- ✅ Event dataclass with EventType enum
- ✅ EventLog class with append(), get_events(), get_latest(), count()
- ✅ JSONL file format for persistence
- ✅ Helper functions for common event types
- ✅ All 15+ EventLog tests pass
- ✅ Events can be filtered by type, phase, task, time range

---

### 3. VF-142: Upgrade to Structured Progress Events

**Intent:** Replace session.add_log() calls in SessionCoordinator with structured event emission using EventLog.

**Current State:**
- SessionCoordinator uses `session.add_log(message)` throughout
- Unstructured strings like "Executing task: task_123 (description)"
- Cannot query or filter these logs programmatically

**Implementation:**

Update SessionCoordinator to use EventLog:
```python
class SessionCoordinator:
    def __init__(
        self,
        session_store: SessionStoreInterface,
        workspace_manager: WorkspaceManager,
        questionnaire_engine: QuestionnaireEngine,
        spec_builder: SpecBuilder,
        orchestrator: Orchestrator,
        agent_framework: Optional[AgentFramework] = None,
        distributor: Optional[Distributor] = None,
    ):
        # ... existing initialization ...

        # NEW: EventLog integration
        self._event_logs: dict[str, EventLog] = {}  # session_id -> EventLog

    def _get_event_log(self, session_id: str) -> EventLog:
        """Get or create EventLog for session."""
        if session_id not in self._event_logs:
            workspace_path = self.workspace_manager.workspace_root / session_id
            log_path = workspace_path / "events.jsonl"
            self._event_logs[session_id] = EventLog(str(log_path))
        return self._event_logs[session_id]

    def _emit_event(self, event: Event) -> None:
        """Emit event to both EventLog and session.logs (legacy)."""
        event_log = self._get_event_log(event.session_id)
        event_log.append(event)

        # Also add to session.logs for backward compatibility (optional)
        session = self.session_store.get_session(event.session_id)
        if session:
            session.add_log(f"[{event.event_type.value}] {event.message}")
            self.session_store.update_session(session)
```

Replace key session.add_log() calls:
```python
# Before:
session.add_log("TaskGraph enqueued for execution")

# After:
self._emit_event(Event(
    event_type=EventType.INFO,
    timestamp=datetime.utcnow(),
    session_id=session_id,
    message="TaskGraph enqueued for execution",
    phase=session.phase.value,
))

# Before:
session.add_log(f"Executing task: {task.task_id} ({task.description})")

# After:
self._emit_event(Event(
    event_type=EventType.TASK_STARTED,
    timestamp=datetime.utcnow(),
    session_id=session_id,
    message=f"Executing task: {task.task_id}",
    phase=session.phase.value,
    task_id=task.task_id,
    metadata={"description": task.description, "role": task.role},
))

# Before:
session.update_phase(SessionPhase.PLAN_REVIEW)
session.add_log(f"Phase transition: IDEA → PLAN_REVIEW")

# After:
old_phase = session.phase
session.update_phase(SessionPhase.PLAN_REVIEW)
self._emit_event(create_phase_transition_event(
    session_id, old_phase.value, SessionPhase.PLAN_REVIEW.value
))
```

**Key events to emit:**
1. **Phase transitions** - Every session.update_phase() call
2. **Task lifecycle** - TASK_STARTED, TASK_COMPLETED, TASK_FAILED, TASK_RETRYING
3. **Agent operations** - When calling agent_framework.runTask()
4. **Gate evaluations** - When gates.evaluate() is called
5. **Diff application** - When PatchApplier.apply_patch() is called
6. **Verification** - When VerifierSuite runs
7. **LLM calls** - When Orchestrator calls models (capture in Orchestrator layer)

**Tests:**
- `test_session_coordinator_emits_phase_transition_events()` - verify phase events
- `test_session_coordinator_emits_task_events()` - verify task lifecycle events
- `test_event_log_persists_across_coordinator_calls()` - verify events persist
- `test_get_session_events()` - verify EventLog can be queried after execution

**Done means:**
- ✅ SessionCoordinator uses EventLog instead of session.add_log()
- ✅ All major operations emit structured events
- ✅ Events persisted to workspaces/{session_id}/events.jsonl
- ✅ Tests verify event emission for phase transitions, tasks, gates, verification
- ✅ Backward compatibility maintained (optional: also add to session.logs)

---

## Verification Commands
```bash
# Test ArtifactStore query APIs
cd apps/api && pytest tests/test_artifact_store.py -v

# Test EventLog implementation
cd apps/api && pytest tests/test_event_log.py -v

# Test SessionCoordinator event emission
cd apps/api && pytest tests/test_session_coordinator.py -k event -v

# Full test suite
cd apps/api && pytest -v
```

## Done Means
- [ ] ArtifactStore has list_artifacts(), artifact_exists(), get_artifact_metadata(), delete_artifact()
- [ ] SessionArtifactQuery provides list_sessions(), query_sessions_by_date(), get_session_summary()
- [ ] Event dataclass with EventType enum (30+ event types)
- [ ] EventLog class with append(), get_events(), get_latest(), count()
- [ ] Events persisted to JSONL files (workspaces/{session_id}/events.jsonl)
- [ ] SessionCoordinator emits structured events for all major operations
- [ ] Helper functions for common event creation (create_phase_transition_event, etc.)
- [ ] All ArtifactStore query tests pass (8+ tests)
- [ ] All EventLog tests pass (15+ tests)
- [ ] All SessionCoordinator event emission tests pass (4+ tests)
- [ ] Full test suite passes (435+ expected)

## Architecture Notes

**Why JSONL for EventLog:**
- Append-only file format (1 JSON object per line)
- Easy to stream and tail (`tail -f events.jsonl`)
- Simple to parse and query
- No database dependency for MVP
- Can migrate to TimescaleDB/InfluxDB later without changing Event model

**Why In-Memory Cache:**
- Fast queries for control UI (no disk I/O)
- Reasonable memory usage (events are small)
- Auto-loads on EventLog creation
- Can disable cache for very long sessions if needed

**Event Granularity:**
- Emit events at key decision points (phase transitions, task boundaries)
- Don't emit events for every line of code (too noisy)
- Balance: detailed enough for debugging, not overwhelming for dashboards

**Token Usage Tracking:**
- VF-172 (token visualization) requires usage metadata in events
- Emit LLM_REQUEST_SENT and LLM_RESPONSE_RECEIVED events with token counts
- Store in metadata: `{"prompt_tokens": 150, "completion_tokens": 300, "total_tokens": 450}`
- Control UI queries events to build cost charts

**Next Steps After WP-0021:**
- WP-0022: API endpoints for event streaming (GET /sessions/{id}/events with SSE)
- WP-0023: Control UI foundation (VF-170 - separate /control route)
- WP-0024: Agent activity dashboard (VF-171 - live status grid)
- WP-0025: Token usage visualization (VF-172 - cost tracking charts)
