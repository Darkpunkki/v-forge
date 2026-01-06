from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from orchestration.coordinator import SessionCoordinator
from orchestration.models import Task, TaskGraph
from vibeforge_api.core.event_log import Event, EventLog, EventType
from vibeforge_api.core.questionnaire import QuestionnaireEngine
from vibeforge_api.core.session import SessionStore
from vibeforge_api.core.spec_builder import SpecBuilder
from vibeforge_api.core.workspace import WorkspaceManager
from vibeforge_api.models.types import SessionPhase
from models.agent_framework import AgentFramework, AgentResult
from models.base.llm_client import LlmUsage


class StubAgent(AgentFramework):
    """Agent that returns a predefined result for testing."""

    def __init__(self, result: AgentResult):
        self.result = result

    async def runTask(self, task, role, context):  # type: ignore[override]
        return self.result

    def get_framework_name(self) -> str:  # type: ignore[override]
        return "stub"


def test_event_log_persists_token_metadata(tmp_path):
    """LLM token metadata is persisted and deserialized correctly."""

    workspace_root = tmp_path / "workspaces"
    log = EventLog(workspace_root)

    token_event = Event(
        event_type=EventType.LLM_RESPONSE_RECEIVED,
        timestamp=datetime.now(timezone.utc),
        session_id="session-1",
        message="LLM response",
        metadata={
            "agent_role": "worker",
            "model": "gpt-4o-mini",
            "prompt_tokens": 120,
            "completion_tokens": 80,
            "total_tokens": 200,
        },
    )

    log.append(token_event)

    loaded = log.get_events("session-1", event_type=EventType.LLM_RESPONSE_RECEIVED)
    assert len(loaded) == 1
    assert loaded[0].metadata["total_tokens"] == 200
    assert loaded[0].metadata["agent_role"] == "worker"


@pytest.mark.asyncio
async def test_execute_task_emits_token_and_agent_events(tmp_path):
    """Token and agent lifecycle events are emitted during execution."""

    session_store = SessionStore()
    workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
    event_log = EventLog(workspace_manager.workspace_root)
    questionnaire_engine = QuestionnaireEngine()
    spec_builder = SpecBuilder()
    orchestrator = AsyncMock()

    usage = LlmUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    agent_result = AgentResult(
        success=True,
        outputs={"response": "ok", "model": "gpt-4o-mini"},
        logs=["ran"],
        usage=usage,
    )
    agent = StubAgent(agent_result)

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
        task_id="t1",
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

    result = await coordinator.execute_next_task(session_id)

    assert result["status"] == "task_complete"

    events = event_log.get_events(session_id)
    token_events = [e for e in events if e.event_type == EventType.LLM_RESPONSE_RECEIVED]
    assert token_events
    assert token_events[0].metadata["total_tokens"] == 30

    agent_events = [e for e in events if e.event_type == EventType.AGENT_COMPLETED]
    assert any(evt.metadata.get("success") is True for evt in agent_events)

    started_events = [e for e in events if e.event_type == EventType.TASK_STARTED]
    assert started_events and started_events[0].metadata["agent_role"] == "worker"
