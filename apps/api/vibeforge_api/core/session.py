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

        # Error history (VF-030: track error details, not just IDs)
        self.error_history: list[dict[str, Any]] = []

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
