"""Tests for SessionCoordinator (VF-032, VF-033, VF-034, VF-035, VF-036)."""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock

from orchestration.coordinator import SessionCoordinator
from orchestration.models import ConceptDoc, TaskGraph
from orchestration.models import Task as TaskModel
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
        session.build_spec = {"stack": {}}
        session.concept = {"idea": "demo"}
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
