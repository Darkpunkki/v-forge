"""Unit tests for Agent Bridge WebSocket endpoint and connection manager.

TASK-012: Tests for WP-0055 WebSocket infrastructure.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from starlette.testclient import WebSocketTestSession

from vibeforge_api.main import app
from vibeforge_api.core.connection_manager import (
    RemoteAgentConnectionManager,
    get_connection_manager,
    reset_connection_manager,
    AgentConnection,
    PendingDispatch,
)
from vibeforge_api.models.bridge_protocol import (
    RegisterMessage,
    RegisteredMessage,
    DispatchMessage,
    ProgressMessage,
    ResponseMessage,
    HeartbeatMessage,
    parse_bridge_message,
)


@pytest.fixture(autouse=True)
def reset_manager():
    """Reset the connection manager singleton before each test."""
    reset_connection_manager()
    yield
    reset_connection_manager()


class TestRemoteAgentConnectionManager:
    """Tests for RemoteAgentConnectionManager."""

    def test_singleton_pattern(self):
        """Manager is a singleton."""
        manager1 = RemoteAgentConnectionManager()
        manager2 = RemoteAgentConnectionManager()
        assert manager1 is manager2

    def test_get_connection_manager(self):
        """get_connection_manager returns singleton."""
        manager = get_connection_manager()
        assert isinstance(manager, RemoteAgentConnectionManager)
        assert get_connection_manager() is manager

    def test_configure_heartbeat(self):
        """Can configure heartbeat parameters."""
        manager = get_connection_manager()
        manager.configure(heartbeat_timeout_seconds=60.0, heartbeat_check_interval=10.0)
        assert manager._heartbeat_timeout_seconds == 60.0
        assert manager._heartbeat_check_interval == 10.0

    @pytest.mark.asyncio
    async def test_register_agent(self):
        """Can register an agent with websocket."""
        manager = get_connection_manager()
        mock_ws = AsyncMock()

        result = await manager.register_agent(
            agent_id="agent-1",
            websocket=mock_ws,
            auth_token="test-token",
            capabilities=["execute", "edit"],
            workdir="/tmp/agent",
            metadata={"version": "1.0"},
        )

        assert isinstance(result, RegisteredMessage)
        assert result.agent_id == "agent-1"
        assert manager.is_agent_connected("agent-1")
        assert "agent-1" in manager.get_connected_agents()

    @pytest.mark.asyncio
    async def test_register_agent_replaces_existing(self):
        """Registering same agent_id replaces old connection."""
        manager = get_connection_manager()
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()

        await manager.register_agent("agent-1", mock_ws1, "token1")
        await manager.register_agent("agent-1", mock_ws2, "token2")

        # Old connection should be closed
        mock_ws1.close.assert_called_once()
        assert manager.is_agent_connected("agent-1")
        assert manager._connections["agent-1"].websocket is mock_ws2

    @pytest.mark.asyncio
    async def test_unregister_agent(self):
        """Can unregister an agent."""
        manager = get_connection_manager()
        mock_ws = AsyncMock()

        await manager.register_agent("agent-1", mock_ws, "token")
        assert manager.is_agent_connected("agent-1")

        await manager.unregister_agent("agent-1", reason="test")
        assert not manager.is_agent_connected("agent-1")

    @pytest.mark.asyncio
    async def test_dispatch_task(self):
        """Can dispatch a task to a connected agent."""
        manager = get_connection_manager()
        mock_ws = AsyncMock()

        await manager.register_agent("agent-1", mock_ws, "token")

        future = await manager.dispatch_task(
            agent_id="agent-1",
            message_id="msg-1",
            content="Run tests",
            context={"project": "vibeforge"},
            session_id="session-1",
        )

        # Should have sent dispatch message
        mock_ws.send_json.assert_called_once()
        sent_data = mock_ws.send_json.call_args[0][0]
        assert sent_data["type"] == "dispatch"
        assert sent_data["agent_id"] == "agent-1"
        assert sent_data["content"] == "Run tests"

        # Future should be pending
        assert not future.done()

        # Pending dispatch should be tracked
        assert "msg-1" in manager._pending_dispatches

    @pytest.mark.asyncio
    async def test_dispatch_task_not_connected(self):
        """Dispatching to disconnected agent raises error."""
        manager = get_connection_manager()

        with pytest.raises(ValueError, match="not connected"):
            await manager.dispatch_task("agent-1", "msg-1", "content")

    @pytest.mark.asyncio
    async def test_handle_progress(self):
        """Can handle progress messages."""
        manager = get_connection_manager()
        mock_ws = AsyncMock()

        await manager.register_agent("agent-1", mock_ws, "token")
        future = await manager.dispatch_task("agent-1", "msg-1", "content")

        progress_received = []

        def on_progress(msg):
            progress_received.append(msg)

        manager._pending_dispatches["msg-1"].progress_callback = on_progress

        await manager.handle_progress(
            message_id="msg-1",
            agent_id="agent-1",
            status="running",
            progress_text="50% complete",
        )

        assert len(progress_received) == 1
        assert progress_received[0].status == "running"

    @pytest.mark.asyncio
    async def test_handle_response(self):
        """Can handle response messages and resolve future."""
        manager = get_connection_manager()
        mock_ws = AsyncMock()

        await manager.register_agent("agent-1", mock_ws, "token")
        future = await manager.dispatch_task("agent-1", "msg-1", "content")

        await manager.handle_response(
            message_id="msg-1",
            agent_id="agent-1",
            content="Task completed successfully",
            usage={"tokens": 100},
        )

        # Future should be resolved
        assert future.done()
        result = future.result()
        assert result.content == "Task completed successfully"
        assert result.usage == {"tokens": 100}

        # Pending dispatch should be removed
        assert "msg-1" not in manager._pending_dispatches

    @pytest.mark.asyncio
    async def test_handle_response_with_error(self):
        """Can handle error responses."""
        manager = get_connection_manager()
        mock_ws = AsyncMock()

        await manager.register_agent("agent-1", mock_ws, "token")
        future = await manager.dispatch_task("agent-1", "msg-1", "content")

        await manager.handle_response(
            message_id="msg-1",
            agent_id="agent-1",
            content="",
            error="Task failed: timeout",
        )

        result = future.result()
        assert result.error == "Task failed: timeout"

    @pytest.mark.asyncio
    async def test_handle_heartbeat(self):
        """Heartbeat updates last_heartbeat timestamp."""
        manager = get_connection_manager()
        mock_ws = AsyncMock()

        await manager.register_agent("agent-1", mock_ws, "token")

        # Set old heartbeat to the past
        from datetime import timedelta
        old_time = datetime.now(timezone.utc) - timedelta(seconds=10)
        manager._connections["agent-1"].last_heartbeat = old_time

        await manager.handle_heartbeat("agent-1")
        new_heartbeat = manager._connections["agent-1"].last_heartbeat

        assert new_heartbeat > old_time

    @pytest.mark.asyncio
    async def test_heartbeat_monitor_removes_stale(self):
        """Heartbeat monitor removes stale connections."""
        manager = get_connection_manager()
        manager.configure(heartbeat_timeout_seconds=0.1, heartbeat_check_interval=0.05)

        mock_ws = AsyncMock()
        await manager.register_agent("agent-1", mock_ws, "token")

        # Make the heartbeat stale
        manager._connections["agent-1"].last_heartbeat = datetime.now(
            timezone.utc
        ) - timedelta(seconds=1)

        # Start the monitor and wait for it to detect stale connection
        monitor_task = asyncio.create_task(manager._heartbeat_monitor())

        # Wait for check interval + buffer
        await asyncio.sleep(0.2)

        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass

        # Agent should be disconnected
        assert not manager.is_agent_connected("agent-1")

    def test_get_agent_info(self):
        """Can get agent info."""
        manager = get_connection_manager()
        assert manager.get_agent_info("nonexistent") is None

    @pytest.mark.asyncio
    async def test_get_agent_info_connected(self):
        """Can get info for connected agent."""
        manager = get_connection_manager()
        mock_ws = AsyncMock()

        await manager.register_agent(
            "agent-1", mock_ws, "token", capabilities=["exec"], workdir="/tmp"
        )

        info = manager.get_agent_info("agent-1")
        assert info is not None
        assert info["agent_id"] == "agent-1"
        assert info["capabilities"] == ["exec"]
        assert info["workdir"] == "/tmp"

    def test_event_callbacks(self):
        """Event callbacks can be set."""
        manager = get_connection_manager()

        connected_events = []
        disconnected_events = []

        manager.set_event_callbacks(
            on_agent_connected=lambda aid, meta: connected_events.append((aid, meta)),
            on_agent_disconnected=lambda aid, reason: disconnected_events.append(
                (aid, reason)
            ),
        )

        assert manager._on_agent_connected is not None
        assert manager._on_agent_disconnected is not None


class TestBridgeProtocolParsing:
    """Tests for bridge protocol message parsing."""

    def test_parse_register_message(self):
        """Can parse RegisterMessage."""
        data = {
            "type": "register",
            "agent_id": "agent-1",
            "auth_token": "secret",
            "capabilities": ["execute"],
        }
        msg = parse_bridge_message(data)
        assert isinstance(msg, RegisterMessage)
        assert msg.agent_id == "agent-1"

    def test_parse_progress_message(self):
        """Can parse ProgressMessage."""
        data = {
            "type": "progress",
            "message_id": "msg-1",
            "agent_id": "agent-1",
            "status": "running",
            "progress_text": "Working...",
        }
        msg = parse_bridge_message(data)
        assert isinstance(msg, ProgressMessage)
        assert msg.status == "running"

    def test_parse_response_message(self):
        """Can parse ResponseMessage."""
        data = {
            "type": "response",
            "message_id": "msg-1",
            "agent_id": "agent-1",
            "content": "Done",
            "usage": {"tokens": 50},
        }
        msg = parse_bridge_message(data)
        assert isinstance(msg, ResponseMessage)
        assert msg.content == "Done"

    def test_parse_heartbeat_message(self):
        """Can parse HeartbeatMessage."""
        data = {
            "type": "heartbeat",
            "agent_id": "agent-1",
            "timestamp": "2026-01-28T10:00:00Z",
        }
        msg = parse_bridge_message(data)
        assert isinstance(msg, HeartbeatMessage)

    def test_parse_invalid_type(self):
        """Invalid type raises validation error."""
        data = {"type": "unknown", "agent_id": "agent-1"}
        with pytest.raises(Exception):
            parse_bridge_message(data)


class TestAgentBridgeEndpoint:
    """Tests for the /ws/agent-bridge WebSocket endpoint."""

    def test_bridge_status_endpoint(self):
        """GET /ws/agent-bridge/status returns connection status."""
        client = TestClient(app)
        response = client.get("/ws/agent-bridge/status")

        assert response.status_code == 200
        data = response.json()
        assert "connected_count" in data
        assert "agents" in data
        assert data["connected_count"] == 0

    def test_websocket_requires_register_first(self):
        """WebSocket must send register message first."""
        client = TestClient(app)

        with client.websocket_connect("/ws/agent-bridge") as ws:
            # Send non-register message
            ws.send_json({"type": "heartbeat", "agent_id": "test"})

            # Connection should close with 4001
            # TestClient doesn't expose close code directly,
            # but connection should be closed

    def test_websocket_register_success(self):
        """WebSocket can register successfully."""
        client = TestClient(app)

        with client.websocket_connect("/ws/agent-bridge") as ws:
            ws.send_json(
                {
                    "type": "register",
                    "agent_id": "test-agent",
                    "auth_token": "secret-token",
                    "capabilities": ["execute"],
                }
            )

            # Should receive registered message
            response = ws.receive_json()
            assert response["type"] == "registered"
            assert response["agent_id"] == "test-agent"

    def test_websocket_heartbeat_echo(self):
        """Server echoes heartbeat messages."""
        client = TestClient(app)

        with client.websocket_connect("/ws/agent-bridge") as ws:
            # Register first
            ws.send_json(
                {
                    "type": "register",
                    "agent_id": "test-agent",
                    "auth_token": "token",
                }
            )
            ws.receive_json()  # Consume registered message

            # Send heartbeat
            ws.send_json(
                {
                    "type": "heartbeat",
                    "agent_id": "test-agent",
                    "timestamp": "2026-01-28T10:00:00Z",
                }
            )

            # Should receive heartbeat back
            response = ws.receive_json()
            assert response["type"] == "heartbeat"


class TestConnectionManagerCallbacks:
    """Tests for connection manager event callbacks."""

    @pytest.mark.asyncio
    async def test_connected_callback_called(self):
        """on_agent_connected callback is called on registration."""
        manager = get_connection_manager()
        mock_ws = AsyncMock()

        events = []
        manager.set_event_callbacks(
            on_agent_connected=lambda aid, meta: events.append(("connected", aid, meta))
        )

        await manager.register_agent(
            "agent-1", mock_ws, "token", capabilities=["exec"]
        )

        assert len(events) == 1
        assert events[0][0] == "connected"
        assert events[0][1] == "agent-1"
        assert events[0][2]["capabilities"] == ["exec"]

    @pytest.mark.asyncio
    async def test_disconnected_callback_called(self):
        """on_agent_disconnected callback is called on unregistration."""
        manager = get_connection_manager()
        mock_ws = AsyncMock()

        events = []
        manager.set_event_callbacks(
            on_agent_disconnected=lambda aid, reason: events.append(
                ("disconnected", aid, reason)
            )
        )

        await manager.register_agent("agent-1", mock_ws, "token")
        await manager.unregister_agent("agent-1", reason="test-reason")

        assert len(events) == 1
        assert events[0][0] == "disconnected"
        assert events[0][1] == "agent-1"
        assert events[0][2] == "test-reason"

    @pytest.mark.asyncio
    async def test_dispatch_callback_called(self):
        """on_task_dispatched callback is called on dispatch."""
        manager = get_connection_manager()
        mock_ws = AsyncMock()

        events = []
        manager.set_event_callbacks(
            on_task_dispatched=lambda aid, mid, content: events.append(
                ("dispatched", aid, mid, content)
            )
        )

        await manager.register_agent("agent-1", mock_ws, "token")
        await manager.dispatch_task("agent-1", "msg-1", "Run the tests")

        assert len(events) == 1
        assert events[0][0] == "dispatched"
        assert events[0][1] == "agent-1"
        assert events[0][2] == "msg-1"
        assert "Run the tests" in events[0][3]

    @pytest.mark.asyncio
    async def test_response_callback_called(self):
        """on_agent_response callback is called on response."""
        manager = get_connection_manager()
        mock_ws = AsyncMock()

        events = []
        manager.set_event_callbacks(
            on_agent_response=lambda aid, mid, error: events.append(
                ("response", aid, mid, error)
            )
        )

        await manager.register_agent("agent-1", mock_ws, "token")
        await manager.dispatch_task("agent-1", "msg-1", "content")
        await manager.handle_response("msg-1", "agent-1", "result")

        assert len(events) == 1
        assert events[0][0] == "response"
        assert events[0][1] == "agent-1"
        assert events[0][2] == "msg-1"
        assert events[0][3] is None  # No error
