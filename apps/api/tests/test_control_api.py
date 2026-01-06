"""Tests for control panel API endpoints."""

import pytest
from datetime import datetime, timezone
from pathlib import Path
import json
from unittest.mock import Mock, patch, AsyncMock

from vibeforge_api.core.event_log import EventLog, Event, EventType
from vibeforge_api.core.workspace import WorkspaceManager
from vibeforge_api.core.session import Session, SessionPhase
from vibeforge_api.core.artifacts import SessionArtifactQuery


class TestControlSessions:
    """Tests for /control/sessions endpoint."""

    @pytest.mark.asyncio
    async def test_list_all_sessions_empty(self, tmp_path):
        """Test listing sessions when workspace is empty."""
        from vibeforge_api.routers.control import list_all_sessions

        # Patch WorkspaceManager in the control module where it's imported
        with patch("vibeforge_api.core.workspace.WorkspaceManager") as mock_wm_class:
            mock_wm = Mock()
            mock_wm.workspace_root = tmp_path
            mock_wm_class.return_value = mock_wm

            # Call endpoint
            result = await list_all_sessions()

            assert result["sessions"] == []
            assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_list_all_sessions_with_data(self, tmp_path):
        """Test listing sessions with existing session data."""
        from vibeforge_api.routers.control import list_all_sessions

        # Create session directories with artifacts
        session1_path = tmp_path / "session-1"
        session1_path.mkdir()
        (session1_path / "artifacts").mkdir()
        (session1_path / "artifacts" / "concept.json").write_text('{"idea": "test1"}')

        session2_path = tmp_path / "session-2"
        session2_path.mkdir()
        (session2_path / "artifacts").mkdir()
        (session2_path / "artifacts" / "build_spec.json").write_text('{"stack": "test"}')

        # Patch WorkspaceManager
        with patch("vibeforge_api.core.workspace.WorkspaceManager") as mock_wm_class:
            mock_wm = Mock()
            mock_wm.workspace_root = tmp_path
            mock_wm_class.return_value = mock_wm

            # Call endpoint
            result = await list_all_sessions()

            assert result["total"] == 2
            assert len(result["sessions"]) == 2
            session_ids = [s["session_id"] for s in result["sessions"]]
            assert "session-1" in session_ids
            assert "session-2" in session_ids


class TestControlActive:
    """Tests for /control/active endpoint."""

    @pytest.mark.asyncio
    async def test_get_active_sessions_empty(self):
        """Test getting active sessions when none exist."""
        from vibeforge_api.routers.control import get_active_sessions

        # Mock empty session store
        with patch("vibeforge_api.core.session.session_store") as mock_store:
            mock_store.list_sessions.return_value = []

            # Call endpoint
            result = await get_active_sessions()

            assert result["active_sessions"] == []
            assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_get_active_sessions_filters_complete(self):
        """Test that completed/failed sessions are filtered out."""
        from vibeforge_api.routers.control import get_active_sessions

        # Create mock sessions
        session1 = Session()
        session1.id = "active-1"
        session1.update_phase(SessionPhase.EXECUTION)
        session1.active_task_id = "task-1"

        session2 = Session()
        session2.id = "complete-1"
        session2.update_phase(SessionPhase.COMPLETE)

        session3 = Session()
        session3.id = "failed-1"
        session3.update_phase(SessionPhase.FAILED)

        session4 = Session()
        session4.id = "active-2"
        session4.update_phase(SessionPhase.PLAN_REVIEW)

        # Mock session store
        with patch("vibeforge_api.core.session.session_store") as mock_store:
            mock_store.list_sessions.return_value = [session1, session2, session3, session4]

            # Call endpoint
            result = await get_active_sessions()

            assert result["total"] == 2
            active_ids = [s["session_id"] for s in result["active_sessions"]]
            assert "active-1" in active_ids
            assert "active-2" in active_ids
            assert "complete-1" not in active_ids
            assert "failed-1" not in active_ids


class TestControlSessionStatus:
    """Tests for /control/sessions/{id}/status endpoint."""

    @pytest.mark.asyncio
    async def test_get_session_status_not_found(self):
        """Test getting status for non-existent session."""
        from vibeforge_api.routers.control import get_session_status
        from fastapi import HTTPException

        # Mock session store returning None
        with patch("vibeforge_api.core.session.session_store") as mock_store:
            mock_store.get_session.return_value = None

            # Call endpoint - should raise 404
            with pytest.raises(HTTPException) as exc_info:
                await get_session_status("nonexistent")

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_session_status_success(self):
        """Test getting status for existing session."""
        from vibeforge_api.routers.control import get_session_status

        # Create mock session
        session = Session()
        session.id = "test-session"
        session.update_phase(SessionPhase.EXECUTION)
        session.active_task_id = "task-123"
        session.completed_task_ids = ["task-1", "task-2"]
        session.failed_task_ids = []

        # Mock session store
        with patch("vibeforge_api.core.session.session_store") as mock_store:
            mock_store.get_session.return_value = session

            # Call endpoint
            result = await get_session_status("test-session")

            assert result["session_id"] == "test-session"
            assert result["phase"] == "EXECUTION"
            assert result["active_task_id"] == "task-123"
            assert result["completed_tasks"] == 2
            assert result["failed_tasks"] == 0
            assert "created_at" in result
            assert "updated_at" in result


class TestControlEventStream:
    """Tests for /control/sessions/{id}/events endpoint (SSE)."""

    @pytest.mark.asyncio
    async def test_stream_session_events_not_found(self, tmp_path):
        """Test streaming events for session with no event log."""
        from vibeforge_api.routers.control import stream_session_events
        from fastapi import HTTPException

        # Mock WorkspaceManager with non-existent session
        with patch("vibeforge_api.core.workspace.WorkspaceManager") as mock_wm_class:
            mock_wm = Mock()
            mock_wm.workspace_root = tmp_path
            mock_wm_class.return_value = mock_wm

            # Call endpoint - should raise 404
            with pytest.raises(HTTPException) as exc_info:
                await stream_session_events("nonexistent")

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_stream_session_events_initial_events(self, tmp_path):
        """Test that SSE returns initial events from log."""
        from vibeforge_api.routers.control import stream_session_events

        # Create session workspace with event log
        session_id = "test-session"
        session_path = tmp_path / session_id
        session_path.mkdir()

        event_log_path = session_path / "events.jsonl"
        event_log = EventLog(str(event_log_path))

        # Add test events
        event_log.append(Event(
            event_type=EventType.PHASE_TRANSITION,
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            message="Test event 1",
            phase="IDEA",
        ))
        event_log.append(Event(
            event_type=EventType.TASK_STARTED,
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            message="Test event 2",
            phase="EXECUTION",
            task_id="task-1",
        ))

        # Mock WorkspaceManager
        with patch("vibeforge_api.core.workspace.WorkspaceManager") as mock_wm_class:
            mock_wm = Mock()
            mock_wm.workspace_root = tmp_path
            mock_wm_class.return_value = mock_wm

            # Call endpoint
            event_source = await stream_session_events(session_id)

            # Extract generator
            generator = event_source.body_iterator

            # Collect first 2 events (skip polling part)
            events = []
            for _ in range(2):
                event = await anext(generator)
                events.append(event)

            # Verify events were streamed
            assert len(events) == 2
            assert events[0]["event"] == "session_event"
            assert events[1]["event"] == "session_event"

            # Parse event data
            event1_data = json.loads(events[0]["data"])
            event2_data = json.loads(events[1]["data"])

            assert event1_data["event_type"] == "phase_transition"
            assert event2_data["event_type"] == "task_started"
            assert event2_data["task_id"] == "task-1"
