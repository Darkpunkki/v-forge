"""Tests for TickEngine (VF-202)."""

import pytest

from apps.api.vibeforge_api.core.event_log import EventType
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
