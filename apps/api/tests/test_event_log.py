from datetime import datetime, timezone

import pytest

from vibeforge_api.core.event_log import Event, EventLog, EventType, create_phase_transition_event


def test_append_and_persist_events(tmp_path):
    workspace_root = tmp_path / "workspaces"
    log = EventLog(workspace_root)

    event = Event(
        event_type=EventType.INFO,
        timestamp=datetime.now(timezone.utc),
        session_id="s1",
        message="hello",
    )

    log.append(event)

    assert (workspace_root / "s1" / "events.jsonl").exists()
    events = log.get_events("s1")
    assert len(events) == 1
    assert events[0].message == "hello"


def test_event_filtering_and_latest(tmp_path):
    workspace_root = tmp_path / "workspaces"
    log = EventLog(workspace_root)

    info_event = Event(
        event_type=EventType.INFO,
        timestamp=datetime.now(timezone.utc),
        session_id="s2",
        message="info",
    )
    phase_event = create_phase_transition_event("s2", "A", "B")

    log.append(info_event)
    log.append(phase_event)

    filtered = log.get_events("s2", event_type=EventType.PHASE_TRANSITION)
    assert len(filtered) == 1
    assert filtered[0].metadata == {"from": "A", "to": "B", "reason": None}
    assert filtered[0].phase == "B"

    latest = log.get_latest("s2", limit=1)
    assert latest[0].event_type == EventType.PHASE_TRANSITION


def test_events_reload_from_disk(tmp_path):
    workspace_root = tmp_path / "workspaces"
    first_log = EventLog(workspace_root)
    first_log.append(
        Event(
            event_type=EventType.WORKSPACE_INITIALIZED,
            timestamp=datetime.now(timezone.utc),
            session_id="s3",
            message="created",
        )
    )

    # New instance should load persisted events
    second_log = EventLog(workspace_root)
    events = second_log.get_events("s3")

    assert len(events) == 1
    assert events[0].event_type == EventType.WORKSPACE_INITIALIZED


# VF-206: Tests for simulation event types and filtering
class TestSimulationEventTypes:
    """Tests for VF-206 simulation event types."""

    def test_simulation_event_types_exist(self):
        """All simulation event types should be defined."""
        assert EventType.SIMULATION_CONFIGURED.value == "simulation_configured"
        assert EventType.SIMULATION_STARTED.value == "simulation_started"
        assert EventType.SIMULATION_RESET.value == "simulation_reset"
        assert EventType.SIMULATION_PAUSED.value == "simulation_paused"
        assert EventType.TICK_STARTED.value == "tick_started"
        assert EventType.TICK_COMPLETED.value == "tick_completed"
        assert EventType.TICK_BLOCKED.value == "tick_blocked"
        assert EventType.AGENT_MESSAGE_SENT.value == "agent_message_sent"
        # From WP-0049
        assert EventType.TICK_ADVANCED.value == "tick_advanced"
        assert EventType.MESSAGE_SENT.value == "message_sent"
        assert EventType.MESSAGE_BLOCKED_BY_GRAPH.value == "message_blocked_by_graph"

    def test_create_simulation_events(self, tmp_path):
        """Can create and persist simulation events."""
        workspace_root = tmp_path / "workspaces"
        log = EventLog(workspace_root)

        log.append(Event(
            event_type=EventType.SIMULATION_STARTED,
            timestamp=datetime.now(timezone.utc),
            session_id="sim1",
            message="Simulation started",
            metadata={"tick_index": 0, "simulation_mode": "manual"},
        ))

        events = log.get_events("sim1")
        assert len(events) == 1
        assert events[0].event_type == EventType.SIMULATION_STARTED


class TestEventLogFiltering:
    """Tests for VF-206 get_events_filtered method."""

    @pytest.fixture
    def log_with_events(self, tmp_path):
        """Create an EventLog with test events."""
        workspace_root = tmp_path / "workspaces"
        log = EventLog(workspace_root)
        session_id = "filter_test"

        # Add events with varying tick_index and agent_id
        for i in range(5):
            log.append(Event(
                event_type=EventType.TICK_ADVANCED,
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
                message=f"Tick {i} advanced",
                metadata={"tick_index": i},
            ))

        # Add message events
        log.append(Event(
            event_type=EventType.MESSAGE_SENT,
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            message="Message from agent_1 to agent_2",
            metadata={"tick_index": 2, "from_agent": "agent_1", "to_agent": "agent_2"},
        ))
        log.append(Event(
            event_type=EventType.MESSAGE_SENT,
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            message="Message from agent_2 to agent_1",
            metadata={"tick_index": 3, "from_agent": "agent_2", "to_agent": "agent_1"},
        ))
        log.append(Event(
            event_type=EventType.MESSAGE_BLOCKED_BY_GRAPH,
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            message="Message blocked",
            metadata={"tick_index": 4, "from_agent": "agent_3", "reason": "no edge"},
        ))

        return log, session_id

    def test_filter_by_event_type(self, log_with_events):
        """Filter events by event_type."""
        log, session_id = log_with_events

        events = log.get_events_filtered(session_id, event_type="tick_advanced")
        assert len(events) == 5
        assert all(e.event_type == EventType.TICK_ADVANCED for e in events)

    def test_filter_by_tick_index(self, log_with_events):
        """Filter events by exact tick_index."""
        log, session_id = log_with_events

        events = log.get_events_filtered(session_id, tick_index=2)
        assert len(events) == 2  # tick_advanced + message_sent at tick 2
        assert all(e.metadata.get("tick_index") == 2 for e in events)

    def test_filter_by_tick_range(self, log_with_events):
        """Filter events by tick range (tick_min, tick_max)."""
        log, session_id = log_with_events

        events = log.get_events_filtered(session_id, tick_min=2, tick_max=3)
        # tick_advanced at 2,3 + message_sent at 2,3 = 4 events
        assert len(events) == 4
        for e in events:
            tick = e.metadata.get("tick_index")
            assert 2 <= tick <= 3

    def test_filter_by_agent_id(self, log_with_events):
        """Filter events by agent_id (from_agent)."""
        log, session_id = log_with_events

        events = log.get_events_filtered(session_id, agent_id="agent_1")
        assert len(events) == 1
        assert events[0].metadata.get("from_agent") == "agent_1"

    def test_filter_combined_criteria(self, log_with_events):
        """Filter with multiple criteria."""
        log, session_id = log_with_events

        events = log.get_events_filtered(
            session_id,
            event_type="message_sent",
            tick_min=2,
            tick_max=3,
        )
        assert len(events) == 2  # message_sent at tick 2 and 3

    def test_filter_with_limit(self, log_with_events):
        """Limit returns most recent events."""
        log, session_id = log_with_events

        events = log.get_events_filtered(session_id, limit=3)
        assert len(events) == 3

    def test_filter_no_matches(self, log_with_events):
        """Empty result when no events match."""
        log, session_id = log_with_events

        events = log.get_events_filtered(session_id, tick_index=999)
        assert len(events) == 0

    def test_filter_tick_min_only(self, log_with_events):
        """Filter with tick_min only."""
        log, session_id = log_with_events

        events = log.get_events_filtered(session_id, tick_min=4)
        # tick_advanced at 4 + message_blocked at 4 = 2 events
        assert len(events) == 2

    def test_filter_tick_max_only(self, log_with_events):
        """Filter with tick_max only."""
        log, session_id = log_with_events

        events = log.get_events_filtered(session_id, tick_max=1)
        # tick_advanced at 0 and 1 = 2 events
        assert len(events) == 2
