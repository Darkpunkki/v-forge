"""Tests for cost tracking inputs from LLM response events."""

from datetime import datetime, timezone

from vibeforge_api.core.event_log import Event, EventLog, EventType


def test_llm_response_event_metadata_persists(tmp_path):
    workspace_root = tmp_path / "workspaces"
    log = EventLog(workspace_root)

    event = Event(
        event_type=EventType.LLM_RESPONSE_RECEIVED,
        timestamp=datetime.now(timezone.utc),
        session_id="session-1",
        message="LLM response received",
        metadata={
            "model": "gpt-4o-mini",
            "prompt_tokens": 120,
            "completion_tokens": 350,
            "total_tokens": 470,
        },
    )

    log.append(event)

    events = log.get_events("session-1", event_type=EventType.LLM_RESPONSE_RECEIVED)
    assert len(events) == 1
    assert events[0].metadata["model"] == "gpt-4o-mini"
    assert events[0].metadata["total_tokens"] == 470
