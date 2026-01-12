"""Session domain model and storage."""

import uuid
from abc import ABC, abstractmethod
from typing import Any, Optional
from datetime import datetime, timezone

from vibeforge_api.models.types import SessionPhase


class Session:
    """Session aggregate containing phase and artifacts."""

    def __init__(self, session_id: str | None = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.phase = SessionPhase.QUESTIONNAIRE
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

        # Questionnaire state
        self.current_question_index = 0
        self.answers: dict[str, Any] = {}

        # Artifacts (populated as session progresses)
        self.intent_profile: Optional[dict] = None
        self.build_spec: Optional[dict] = None
        self.concept: Optional[dict] = None
        self.task_graph: Optional[dict] = None

        # Execution state
        self.completed_task_ids: list[str] = []
        self.failed_task_ids: list[str] = []
        self.active_task_id: Optional[str] = None
        self.logs: list[str] = []

        # Clarification state (for gates/agents)
        self.pending_clarification: Optional[dict] = None
        self.clarification_answer: Optional[str] = None
        self.clarification_context: Optional[dict] = None

        # Error history (VF-030: track error details, not just IDs)
        self.error_history: list[dict[str, Any]] = []

        # Failure/abort state (VF-163, VF-165)
        self.failure_reason: Optional[str] = None
        self.failure_artifact: Optional[dict] = None
        self.is_aborted: bool = False
        self.abort_reason: Optional[str] = None

        # Fix loop tracking (VF-164)
        self.fix_loop_count: int = 0
        self.max_fix_loops: int = 3  # Prevent infinite fix loops

    def update_phase(self, new_phase: SessionPhase):
        """Update session phase."""
        self.phase = new_phase
        self.updated_at = datetime.now(timezone.utc)

    def add_answer(self, question_id: str, answer: Any):
        """Store an answer for a question."""
        self.answers[question_id] = answer
        self.updated_at = datetime.now(timezone.utc)

    def add_log(self, message: str):
        """Add a log entry."""
        self.logs.append(f"[{datetime.now(timezone.utc).isoformat()}] {message}")

    def add_error(self, task_id: str, error_message: str, phase: Optional[SessionPhase] = None):
        """Add an error to the error history.

        Args:
            task_id: ID of the task that failed
            error_message: Error message or description
            phase: Session phase when error occurred (defaults to current phase)
        """
        error_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task_id,
            "error_message": error_message,
            "phase": (phase or self.phase).value,
        }
        self.error_history.append(error_entry)
        self.updated_at = datetime.now(timezone.utc)

    def get_recovery_options(self) -> list[dict[str, str]]:
        """Get available recovery options for a failed/aborted session.

        Returns:
            List of recovery options with value and label
        """
        options = []

        if self.phase == SessionPhase.FAILED or self.is_aborted:
            options.append({
                "value": "restart_session",
                "label": "Start a new session",
                "description": "Abandon this session and start fresh"
            })
            options.append({
                "value": "export_logs",
                "label": "Export session logs",
                "description": "Download logs and artifacts for debugging"
            })

            # Only offer reduce_scope if we got past planning
            if self.task_graph or self.concept:
                options.append({
                    "value": "reduce_scope",
                    "label": "Retry with reduced scope",
                    "description": "Start new session with simpler requirements"
                })

        return options

    def increment_fix_loop(self) -> bool:
        """Increment fix loop counter and check if limit exceeded.

        Returns:
            True if fix loops still allowed, False if max reached
        """
        self.fix_loop_count += 1
        self.updated_at = datetime.now(timezone.utc)
        return self.fix_loop_count < self.max_fix_loops

    def reset_fix_loop(self) -> None:
        """Reset fix loop counter (called on successful task completion)."""
        self.fix_loop_count = 0
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """Serialize session state to a dictionary for persistence (VF-167).

        Returns:
            dict: Session state that can be serialized to JSON
        """
        return {
            "session_id": self.session_id,
            "phase": self.phase.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            # Questionnaire state
            "current_question_index": self.current_question_index,
            "answers": self.answers,
            # Artifacts
            "intent_profile": self.intent_profile,
            "build_spec": self.build_spec,
            "concept": self.concept,
            "task_graph": self.task_graph,
            # Execution state
            "completed_task_ids": self.completed_task_ids,
            "failed_task_ids": self.failed_task_ids,
            "active_task_id": self.active_task_id,
            "logs": self.logs,
            # Clarification state
            "pending_clarification": self.pending_clarification,
            "clarification_answer": self.clarification_answer,
            "clarification_context": self.clarification_context,
            # Error history
            "error_history": self.error_history,
            # Failure/abort state
            "failure_reason": self.failure_reason,
            "failure_artifact": self.failure_artifact,
            "is_aborted": self.is_aborted,
            "abort_reason": self.abort_reason,
            # Fix loop tracking
            "fix_loop_count": self.fix_loop_count,
            "max_fix_loops": self.max_fix_loops,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """Restore session state from a dictionary (VF-167).

        Args:
            data: Session state dictionary from to_dict()

        Returns:
            Session: Restored session instance
        """
        session = cls(session_id=data.get("session_id"))

        # Phase
        phase_value = data.get("phase", "QUESTIONNAIRE")
        session.phase = SessionPhase(phase_value)

        # Timestamps
        if data.get("created_at"):
            session.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            session.updated_at = datetime.fromisoformat(data["updated_at"])

        # Questionnaire state
        session.current_question_index = data.get("current_question_index", 0)
        session.answers = data.get("answers", {})

        # Artifacts
        session.intent_profile = data.get("intent_profile")
        session.build_spec = data.get("build_spec")
        session.concept = data.get("concept")
        session.task_graph = data.get("task_graph")

        # Execution state
        session.completed_task_ids = data.get("completed_task_ids", [])
        session.failed_task_ids = data.get("failed_task_ids", [])
        session.active_task_id = data.get("active_task_id")
        session.logs = data.get("logs", [])

        # Clarification state
        session.pending_clarification = data.get("pending_clarification")
        session.clarification_answer = data.get("clarification_answer")
        session.clarification_context = data.get("clarification_context")

        # Error history
        session.error_history = data.get("error_history", [])

        # Failure/abort state
        session.failure_reason = data.get("failure_reason")
        session.failure_artifact = data.get("failure_artifact")
        session.is_aborted = data.get("is_aborted", False)
        session.abort_reason = data.get("abort_reason")

        # Fix loop tracking
        session.fix_loop_count = data.get("fix_loop_count", 0)
        session.max_fix_loops = data.get("max_fix_loops", 3)

        return session


class SessionStoreInterface(ABC):
    """Abstract interface for session persistence.

    This interface defines the persistence seam for sessions (VF-031).
    Implementations can store sessions in memory (MVP), on disk, or in a database
    without changing the core business logic that uses this interface.

    Design principles:
    - Simple CRUD operations
    - No implementation details leaked
    - Easy to swap implementations
    """

    @abstractmethod
    def create_session(self) -> Session:
        """Create and store a new session.

        Returns:
            New Session instance with generated ID
        """
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session if found, None otherwise
        """
        pass

    @abstractmethod
    def update_session(self, session: Session) -> None:
        """Update an existing session.

        Args:
            session: Session instance to update
        """
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> None:
        """Delete a session.

        Args:
            session_id: Session identifier
        """
        pass

    @abstractmethod
    def list_sessions(self) -> list[str]:
        """List all session IDs.

        Returns:
            List of session identifiers
        """
        pass


class SessionStore(SessionStoreInterface):
    """In-memory session storage (MVP).

    This is the MVP implementation of SessionStoreInterface using in-memory storage.
    For production, this can be replaced with DiskSessionStore or DatabaseSessionStore
    without changing code that depends on SessionStoreInterface.
    """

    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def create_session(self) -> Session:
        """Create and store a new session."""
        session = Session()
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by ID."""
        return self._sessions.get(session_id)

    def update_session(self, session: Session):
        """Update an existing session."""
        self._sessions[session.session_id] = session

    def delete_session(self, session_id: str):
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]

    def list_sessions(self) -> list[str]:
        """List all session IDs."""
        return list(self._sessions.keys())


# Global session store instance (MVP: in-memory)
session_store = SessionStore()
