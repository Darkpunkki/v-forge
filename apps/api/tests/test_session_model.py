"""Tests for Session domain model."""

import pytest
from datetime import datetime, timezone

from vibeforge_api.core.session import Session
from vibeforge_api.models.types import SessionPhase


class TestSessionModel:
    """Test Session domain model."""

    def test_session_initialization(self):
        """Test that Session initializes with correct defaults."""
        session = Session()

        assert session.session_id is not None
        assert session.phase == SessionPhase.QUESTIONNAIRE
        assert session.created_at is not None
        assert session.updated_at is not None
        assert session.current_question_index == 0
        assert session.answers == {}
        assert session.intent_profile is None
        assert session.build_spec is None
        assert session.concept is None
        assert session.task_graph is None
        assert session.completed_task_ids == []
        assert session.failed_task_ids == []
        assert session.active_task_id is None
        assert session.logs == []
        assert session.pending_clarification is None
        assert session.clarification_answer is None
        assert session.error_history == []

    def test_session_with_custom_id(self):
        """Test Session accepts custom session ID."""
        session = Session(session_id="custom-id-123")
        assert session.session_id == "custom-id-123"

    def test_update_phase(self):
        """Test phase updates correctly."""
        session = Session()
        initial_updated_at = session.updated_at

        # Small delay to ensure timestamp changes
        import time
        time.sleep(0.001)

        session.update_phase(SessionPhase.BUILD_SPEC)

        assert session.phase == SessionPhase.BUILD_SPEC
        assert session.updated_at > initial_updated_at

    def test_add_answer(self):
        """Test adding answers updates state correctly."""
        session = Session()
        initial_updated_at = session.updated_at

        import time
        time.sleep(0.001)

        session.add_answer("q1_audience", "general")

        assert session.answers["q1_audience"] == "general"
        assert session.updated_at > initial_updated_at

    def test_add_multiple_answers(self):
        """Test adding multiple answers."""
        session = Session()

        session.add_answer("q1", "answer1")
        session.add_answer("q2", "answer2")
        session.add_answer("q3", "answer3")

        assert len(session.answers) == 3
        assert session.answers["q1"] == "answer1"
        assert session.answers["q2"] == "answer2"
        assert session.answers["q3"] == "answer3"

    def test_add_log(self):
        """Test log entries are added with timestamps."""
        session = Session()

        session.add_log("Test log message")

        assert len(session.logs) == 1
        assert "Test log message" in session.logs[0]
        # Check that timestamp is included
        assert "[" in session.logs[0]
        assert "]" in session.logs[0]

    def test_add_multiple_logs(self):
        """Test adding multiple log entries."""
        session = Session()

        session.add_log("Log 1")
        session.add_log("Log 2")
        session.add_log("Log 3")

        assert len(session.logs) == 3
        assert "Log 1" in session.logs[0]
        assert "Log 2" in session.logs[1]
        assert "Log 3" in session.logs[2]

    def test_add_error(self):
        """Test VF-030: adding error to error history."""
        session = Session()
        initial_updated_at = session.updated_at

        import time
        time.sleep(0.001)

        session.add_error("task-123", "Build failed: syntax error")

        assert len(session.error_history) == 1
        error = session.error_history[0]
        assert error["task_id"] == "task-123"
        assert error["error_message"] == "Build failed: syntax error"
        assert error["phase"] == SessionPhase.QUESTIONNAIRE.value
        assert "timestamp" in error
        assert session.updated_at > initial_updated_at

    def test_add_error_with_custom_phase(self):
        """Test adding error with explicit phase."""
        session = Session()

        session.add_error(
            "task-456",
            "Verification failed",
            phase=SessionPhase.VERIFICATION,
        )

        error = session.error_history[0]
        assert error["phase"] == SessionPhase.VERIFICATION.value

    def test_add_multiple_errors(self):
        """Test adding multiple errors to history."""
        session = Session()

        session.add_error("task-1", "Error 1")
        session.add_error("task-2", "Error 2")
        session.add_error("task-3", "Error 3")

        assert len(session.error_history) == 3
        assert session.error_history[0]["task_id"] == "task-1"
        assert session.error_history[1]["task_id"] == "task-2"
        assert session.error_history[2]["task_id"] == "task-3"

    def test_error_history_preserves_order(self):
        """Test that error history maintains chronological order."""
        session = Session()

        session.add_error("task-1", "First error")
        session.add_error("task-2", "Second error")
        session.add_error("task-3", "Third error")

        # Parse timestamps and verify ordering
        timestamps = [error["timestamp"] for error in session.error_history]
        assert timestamps == sorted(timestamps)

    def test_artifact_pointers(self):
        """Test that artifact pointers can be set."""
        session = Session()

        session.intent_profile = {"platform": "web", "audience": "general"}
        session.build_spec = {"stack": "vite-react", "scope": "small"}
        session.concept = {"title": "Test App", "features": ["auth", "dashboard"]}
        session.task_graph = {"tasks": [{"id": "t1", "title": "Setup"}]}

        assert session.intent_profile["platform"] == "web"
        assert session.build_spec["stack"] == "vite-react"
        assert session.concept["title"] == "Test App"
        assert session.task_graph["tasks"][0]["id"] == "t1"

    def test_execution_state_tracking(self):
        """Test execution state fields."""
        session = Session()

        session.active_task_id = "task-current"
        session.completed_task_ids.append("task-1")
        session.completed_task_ids.append("task-2")
        session.failed_task_ids.append("task-3")

        assert session.active_task_id == "task-current"
        assert len(session.completed_task_ids) == 2
        assert len(session.failed_task_ids) == 1
        assert "task-1" in session.completed_task_ids
        assert "task-3" in session.failed_task_ids

    def test_clarification_state(self):
        """Test clarification state fields."""
        session = Session()

        session.pending_clarification = {
            "question": "Proceed with high complexity?",
            "options": [{"value": "yes", "label": "Yes"}],
        }
        session.clarification_answer = "yes"

        assert session.pending_clarification["question"] == "Proceed with high complexity?"
        assert session.clarification_answer == "yes"

    def test_timestamps_are_utc(self):
        """Test that timestamps use UTC timezone."""
        session = Session()

        # Timestamps should be timezone-aware UTC
        assert session.created_at.tzinfo == timezone.utc
        assert session.updated_at.tzinfo == timezone.utc
