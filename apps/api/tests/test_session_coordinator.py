"""Tests for SessionCoordinator (VF-032, VF-033, VF-034, VF-035, VF-036)."""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock

from orchestration.coordinator import SessionCoordinator
from orchestration.models import ConceptDoc, TaskGraph
from orchestration.models import Task as TaskModel
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
        assert any("Plan rejected by user: Too complex" in log for log in session.logs)
