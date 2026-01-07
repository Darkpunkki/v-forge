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
