"""Integration tests for phase transitions (VF-166).

These tests exercise the full phase transition flow through SessionCoordinator,
verifying that:
1. Valid transitions succeed and emit expected events
2. Illegal transitions are rejected with proper errors
3. Artifacts are persisted at key phases
4. Exit criteria enforcement works correctly
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone

from orchestration.coordinator import SessionCoordinator
from orchestration.coordinator.state_machine import (
    TransitionError,
    ExitCriteriaNotMet,
    ALLOWED_TRANSITIONS,
)
from orchestration.orchestrator import Orchestrator
from vibeforge_api.core.session import Session, SessionStore
from vibeforge_api.core.workspace import WorkspaceManager
from vibeforge_api.core.questionnaire import QuestionnaireEngine
from vibeforge_api.core.spec_builder import SpecBuilder
from vibeforge_api.core.event_log import EventType
from vibeforge_api.models.types import SessionPhase


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def session_store():
    """Create a fresh session store for each test."""
    return SessionStore()


@pytest.fixture
def workspace_manager(tmp_path):
    """Create workspace manager with temp directory."""
    return WorkspaceManager(tmp_path)


@pytest.fixture
def coordinator(session_store, workspace_manager):
    """Create a SessionCoordinator with mock orchestrator."""
    questionnaire_engine = QuestionnaireEngine()
    spec_builder = SpecBuilder()
    mock_orchestrator = MagicMock(spec=Orchestrator)

    return SessionCoordinator(
        session_store=session_store,
        workspace_manager=workspace_manager,
        questionnaire_engine=questionnaire_engine,
        spec_builder=spec_builder,
        orchestrator=mock_orchestrator,
    )


# =============================================================================
# VF-166: Integration Tests for Phase Transitions
# =============================================================================


class TestVF166_PhaseTransitionIntegration:
    """Integration tests for complete phase transition flows."""

    # -------------------------------------------------------------------------
    # Valid Transition Flows
    # -------------------------------------------------------------------------

    def test_questionnaire_to_build_spec_transition(self, coordinator, session_store):
        """Complete questionnaire flow transitions to BUILD_SPEC."""
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        # Answer all questions
        questions_answered = 0
        while True:
            question = coordinator.get_next_question(session_id)
            if question is None:
                break
            # Submit a valid answer (first option)
            coordinator.submit_answer(session_id, question.question_id, question.options[0].value)
            questions_answered += 1

        # Finalize questionnaire - transitions to BUILD_SPEC
        coordinator.finalize_questionnaire(session_id)

        session = session_store.get_session(session_id)
        assert session.phase == SessionPhase.BUILD_SPEC
        assert session.intent_profile is not None
        assert questions_answered > 0

    def test_build_spec_to_idea_transition(self, coordinator, session_store, workspace_manager, tmp_path):
        """BUILD_SPEC → IDEA transition via direct phase manipulation."""
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        # Set up session state for BUILD_SPEC → IDEA transition
        session.answers = {"q1": "answer"}
        session.intent_profile = {"app_type": "web"}
        session.build_spec = {"stack": "vite-react"}
        session.update_phase(SessionPhase.BUILD_SPEC)
        session_store.update_session(session)

        # Now set concept (exit criteria) and transition
        session.concept = {"description": "Test concept", "features": []}
        session_store.update_session(session)

        # Transition to IDEA
        coordinator._transition_phase(session, SessionPhase.IDEA, "Concept generated")

        session = session_store.get_session(session_id)
        assert session.phase == SessionPhase.IDEA

    def test_idea_to_plan_review_transition(self, coordinator, session_store):
        """IDEA → PLAN_REVIEW transition via direct phase manipulation."""
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        # Set up session state for IDEA phase
        session.answers = {"q1": "answer"}
        session.intent_profile = {"app_type": "web"}
        session.build_spec = {"stack": "vite-react"}
        session.concept = {"description": "Test concept", "features": []}
        session.update_phase(SessionPhase.IDEA)
        session_store.update_session(session)

        # Set task_graph (exit criteria) and transition
        session.task_graph = {"tasks": []}
        session_store.update_session(session)

        # Transition to PLAN_REVIEW
        coordinator._transition_phase(session, SessionPhase.PLAN_REVIEW, "Plan generated")

        session = session_store.get_session(session_id)
        assert session.phase == SessionPhase.PLAN_REVIEW

    def test_plan_review_to_execution_on_approval(self, coordinator, session_store):
        """PLAN_REVIEW → EXECUTION on plan approval."""
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        # Set up session state for PLAN_REVIEW phase
        session.answers = {"q1": "answer"}
        session.intent_profile = {"app_type": "web"}
        session.build_spec = {"stack": "vite-react"}
        session.concept = {"description": "Test concept"}
        session.task_graph = {"tasks": []}
        session.update_phase(SessionPhase.PLAN_REVIEW)
        session_store.update_session(session)

        # Approve plan - transitions to EXECUTION
        coordinator.approve_plan(session_id)

        session = session_store.get_session(session_id)
        assert session.phase == SessionPhase.EXECUTION

    def test_plan_review_to_idea_on_rejection(self, coordinator, session_store):
        """PLAN_REVIEW → IDEA on plan rejection."""
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        # Set up session state for PLAN_REVIEW phase
        session.answers = {"q1": "answer"}
        session.intent_profile = {"app_type": "web"}
        session.build_spec = {"stack": "vite-react"}
        session.concept = {"description": "Test concept"}
        session.task_graph = {"tasks": []}
        session.update_phase(SessionPhase.PLAN_REVIEW)
        session_store.update_session(session)

        # Reject plan - transitions back to IDEA
        coordinator.reject_plan(session_id)

        session = session_store.get_session(session_id)
        assert session.phase == SessionPhase.IDEA

    def test_execution_to_clarification_transition(self, coordinator, session_store):
        """EXECUTION → CLARIFICATION when clarification is needed."""
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        # Set up for EXECUTION phase
        session.answers = {"q1": "answer"}
        session.intent_profile = {"app_type": "web"}
        session.build_spec = {"stack": "vite-react"}
        session.concept = {"description": "test"}
        session.task_graph = {"tasks": []}
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        # Directly transition to CLARIFICATION (simulating clarification request)
        session.pending_clarification = {"question": "Which approach?"}
        coordinator._transition_phase(session, SessionPhase.CLARIFICATION, "Need user input")
        session_store.update_session(session)

        session = session_store.get_session(session_id)
        assert session.phase == SessionPhase.CLARIFICATION
        assert session.pending_clarification is not None

    def test_clarification_to_execution_resume(self, coordinator, session_store):
        """CLARIFICATION → EXECUTION when answer is provided."""
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        # Setup for CLARIFICATION
        session.answers = {"q1": "answer"}
        session.intent_profile = {"app_type": "web"}
        session.build_spec = {"stack": "vite-react"}
        session.concept = {"description": "test"}
        session.task_graph = {"tasks": []}
        session.update_phase(SessionPhase.CLARIFICATION)
        session.pending_clarification = {"question": "Which approach?"}
        session.clarification_answer = "option_a"
        session_store.update_session(session)

        # Resume execution
        coordinator.resume_execution(session_id)

        session = session_store.get_session(session_id)
        assert session.phase == SessionPhase.EXECUTION

    # -------------------------------------------------------------------------
    # Illegal Transition Rejection
    # -------------------------------------------------------------------------

    def test_illegal_transition_questionnaire_to_execution_rejected(self, coordinator, session_store):
        """Direct QUESTIONNAIRE → EXECUTION is rejected."""
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        # Set answers so exit criteria pass, but transition is still illegal
        session.answers = {"q1": "answer"}
        session_store.update_session(session)

        # Attempt illegal direct transition (QUESTIONNAIRE can only go to BUILD_SPEC or FAILED)
        with pytest.raises(TransitionError) as exc_info:
            coordinator._transition_phase(session, SessionPhase.EXECUTION, "Test")

        assert exc_info.value.from_phase == SessionPhase.QUESTIONNAIRE
        assert exc_info.value.to_phase == SessionPhase.EXECUTION

    def test_illegal_transition_from_complete_rejected(self, coordinator, session_store):
        """Transitions from COMPLETE are rejected (exit criteria check catches it)."""
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        # Force session to COMPLETE
        session.answers = {"q1": "a"}
        session.intent_profile = {"type": "web"}
        session.build_spec = {"stack": "vite"}
        session.concept = {"desc": "test"}
        session.task_graph = {"tasks": []}
        session.update_phase(SessionPhase.COMPLETE)
        session_store.update_session(session)

        # Attempt transition from terminal state - blocked by exit criteria
        with pytest.raises((TransitionError, ExitCriteriaNotMet)) as exc_info:
            coordinator._transition_phase(session, SessionPhase.EXECUTION, "Test")

        # Either TransitionError or ExitCriteriaNotMet is acceptable
        assert "COMPLETE" in str(exc_info.value) or "Terminal" in str(exc_info.value)

    def test_illegal_transition_from_failed_rejected(self, coordinator, session_store):
        """Transitions from FAILED are rejected (exit criteria check catches it)."""
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        # Force session to FAILED
        session.update_phase(SessionPhase.FAILED)
        session_store.update_session(session)

        # Attempt transition from terminal state - blocked by exit criteria
        with pytest.raises((TransitionError, ExitCriteriaNotMet)) as exc_info:
            coordinator._transition_phase(session, SessionPhase.QUESTIONNAIRE, "Test")

        # Either TransitionError or ExitCriteriaNotMet is acceptable
        assert "FAILED" in str(exc_info.value) or "Terminal" in str(exc_info.value)

    def test_illegal_transition_clarification_to_verification_rejected(self, coordinator, session_store):
        """Direct CLARIFICATION → VERIFICATION is rejected."""
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        # Setup for CLARIFICATION
        session.answers = {"q1": "a"}
        session.clarification_answer = "yes"
        session.update_phase(SessionPhase.CLARIFICATION)
        session_store.update_session(session)

        # CLARIFICATION can only go to EXECUTION or FAILED, not VERIFICATION
        with pytest.raises(TransitionError) as exc_info:
            coordinator._transition_phase(session, SessionPhase.VERIFICATION, "Test")

        assert exc_info.value.from_phase == SessionPhase.CLARIFICATION

    # -------------------------------------------------------------------------
    # Exit Criteria Enforcement
    # -------------------------------------------------------------------------

    def test_exit_criteria_enforced_questionnaire_no_answers(self, coordinator, session_store):
        """Cannot exit QUESTIONNAIRE without answers."""
        session_id = coordinator.start_session()

        # Try to finalize without answering questions
        with pytest.raises(ValueError) as exc_info:
            coordinator.finalize_questionnaire(session_id)

        assert "incomplete" in str(exc_info.value).lower() or "question" in str(exc_info.value).lower()

    def test_exit_criteria_enforced_build_spec_no_profile(self, coordinator, session_store):
        """Cannot exit BUILD_SPEC without intent profile."""
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        # Force to BUILD_SPEC without intent profile
        session.answers = {"q1": "a"}
        session.update_phase(SessionPhase.BUILD_SPEC)
        session_store.update_session(session)

        # Direct transition should fail exit criteria
        with pytest.raises(ExitCriteriaNotMet):
            coordinator._transition_phase(session, SessionPhase.IDEA, "Test")

    # -------------------------------------------------------------------------
    # Event Emission Verification
    # -------------------------------------------------------------------------

    def test_phase_transition_emits_events(self, coordinator, session_store):
        """Phase transitions emit appropriate events."""
        session_id = coordinator.start_session()

        events_emitted = []
        original_emit = coordinator._emit_event

        def capture_event(event):
            events_emitted.append(event)
            original_emit(event)

        coordinator._emit_event = capture_event

        # Complete questionnaire
        while True:
            question = coordinator.get_next_question(session_id)
            if question is None:
                break
            coordinator.submit_answer(session_id, question.question_id, question.options[0].value)
        coordinator.finalize_questionnaire(session_id)

        # Check events were emitted
        phase_events = [e for e in events_emitted if e.event_type == EventType.PHASE_TRANSITION]
        assert len(phase_events) >= 1

    def test_fail_session_emits_session_failed_event(self, coordinator, session_store):
        """fail_session emits SESSION_FAILED event."""
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        events_emitted = []
        original_emit = coordinator._emit_event

        def capture_event(event):
            events_emitted.append(event)
            original_emit(event)

        coordinator._emit_event = capture_event

        coordinator.fail_session(session_id, "Test failure")

        failed_events = [e for e in events_emitted if e.event_type == EventType.SESSION_FAILED]
        assert len(failed_events) == 1
        assert "Test failure" in failed_events[0].message

    # -------------------------------------------------------------------------
    # Artifact Persistence Verification
    # -------------------------------------------------------------------------

    def test_build_spec_artifact_persisted(self, coordinator, session_store, tmp_path):
        """BuildSpec is persisted as artifact."""
        session_id = coordinator.start_session()

        # Complete questionnaire
        while True:
            question = coordinator.get_next_question(session_id)
            if question is None:
                break
            coordinator.submit_answer(session_id, question.question_id, question.options[0].value)
        coordinator.finalize_questionnaire(session_id)
        coordinator.generate_build_spec(session_id)

        # Check artifact file exists
        artifact_path = tmp_path / session_id / "artifacts" / "build_spec.json"
        assert artifact_path.exists()

    def test_failure_artifact_persisted(self, coordinator, session_store, tmp_path):
        """Failure artifact is persisted when session fails."""
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        coordinator.fail_session(session_id, "Test failure")

        # Check failure artifact exists
        failure_path = tmp_path / session_id / "artifacts" / "failure_report.json"
        assert failure_path.exists()

    # -------------------------------------------------------------------------
    # Fix Loop Integration
    # -------------------------------------------------------------------------

    def test_fix_loop_transition_increments_counter(self, coordinator, session_store):
        """Fix loop transition increments fix_loop_count."""
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        # Setup for EXECUTION
        session.answers = {"q1": "a"}
        session.intent_profile = {"type": "web"}
        session.build_spec = {"stack": "vite"}
        session.concept = {"desc": "test"}
        session.task_graph = {"tasks": []}
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        initial_count = session.fix_loop_count

        # Trigger fix loop
        result = coordinator.trigger_fix_loop(session_id, "Verification failed")

        session = session_store.get_session(session_id)
        assert session.fix_loop_count == initial_count + 1
        assert result["status"] == "fix_loop_triggered"

    def test_fix_loop_limit_causes_failure(self, coordinator, session_store):
        """Fix loop at limit causes session failure."""
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        # Setup for EXECUTION at fix loop limit
        session.answers = {"q1": "a"}
        session.intent_profile = {"type": "web"}
        session.build_spec = {"stack": "vite"}
        session.concept = {"desc": "test"}
        session.task_graph = {"tasks": []}
        session.update_phase(SessionPhase.EXECUTION)
        session.fix_loop_count = 3  # At limit
        session_store.update_session(session)

        # Trigger fix loop should fail
        result = coordinator.trigger_fix_loop(session_id, "Verification failed again")

        assert result["status"] == "failed"
        session = session_store.get_session(session_id)
        assert session.phase == SessionPhase.FAILED


class TestVF166_TransitionCoverage:
    """Ensure all valid transitions are covered by tests."""

    def test_all_non_terminal_phases_have_valid_outgoing_transitions(self):
        """Every non-terminal phase has at least one valid outgoing transition."""
        terminal = {SessionPhase.COMPLETE, SessionPhase.FAILED}

        for phase in SessionPhase:
            if phase not in terminal:
                transitions = ALLOWED_TRANSITIONS.get(phase, set())
                assert len(transitions) > 0, f"{phase.value} has no outgoing transitions"

    def test_terminal_phases_have_no_outgoing_transitions(self):
        """Terminal phases have empty transition sets."""
        terminal = {SessionPhase.COMPLETE, SessionPhase.FAILED}

        for phase in terminal:
            transitions = ALLOWED_TRANSITIONS.get(phase, set())
            assert len(transitions) == 0, f"Terminal {phase.value} has outgoing transitions"


# =============================================================================
# VF-167: Session Resume Tests
# =============================================================================


class TestVF167_SessionResume:
    """Tests for VF-167: Resume session from stored artifacts."""

    def test_session_to_dict_serializes_all_fields(self, session_store):
        """Session.to_dict() serializes all important fields."""
        session = session_store.create_session()
        session.answers = {"q1": "answer1"}
        session.intent_profile = {"app_type": "web"}
        session.build_spec = {"stack": "vite"}
        session.concept = {"description": "test"}
        session.task_graph = {"tasks": []}
        session.completed_task_ids = ["task-1", "task-2"]
        session.failed_task_ids = ["task-3"]
        session.fix_loop_count = 2

        data = session.to_dict()

        assert data["session_id"] == session.session_id
        assert data["phase"] == session.phase.value
        assert data["answers"] == {"q1": "answer1"}
        assert data["intent_profile"] == {"app_type": "web"}
        assert data["build_spec"] == {"stack": "vite"}
        assert data["concept"] == {"description": "test"}
        assert data["task_graph"] == {"tasks": []}
        assert data["completed_task_ids"] == ["task-1", "task-2"]
        assert data["failed_task_ids"] == ["task-3"]
        assert data["fix_loop_count"] == 2

    def test_session_from_dict_restores_all_fields(self):
        """Session.from_dict() restores all fields from serialized data."""
        from vibeforge_api.core.session import Session

        data = {
            "session_id": "test-123",
            "phase": "EXECUTION",
            "created_at": "2026-01-12T10:00:00+00:00",
            "updated_at": "2026-01-12T11:00:00+00:00",
            "answers": {"q1": "a"},
            "intent_profile": {"type": "web"},
            "build_spec": {"stack": "vite"},
            "concept": {"desc": "test"},
            "task_graph": {"tasks": []},
            "completed_task_ids": ["t1", "t2"],
            "failed_task_ids": ["t3"],
            "fix_loop_count": 1,
            "is_aborted": False,
        }

        session = Session.from_dict(data)

        assert session.session_id == "test-123"
        assert session.phase == SessionPhase.EXECUTION
        assert session.answers == {"q1": "a"}
        assert session.completed_task_ids == ["t1", "t2"]
        assert session.fix_loop_count == 1

    def test_save_session_state_creates_artifact(self, coordinator, session_store, tmp_path):
        """save_session_state() creates session_state.json artifact."""
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.answers = {"q1": "answer"}
        session_store.update_session(session)

        result = coordinator.save_session_state(session_id)

        assert result["status"] == "saved"
        assert result["session_id"] == session_id

        state_path = tmp_path / session_id / "artifacts" / "session_state.json"
        assert state_path.exists()

    def test_resume_session_restores_state(self, coordinator, session_store, tmp_path):
        """resume_session() restores session state from artifact."""
        import json

        # Create a saved session state file
        session_id = "resume-test-123"
        state_data = {
            "session_id": session_id,
            "phase": "PLAN_REVIEW",
            "created_at": "2026-01-12T10:00:00+00:00",
            "updated_at": "2026-01-12T11:00:00+00:00",
            "answers": {"q1": "a"},
            "intent_profile": {"type": "web"},
            "build_spec": {"stack": "vite"},
            "concept": {"desc": "test"},
            "task_graph": {"tasks": []},
            "completed_task_ids": [],
            "failed_task_ids": [],
            "current_question_index": 0,
            "logs": [],
            "error_history": [],
            "fix_loop_count": 0,
            "max_fix_loops": 3,
            "is_aborted": False,
        }

        # Create the artifact directory and file
        artifacts_dir = tmp_path / session_id / "artifacts"
        artifacts_dir.mkdir(parents=True)
        state_path = artifacts_dir / "session_state.json"
        with open(state_path, "w") as f:
            json.dump(state_data, f)

        # Resume session
        result = coordinator.resume_session(session_id)

        assert result["status"] == "resumed"
        assert result["session_id"] == session_id
        assert result["phase"] == "PLAN_REVIEW"

        # Verify session is in store
        session = session_store.get_session(session_id)
        assert session is not None
        assert session.phase == SessionPhase.PLAN_REVIEW
        assert session.answers == {"q1": "a"}

    def test_resume_session_terminal_phase_returns_not_resumable(self, coordinator, session_store, tmp_path):
        """resume_session() returns not_resumable for terminal phases."""
        import json

        session_id = "terminal-test-123"
        state_data = {
            "session_id": session_id,
            "phase": "COMPLETE",
            "created_at": "2026-01-12T10:00:00+00:00",
            "updated_at": "2026-01-12T11:00:00+00:00",
            "answers": {},
            "completed_task_ids": [],
            "failed_task_ids": [],
            "current_question_index": 0,
            "logs": [],
            "error_history": [],
            "fix_loop_count": 0,
            "max_fix_loops": 3,
            "is_aborted": False,
        }

        artifacts_dir = tmp_path / session_id / "artifacts"
        artifacts_dir.mkdir(parents=True)
        with open(artifacts_dir / "session_state.json", "w") as f:
            json.dump(state_data, f)

        result = coordinator.resume_session(session_id)

        assert result["status"] == "not_resumable"
        assert "terminal" in result["reason"].lower()

    def test_resume_session_execution_with_active_task_warns(self, coordinator, session_store, tmp_path):
        """resume_session() warns when EXECUTION phase has active task."""
        import json

        session_id = "active-task-test-123"
        state_data = {
            "session_id": session_id,
            "phase": "EXECUTION",
            "created_at": "2026-01-12T10:00:00+00:00",
            "updated_at": "2026-01-12T11:00:00+00:00",
            "answers": {"q1": "a"},
            "intent_profile": {"type": "web"},
            "build_spec": {"stack": "vite"},
            "concept": {"desc": "test"},
            "task_graph": {"tasks": []},
            "completed_task_ids": ["t1"],
            "failed_task_ids": [],
            "active_task_id": "task-in-progress",
            "current_question_index": 0,
            "logs": [],
            "error_history": [],
            "fix_loop_count": 0,
            "max_fix_loops": 3,
            "is_aborted": False,
        }

        artifacts_dir = tmp_path / session_id / "artifacts"
        artifacts_dir.mkdir(parents=True)
        with open(artifacts_dir / "session_state.json", "w") as f:
            json.dump(state_data, f)

        result = coordinator.resume_session(session_id)

        assert result["status"] == "resumed"
        assert result["warnings"] is not None
        assert any("active task" in w.lower() for w in result["warnings"])

        # Active task should be cleared
        session = session_store.get_session(session_id)
        assert session.active_task_id is None

    def test_resume_session_not_found_raises(self, coordinator):
        """resume_session() raises ValueError when state file not found."""
        with pytest.raises(ValueError) as exc_info:
            coordinator.resume_session("nonexistent-session")

        assert "No saved session state" in str(exc_info.value)

    def test_save_and_resume_roundtrip(self, coordinator, session_store, tmp_path):
        """Full roundtrip: save session state, then resume it."""
        # Start and progress a session
        session_id = coordinator.start_session()

        # Answer questions
        while True:
            question = coordinator.get_next_question(session_id)
            if question is None:
                break
            coordinator.submit_answer(session_id, question.question_id, question.options[0].value)
        coordinator.finalize_questionnaire(session_id)

        session = session_store.get_session(session_id)
        original_answers = session.answers.copy()
        original_phase = session.phase

        # Save state
        save_result = coordinator.save_session_state(session_id)
        assert save_result["status"] == "saved"

        # Clear in-memory session (simulate restart)
        session_store.delete_session(session_id)
        assert session_store.get_session(session_id) is None

        # Resume session
        resume_result = coordinator.resume_session(session_id)
        assert resume_result["status"] == "resumed"

        # Verify restored session
        restored = session_store.get_session(session_id)
        assert restored is not None
        assert restored.answers == original_answers
        assert restored.phase == original_phase

    def test_list_resumable_sessions(self, coordinator, tmp_path):
        """list_resumable_sessions() finds sessions with saved state."""
        import json

        # Create some saved sessions
        for i, phase in enumerate(["EXECUTION", "PLAN_REVIEW", "COMPLETE"]):
            session_id = f"test-session-{i}"
            artifacts_dir = tmp_path / session_id / "artifacts"
            artifacts_dir.mkdir(parents=True)
            with open(artifacts_dir / "session_state.json", "w") as f:
                json.dump({
                    "session_id": session_id,
                    "phase": phase,
                    "completed_task_ids": [],
                    "failed_task_ids": [],
                }, f)

        resumable = coordinator.list_resumable_sessions()

        assert len(resumable) == 3

        # Check that terminal sessions are marked correctly
        phases = {r["session_id"]: r for r in resumable}
        assert phases["test-session-0"]["is_resumable"] is True
        assert phases["test-session-1"]["is_resumable"] is True
        assert phases["test-session-2"]["is_resumable"] is False  # COMPLETE is terminal
