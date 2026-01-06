"""Tests for SessionCoordinator (VF-032, VF-033, VF-034)."""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock

from orchestration.coordinator import SessionCoordinator
from vibeforge_api.core.session import Session, SessionStore
from vibeforge_api.core.workspace import WorkspaceManager
from vibeforge_api.core.questionnaire import QuestionnaireEngine
from vibeforge_api.core.spec_builder import SpecBuilder
from vibeforge_api.models.types import SessionPhase
from vibeforge_api.models.responses import QuestionResponse, QuestionOption


class TestSessionCoordinatorStartSession:
    """Test VF-032: SessionCoordinator.start_session()."""

    def test_start_session_creates_session_and_workspace(self, tmp_path):
        """Test starting a new session initializes session and workspace."""
        # Setup
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
        )

        # Execute
        session_id = coordinator.start_session()

        # Verify
        assert session_id is not None
        session = session_store.get_session(session_id)
        assert session is not None
        assert session.phase == SessionPhase.QUESTIONNAIRE
        assert len(session.logs) > 0
        assert "Workspace initialized" in session.logs[0]

        # Verify workspace created
        workspace_path = tmp_path / "workspaces" / session_id
        assert workspace_path.exists()
        assert (workspace_path / "repo").exists()
        assert (workspace_path / "artifacts").exists()

    def test_start_session_logs_workspace_path(self, tmp_path):
        """Test that workspace path is logged on session start."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
        )

        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        assert any("Workspace initialized" in log for log in session.logs)

    def test_start_session_handles_workspace_init_failure(self, tmp_path):
        """Test that workspace initialization failure is handled gracefully."""
        session_store = SessionStore()

        # Create mock workspace manager that fails
        workspace_manager = Mock(spec=WorkspaceManager)
        workspace_manager.init_repo.side_effect = RuntimeError("Disk full")

        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
        )

        # Execute and verify exception
        with pytest.raises(RuntimeError) as exc_info:
            coordinator.start_session()

        assert "Failed to initialize session workspace" in str(exc_info.value)


class TestSessionCoordinatorQuestionnaire:
    """Test VF-033: SessionCoordinator questionnaire loop."""

    def test_get_next_question_returns_first_question(self, tmp_path):
        """Test getting the first questionnaire question."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
        )

        session_id = coordinator.start_session()

        # Get first question
        question = coordinator.get_next_question(session_id)

        assert question is not None
        assert question.question_id == "q1_audience"
        assert question.text is not None
        assert len(question.options) > 0

    def test_get_next_question_raises_if_wrong_phase(self, tmp_path):
        """Test that getting question in wrong phase raises error."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
        )

        session_id = coordinator.start_session()

        # Manually change phase
        session = session_store.get_session(session_id)
        session.update_phase(SessionPhase.BUILD_SPEC)
        session_store.update_session(session)

        # Try to get question
        with pytest.raises(ValueError) as exc_info:
            coordinator.get_next_question(session_id)

        assert "expected QUESTIONNAIRE" in str(exc_info.value)

    def test_submit_answer_validates_and_stores_answer(self, tmp_path):
        """Test submitting a valid answer."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
        )

        session_id = coordinator.start_session()

        # Submit answer
        coordinator.submit_answer(session_id, "q1_audience", "developers")

        # Verify
        session = session_store.get_session(session_id)
        assert session.answers["q1_audience"] == "developers"
        assert session.current_question_index == 1
        assert any("Answer submitted for q1_audience" in log for log in session.logs)

    def test_submit_answer_raises_if_invalid_answer(self, tmp_path):
        """Test that invalid answers are rejected."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
        )

        session_id = coordinator.start_session()

        # Submit invalid answer
        with pytest.raises(ValueError) as exc_info:
            coordinator.submit_answer(session_id, "q1_audience", "invalid_option")

        assert "Invalid answer" in str(exc_info.value)

    def test_submit_answer_raises_if_question_id_mismatch(self, tmp_path):
        """Test that question ID mismatch raises error."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
        )

        session_id = coordinator.start_session()

        # Submit answer with wrong question ID
        with pytest.raises(ValueError) as exc_info:
            coordinator.submit_answer(session_id, "q2_platform", "web")

        assert "Question ID mismatch" in str(exc_info.value)

    def test_finalize_questionnaire_generates_intent_profile(self, tmp_path):
        """Test finalizing questionnaire generates IntentProfile."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
        )

        session_id = coordinator.start_session()

        # Answer all questions
        coordinator.submit_answer(session_id, "q1_audience", "developers")
        coordinator.submit_answer(session_id, "q2_platform", "web")
        coordinator.submit_answer(session_id, "q3_complexity", "simple")

        # Finalize
        intent_profile = coordinator.finalize_questionnaire(session_id)

        # Verify
        assert intent_profile is not None
        assert intent_profile["sessionId"] == session_id
        assert "audience" in intent_profile
        assert "platformPreference" in intent_profile

        # Verify session updated
        session = session_store.get_session(session_id)
        assert session.intent_profile == intent_profile
        assert session.phase == SessionPhase.BUILD_SPEC
        assert any("IntentProfile generated" in log for log in session.logs)
        assert any("QUESTIONNAIRE → BUILD_SPEC" in log for log in session.logs)

    def test_finalize_questionnaire_raises_if_incomplete(self, tmp_path):
        """Test that finalizing incomplete questionnaire raises error."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
        )

        session_id = coordinator.start_session()

        # Answer only 1 of 3 questions
        coordinator.submit_answer(session_id, "q1_audience", "developers")

        # Try to finalize
        with pytest.raises(ValueError) as exc_info:
            coordinator.finalize_questionnaire(session_id)

        assert "Questionnaire incomplete" in str(exc_info.value)

    def test_finalize_questionnaire_raises_if_wrong_phase(self, tmp_path):
        """Test that finalizing in wrong phase raises error."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
        )

        session_id = coordinator.start_session()

        # Manually change phase
        session = session_store.get_session(session_id)
        session.update_phase(SessionPhase.BUILD_SPEC)
        session_store.update_session(session)

        # Try to finalize
        with pytest.raises(ValueError) as exc_info:
            coordinator.finalize_questionnaire(session_id)

        assert "expected QUESTIONNAIRE" in str(exc_info.value)


class TestSessionCoordinatorBuildSpec:
    """Test VF-034: SessionCoordinator.generate_build_spec()."""

    def test_generate_build_spec_converts_intent_to_spec(self, tmp_path):
        """Test generating BuildSpec from IntentProfile."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
        )

        session_id = coordinator.start_session()

        # Complete questionnaire
        coordinator.submit_answer(session_id, "q1_audience", "developers")
        coordinator.submit_answer(session_id, "q2_platform", "web")
        coordinator.submit_answer(session_id, "q3_complexity", "simple")
        coordinator.finalize_questionnaire(session_id)

        # Generate BuildSpec
        build_spec = coordinator.generate_build_spec(session_id)

        # Verify
        assert build_spec is not None
        assert build_spec["sessionId"] == session_id
        assert "target" in build_spec
        assert "platform" in build_spec["target"]
        assert "stack" in build_spec
        assert "ideaSeed" in build_spec

        # Verify session updated
        session = session_store.get_session(session_id)
        assert session.build_spec == build_spec
        assert session.phase == SessionPhase.IDEA
        assert any("BuildSpec generated" in log for log in session.logs)
        assert any("BUILD_SPEC → IDEA" in log for log in session.logs)

    def test_generate_build_spec_persists_artifact(self, tmp_path):
        """Test that BuildSpec is persisted to artifacts."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
        )

        session_id = coordinator.start_session()

        # Complete questionnaire
        coordinator.submit_answer(session_id, "q1_audience", "developers")
        coordinator.submit_answer(session_id, "q2_platform", "web")
        coordinator.submit_answer(session_id, "q3_complexity", "simple")
        coordinator.finalize_questionnaire(session_id)

        # Generate BuildSpec
        coordinator.generate_build_spec(session_id)

        # Verify artifact exists
        artifact_path = tmp_path / "workspaces" / session_id / "artifacts" / "build_spec.json"
        assert artifact_path.exists()

        # Verify log entry
        session = session_store.get_session(session_id)
        assert any("BuildSpec persisted to artifacts/build_spec.json" in log for log in session.logs)

    def test_generate_build_spec_raises_if_wrong_phase(self, tmp_path):
        """Test that generating BuildSpec in wrong phase raises error."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
        )

        session_id = coordinator.start_session()

        # Try to generate BuildSpec without completing questionnaire
        with pytest.raises(ValueError) as exc_info:
            coordinator.generate_build_spec(session_id)

        assert "expected BUILD_SPEC" in str(exc_info.value)

    def test_generate_build_spec_raises_if_intent_profile_missing(self, tmp_path):
        """Test that generating BuildSpec without IntentProfile raises error."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
        )

        session_id = coordinator.start_session()

        # Manually change phase to BUILD_SPEC without IntentProfile
        session = session_store.get_session(session_id)
        session.update_phase(SessionPhase.BUILD_SPEC)
        session_store.update_session(session)

        # Try to generate BuildSpec
        with pytest.raises(ValueError) as exc_info:
            coordinator.generate_build_spec(session_id)

        assert "IntentProfile missing" in str(exc_info.value)


class TestSessionCoordinatorHelpers:
    """Test SessionCoordinator helper methods."""

    def test_get_session_or_raise_returns_session(self, tmp_path):
        """Test that helper returns session if it exists."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
        )

        session_id = coordinator.start_session()

        # Should not raise
        session = coordinator._get_session_or_raise(session_id)
        assert session is not None
        assert session.session_id == session_id

    def test_get_session_or_raise_raises_if_not_found(self, tmp_path):
        """Test that helper raises ValueError if session not found."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
        )

        # Try to get non-existent session
        with pytest.raises(ValueError) as exc_info:
            coordinator._get_session_or_raise("nonexistent")

        assert "Session not found" in str(exc_info.value)


class TestSessionCoordinatorIntegration:
    """Integration tests for SessionCoordinator end-to-end flow."""

    def test_full_questionnaire_to_build_spec_flow(self, tmp_path):
        """Test complete flow from session start to BuildSpec generation."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
        )

        # Start session
        session_id = coordinator.start_session()
        assert session_id is not None

        # Answer all questions
        q1 = coordinator.get_next_question(session_id)
        assert q1.question_id == "q1_audience"
        coordinator.submit_answer(session_id, "q1_audience", "developers")

        q2 = coordinator.get_next_question(session_id)
        assert q2.question_id == "q2_platform"
        coordinator.submit_answer(session_id, "q2_platform", "web")

        q3 = coordinator.get_next_question(session_id)
        assert q3.question_id == "q3_complexity"
        coordinator.submit_answer(session_id, "q3_complexity", "simple")

        # Verify no more questions
        q4 = coordinator.get_next_question(session_id)
        assert q4 is None

        # Finalize questionnaire
        intent_profile = coordinator.finalize_questionnaire(session_id)
        assert intent_profile is not None

        # Generate BuildSpec
        build_spec = coordinator.generate_build_spec(session_id)
        assert build_spec is not None

        # Verify final state
        session = session_store.get_session(session_id)
        assert session.phase == SessionPhase.IDEA
        assert session.intent_profile is not None
        assert session.build_spec is not None
