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

        # Agent workflow fields (VF-190: for control panel simulation mode)
        self.agents: list[dict] = []  # List of AgentConfig dicts
        self.agent_roles: dict[str, str] = {}  # agent_id -> role
        self.agent_models: dict[str, str] = {}  # agent_id -> model_id
        self.agent_graph: Optional[dict] = None  # AgentFlowGraph dict
        self.main_task: Optional[str] = None  # Orchestration goal

        # Simulation control fields (VF-190: tick-based simulation)
        self.initial_prompt: Optional[str] = None
        self.first_agent_id: Optional[str] = None
        self.simulation_mode: str = "manual"  # "manual" | "auto"
        self.tick_index: int = 0
        self.tick_status: str = "idle"  # "idle" | "running" | "blocked" | "completed"
        self.auto_delay_ms: Optional[int] = None
        self.tick_budget: Optional[int] = None  # Max events/messages per tick
        self.simulation_message_queue: list[dict[str, Any]] = []
        self.simulation_message_counter: int = 0
        self.simulation_agent_conversations: dict[str, list[dict[str, Any]]] = {}
        self.simulation_expected_responses: list[str] = []
        self.simulation_delegation_tracking: dict[str, list[str]] = {}
        self.simulation_final_answer: Optional[str] = None
        self.use_real_llm: bool = False
        self.llm_provider: str = "openai"
        self.default_model: str = "gpt-4o-mini"
        self.default_temperature: float = 0.7
        self.simulation_cost_usd: float = 0.0
        self.max_history_depth: int = 20
        self.max_cost_usd: float = 1.0
        self.tick_rate_limit_ms: int = 1000
        self.last_tick_timestamp: Optional[datetime] = None

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
            # Agent workflow fields
            "agents": self.agents,
            "agent_roles": self.agent_roles,
            "agent_models": self.agent_models,
            "agent_graph": self.agent_graph,
            "main_task": self.main_task,
            # Simulation control fields
            "initial_prompt": self.initial_prompt,
            "first_agent_id": self.first_agent_id,
            "simulation_mode": self.simulation_mode,
            "tick_index": self.tick_index,
            "tick_status": self.tick_status,
            "auto_delay_ms": self.auto_delay_ms,
            "tick_budget": self.tick_budget,
            "simulation_message_queue": self.simulation_message_queue,
            "simulation_message_counter": self.simulation_message_counter,
            "simulation_agent_conversations": self.simulation_agent_conversations,
            "simulation_expected_responses": self.simulation_expected_responses,
            "simulation_delegation_tracking": self.simulation_delegation_tracking,
            "simulation_final_answer": self.simulation_final_answer,
            "use_real_llm": self.use_real_llm,
            "llm_provider": self.llm_provider,
            "default_model": self.default_model,
            "default_temperature": self.default_temperature,
            "simulation_cost_usd": self.simulation_cost_usd,
            "max_history_depth": self.max_history_depth,
            "max_cost_usd": self.max_cost_usd,
            "tick_rate_limit_ms": self.tick_rate_limit_ms,
            "last_tick_timestamp": (
                self.last_tick_timestamp.isoformat()
                if self.last_tick_timestamp
                else None
            ),
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

        # Agent workflow fields
        session.agents = data.get("agents", [])
        session.agent_roles = data.get("agent_roles", {})
        session.agent_models = data.get("agent_models", {})
        session.agent_graph = data.get("agent_graph")
        session.main_task = data.get("main_task")

        # Simulation control fields
        session.initial_prompt = data.get("initial_prompt")
        session.first_agent_id = data.get("first_agent_id")
        session.simulation_mode = data.get("simulation_mode", "manual")
        session.tick_index = data.get("tick_index", 0)
        session.tick_status = data.get("tick_status", "idle")
        session.auto_delay_ms = data.get("auto_delay_ms")
        session.tick_budget = data.get("tick_budget")
        session.simulation_message_queue = data.get("simulation_message_queue", [])
        session.simulation_message_counter = data.get("simulation_message_counter", 0)
        session.simulation_agent_conversations = data.get(
            "simulation_agent_conversations", {}
        )
        session.simulation_expected_responses = data.get(
            "simulation_expected_responses", []
        )
        session.simulation_delegation_tracking = data.get(
            "simulation_delegation_tracking", {}
        )
        session.simulation_final_answer = data.get("simulation_final_answer")
        session.use_real_llm = data.get("use_real_llm", False)
        session.llm_provider = data.get("llm_provider", "openai")
        session.default_model = data.get("default_model", "gpt-4o-mini")
        session.default_temperature = data.get("default_temperature", 0.7)
        session.simulation_cost_usd = data.get("simulation_cost_usd", 0.0)
        session.max_history_depth = data.get("max_history_depth", 20)
        session.max_cost_usd = data.get("max_cost_usd", 1.0)
        session.tick_rate_limit_ms = data.get("tick_rate_limit_ms", 1000)
        last_tick_timestamp = data.get("last_tick_timestamp")
        if last_tick_timestamp:
            session.last_tick_timestamp = datetime.fromisoformat(last_tick_timestamp)

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
