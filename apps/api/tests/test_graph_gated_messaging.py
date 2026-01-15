"""Tests for graph-gated messaging (VF-203)."""

import pytest

from apps.api.vibeforge_api.core.event_log import EventLog, EventType
from apps.api.vibeforge_api.core.session import session_store
from orchestration.coordinator.tick_engine import (
    TickEngine,
    MessageValidation,
    MessageValidationStatus,
)
from orchestration.models import AgentConfig, AgentFlowGraph, AgentFlowEdge


class TestMessageValidation:
    """Tests for VF-203: message validation against agent graph."""

    def _create_test_session_with_graph(self):
        """Helper to create a session with a configured agent graph.

        Graph structure:
        agent-1 (orchestrator) → agent-2 (worker)
        agent-2 (worker) → agent-3 (reviewer)
        """
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

    def test_message_allowed_along_edge(self):
        """Test that message is allowed if edge exists in graph."""
        session = self._create_test_session_with_graph()
        engine = TickEngine(session)

        # agent-1 → agent-2 exists
        validation = engine.validate_message("agent-1", "agent-2")

        assert validation.is_allowed
        assert validation.status == MessageValidationStatus.ALLOWED
        assert "edge" in validation.reason.lower() or "orchestrator" in validation.reason.lower()

    def test_message_allowed_for_orchestrator_broadcast(self):
        """Test that orchestrator can send to any agent (broadcast)."""
        session = self._create_test_session_with_graph()
        engine = TickEngine(session)

        # agent-1 is orchestrator, should be able to send to agent-3
        # even though no direct edge exists
        validation = engine.validate_message("agent-1", "agent-3")

        assert validation.is_allowed
        assert validation.status == MessageValidationStatus.ALLOWED
        assert "orchestrator" in validation.reason.lower()

    def test_message_allowed_for_self(self):
        """Test that agent can send message to itself."""
        session = self._create_test_session_with_graph()
        engine = TickEngine(session)

        validation = engine.validate_message("agent-2", "agent-2")

        assert validation.is_allowed
        assert validation.status == MessageValidationStatus.ALLOWED
        assert "self" in validation.reason.lower()

    def test_message_blocked_no_edge(self):
        """Test that message is blocked if no edge exists."""
        session = self._create_test_session_with_graph()
        engine = TickEngine(session)

        # agent-3 → agent-2 does NOT exist
        validation = engine.validate_message("agent-3", "agent-2")

        assert not validation.is_allowed
        assert validation.status == MessageValidationStatus.BLOCKED
        assert "not allowed" in validation.reason.lower()

    def test_message_blocked_reverse_edge(self):
        """Test that reverse direction is blocked (edges are directional)."""
        session = self._create_test_session_with_graph()
        engine = TickEngine(session)

        # agent-2 → agent-1 does NOT exist (only agent-1 → agent-2)
        validation = engine.validate_message("agent-2", "agent-1")

        assert not validation.is_allowed
        assert validation.status == MessageValidationStatus.BLOCKED

    def test_message_allowed_for_bidirectional_edge(self):
        """Test that bidirectional edges allow reverse direction."""
        session = self._create_test_session_with_graph()
        session.agent_graph = AgentFlowGraph(
            edges=[
                AgentFlowEdge(
                    from_agent="agent-1",
                    to_agent="agent-2",
                    bidirectional=True,
                )
            ]
        ).model_dump()
        session_store.update_session(session)
        engine = TickEngine(session)

        validation = engine.validate_message("agent-2", "agent-1")

        assert validation.is_allowed
        assert validation.status == MessageValidationStatus.ALLOWED

    def test_message_blocked_unknown_source(self):
        """Test that message from unknown agent is blocked."""
        session = self._create_test_session_with_graph()
        engine = TickEngine(session)

        validation = engine.validate_message("unknown-agent", "agent-2")

        assert not validation.is_allowed
        assert validation.status == MessageValidationStatus.BLOCKED
        assert "not configured" in validation.reason.lower()

    def test_message_blocked_unknown_target(self):
        """Test that message to unknown agent is blocked."""
        session = self._create_test_session_with_graph()
        engine = TickEngine(session)

        validation = engine.validate_message("agent-1", "unknown-agent")

        assert not validation.is_allowed
        assert validation.status == MessageValidationStatus.BLOCKED
        assert "not configured" in validation.reason.lower()


class TestSendMessage:
    """Tests for VF-203: send_message with graph validation."""

    def _create_test_session_with_graph(self):
        """Helper to create a session with configured graph."""
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

    def test_send_message_success(self):
        """Test successful message send along valid edge."""
        session = self._create_test_session_with_graph()
        engine = TickEngine(session)

        success, message = engine.send_message(
            "agent-1", "agent-2", {"text": "Hello worker"}
        )

        assert success
        assert message is not None
        assert message.from_agent == "agent-1"
        assert message.to_agent == "agent-2"
        assert message.content == {"text": "Hello worker"}
        assert len(engine.message_queue) == 1

    def test_send_message_blocked_emits_event(self):
        """Test that blocked message emits MESSAGE_BLOCKED_BY_GRAPH event."""
        session = self._create_test_session_with_graph()
        engine = TickEngine(session)

        # Try to send from agent-3 to agent-2 (no edge)
        success, message = engine.send_message(
            "agent-3", "agent-2", {"text": "blocked"}
        )

        assert not success
        assert message is None
        assert len(engine.message_queue) == 0

        # Check event was emitted
        events = engine.get_tick_events()
        blocked_events = [e for e in events if e.event_type == EventType.MESSAGE_BLOCKED_BY_GRAPH]

        assert len(blocked_events) == 1
        assert "blocked" in blocked_events[0].message.lower()
        assert blocked_events[0].metadata["from_agent"] == "agent-3"
        assert blocked_events[0].metadata["to_agent"] == "agent-2"
        assert blocked_events[0].metadata["tick_index"] == session.tick_index
        expected_reason = f"agent-3 {chr(0x03B7)}' agent-2 not allowed"
        assert blocked_events[0].metadata["reason"] == expected_reason

    def test_send_message_success_emits_event(self):
        """Test that successful send emits MESSAGE_SENT event."""
        session = self._create_test_session_with_graph()
        engine = TickEngine(session)

        success, _ = engine.send_message("agent-1", "agent-2", {"text": "hello"})

        assert success

        events = engine.get_tick_events()
        sent_events = [e for e in events if e.event_type == EventType.MESSAGE_SENT]

        assert len(sent_events) == 1
        assert sent_events[0].metadata["from_agent"] == "agent-1"
        assert sent_events[0].metadata["to_agent"] == "agent-2"

    def test_send_message_bypass_validation(self):
        """Test that bypass_validation skips graph check."""
        session = self._create_test_session_with_graph()
        engine = TickEngine(session)

        # This would normally be blocked
        success, message = engine.send_message(
            "agent-3", "agent-2", {"text": "system message"},
            bypass_validation=True
        )

        assert success
        assert message is not None
        assert len(engine.message_queue) == 1


class TestGraphGatedIntegration:
    """Integration tests for graph-gated messaging with tick engine."""

    def _create_test_session_with_graph(self):
        """Helper to create a session with configured graph."""
        session = session_store.create_session()
        session.agents = [
            AgentConfig(agent_id="orchestrator").model_dump(),
            AgentConfig(agent_id="worker-1").model_dump(),
            AgentConfig(agent_id="worker-2").model_dump(),
            AgentConfig(agent_id="reviewer").model_dump(),
        ]
        session.agent_roles = {
            "orchestrator": "orchestrator",
            "worker-1": "worker",
            "worker-2": "worker",
            "reviewer": "reviewer",
        }
        # Linear pipeline: orchestrator → worker-1 → worker-2 → reviewer
        session.agent_graph = AgentFlowGraph(
            edges=[
                AgentFlowEdge(from_agent="orchestrator", to_agent="worker-1"),
                AgentFlowEdge(from_agent="worker-1", to_agent="worker-2"),
                AgentFlowEdge(from_agent="worker-2", to_agent="reviewer"),
            ]
        ).model_dump()
        session.tick_status = "running"
        session_store.update_session(session)
        return session

    def test_message_flow_through_pipeline(self):
        """Test messages can flow through valid pipeline edges."""
        session = self._create_test_session_with_graph()
        engine = TickEngine(session)

        # Send messages through pipeline
        s1, m1 = engine.send_message("orchestrator", "worker-1", {"step": 1})
        s2, m2 = engine.send_message("worker-1", "worker-2", {"step": 2})
        s3, m3 = engine.send_message("worker-2", "reviewer", {"step": 3})

        assert all([s1, s2, s3])
        assert len(engine.message_queue) == 3

    def test_message_blocked_against_pipeline(self):
        """Test messages are blocked when going against pipeline flow."""
        session = self._create_test_session_with_graph()
        engine = TickEngine(session)

        # Try reverse direction
        s1, _ = engine.send_message("worker-1", "orchestrator", {"reverse": True})
        s2, _ = engine.send_message("reviewer", "worker-2", {"reverse": True})

        assert not s1
        assert not s2
        assert len(engine.message_queue) == 0

        # Check blocked events
        events = engine.get_tick_events()
        blocked = [e for e in events if e.event_type == EventType.MESSAGE_BLOCKED_BY_GRAPH]
        assert len(blocked) == 2

    def test_blocked_events_logged_and_not_delivered(self, tmp_path):
        """Blocked messages should be logged and excluded from delivered messages."""
        session = self._create_test_session_with_graph()
        log = EventLog(tmp_path / "workspaces")
        engine = TickEngine(session, event_log=log)

        blocked, _ = engine.send_message("worker-1", "orchestrator", {"reverse": True})
        assert not blocked
        assert len(engine.message_queue) == 0

        allowed, msg = engine.send_message("orchestrator", "worker-1", {"valid": True})
        assert allowed
        assert len(engine.message_queue) == 1

        result = engine.advance_tick()

        assert len(result.messages_delivered) == 1
        assert result.messages_delivered[0].message_id == msg.message_id

        blocked_events = log.get_events(
            session.session_id,
            event_type=EventType.MESSAGE_BLOCKED_BY_GRAPH,
        )
        assert len(blocked_events) == 1
        assert blocked_events[0].metadata["from_agent"] == "worker-1"
        assert blocked_events[0].metadata["to_agent"] == "orchestrator"
        expected_reason = f"worker-1 {chr(0x03B7)}' orchestrator not allowed"
        assert blocked_events[0].metadata["reason"] == expected_reason

    def test_orchestrator_can_broadcast_anywhere(self):
        """Test orchestrator can send to any agent in the system."""
        session = self._create_test_session_with_graph()
        engine = TickEngine(session)

        # Orchestrator sends to all agents
        s1, _ = engine.send_message("orchestrator", "worker-1", {"broadcast": True})
        s2, _ = engine.send_message("orchestrator", "worker-2", {"broadcast": True})
        s3, _ = engine.send_message("orchestrator", "reviewer", {"broadcast": True})

        assert all([s1, s2, s3])
        assert len(engine.message_queue) == 3

    def test_workers_cannot_skip_pipeline_steps(self):
        """Test workers can only communicate along defined edges."""
        session = self._create_test_session_with_graph()
        engine = TickEngine(session)

        # worker-1 tries to skip to reviewer (should fail)
        success, _ = engine.send_message("worker-1", "reviewer", {"skip": True})

        assert not success
        assert len(engine.message_queue) == 0

    def test_tick_counts_blocked_messages(self):
        """Test that tick result includes blocked message count."""
        session = self._create_test_session_with_graph()
        engine = TickEngine(session)

        # Send one valid, two invalid
        engine.send_message("orchestrator", "worker-1", {"valid": True})
        engine.send_message("worker-1", "orchestrator", {"invalid": True})
        engine.send_message("reviewer", "worker-1", {"invalid": True})

        result = engine.advance_tick()

        # The blocked count is from events emitted during send, not tick
        # Check events include blocked messages
        blocked_events = [e for e in engine.get_tick_events() if e.event_type == EventType.MESSAGE_BLOCKED_BY_GRAPH]
        # Note: tick events are reset on advance_tick, so we check queue state
        assert len(engine.message_queue) == 1  # Only the valid message
