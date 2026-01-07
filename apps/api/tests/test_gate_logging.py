import pytest
from unittest.mock import AsyncMock

from vibeforge_api.core.event_log import EventLog, EventType
from vibeforge_api.core.questionnaire import QuestionnaireEngine
from vibeforge_api.core.session import SessionStore
from vibeforge_api.core.spec_builder import SpecBuilder
from vibeforge_api.core.workspace import WorkspaceManager
from vibeforge_api.models.types import SessionPhase
from orchestration.coordinator.session_coordinator import SessionCoordinator
from orchestration.models import Task, TaskGraph
from models.agent_framework import AgentResult


@pytest.mark.asyncio
async def test_gate_evaluations_logged_on_block(tmp_path):
    session_store = SessionStore()
    workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
    questionnaire_engine = QuestionnaireEngine()
    spec_builder = SpecBuilder()
    orchestrator = AsyncMock()
    agent = AsyncMock()

    agent.runTask.return_value = AgentResult(
        success=True,
        outputs={"diff": "", "commands": ["rm -rf /"]},
        logs=["Dangerous command"],
    )

    event_log = EventLog(workspace_manager.workspace_root)

    coordinator = SessionCoordinator(
        session_store,
        workspace_manager,
        questionnaire_engine,
        spec_builder,
        orchestrator,
        agent,
        event_log=event_log,
    )

    session_id = coordinator.start_session()
    session = session_store.get_session(session_id)

    task = Task(
        task_id="gate_test_task",
        description="Test gate logging",
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

    await coordinator.execute_next_task(session_id)

    gate_events = event_log.get_events(session_id, event_type=EventType.GATE_EVALUATED)

    assert gate_events, "Expected gate evaluation events to be logged"

    blocked = [event for event in gate_events if event.metadata.get("status") == "BLOCK"]
    assert blocked, "Expected at least one blocked gate event"

    event = blocked[0]
    assert event.metadata.get("gate_name") in {"PolicyGate", "DiffAndCommandGate"}
    assert event.message
    assert isinstance(event.metadata.get("details"), dict)
