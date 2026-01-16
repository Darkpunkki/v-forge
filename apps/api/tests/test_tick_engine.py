"""Tests for TickEngine (VF-202)."""

import logging
from datetime import datetime

import pytest

from apps.api.vibeforge_api.core.event_log import EventLog, EventType
from apps.api.vibeforge_api.core.session import session_store
from orchestration.coordinator.tick_engine import TickEngine, TickResult
from orchestration.models import AgentConfig, AgentFlowGraph, AgentFlowEdge


class TestTickEngineBasic:
    """Basic tests for TickEngine initialization and state."""

    def _create_test_session_with_agents(self):
        """Helper to create a session with configured agents."""
        session = session_store.create_session()
        session.agents = [
            AgentConfig(agent_id="agent-1").model_dump(),
            AgentConfig(agent_id="agent-2").model_dump(),
            AgentConfig(agent_id="agent-3").model_dump(),
        ]
        session.agent_roles = {
            "agent-1": "orchestrator",
            "agent-2": "worker",
            "agent-3": "reviewer",
        }
        session.agent_graph = AgentFlowGraph(
            edges=[
                AgentFlowEdge(from_agent="agent-1", to_agent="agent-2"),
                AgentFlowEdge(from_agent="agent-2", to_agent="agent-3"),
            ]
        ).model_dump()
        session.tick_status = "running"
        session_store.update_session(session)
        return session

    def test_init_with_session(self):
        """Test TickEngine initializes correctly with session."""
        session = self._create_test_session_with_agents()

        engine = TickEngine(session)

        assert engine.session == session
        assert len(engine.agent_graph.edges) == 2
        assert len(engine.message_queue) == 0

    def test_init_with_explicit_graph(self):
        """Test TickEngine initializes with explicitly provided graph."""
        session = session_store.create_session()
        custom_graph = AgentFlowGraph(
            edges=[AgentFlowEdge(from_agent="a", to_agent="b")]
        )

        engine = TickEngine(session, agent_graph=custom_graph)

        assert len(engine.agent_graph.edges) == 1
        assert engine.agent_graph.edges[0].from_agent == "a"

    def test_init_with_no_graph(self):
        """Test TickEngine initializes with empty graph when none provided."""
        session = session_store.create_session()
        # No agent_graph set

        engine = TickEngine(session)

        assert len(engine.agent_graph.edges) == 0


class TestTickAdvancement:
    """Tests for VF-202: tick advancement."""

    def _create_test_session_with_agents(self):
        """Helper to create a session with configured agents."""
        session = session_store.create_session()
        session.agents = [
            AgentConfig(agent_id="agent-1").model_dump(),
            AgentConfig(agent_id="agent-2").model_dump(),
        ]
        session.agent_roles = {
            "agent-1": "orchestrator",
            "agent-2": "worker",
        }
        session.agent_graph = AgentFlowGraph(
            edges=[AgentFlowEdge(from_agent="agent-1", to_agent="agent-2")]
        ).model_dump()
        session.tick_status = "running"
        session.tick_index = 0
        session_store.update_session(session)
        return session

    def test_advance_tick_increments_index(self):
        """Test that advance_tick increments tick_index."""
        session = self._create_test_session_with_agents()
        engine = TickEngine(session)

        assert session.tick_index == 0

        result = engine.advance_tick()

        assert session.tick_index == 1
        assert result.tick_index == 1

    def test_advance_tick_returns_tick_result(self):
        """Test that advance_tick returns proper TickResult."""
        session = self._create_test_session_with_agents()
        engine = TickEngine(session)

        result = engine.advance_tick()

        assert isinstance(result, TickResult)
        assert result.tick_index == 1
        assert result.events_in_tick >= 1  # At least TICK_ADVANCED event
        assert result.messages_in_tick == 0
        assert result.messages_blocked == 0

    def test_advance_tick_emits_event(self):
        """Test that advance_tick emits TICK_ADVANCED event."""
        session = self._create_test_session_with_agents()
        engine = TickEngine(session)

        result = engine.advance_tick()
        tick_events = [e for e in result.events if e.event_type == EventType.TICK_ADVANCED]

        assert len(tick_events) == 1
        assert tick_events[0].metadata["old_tick_index"] == 0
        assert tick_events[0].metadata["new_tick_index"] == 1
        assert tick_events[0].metadata["old_tick"] == 0
        assert tick_events[0].metadata["new_tick"] == 1

    def test_multiple_tick_advancement(self):
        """Test advancing multiple ticks sequentially."""
        session = self._create_test_session_with_agents()
        engine = TickEngine(session)

        result1 = engine.advance_tick()
        result2 = engine.advance_tick()
        result3 = engine.advance_tick()

        assert result1.tick_index == 1
        assert result2.tick_index == 2
        assert result3.tick_index == 3
        assert session.tick_index == 3


class TestTickState:
    """Tests for tick state retrieval."""

    def _create_test_session_with_agents(self):
        """Helper to create a session with configured agents."""
        session = session_store.create_session()
        session.agents = [
            AgentConfig(agent_id="agent-1").model_dump(),
            AgentConfig(agent_id="agent-2").model_dump(),
        ]
        session.agent_roles = {
            "agent-1": "orchestrator",
            "agent-2": "worker",
        }
        session.agent_graph = AgentFlowGraph(
            edges=[AgentFlowEdge(from_agent="agent-1", to_agent="agent-2")]
        ).model_dump()
        session.tick_status = "running"
        session_store.update_session(session)
        return session

    def test_get_tick_state(self):
        """Test get_tick_state returns correct state."""
        session = self._create_test_session_with_agents()
        engine = TickEngine(session)

        state = engine.get_tick_state()

        assert state["tick_index"] == 0
        assert state["tick_status"] == "running"
        assert state["pending_messages"] == 0
        assert state["delivered_messages"] == 0
        assert state["total_messages"] == 0

    def test_get_tick_state_with_messages(self):
        """Test get_tick_state reflects message counts."""
        session = self._create_test_session_with_agents()
        engine = TickEngine(session)

        # Send a message
        engine.send_message("agent-1", "agent-2", {"text": "hello"})

        state = engine.get_tick_state()

        assert state["pending_messages"] == 1
        assert state["total_messages"] == 1

    def test_get_tick_events(self):
        """Test get_tick_events returns events from current tick."""
        session = self._create_test_session_with_agents()
        engine = TickEngine(session)

        # Advance tick to generate events
        engine.advance_tick()
        events = engine.get_tick_events()

        assert len(events) >= 1
        assert any(e.event_type == EventType.TICK_ADVANCED for e in events)


class TestMessageDelivery:
    """Tests for message delivery during ticks."""

    def _create_test_session_with_agents(self):
        """Helper to create a session with configured agents."""
        session = session_store.create_session()
        session.agents = [
            AgentConfig(agent_id="agent-1").model_dump(),
            AgentConfig(agent_id="agent-2").model_dump(),
        ]
        session.agent_roles = {
            "agent-1": "orchestrator",
            "agent-2": "worker",
        }
        session.agent_graph = AgentFlowGraph(
            edges=[AgentFlowEdge(from_agent="agent-1", to_agent="agent-2")]
        ).model_dump()
        session.tick_status = "running"
        session_store.update_session(session)
        return session

    def test_messages_delivered_on_tick(self):
        """Test that pending messages are delivered on tick advance."""
        session = self._create_test_session_with_agents()
        engine = TickEngine(session)

        # Queue a message
        success, msg = engine.send_message("agent-1", "agent-2", {"text": "hello"})
        assert success
        assert not msg.is_delivered

        # Advance tick
        result = engine.advance_tick()

        assert len(result.messages_delivered) == 1
        assert msg.is_delivered
        assert msg.tick_delivered == 1

    def test_get_pending_messages_for_agent(self):
        """Test getting pending messages for a specific agent."""
        session = self._create_test_session_with_agents()
        engine = TickEngine(session)

        # Queue messages for different agents
        engine.send_message("agent-1", "agent-2", {"text": "for agent-2"})

        pending_for_1 = engine.get_pending_messages("agent-1")
        pending_for_2 = engine.get_pending_messages("agent-2")

        assert len(pending_for_1) == 0  # No messages for agent-1
        assert len(pending_for_2) == 1  # One message for agent-2

    def test_clear_delivered_messages(self):
        """Test clearing delivered messages from queue."""
        session = self._create_test_session_with_agents()
        engine = TickEngine(session)

        # Send and deliver a message
        engine.send_message("agent-1", "agent-2", {"text": "hello"})
        engine.advance_tick()

        assert len(engine.message_queue) == 1
        assert engine.message_queue[0].is_delivered

        # Clear delivered
        cleared = engine.clear_delivered_messages()

        assert cleared == 1
        assert len(engine.message_queue) == 0


class TestTickQueueProcessing:
    """Tests for FIFO processing and per-agent activity cap."""

    def _create_test_session_with_agents(self):
        session = session_store.create_session()
        session.agents = [
            AgentConfig(agent_id="agent-1").model_dump(),
            AgentConfig(agent_id="agent-2").model_dump(),
        ]
        session.agent_roles = {
            "agent-1": "orchestrator",
            "agent-2": "worker",
        }
        session.agent_graph = AgentFlowGraph(
            edges=[AgentFlowEdge(from_agent="agent-1", to_agent="agent-2")]
        ).model_dump()
        session.tick_status = "running"
        session_store.update_session(session)
        return session

    def test_fifo_single_event_per_tick(self):
        """Only the first queued message is delivered per tick."""
        session = self._create_test_session_with_agents()
        engine = TickEngine(session)

        engine.send_message("agent-1", "agent-2", {"text": "first"})
        engine.send_message("agent-1", "agent-2", {"text": "second"})
        engine.send_message("agent-1", "agent-2", {"text": "third"})

        result = engine.advance_tick()

        assert len(result.messages_delivered) == 1
        assert result.messages_delivered[0].content["text"] == "first"
        pending = [m for m in engine.message_queue if not m.is_delivered]
        assert [m.content["text"] for m in pending] == ["second", "third"]

    def test_activity_cap_defers_same_agent_until_next_tick(self):
        """Messages from the same agent are deferred to the next tick."""
        session = self._create_test_session_with_agents()
        engine = TickEngine(session)

        engine.send_message("agent-1", "agent-2", {"text": "first"})
        engine.send_message("agent-1", "agent-2", {"text": "second"})

        result1 = engine.advance_tick()
        assert len(result1.messages_delivered) == 1
        assert result1.messages_delivered[0].content["text"] == "first"

        result2 = engine.advance_tick()
        assert len(result2.messages_delivered) == 1
        assert result2.messages_delivered[0].content["text"] == "second"


class TestStubbedResponses:
    """Tests for deterministic stubbed responses."""

    def _create_test_session_with_agents(self):
        session = session_store.create_session()
        session.agents = [
            AgentConfig(agent_id="agent-1").model_dump(),
            AgentConfig(agent_id="agent-2").model_dump(),
        ]
        session.agent_roles = {
            "agent-1": "orchestrator",
            "agent-2": "worker",
        }
        session.agent_graph = AgentFlowGraph(
            edges=[AgentFlowEdge(from_agent="agent-1", to_agent="agent-2")]
        ).model_dump()
        session.tick_status = "running"
        session_store.update_session(session)
        return session

    def test_generate_stub_response_deterministic(self):
        """Stub responses should be deterministic and labeled."""
        session = self._create_test_session_with_agents()
        engine = TickEngine(session)
        content = {"text": "ping", "expect_response": True}

        stub1 = engine.generate_stub_response("agent-2", "agent-1", content, 1)
        stub2 = engine.generate_stub_response("agent-2", "agent-1", content, 1)
        stub3 = engine.generate_stub_response("agent-2", "agent-1", {"text": "pong"}, 1)

        assert stub1 == stub2
        assert "[STUB]" in stub1["text"]
        assert "agent-2" in stub1["text"]
        assert "tick 1" in stub1["text"]
        assert stub1["stub_hash"] != stub3["stub_hash"]

    def test_stub_response_queued_on_delivery(self):
        """Delivered messages expecting a response queue a stub reply."""
        session = self._create_test_session_with_agents()
        engine = TickEngine(session)

        success, message = engine.send_message(
            "agent-1",
            "agent-2",
            {"text": "ping", "expect_response": True},
        )
        assert success

        result = engine.advance_tick()

        assert len(result.messages_delivered) == 1
        stub_messages = [
            msg for msg in engine.message_queue
            if isinstance(msg.content, dict) and msg.content.get("is_stub")
        ]
        assert len(stub_messages) == 1
        stub_message = stub_messages[0]
        assert stub_message.from_agent == "agent-2"
        assert stub_message.to_agent == "agent-1"
        assert not stub_message.is_delivered
        assert stub_message.content["in_response_to"] == message.message_id

        stub_events = [
            event for event in engine.get_tick_events()
            if event.event_type == EventType.MESSAGE_SENT
            and event.metadata.get("is_stub")
        ]
        assert len(stub_events) == 1


class TestEventLogPersistence:
    """Tests for event log persistence and resilience."""

    def _create_test_session_with_agents(self):
        session = session_store.create_session()
        session.agents = [
            AgentConfig(agent_id="agent-1").model_dump(),
            AgentConfig(agent_id="agent-2").model_dump(),
        ]
        session.agent_roles = {
            "agent-1": "orchestrator",
            "agent-2": "worker",
        }
        session.agent_graph = AgentFlowGraph(
            edges=[AgentFlowEdge(from_agent="agent-1", to_agent="agent-2")]
        ).model_dump()
        session.tick_status = "running"
        session.tick_index = 0
        session_store.update_session(session)
        return session

    def test_tick_events_persisted_to_event_log(self, tmp_path):
        """Tick events should be persisted with timestamps and metadata."""
        session = self._create_test_session_with_agents()
        workspace_root = tmp_path / "workspaces"
        event_log = EventLog(workspace_root)
        engine = TickEngine(session, event_log=event_log)

        result = engine.advance_tick()

        fresh_log = EventLog(workspace_root)
        events = fresh_log.get_events(session.session_id)
        tick_events = [e for e in events if e.event_type == EventType.TICK_ADVANCED]

        assert len(tick_events) == 1
        tick_event = tick_events[0]
        assert tick_event.session_id == session.session_id
        assert isinstance(tick_event.timestamp, datetime)
        assert "T" in tick_event.timestamp.isoformat()
        assert tick_event.metadata["new_tick_index"] == result.tick_index

    def test_message_events_persisted_to_event_log(self, tmp_path):
        """Message events should persist sender/receiver metadata."""
        session = self._create_test_session_with_agents()
        workspace_root = tmp_path / "workspaces"
        event_log = EventLog(workspace_root)
        engine = TickEngine(session, event_log=event_log)

        success, _ = engine.send_message("agent-1", "agent-2", {"text": "hello"})
        assert success
        blocked, _ = engine.send_message("agent-2", "agent-1", {"text": "blocked"})
        assert not blocked

        fresh_log = EventLog(workspace_root)
        events = fresh_log.get_events(session.session_id)

        sent_events = [e for e in events if e.event_type == EventType.MESSAGE_SENT]
        blocked_events = [
            e for e in events if e.event_type == EventType.MESSAGE_BLOCKED_BY_GRAPH
        ]

        assert sent_events
        sent_meta = sent_events[-1].metadata
        assert sent_meta["from_agent"] == "agent-1"
        assert sent_meta["to_agent"] == "agent-2"
        assert sent_meta["tick_index"] == 0
        assert sent_meta["content"]["text"] == "hello"

        assert blocked_events
        blocked_meta = blocked_events[-1].metadata
        assert blocked_meta["from_agent"] == "agent-2"
        assert blocked_meta["to_agent"] == "agent-1"
        assert blocked_meta["tick_index"] == 0
        assert "reason" in blocked_meta

    def test_event_log_failure_does_not_block_tick(self, caplog):
        """Event log failures should not stop tick processing."""
        session = self._create_test_session_with_agents()

        class FailingEventLog:
            def append(self, event):  # pragma: no cover - executed in test
                raise OSError("disk error")

        engine = TickEngine(session, event_log=FailingEventLog())
        with caplog.at_level(logging.WARNING):
            result = engine.advance_tick()

        assert result.tick_index == 1
        assert session.tick_index == 1
        assert any(
            "Failed to append event log" in record.message
            for record in caplog.records
        )
