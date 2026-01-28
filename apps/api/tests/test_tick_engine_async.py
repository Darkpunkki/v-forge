"""Tests for async dispatch + response buffering in TickEngine (WP-0058)."""

from datetime import datetime, timedelta, timezone

import pytest

from apps.api.vibeforge_api.core.event_log import EventType
from apps.api.vibeforge_api.core.session import session_store
from orchestration.coordinator.tick_engine import TickEngine
from orchestration.models import AgentConfig


class FakeConnectionManager:
    def __init__(self):
        self.dispatched = []
        self.response_buffer = []
        self.pending_dispatches = []
        self.cleared = []
        self.connected_agents = set()

    def is_agent_connected(self, agent_id: str) -> bool:
        return agent_id in self.connected_agents

    async def dispatch_task(self, agent_id, message_id, content, context=None, session_id=None, progress_callback=None):
        self.dispatched.append(
            {
                "agent_id": agent_id,
                "message_id": message_id,
                "content": content,
                "context": context or {},
                "session_id": session_id,
            }
        )
        return None

    def pop_response_buffer(self, session_id: str):
        responses = list(self.response_buffer)
        self.response_buffer = []
        return responses

    def get_pending_dispatches(self, session_id=None):
        if session_id is None:
            return list(self.pending_dispatches)
        return [p for p in self.pending_dispatches if p.get("session_id") == session_id]

    def clear_pending_dispatch(self, message_id: str, reason: str):
        self.cleared.append((message_id, reason))
        self.pending_dispatches = [p for p in self.pending_dispatches if p.get("message_id") != message_id]
        return True


@pytest.mark.asyncio
async def test_remote_agent_dispatch_path(monkeypatch):
    session = session_store.create_session()
    session.agents = [
        AgentConfig(agent_id="agent-1").model_dump(),
        AgentConfig(agent_id="agent-2", agent_type="remote").model_dump(),
    ]
    session.agent_roles = {"agent-1": "orchestrator", "agent-2": "worker"}
    session.tick_status = "running"
    session_store.update_session(session)

    engine = TickEngine(session)
    engine.send_message("agent-1", "agent-2", {"text": "ping", "expect_response": True})

    fake_manager = FakeConnectionManager()
    fake_manager.connected_agents.add("agent-2")
    monkeypatch.setattr(
        "apps.api.vibeforge_api.core.connection_manager.get_connection_manager",
        lambda: fake_manager,
    )

    result = await engine.advance_tick()

    assert fake_manager.dispatched
    dispatched = fake_manager.dispatched[0]
    assert dispatched["agent_id"] == "agent-2"
    assert "ping" in dispatched["content"]
    assert any(e.event_type == EventType.TASK_DISPATCHED for e in result.events)


@pytest.mark.asyncio
async def test_response_buffer_processing(monkeypatch):
    session = session_store.create_session()
    session.agents = [
        AgentConfig(agent_id="agent-1").model_dump(),
        AgentConfig(agent_id="agent-2", agent_type="remote").model_dump(),
    ]
    session.agent_roles = {"agent-1": "orchestrator", "agent-2": "worker"}
    session.tick_status = "running"
    session_store.update_session(session)

    engine = TickEngine(session)

    fake_manager = FakeConnectionManager()
    fake_manager.response_buffer = [
        {
            "agent_id": "agent-2",
            "message_id": "dispatch-1",
            "content": "done",
            "error": None,
            "context": {
                "from_agent": "agent-1",
                "origin_message_id": "orig-1",
            },
        }
    ]
    session.pending_dispatches = {"dispatch-1": {"agent_id": "agent-2"}}

    monkeypatch.setattr(
        "apps.api.vibeforge_api.core.connection_manager.get_connection_manager",
        lambda: fake_manager,
    )

    result = await engine.advance_tick()

    assert any(e.event_type == EventType.AGENT_RESPONSE for e in result.events)
    delivered = [m for m in engine.message_queue if m.is_delivered]
    assert delivered
    response_message = delivered[0]
    assert response_message.content.get("text") == "done"
    assert response_message.content.get("in_response_to") == "orig-1"
    assert "dispatch-1" not in session.pending_dispatches


@pytest.mark.asyncio
async def test_dispatch_timeout_emits_error(monkeypatch):
    session = session_store.create_session()
    session.agents = [
        AgentConfig(agent_id="agent-1").model_dump(),
        AgentConfig(agent_id="agent-2", agent_type="remote").model_dump(),
    ]
    session.agent_roles = {"agent-1": "orchestrator", "agent-2": "worker"}
    session.tick_status = "running"
    session_store.update_session(session)

    engine = TickEngine(session)

    fake_manager = FakeConnectionManager()
    fake_manager.pending_dispatches = [
        {
            "message_id": "dispatch-2",
            "agent_id": "agent-2",
            "session_id": session.session_id,
            "context": {"from_agent": "agent-1", "origin_message_id": "orig-2"},
            "dispatched_at": datetime.now(timezone.utc) - timedelta(seconds=400),
        }
    ]

    monkeypatch.setattr(
        "apps.api.vibeforge_api.core.connection_manager.get_connection_manager",
        lambda: fake_manager,
    )

    result = await engine.advance_tick()

    assert fake_manager.cleared
    assert any(e.event_type == EventType.AGENT_ERROR for e in result.events)
    delivered = [m for m in engine.message_queue if m.is_delivered]
    assert delivered
    assert "ERROR" in delivered[0].content.get("text", "")
