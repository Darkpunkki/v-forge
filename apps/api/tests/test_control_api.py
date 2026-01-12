"""Tests for control panel API endpoints."""

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

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
            with patch("vibeforge_api.core.session.session_store") as mock_store:
                mock_store.list_sessions.return_value = []
                mock_store.get_session.return_value = None

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
            with patch("vibeforge_api.core.session.session_store") as mock_store:
                mock_store.list_sessions.return_value = []
                mock_store.get_session.return_value = None

                # Call endpoint
                result = await list_all_sessions()

                assert result["total"] == 2
                assert len(result["sessions"]) == 2
                session_ids = [s["session_id"] for s in result["sessions"]]
                assert "session-1" in session_ids
                assert "session-2" in session_ids
                for session in result["sessions"]:
                    assert "phase" in session
                    assert "updated_at" in session
                    assert "artifacts" in session


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
        session1.session_id = "active-1"
        session1.update_phase(SessionPhase.EXECUTION)
        session1.active_task_id = "task-1"

        session2 = Session()
        session2.session_id = "complete-1"
        session2.update_phase(SessionPhase.COMPLETE)

        session3 = Session()
        session3.session_id = "failed-1"
        session3.update_phase(SessionPhase.FAILED)

        session4 = Session()
        session4.session_id = "active-2"
        session4.update_phase(SessionPhase.PLAN_REVIEW)

        sessions = {
            "active-1": session1,
            "complete-1": session2,
            "failed-1": session3,
            "active-2": session4,
        }

        # Mock session store
        with patch("vibeforge_api.core.session.session_store") as mock_store:
            mock_store.list_sessions.return_value = list(sessions.keys())
            mock_store.get_session.side_effect = lambda session_id: sessions.get(session_id)

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
        session.session_id = "test-session"
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
        event_log = EventLog(tmp_path)

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


class TestControlPrompts:
    """Tests for /control/sessions/{id}/prompts endpoint."""

    @pytest.mark.asyncio
    async def test_get_session_prompts(self, tmp_path):
        """Test prompt retrieval endpoint."""
        from vibeforge_api.routers.control import get_session_prompts

        session_id = "test-session"
        event_log = EventLog(tmp_path)
        event_log.append(
            Event(
                event_type=EventType.LLM_REQUEST_SENT,
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
                message="LLM request",
                task_id="task-1",
                metadata={
                    "agent_role": "worker",
                    "model": "gpt-4o-mini",
                    "prompt": "Write a Python function to add two numbers",
                    "system_message": "You are a helpful coding assistant",
                    "max_tokens": 1000,
                    "temperature": 0.7,
                },
            )
        )

        with patch("vibeforge_api.core.workspace.WorkspaceManager") as mock_wm_class:
            mock_wm = Mock()
            mock_wm.workspace_root = tmp_path
            mock_wm_class.return_value = mock_wm

            response = await get_session_prompts(session_id)

        assert response["total"] == 1
        prompt = response["prompts"][0]
        assert prompt["model"] == "gpt-4o-mini"
        assert "add two numbers" in prompt["prompt"]


class TestControlRunBundle:
    """Tests for /control/sessions/{id}/bundle endpoint."""

    @pytest.mark.asyncio
    async def test_export_run_bundle_not_found(self, tmp_path):
        """Ensure missing sessions return 404."""
        from fastapi import HTTPException
        from vibeforge_api.routers.control import export_run_bundle

        with patch("vibeforge_api.core.workspace.WorkspaceManager") as mock_wm_class:
            mock_wm = Mock()
            mock_wm.workspace_root = tmp_path
            mock_wm_class.return_value = mock_wm

            with pytest.raises(HTTPException) as exc_info:
                await export_run_bundle("missing-session")

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_export_run_bundle_success(self, tmp_path):
        """Ensure bundle export returns a zip response."""
        from vibeforge_api.routers.control import export_run_bundle

        session_id = "session-1"
        workspace_path = tmp_path / session_id
        (workspace_path / "repo").mkdir(parents=True)
        (workspace_path / "artifacts").mkdir()
        (workspace_path / "repo" / "README.md").write_text("# Demo\n")
        (workspace_path / "artifacts" / "run_summary.json").write_text("{}")

        with patch("vibeforge_api.core.workspace.WorkspaceManager") as mock_wm_class:
            mock_wm = Mock()
            mock_wm.workspace_root = tmp_path
            mock_wm_class.return_value = mock_wm

            response = await export_run_bundle(session_id)

        assert response.media_type == "application/zip"
        assert Path(response.path).exists()


class TestControlLlmTrace:
    """Tests for /control/sessions/{id}/llm-trace endpoint."""

    @pytest.mark.asyncio
    async def test_get_session_llm_trace(self, tmp_path):
        """Ensure LLM trace combines prompts and responses."""
        from vibeforge_api.routers.control import get_session_llm_trace

        session_id = "trace-session"
        request_id = "req-123"
        event_log = EventLog(tmp_path)
        event_log.append(
            Event(
                event_type=EventType.LLM_REQUEST_SENT,
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
                message="LLM request",
                task_id="task-1",
                metadata={
                    "agent_role": "worker",
                    "model": "gpt-4o-mini",
                    "prompt": "Write a Python function to add two numbers",
                    "system_message": "You are a helpful coding assistant",
                    "max_tokens": 1000,
                    "temperature": 0.7,
                    "request_id": request_id,
                },
            )
        )
        event_log.append(
            Event(
                event_type=EventType.LLM_RESPONSE_RECEIVED,
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
                message="LLM response",
                task_id="task-1",
                metadata={
                    "agent_role": "worker",
                    "model": "gpt-4o-mini",
                    "response": "Here is the function...",
                    "prompt_tokens": 12,
                    "completion_tokens": 8,
                    "total_tokens": 20,
                    "request_id": request_id,
                },
            )
        )

        with patch("vibeforge_api.core.workspace.WorkspaceManager") as mock_wm_class:
            mock_wm = Mock()
            mock_wm.workspace_root = tmp_path
            mock_wm_class.return_value = mock_wm

            response = await get_session_llm_trace(session_id)

        assert response["total"] == 1
        trace = response["traces"][0]
        assert trace["response"] == "Here is the function..."
        assert "add two numbers" in trace["prompt"]
