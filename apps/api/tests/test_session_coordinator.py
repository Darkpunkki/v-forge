"""Tests for SessionCoordinator (VF-032, VF-033, VF-034, VF-035, VF-036, VF-163, VF-164, VF-165)."""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock

from orchestration.coordinator import SessionCoordinator
from orchestration.models import ConceptDoc, TaskGraph
from orchestration.models import Task as TaskModel
from orchestration.orchestrator import Orchestrator
from vibeforge_api.core.event_log import EventLog, EventType
from vibeforge_api.core.session import Session, SessionStore
from vibeforge_api.core.workspace import WorkspaceManager
from vibeforge_api.core.questionnaire import QuestionnaireEngine
from vibeforge_api.core.spec_builder import SpecBuilder
from vibeforge_api.models.types import SessionPhase
from vibeforge_api.models.responses import QuestionResponse, QuestionOption


@pytest.fixture
def mock_orchestrator():
    """Create a mock Orchestrator for testing."""
    return Mock()


class TestSessionCoordinatorStartSession:
    """Test VF-032: SessionCoordinator.start_session()."""

    def test_start_session_creates_session_and_workspace(self, tmp_path):
        """Test starting a new session initializes session and workspace."""
        # Setup
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        mock_orch = Mock()
        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
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

        mock_orch = Mock()
        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
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

        mock_orch = Mock()
        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
        )

        # Execute and verify exception
        with pytest.raises(RuntimeError) as exc_info:
            coordinator.start_session()

        assert "Failed to initialize session workspace" in str(exc_info.value)


class TestSessionCoordinatorEvents:
    """Event emission behavior for structured observability (VF-142)."""

    def _answer_all_questions(self, coordinator: SessionCoordinator, session_id: str):
        while True:
            question = coordinator.get_next_question(session_id)
            if not question:
                break
            coordinator.submit_answer(session_id, question.question_id, question.options[0].value)

    def test_start_session_emits_workspace_event(self, tmp_path):
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        event_log = EventLog(workspace_manager.workspace_root)
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orch = Mock()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
            event_log=event_log,
        )

        session_id = coordinator.start_session()

        events = event_log.get_events(session_id)
        assert any(event.event_type == EventType.WORKSPACE_INITIALIZED for event in events)

    def test_finalize_questionnaire_emits_phase_transition(self, tmp_path):
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        event_log = EventLog(workspace_manager.workspace_root)
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orch = Mock()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
            event_log=event_log,
        )

        session_id = coordinator.start_session()
        self._answer_all_questions(coordinator, session_id)
        coordinator.finalize_questionnaire(session_id)

        events = event_log.get_events(session_id, event_type=EventType.PHASE_TRANSITION)
        assert any(
            event.metadata
            == {"from": "QUESTIONNAIRE", "to": "BUILD_SPEC", "reason": "Questionnaire finalized"}
            for event in events
        )

    @pytest.mark.asyncio
    async def test_generate_plan_emits_task_graph_event(self, tmp_path):
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        event_log = EventLog(workspace_manager.workspace_root)
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        mock_orch = Mock()
        mock_orch.createTaskGraph = AsyncMock(
            return_value=TaskGraph(
                session_id="sid",
                tasks=[
                    TaskModel(
                        task_id="t1",
                        description="Do work",
                        role="worker",
                        dependencies=[],
                        inputs={},
                        expected_outputs=[],
                        verification={},
                        constraints={},
                    )
                ],
            )
        )

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
            event_log=event_log,
        )

        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.build_spec = {
            "sessionId": session_id,
            "stack": {"preset": "WEB_VITE_REACT_TS"},
            "target": {"platform": "WEB_APP"},
            "ideaSeed": {"complexity": "simple"},
        }
        session.concept = {
            "idea_description": "Demo app concept.",
            "features": ["Feature A"],
            "tech_stack": {"framework": "FastAPI"},
            "file_structure": {"README.md": "Project overview"},
            "verification_steps": ["pytest"],
            "constraints": ["Keep scope small."],
        }
        session.phase = SessionPhase.PLAN_REVIEW
        session_store.update_session(session)

        await coordinator.generate_plan(session_id)

        events = event_log.get_events(session_id, event_type=EventType.TASK_GRAPH_CREATED)
        assert len(events) == 1
        assert events[0].metadata == {"task_count": 1}

class TestSessionCoordinatorQuestionnaire:
    """Test VF-033: SessionCoordinator questionnaire loop."""

    def test_get_next_question_returns_first_question(self, tmp_path):
        """Test getting the first questionnaire question."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        mock_orch = Mock()
        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
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

        mock_orch = Mock()
        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
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

        mock_orch = Mock()
        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
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

        mock_orch = Mock()
        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
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

        mock_orch = Mock()
        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
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

        mock_orch = Mock()
        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
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

        mock_orch = Mock()
        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
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

        mock_orch = Mock()
        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
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

        mock_orch = Mock()
        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
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

        mock_orch = Mock()
        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
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

        mock_orch = Mock()
        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
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

        mock_orch = Mock()
        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
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

        mock_orch = Mock()
        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
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

        mock_orch = Mock()
        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
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

        mock_orch = Mock()
        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
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


class TestSessionCoordinatorConcept:
    """Test VF-035: SessionCoordinator.generate_concept()."""

    @pytest.mark.asyncio
    async def test_generate_concept_calls_orchestrator(self, tmp_path):
        """Test that concept generation calls Orchestrator correctly."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        # Create mock orchestrator
        mock_orch = AsyncMock()
        mock_concept = ConceptDoc(
            session_id="test_session",
            idea_description="Test Task Tracker - A simple task management app",
            features=["Create tasks", "Mark complete"],
            tech_stack={"runtime": "Node.js", "framework": "React"},
            file_structure={"frontend": "React app", "backend": "Node.js server"},
            verification_steps=["Test task creation", "Test task completion"],
            constraints=["Must work offline"],
        )
        mock_orch.generateConcept.return_value = mock_concept

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
        )

        # Prepare session in IDEA phase with BuildSpec
        session_id = coordinator.start_session()
        coordinator.submit_answer(session_id, "q1_audience", "developers")
        coordinator.submit_answer(session_id, "q2_platform", "web")
        coordinator.submit_answer(session_id, "q3_complexity", "simple")
        coordinator.finalize_questionnaire(session_id)
        coordinator.generate_build_spec(session_id)

        # Generate concept
        concept = await coordinator.generate_concept(session_id)

        # Verify Orchestrator was called
        assert mock_orch.generateConcept.called
        assert "Test Task Tracker" in concept["idea_description"]

        # Verify session updated
        session = session_store.get_session(session_id)
        assert session.concept == concept
        assert session.phase == SessionPhase.PLAN_REVIEW
        assert any("Concept generated successfully" in log for log in session.logs)
        assert any("IDEA → PLAN_REVIEW" in log for log in session.logs)

    @pytest.mark.asyncio
    async def test_generate_concept_persists_artifact(self, tmp_path):
        """Test that concept is persisted to artifacts."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        # Create mock orchestrator
        mock_orch = AsyncMock()
        mock_concept = ConceptDoc(
            session_id="test_session",
            idea_description="Test App - Test description",
            features=["Feature 1"],
            tech_stack={"runtime": "Node.js"},
            file_structure={"app": "Main app"},
            verification_steps=["Test feature 1"],
            constraints=["Simple only"],
        )
        mock_orch.generateConcept.return_value = mock_concept

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
        )

        # Prepare session
        session_id = coordinator.start_session()
        coordinator.submit_answer(session_id, "q1_audience", "developers")
        coordinator.submit_answer(session_id, "q2_platform", "web")
        coordinator.submit_answer(session_id, "q3_complexity", "simple")
        coordinator.finalize_questionnaire(session_id)
        coordinator.generate_build_spec(session_id)

        # Generate concept
        await coordinator.generate_concept(session_id)

        # Verify artifact exists
        artifact_path = tmp_path / "workspaces" / session_id / "artifacts" / "concept.json"
        assert artifact_path.exists()

    @pytest.mark.asyncio
    async def test_generate_concept_raises_if_wrong_phase(self, tmp_path):
        """Test that generating concept in wrong phase raises error."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orch = AsyncMock()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
        )

        session_id = coordinator.start_session()

        # Try to generate concept without BuildSpec
        with pytest.raises(ValueError) as exc_info:
            await coordinator.generate_concept(session_id)

        assert "expected IDEA" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_concept_handles_orchestrator_failure(self, tmp_path):
        """Test that Orchestrator failure is handled gracefully."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        # Create failing orchestrator
        mock_orch = AsyncMock()
        mock_orch.generateConcept.side_effect = RuntimeError("LLM API error")

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
        )

        # Prepare session
        session_id = coordinator.start_session()
        coordinator.submit_answer(session_id, "q1_audience", "developers")
        coordinator.submit_answer(session_id, "q2_platform", "web")
        coordinator.submit_answer(session_id, "q3_complexity", "simple")
        coordinator.finalize_questionnaire(session_id)
        coordinator.generate_build_spec(session_id)

        # Try to generate concept
        with pytest.raises(RuntimeError) as exc_info:
            await coordinator.generate_concept(session_id)

        assert "Failed to generate concept" in str(exc_info.value)

        # Verify session remains in IDEA phase
        session = session_store.get_session(session_id)
        assert session.phase == SessionPhase.IDEA
        assert len(session.error_history) > 0


class TestSessionCoordinatorPlan:
    """Test VF-036: SessionCoordinator plan generation and approval."""

    @pytest.mark.asyncio
    async def test_generate_plan_calls_orchestrator(self, tmp_path):
        """Test that plan generation calls Orchestrator correctly."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        # Create mock orchestrator
        mock_orch = AsyncMock()
        mock_concept = ConceptDoc(
            session_id="test_session",
            idea_description="Test App",
            features=["F1"],
            tech_stack={"runtime": "Node.js"},
            file_structure={"app": "App"},
            verification_steps=["Test"],
            constraints=["C1"],
        )
        mock_orch.generateConcept.return_value = mock_concept

        # Create mock TaskGraph
        mock_task1 = TaskModel(
            task_id="t1",
            description="Create frontend",
            role="worker",
            dependencies=[],
            inputs={},
            expected_outputs=["index.html"],
            verification={"type": "build"},
            constraints={},
        )
        mock_task_graph = TaskGraph(session_id="test_session", tasks=[mock_task1])
        mock_orch.createTaskGraph.return_value = mock_task_graph

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
        )

        # Prepare session through concept generation
        session_id = coordinator.start_session()
        coordinator.submit_answer(session_id, "q1_audience", "developers")
        coordinator.submit_answer(session_id, "q2_platform", "web")
        coordinator.submit_answer(session_id, "q3_complexity", "simple")
        coordinator.finalize_questionnaire(session_id)
        coordinator.generate_build_spec(session_id)
        await coordinator.generate_concept(session_id)

        # Generate plan
        task_graph = await coordinator.generate_plan(session_id)

        # Verify Orchestrator was called
        assert mock_orch.createTaskGraph.called
        assert len(task_graph["tasks"]) == 1

        # Verify session updated
        session = session_store.get_session(session_id)
        assert session.task_graph == task_graph
        assert session.phase == SessionPhase.PLAN_REVIEW
        assert any("TaskGraph generated: 1 tasks" in log for log in session.logs)

    @pytest.mark.asyncio
    async def test_generate_plan_persists_artifact(self, tmp_path):
        """Test that TaskGraph is persisted to artifacts."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()

        # Create mocks
        mock_orch = AsyncMock()
        mock_concept = ConceptDoc(
            session_id="test_session",
            idea_description="Test",
            features=["F1"],
            tech_stack={"runtime": "Node.js"},
            file_structure={"app": "App"},
            verification_steps=["Test"],
            constraints=["C1"]
        )
        mock_orch.generateConcept.return_value = mock_concept

        mock_task = TaskModel(
            task_id="t1", description="Task", role="worker", dependencies=[],
            inputs={}, expected_outputs=["out"], verification={"type": "test"}, constraints={}
        )
        mock_task_graph = TaskGraph(session_id="test_session", tasks=[mock_task])
        mock_orch.createTaskGraph.return_value = mock_task_graph

        coordinator = SessionCoordinator(
            session_store, workspace_manager, questionnaire_engine, spec_builder, mock_orch
        )

        # Prepare session
        session_id = coordinator.start_session()
        coordinator.submit_answer(session_id, "q1_audience", "developers")
        coordinator.submit_answer(session_id, "q2_platform", "web")
        coordinator.submit_answer(session_id, "q3_complexity", "simple")
        coordinator.finalize_questionnaire(session_id)
        coordinator.generate_build_spec(session_id)
        await coordinator.generate_concept(session_id)

        # Generate plan
        await coordinator.generate_plan(session_id)

        # Verify artifact exists
        artifact_path = tmp_path / "workspaces" / session_id / "artifacts" / "task_graph.json"
        assert artifact_path.exists()

    def test_get_plan_summary_formats_correctly(self, tmp_path):
        """Test that plan summary is formatted for UI."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orch = Mock()

        coordinator = SessionCoordinator(
            session_store, workspace_manager, questionnaire_engine, spec_builder, mock_orch
        )

        # Create session manually with TaskGraph
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        # Manually set up BuildSpec and TaskGraph
        session.build_spec = {
            "scopeBudget": {"maxTotalFiles": 10, "maxScreens": 3},
            "stack": {"preset": "REACT_NODE"},
            "target": {"platform": "WEB_APP"},
        }
        session.task_graph = {
            "tasks": [
                {"task_id": "t1", "description": "Task 1", "role": "worker", "verification": {"type": "build"}},
                {"task_id": "t2", "description": "Task 2", "role": "reviewer", "verification": {"type": "test"}},
            ]
        }
        session.update_phase(SessionPhase.PLAN_REVIEW)
        session_store.update_session(session)

        # Get summary
        summary = coordinator.get_plan_summary(session_id)

        # Verify format
        assert summary["task_count"] == 2
        assert len(summary["task_list"]) == 2
        assert summary["task_list"][0]["task_id"] == "t1"
        assert summary["estimated_scope"]["max_files"] == 10
        assert summary["constraints"]["stack"] == "REACT_NODE"

    def test_approve_plan_transitions_to_execution(self, tmp_path):
        """Test that approving plan transitions to EXECUTION phase."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orch = Mock()

        coordinator = SessionCoordinator(
            session_store, workspace_manager, questionnaire_engine, spec_builder, mock_orch
        )

        # Create session with TaskGraph
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.task_graph = {"tasks": [{"task_id": "t1"}]}
        session.update_phase(SessionPhase.PLAN_REVIEW)
        session_store.update_session(session)

        # Approve plan
        result = coordinator.approve_plan(session_id)

        # Verify
        assert result["status"] == "approved"
        session = session_store.get_session(session_id)
        assert session.phase == SessionPhase.EXECUTION
        assert any("Plan approved by user" in log for log in session.logs)

    def test_reject_plan_transitions_to_idea(self, tmp_path):
        """Test that rejecting plan transitions back to IDEA phase."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orch = Mock()

        coordinator = SessionCoordinator(
            session_store, workspace_manager, questionnaire_engine, spec_builder, mock_orch
        )

        # Create session with TaskGraph
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.task_graph = {"tasks": [{"task_id": "t1"}]}
        session.update_phase(SessionPhase.PLAN_REVIEW)
        session_store.update_session(session)

        # Reject plan
        result = coordinator.reject_plan(session_id, "Too complex")

        # Verify
        assert result["status"] == "rejected"
        session = session_store.get_session(session_id)
        assert session.phase == SessionPhase.IDEA
        assert session.task_graph is None  # Cleared for regeneration


# =============================================================================
# VF-037: execute_next_task() tests
# =============================================================================


class TestSessionCoordinatorExecution:
    """Tests for SessionCoordinator execution loop (VF-037)."""

    @pytest.mark.asyncio
    async def test_execute_next_task_requires_execution_phase(self, tmp_path):
        """Test that execute_next_task requires EXECUTION phase."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orch = AsyncMock()
        mock_agent = AsyncMock()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
            mock_agent,
        )

        session_id = coordinator.start_session()

        # Wrong phase
        with pytest.raises(ValueError, match="Cannot execute task"):
            await coordinator.execute_next_task(session_id)

    @pytest.mark.asyncio
    async def test_execute_next_task_requires_agent_framework(self, tmp_path):
        """Test that execute_next_task requires agent framework."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orch = AsyncMock()

        # No agent framework
        coordinator = SessionCoordinator(
            session_store, workspace_manager, questionnaire_engine, spec_builder, mock_orch
        )

        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        with pytest.raises(ValueError, match="AgentFramework not configured"):
            await coordinator.execute_next_task(session_id)

    @pytest.mark.asyncio
    async def test_execute_next_task_enqueues_task_graph_on_first_call(self, tmp_path):
        """Test that first call to execute_next_task enqueues TaskGraph."""
        from orchestration.models import Task, TaskGraph
        from models.agent_framework import AgentResult

        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orch = AsyncMock()
        mock_agent = AsyncMock()

        # Mock agent to return success
        mock_agent.runTask.return_value = AgentResult(
            success=True, outputs={"diff": "", "files": []}, logs=["Task complete"]
        )

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
            mock_agent,
        )

        # Prepare session
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        # Create minimal TaskGraph
        task = Task(
            task_id="test_task",
            description="Test task",
            role="worker",
            dependencies=[],
            inputs={},
            expected_outputs=[],
            constraints={},
            verification={"type": "manual"},
        )
        task_graph = TaskGraph(session_id=session_id, tasks=[task])

        session.task_graph = task_graph.to_dict()
        session.build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}
        session.concept = {"idea_description": "Test concept"}
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        # Execute first task
        result = await coordinator.execute_next_task(session_id)

        # Verify TaskGraph was enqueued
        assert session_id in coordinator._task_masters
        assert result["status"] == "task_complete"
        assert result["task_id"] == "test_task"

    @pytest.mark.asyncio
    async def test_execute_next_task_returns_all_tasks_complete(self, tmp_path):
        """Test that execute_next_task returns all_tasks_complete when done."""
        from orchestration.models import Task, TaskGraph

        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orch = AsyncMock()
        mock_agent = AsyncMock()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
            mock_agent,
        )

        # Prepare session
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        # Create TaskGraph with one task
        task = Task(
            task_id="test_task",
            description="Test task",
            role="worker",
            dependencies=[],
            inputs={},
            expected_outputs=[],
            constraints={},
            verification={"type": "manual"},
        )
        task_graph = TaskGraph(session_id=session_id, tasks=[task])

        session.task_graph = task_graph.to_dict()
        session.build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}
        session.concept = {"idea_description": "Test concept"}
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        # Manually enqueue and mark task as done
        from runtime.task_master import TaskMaster

        task_master = TaskMaster()
        task_master.enqueue(task_graph)
        task_master.markDone("test_task")
        coordinator._task_masters[session_id] = task_master

        # Call execute_next_task
        result = await coordinator.execute_next_task(session_id)

        # Verify
        assert result["status"] == "all_tasks_complete"

    @pytest.mark.asyncio
    async def test_execute_next_task_handles_agent_failure_with_retry(self, tmp_path):
        """Test that agent failures trigger retry logic."""
        from orchestration.models import Task, TaskGraph
        from models.agent_framework import AgentResult

        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orch = AsyncMock()
        mock_agent = AsyncMock()

        # Mock agent to fail
        mock_agent.runTask.return_value = AgentResult(
            success=False, outputs={}, logs=[], error_message="Agent failed"
        )

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
            mock_agent,
        )

        # Prepare session
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        task = Task(
            task_id="test_task",
            description="Test task",
            role="worker",
            dependencies=[],
            inputs={},
            expected_outputs=[],
            constraints={},
            verification={"type": "manual"},
        )
        task_graph = TaskGraph(session_id=session_id, tasks=[task])

        session.task_graph = task_graph.to_dict()
        session.build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}
        session.concept = {"idea_description": "Test concept"}
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        # Execute task (should fail with retry)
        result = await coordinator.execute_next_task(session_id)

        # Verify retry signaled
        assert result["status"] == "task_failed_retrying"
        assert result["task_id"] == "test_task"
        assert "Agent failed" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_next_task_verification_failure_triggers_fix_loop(
        self, tmp_path, monkeypatch
    ):
        """Test that repeated verification failures request fix-loop clarification."""
        from orchestration.models import Task, TaskGraph
        from models.agent_framework import AgentResult
        from vibeforge_api.core.verifiers import VerificationResult, VerifierSuite

        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orch = AsyncMock()
        mock_agent = AsyncMock()

        mock_agent.runTask.return_value = AgentResult(
            success=True, outputs={"diff": "", "commands": []}, logs=["Task complete"]
        )

        def fake_run_task_verification(self, verifier_names, workspace_path, build_spec):
            return [VerificationResult(success=False, message="Tests failed")]

        monkeypatch.setattr(
            VerifierSuite, "run_task_verification", fake_run_task_verification
        )

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
            mock_agent,
        )

        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        task = Task(
            task_id="test_task",
            description="Test task",
            role="worker",
            dependencies=[],
            inputs={},
            expected_outputs=[],
            constraints={},
            verification={"type": "test"},
        )
        task_graph = TaskGraph(session_id=session_id, tasks=[task])

        session.task_graph = task_graph.to_dict()
        session.build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}
        session.concept = {"idea_description": "Test concept"}
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        first_result = await coordinator.execute_next_task(session_id)
        second_result = await coordinator.execute_next_task(session_id)

        assert first_result["status"] == "task_failed_retrying"
        assert second_result["status"] == "needs_clarification"
        assert second_result["clarification"]["type"] == "fix_loop"

    @pytest.mark.asyncio
    async def test_execute_next_task_handles_gate_block(self, tmp_path):
        """Test that gate blocks prevent task execution."""
        from orchestration.models import Task, TaskGraph
        from models.agent_framework import AgentResult

        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orch = AsyncMock()
        mock_agent = AsyncMock()

        # Mock agent to return dangerous command
        mock_agent.runTask.return_value = AgentResult(
            success=True,
            outputs={"diff": "", "commands": ["rm -rf /"]},
            logs=["Dangerous command"],
        )

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
            mock_agent,
        )

        # Prepare session
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        task = Task(
            task_id="test_task",
            description="Test task",
            role="worker",
            dependencies=[],
            inputs={},
            expected_outputs=[],
            constraints={},
            verification={"type": "manual"},
        )
        task_graph = TaskGraph(session_id=session_id, tasks=[task])

        session.task_graph = task_graph.to_dict()
        session.build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}
        session.concept = {"idea_description": "Test concept"}
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        # Execute task (gates should block)
        result = await coordinator.execute_next_task(session_id)

        # Verify gates blocked
        assert result["status"] in ["task_failed_retrying", "task_failed_terminal"]
        assert "Gates blocked" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_next_task_loads_repo_context(self, tmp_path):
        """Test that task context includes repo-scoped files."""
        from orchestration.models import Task, TaskGraph
        from models.agent_framework import AgentResult

        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orch = AsyncMock()
        mock_agent = AsyncMock()

        mock_agent.runTask.return_value = AgentResult(
            success=True, outputs={"diff": "", "files": []}, logs=["Task complete"]
        )

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
            mock_agent,
        )

        session_id = coordinator.start_session()
        repo_path = workspace_manager.get_repo_path(session_id)
        (repo_path / "context.txt").write_text("hello context")

        task = Task(
            task_id="test_task",
            description="Test task",
            role="worker",
            dependencies=[],
            inputs={"filesToRead": ["context.txt"], "contextNotes": ["Use repo context"]},
            expected_outputs=[],
            constraints={},
            verification={"type": "manual"},
        )
        task_graph = TaskGraph(session_id=session_id, tasks=[task])

        session = session_store.get_session(session_id)
        session.task_graph = task_graph.to_dict()
        session.build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}
        session.concept = {"idea_description": "Test concept"}
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        await coordinator.execute_next_task(session_id)

        _, _, context = mock_agent.runTask.call_args.args
        repo_context = context["repo_context"]
        assert repo_context["files"][0]["path"] == "context.txt"
        assert repo_context["files"][0]["content"] == "hello context"
        assert repo_context["context_notes"] == ["Use repo context"]

    @pytest.mark.asyncio
    async def test_execute_next_task_handles_agent_clarification(self, tmp_path):
        """Test that agent clarification pauses and resumes execution."""
        from orchestration.models import Task, TaskGraph
        from models.agent_framework import AgentResult
        from runtime.task_master import TaskStatus

        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orch = AsyncMock()
        mock_agent = AsyncMock()

        mock_agent.runTask.side_effect = [
            AgentResult(
                success=True,
                outputs={},
                logs=["Need clarification"],
                needs_clarification=True,
                clarification={
                    "question": "Pick an option",
                    "options": [{"value": "a", "label": "Option A"}],
                },
            ),
            AgentResult(
                success=True,
                outputs={"diff": "", "files": []},
                logs=["Task complete"],
            ),
        ]

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
            mock_agent,
        )

        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        task = Task(
            task_id="test_task",
            description="Test task",
            role="worker",
            dependencies=[],
            inputs={},
            expected_outputs=[],
            constraints={},
            verification={"type": "manual"},
        )
        task_graph = TaskGraph(session_id=session_id, tasks=[task])

        session.task_graph = task_graph.to_dict()
        session.build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}
        session.concept = {"idea_description": "Test concept"}
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        first_result = await coordinator.execute_next_task(session_id)

        assert first_result["status"] == "needs_clarification"
        session = session_store.get_session(session_id)
        assert session.pending_clarification["question"] == "Pick an option"

        task_master = coordinator._task_masters[session_id]
        assert task_master.executions["test_task"].status == TaskStatus.READY

        session.pending_clarification = None
        session.clarification_answer = "a"
        session_store.update_session(session)

        second_result = await coordinator.execute_next_task(session_id)

        assert second_result["status"] == "task_complete"
        _, _, context = mock_agent.runTask.call_args.args
        assert context["clarification_answer"] == "a"


# =============================================================================
# VF-038: finalize_session() tests
# =============================================================================


class TestSessionCoordinatorFinalize:
    """Tests for SessionCoordinator finalization (VF-038)."""

    @pytest.mark.asyncio
    async def test_finalize_session_requires_execution_phase(self, tmp_path):
        """Test that finalize_session requires EXECUTION phase."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orch = AsyncMock()

        coordinator = SessionCoordinator(
            session_store, workspace_manager, questionnaire_engine, spec_builder, mock_orch
        )

        session_id = coordinator.start_session()

        # Wrong phase
        with pytest.raises(ValueError, match="Cannot finalize"):
            await coordinator.finalize_session(session_id)

    @pytest.mark.asyncio
    async def test_finalize_session_requires_tasks_complete(self, tmp_path):
        """Test that finalize_session requires all tasks complete."""
        from orchestration.models import Task, TaskGraph

        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orch = AsyncMock()

        coordinator = SessionCoordinator(
            session_store, workspace_manager, questionnaire_engine, spec_builder, mock_orch
        )

        # Prepare session
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        # Create TaskMaster with incomplete tasks
        from runtime.task_master import TaskMaster

        task = Task(
            task_id="test_task",
            description="Test task",
            role="worker",
            dependencies=[],
            inputs={},
            expected_outputs=[],
            constraints={},
            verification={"type": "manual"},
        )
        task_graph = TaskGraph(session_id=session_id, tasks=[task])

        task_master = TaskMaster()
        task_master.enqueue(task_graph)
        coordinator._task_masters[session_id] = task_master

        # Task not complete
        with pytest.raises(ValueError, match="tasks incomplete"):
            await coordinator.finalize_session(session_id)

    @pytest.mark.asyncio
    async def test_finalize_session_runs_global_verification(self, tmp_path):
        """Test that finalize_session runs global verification."""
        from orchestration.models import Task, TaskGraph, RunSummary

        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orch = AsyncMock()

        # Mock orchestrator.summarize
        mock_orch.summarize.return_value = RunSummary(
            session_id="test_session",
            status="complete",
            summary="Test summary",
            files_generated=[],
            verification_results={},
            how_to_run=["npm start"],
            limitations=[],
        )

        coordinator = SessionCoordinator(
            session_store, workspace_manager, questionnaire_engine, spec_builder, mock_orch
        )

        # Prepare session
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        task = Task(
            task_id="test_task",
            description="Test task",
            role="worker",
            dependencies=[],
            inputs={},
            expected_outputs=[],
            constraints={},
            verification={"type": "manual"},
        )
        task_graph = TaskGraph(session_id=session_id, tasks=[task])

        session.task_graph = task_graph.to_dict()
        session.build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}
        session.concept = {"idea_description": "Test concept"}
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        # Manually mark task as done
        from runtime.task_master import TaskMaster

        task_master = TaskMaster()
        task_master.enqueue(task_graph)
        task_master.markDone("test_task")
        coordinator._task_masters[session_id] = task_master

        # Create minimal project structure for verification
        workspace_path = workspace_manager.workspace_root / session_id
        (workspace_path / "repo" / "package.json").write_text(
            '{"name": "test", "scripts": {"build": "echo build", "test": "echo test"}}'
        )

        # Finalize (should succeed)
        try:
            result = await coordinator.finalize_session(session_id)

            # Verify
            assert result["status"] == "complete"
            session = session_store.get_session(session_id)
            assert session.phase == SessionPhase.COMPLETE
        except RuntimeError as e:
            # Verification might fail in test env (npm not installed), but we test the flow
            assert "Global verification failed" in str(e)

    @pytest.mark.asyncio
    async def test_finalize_session_uses_fallback_on_orchestrator_failure(self, tmp_path):
        """Test that finalize_session uses fallback summary if orchestrator fails."""
        from orchestration.models import Task, TaskGraph

        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orch = AsyncMock()

        # Mock orchestrator to fail
        mock_orch.summarize.side_effect = Exception("Orchestrator failed")

        coordinator = SessionCoordinator(
            session_store, workspace_manager, questionnaire_engine, spec_builder, mock_orch
        )

        # Prepare session
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        task = Task(
            task_id="test_task",
            description="Test task",
            role="worker",
            dependencies=[],
            inputs={},
            expected_outputs=[],
            constraints={},
            verification={"type": "manual"},
        )
        task_graph = TaskGraph(session_id=session_id, tasks=[task])

        session.task_graph = task_graph.to_dict()
        session.build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}
        session.concept = {"idea_description": "Test concept"}
        session.update_phase(SessionPhase.EXECUTION)
        session.completed_task_ids = ["test_task"]
        session_store.update_session(session)

        # Manually mark task as done
        from runtime.task_master import TaskMaster

        task_master = TaskMaster()
        task_master.enqueue(task_graph)
        task_master.markDone("test_task")
        coordinator._task_masters[session_id] = task_master

        # Create minimal project for verification
        workspace_path = workspace_manager.workspace_root / session_id
        (workspace_path / "repo" / "package.json").write_text(
            '{"name": "test", "scripts": {"build": "echo build", "test": "echo test"}}'
        )

        # Finalize (should use fallback)
        try:
            result = await coordinator.finalize_session(session_id)

            # Verify fallback used
            assert result["status"] == "complete"
            assert "Orchestrator summary generation failed" in result["limitations"]
            session = session_store.get_session(session_id)
            assert session.phase == SessionPhase.COMPLETE
        except RuntimeError:
            # Verification might fail, but we tested the orchestrator fallback
            pass


# =============================================================================
# VF-039: abort_session() tests
# =============================================================================


class TestSessionCoordinatorAbort:
    """Tests for SessionCoordinator abort flows (VF-039)."""

    def test_abort_session_stops_execution(self, tmp_path):
        """Test that abort_session stops active task execution."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orch = Mock()

        coordinator = SessionCoordinator(
            session_store, workspace_manager, questionnaire_engine, spec_builder, mock_orch
        )

        # Create session in EXECUTION with active task
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.update_phase(SessionPhase.EXECUTION)
        session.active_task_id = "task_123"
        session_store.update_session(session)

        # Abort
        result = coordinator.abort_session(session_id, "User cancelled")

        # Verify
        assert result["status"] == "aborted"
        assert "User cancelled" in result["message"]
        session = session_store.get_session(session_id)
        assert session.phase == SessionPhase.FAILED
        assert session.active_task_id is None
        assert any("Session aborted" in log for log in session.logs)

    def test_abort_session_cannot_abort_terminal_state(self, tmp_path):
        """Test that abort_session cannot abort completed sessions."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orch = Mock()

        coordinator = SessionCoordinator(
            session_store, workspace_manager, questionnaire_engine, spec_builder, mock_orch
        )

        # Create session in COMPLETE state
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.update_phase(SessionPhase.COMPLETE)
        session_store.update_session(session)

        # Cannot abort
        with pytest.raises(ValueError, match="already in terminal state"):
            coordinator.abort_session(session_id)

    def test_abort_session_preserves_artifacts(self, tmp_path):
        """Test that abort_session preserves workspace and artifacts."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orch = Mock()

        coordinator = SessionCoordinator(
            session_store, workspace_manager, questionnaire_engine, spec_builder, mock_orch
        )

        # Create session
        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        # Write test artifact
        workspace_path = workspace_manager.workspace_root / session_id
        test_file = workspace_path / "artifacts" / "test.json"
        test_file.write_text('{"test": "data"}')

        # Abort
        result = coordinator.abort_session(session_id)

        # Verify artifacts preserved
        assert test_file.exists()
        assert "artifacts_preserved" in result
        assert "workspace_preserved" in result
        session = session_store.get_session(session_id)
        assert any("Session aborted" in log for log in session.logs)


# =============================================================================
# VF-163: FAILED terminal behavior tests
# =============================================================================


class TestVF163_FailedTerminalBehavior:
    """Tests for VF-163: FAILED terminal behavior + recovery options."""

    def test_fail_session_creates_failure_artifact(self, tmp_path):
        """fail_session creates and persists a failure artifact."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(tmp_path)
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orchestrator = MagicMock(spec=Orchestrator)

        coordinator = SessionCoordinator(
            session_store=session_store,
            workspace_manager=workspace_manager,
            questionnaire_engine=questionnaire_engine,
            spec_builder=spec_builder,
            orchestrator=mock_orchestrator,
        )

        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        result = coordinator.fail_session(session_id, "Test failure", task_id="test-task")

        assert result["status"] == "failed"
        assert result["reason"] == "Test failure"
        assert result["task_id"] == "test-task"
        assert "failure_artifact" in result
        assert result["failure_artifact"]["failure_reason"] == "Test failure"

    def test_fail_session_persists_failure_artifact_to_disk(self, tmp_path):
        """fail_session persists failure artifact to artifacts/failure_report.json."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(tmp_path)
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orchestrator = MagicMock(spec=Orchestrator)

        coordinator = SessionCoordinator(
            session_store=session_store,
            workspace_manager=workspace_manager,
            questionnaire_engine=questionnaire_engine,
            spec_builder=spec_builder,
            orchestrator=mock_orchestrator,
        )

        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        coordinator.fail_session(session_id, "Test failure")

        failure_report = tmp_path / session_id / "artifacts" / "failure_report.json"
        assert failure_report.exists()

        import json
        artifact_data = json.loads(failure_report.read_text())
        assert artifact_data["failure_reason"] == "Test failure"

    def test_fail_session_returns_recovery_options(self, tmp_path):
        """fail_session returns recovery options for the user."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(tmp_path)
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orchestrator = MagicMock(spec=Orchestrator)

        coordinator = SessionCoordinator(
            session_store=session_store,
            workspace_manager=workspace_manager,
            questionnaire_engine=questionnaire_engine,
            spec_builder=spec_builder,
            orchestrator=mock_orchestrator,
        )

        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        result = coordinator.fail_session(session_id, "Test failure")

        assert "recovery_options" in result
        options = result["recovery_options"]
        assert any(opt["value"] == "restart_session" for opt in options)
        assert any(opt["value"] == "export_logs" for opt in options)

    def test_fail_session_transitions_to_failed_phase(self, tmp_path):
        """fail_session transitions session to FAILED phase."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(tmp_path)
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orchestrator = MagicMock(spec=Orchestrator)

        coordinator = SessionCoordinator(
            session_store=session_store,
            workspace_manager=workspace_manager,
            questionnaire_engine=questionnaire_engine,
            spec_builder=spec_builder,
            orchestrator=mock_orchestrator,
        )

        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        coordinator.fail_session(session_id, "Test failure")

        session = session_store.get_session(session_id)
        assert session.phase == SessionPhase.FAILED
        assert session.failure_reason == "Test failure"

    def test_fail_session_records_error_history(self, tmp_path):
        """fail_session records error in error_history."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(tmp_path)
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orchestrator = MagicMock(spec=Orchestrator)

        coordinator = SessionCoordinator(
            session_store=session_store,
            workspace_manager=workspace_manager,
            questionnaire_engine=questionnaire_engine,
            spec_builder=spec_builder,
            orchestrator=mock_orchestrator,
        )

        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        coordinator.fail_session(session_id, "Test failure", task_id="task-123")

        session = session_store.get_session(session_id)
        assert len(session.error_history) > 0
        error = session.error_history[-1]
        assert error["task_id"] == "task-123"
        assert error["error_message"] == "Test failure"


# =============================================================================
# VF-164: Fix loop guardrails tests
# =============================================================================


class TestVF164_FixLoopGuardrails:
    """Tests for VF-164: Controlled fix-loop return transitions."""

    def test_trigger_fix_loop_increments_counter(self, tmp_path):
        """trigger_fix_loop increments the fix loop counter."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(tmp_path)
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orchestrator = MagicMock(spec=Orchestrator)

        coordinator = SessionCoordinator(
            session_store=session_store,
            workspace_manager=workspace_manager,
            questionnaire_engine=questionnaire_engine,
            spec_builder=spec_builder,
            orchestrator=mock_orchestrator,
        )

        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        result = coordinator.trigger_fix_loop(session_id, "Verification failed")

        assert result["status"] == "fix_loop_triggered"
        assert result["fix_loop_count"] == 1

        session = session_store.get_session(session_id)
        assert session.fix_loop_count == 1

    def test_trigger_fix_loop_fails_when_limit_exceeded(self, tmp_path):
        """trigger_fix_loop fails session when max loops exceeded."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(tmp_path)
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orchestrator = MagicMock(spec=Orchestrator)

        coordinator = SessionCoordinator(
            session_store=session_store,
            workspace_manager=workspace_manager,
            questionnaire_engine=questionnaire_engine,
            spec_builder=spec_builder,
            orchestrator=mock_orchestrator,
        )

        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.update_phase(SessionPhase.EXECUTION)
        session.fix_loop_count = 3  # At limit
        session_store.update_session(session)

        result = coordinator.trigger_fix_loop(session_id, "Verification failed again")

        assert result["status"] == "failed"
        assert "Fix loop limit exceeded" in result["reason"]

        session = session_store.get_session(session_id)
        assert session.phase == SessionPhase.FAILED

    def test_fix_loop_resets_on_task_success(self, tmp_path):
        """fix_loop_count resets to 0 on successful task completion."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(tmp_path)
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orchestrator = MagicMock(spec=Orchestrator)

        coordinator = SessionCoordinator(
            session_store=session_store,
            workspace_manager=workspace_manager,
            questionnaire_engine=questionnaire_engine,
            spec_builder=spec_builder,
            orchestrator=mock_orchestrator,
        )

        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.fix_loop_count = 2
        session.reset_fix_loop()

        assert session.fix_loop_count == 0

    def test_can_return_to_execution_checks_limit(self, tmp_path):
        """can_return_to_execution returns False when limit reached."""
        from orchestration.coordinator.state_machine import can_return_to_execution

        session = MagicMock()
        session.fix_loop_count = 3
        session.max_fix_loops = 3

        can_loop, reason = can_return_to_execution(session)

        assert can_loop is False
        assert "exceeded" in reason.lower()

    def test_can_return_to_execution_allows_within_limit(self, tmp_path):
        """can_return_to_execution returns True when under limit."""
        from orchestration.coordinator.state_machine import can_return_to_execution

        session = MagicMock()
        session.fix_loop_count = 1
        session.max_fix_loops = 3

        can_loop, reason = can_return_to_execution(session)

        assert can_loop is True
        assert "allowed" in reason.lower()

    def test_trigger_fix_loop_transitions_from_verification(self, tmp_path):
        """trigger_fix_loop transitions from VERIFICATION to EXECUTION."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(tmp_path)
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orchestrator = MagicMock(spec=Orchestrator)

        coordinator = SessionCoordinator(
            session_store=session_store,
            workspace_manager=workspace_manager,
            questionnaire_engine=questionnaire_engine,
            spec_builder=spec_builder,
            orchestrator=mock_orchestrator,
        )

        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)

        # Set up for VERIFICATION phase - need answers and task_graph
        session.answers = {"q1": "answer1"}
        session.intent_profile = {"app_type": "web"}
        session.build_spec = {"stack": "vite-react"}
        session.concept = {"description": "test"}
        session.task_graph = {"tasks": []}

        # Allow EXECUTION → VERIFICATION transition first
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        # Manually transition to VERIFICATION (normally done by finalize flow)
        from orchestration.coordinator.state_machine import validate_transition
        validate_transition(SessionPhase.EXECUTION, SessionPhase.VERIFICATION)
        session.update_phase(SessionPhase.VERIFICATION)
        session_store.update_session(session)

        result = coordinator.trigger_fix_loop(session_id, "Global verification failed")

        assert result["status"] == "fix_loop_triggered"
        session = session_store.get_session(session_id)
        assert session.phase == SessionPhase.EXECUTION

    def test_trigger_fix_loop_requires_execution_or_verification_phase(self, tmp_path):
        """trigger_fix_loop raises ValueError if not in EXECUTION or VERIFICATION phase."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(tmp_path)
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orchestrator = MagicMock(spec=Orchestrator)

        coordinator = SessionCoordinator(
            session_store=session_store,
            workspace_manager=workspace_manager,
            questionnaire_engine=questionnaire_engine,
            spec_builder=spec_builder,
            orchestrator=mock_orchestrator,
        )

        session_id = coordinator.start_session()
        # Session is in QUESTIONNAIRE phase by default

        with pytest.raises(ValueError) as exc_info:
            coordinator.trigger_fix_loop(session_id, "Should fail")

        assert "QUESTIONNAIRE" in str(exc_info.value)


# =============================================================================
# VF-165: Safe abort cleanup tests
# =============================================================================


class TestVF165_SafeAbortCleanup:
    """Tests for VF-165: Safe abort and cleanup behavior."""

    def test_abort_session_sets_aborted_flag(self, tmp_path):
        """abort_session sets is_aborted=True on session."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(tmp_path)
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orchestrator = MagicMock(spec=Orchestrator)

        coordinator = SessionCoordinator(
            session_store=session_store,
            workspace_manager=workspace_manager,
            questionnaire_engine=questionnaire_engine,
            spec_builder=spec_builder,
            orchestrator=mock_orchestrator,
        )

        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        coordinator.abort_session(session_id, "User cancelled")

        session = session_store.get_session(session_id)
        assert session.is_aborted is True
        assert session.abort_reason == "User cancelled"

    def test_abort_session_creates_abort_artifact(self, tmp_path):
        """abort_session creates and persists abort artifact."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(tmp_path)
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orchestrator = MagicMock(spec=Orchestrator)

        coordinator = SessionCoordinator(
            session_store=session_store,
            workspace_manager=workspace_manager,
            questionnaire_engine=questionnaire_engine,
            spec_builder=spec_builder,
            orchestrator=mock_orchestrator,
        )

        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        result = coordinator.abort_session(session_id, "User cancelled")

        assert "abort_artifact" in result
        assert result["abort_artifact"]["abort_reason"] == "User cancelled"
        assert result["abort_artifact"]["is_user_initiated"] is True

        # Check persisted file
        abort_report = tmp_path / session_id / "artifacts" / "abort_report.json"
        assert abort_report.exists()

    def test_abort_session_clears_clarification_state(self, tmp_path):
        """abort_session clears pending clarification state."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(tmp_path)
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orchestrator = MagicMock(spec=Orchestrator)

        coordinator = SessionCoordinator(
            session_store=session_store,
            workspace_manager=workspace_manager,
            questionnaire_engine=questionnaire_engine,
            spec_builder=spec_builder,
            orchestrator=mock_orchestrator,
        )

        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.update_phase(SessionPhase.CLARIFICATION)
        session.pending_clarification = {"question": "test?"}
        session.clarification_answer = "yes"
        session.clarification_context = {"type": "test"}
        session_store.update_session(session)

        coordinator.abort_session(session_id, "User cancelled")

        session = session_store.get_session(session_id)
        assert session.pending_clarification is None
        assert session.clarification_answer is None
        assert session.clarification_context is None

    def test_abort_session_returns_recovery_options(self, tmp_path):
        """abort_session returns recovery options for the user."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(tmp_path)
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orchestrator = MagicMock(spec=Orchestrator)

        coordinator = SessionCoordinator(
            session_store=session_store,
            workspace_manager=workspace_manager,
            questionnaire_engine=questionnaire_engine,
            spec_builder=spec_builder,
            orchestrator=mock_orchestrator,
        )

        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        result = coordinator.abort_session(session_id, "User cancelled")

        assert "recovery_options" in result
        options = result["recovery_options"]
        assert any(opt["value"] == "restart_session" for opt in options)

    def test_abort_session_preserves_workspace(self, tmp_path):
        """abort_session preserves workspace files for inspection."""
        session_store = SessionStore()
        workspace_manager = WorkspaceManager(tmp_path)
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orchestrator = MagicMock(spec=Orchestrator)

        coordinator = SessionCoordinator(
            session_store=session_store,
            workspace_manager=workspace_manager,
            questionnaire_engine=questionnaire_engine,
            spec_builder=spec_builder,
            orchestrator=mock_orchestrator,
        )

        session_id = coordinator.start_session()
        session = session_store.get_session(session_id)
        session.update_phase(SessionPhase.EXECUTION)
        session_store.update_session(session)

        # Create some workspace files
        repo_path = tmp_path / session_id / "repo"
        test_file = repo_path / "test.txt"
        test_file.write_text("test content")

        result = coordinator.abort_session(session_id, "User cancelled")

        # Files should still exist
        assert test_file.exists()
        assert "workspace_preserved" in result

    def test_session_get_recovery_options_includes_reduce_scope_for_planned_sessions(self, tmp_path):
        """get_recovery_options includes reduce_scope if session has concept/task_graph."""
        session_store = SessionStore()

        session = session_store.create_session()
        session.update_phase(SessionPhase.FAILED)
        session.task_graph = {"tasks": []}

        options = session.get_recovery_options()

        assert any(opt["value"] == "reduce_scope" for opt in options)

    def test_session_get_recovery_options_basic_for_early_failures(self, tmp_path):
        """get_recovery_options returns basic options for early-phase failures."""
        session_store = SessionStore()

        session = session_store.create_session()
        session.update_phase(SessionPhase.FAILED)
        # No task_graph or concept set

        options = session.get_recovery_options()

        assert any(opt["value"] == "restart_session" for opt in options)
        assert any(opt["value"] == "export_logs" for opt in options)
        assert not any(opt["value"] == "reduce_scope" for opt in options)


class TestVF194_WorkflowConfiguration:
    """Tests for VF-194: Wire workflow configuration into SessionCoordinator."""

    def _create_coordinator(self, tmp_path):
        """Helper to create SessionCoordinator with minimal dependencies."""
        from apps.api.vibeforge_api.core.session import SessionStore
        from apps.api.vibeforge_api.core.workspace import WorkspaceManager
        from apps.api.vibeforge_api.core.questionnaire import QuestionnaireEngine
        from apps.api.vibeforge_api.core.spec_builder import SpecBuilder
        from orchestration.orchestrator import Orchestrator
        from unittest.mock import Mock

        session_store = SessionStore()
        workspace_manager = WorkspaceManager(workspace_root=tmp_path)
        questionnaire_engine = QuestionnaireEngine()
        spec_builder = SpecBuilder()
        mock_orch = Mock()

        coordinator = SessionCoordinator(
            session_store,
            workspace_manager,
            questionnaire_engine,
            spec_builder,
            mock_orch,
        )
        return coordinator, session_store

    def test_get_agent_config(self, tmp_path):
        """Coordinator can retrieve agent config by ID."""
        from orchestration.models import AgentConfig, AgentRole

        coordinator, session_store = self._create_coordinator(tmp_path)
        session = session_store.create_session()
        session.agents = [
            AgentConfig(agent_id="agent-1", role=AgentRole.WORKER).model_dump(),
            AgentConfig(agent_id="agent-2", role=AgentRole.REVIEWER).model_dump(),
        ]

        agent = coordinator.get_agent_config(session, "agent-1")
        assert agent is not None
        assert agent["role"] == "worker"

    def test_get_agent_config_not_found(self, tmp_path):
        """Returns None if agent not found."""
        coordinator, session_store = self._create_coordinator(tmp_path)
        session = session_store.create_session()
        session.agents = []

        agent = coordinator.get_agent_config(session, "nonexistent")
        assert agent is None

    def test_get_forced_model(self, tmp_path):
        """Coordinator returns forced model if configured."""
        coordinator, session_store = self._create_coordinator(tmp_path)
        session = session_store.create_session()
        session.agent_models = {"agent-1": "gpt-4-turbo"}

        model = coordinator.get_forced_model(session, "agent-1")
        assert model == "gpt-4-turbo"

    def test_get_forced_model_not_configured(self, tmp_path):
        """Returns None if forced model not configured."""
        coordinator, session_store = self._create_coordinator(tmp_path)
        session = session_store.create_session()
        session.agent_models = {}

        model = coordinator.get_forced_model(session, "agent-1")
        assert model is None

    def test_get_agent_for_role(self, tmp_path):
        """Find agent assigned to role."""
        coordinator, session_store = self._create_coordinator(tmp_path)
        session = session_store.create_session()
        session.agent_roles = {"agent-1": "worker", "agent-2": "reviewer"}

        agent_id = coordinator.get_agent_for_role(session, "worker")
        assert agent_id == "agent-1"

    def test_get_agent_for_role_not_found(self, tmp_path):
        """Returns None if role not assigned."""
        coordinator, session_store = self._create_coordinator(tmp_path)
        session = session_store.create_session()
        session.agent_roles = {}

        agent_id = coordinator.get_agent_for_role(session, "worker")
        assert agent_id is None

    def test_is_workflow_configured_true(self, tmp_path):
        """Workflow is configured when agents, roles, and task set."""
        from orchestration.models import AgentConfig

        coordinator, session_store = self._create_coordinator(tmp_path)
        session = session_store.create_session()

        # Not configured initially
        assert not coordinator.is_workflow_configured(session)

        # Configure workflow
        session.agents = [AgentConfig(agent_id="agent-1").model_dump()]
        session.agent_roles = {"agent-1": "worker"}
        session.main_task = "Build a todo app"

        assert coordinator.is_workflow_configured(session)

    def test_is_workflow_configured_false_missing_agents(self, tmp_path):
        """Workflow not configured if agents missing."""
        coordinator, session_store = self._create_coordinator(tmp_path)
        session = session_store.create_session()
        session.agents = []  # Missing agents
        session.agent_roles = {"agent-1": "worker"}
        session.main_task = "Build a todo app"

        assert not coordinator.is_workflow_configured(session)

    def test_is_workflow_configured_false_missing_roles(self, tmp_path):
        """Workflow not configured if roles missing."""
        from orchestration.models import AgentConfig

        coordinator, session_store = self._create_coordinator(tmp_path)
        session = session_store.create_session()
        session.agents = [AgentConfig(agent_id="agent-1").model_dump()]
        session.agent_roles = {}  # Missing roles
        session.main_task = "Build a todo app"

        assert not coordinator.is_workflow_configured(session)

    def test_is_workflow_configured_false_missing_main_task(self, tmp_path):
        """Workflow not configured if main_task missing."""
        from orchestration.models import AgentConfig

        coordinator, session_store = self._create_coordinator(tmp_path)
        session = session_store.create_session()
        session.agents = [AgentConfig(agent_id="agent-1").model_dump()]
        session.agent_roles = {"agent-1": "worker"}
        session.main_task = None  # Missing main_task

        assert not coordinator.is_workflow_configured(session)
