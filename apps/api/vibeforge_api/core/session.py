"""Session domain model and storage."""

import uuid
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


class SessionStore:
    """In-memory session storage (MVP)."""

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


# Global session store instance (MVP: in-memory)
session_store = SessionStore()
