"""Remote Agent Connection Manager.

TASK-010, TASK-011: Manages WebSocket connections to remote Agent Bridge services.
Handles agent registration, task dispatch, response buffering, and heartbeat monitoring.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from fastapi import WebSocket

from vibeforge_api.models.bridge_protocol import (
    DispatchMessage,
    RegisteredMessage,
    ResponseMessage,
    ProgressMessage,
)


@dataclass
class AgentConnection:
    """Represents a connected remote agent."""

    agent_id: str
    websocket: WebSocket
    auth_token: str
    capabilities: list[str] = field(default_factory=list)
    workdir: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PendingDispatch:
    """Tracks a pending task dispatch waiting for response."""

    message_id: str
    agent_id: str
    session_id: Optional[str]
    content: str
    context: dict[str, Any]
    dispatched_at: datetime
    future: asyncio.Future[ResponseMessage]
    progress_callback: Optional[Callable[[ProgressMessage], None]] = None


class RemoteAgentConnectionManager:
    """Singleton that manages WebSocket connections to remote agent bridges.

    Responsibilities:
    - Maintain registry of connected agents and their WebSocket connections
    - Dispatch tasks to agents and track pending responses
    - Buffer responses for async consumption
    - Monitor heartbeats and detect stale connections
    """

    _instance: Optional["RemoteAgentConnectionManager"] = None

    def __new__(cls) -> "RemoteAgentConnectionManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # agent_id -> AgentConnection
        self._connections: dict[str, AgentConnection] = {}

        # message_id -> PendingDispatch
        self._pending_dispatches: dict[str, PendingDispatch] = {}

        # Heartbeat configuration
        self._heartbeat_timeout_seconds: float = 30.0
        self._heartbeat_check_interval: float = 5.0

        # Event callbacks (for event logging integration)
        self._on_agent_connected: Optional[Callable[[str, dict], None]] = None
        self._on_agent_disconnected: Optional[Callable[[str, str], None]] = None
        self._on_task_dispatched: Optional[Callable[[str, str, str], None]] = None
        self._on_agent_progress: Optional[Callable[[str, str, str], None]] = None
        self._on_agent_response: Optional[Callable[[str, str, Optional[str]], None]] = None
        self._on_heartbeat_lost: Optional[Callable[[str], None]] = None

        # Background task for heartbeat monitoring
        self._heartbeat_task: Optional[asyncio.Task] = None

    def configure(
        self,
        heartbeat_timeout_seconds: float = 30.0,
        heartbeat_check_interval: float = 5.0,
    ) -> None:
        """Configure heartbeat parameters.

        Args:
            heartbeat_timeout_seconds: How long without heartbeat before considering agent dead
            heartbeat_check_interval: How often to check for stale connections
        """
        self._heartbeat_timeout_seconds = heartbeat_timeout_seconds
        self._heartbeat_check_interval = heartbeat_check_interval

    def set_event_callbacks(
        self,
        on_agent_connected: Optional[Callable[[str, dict], None]] = None,
        on_agent_disconnected: Optional[Callable[[str, str], None]] = None,
        on_task_dispatched: Optional[Callable[[str, str, str], None]] = None,
        on_agent_progress: Optional[Callable[[str, str, str], None]] = None,
        on_agent_response: Optional[Callable[[str, str, Optional[str]], None]] = None,
        on_heartbeat_lost: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Set callbacks for event logging integration."""
        self._on_agent_connected = on_agent_connected
        self._on_agent_disconnected = on_agent_disconnected
        self._on_task_dispatched = on_task_dispatched
        self._on_agent_progress = on_agent_progress
        self._on_agent_response = on_agent_response
        self._on_heartbeat_lost = on_heartbeat_lost

    async def register_agent(
        self,
        agent_id: str,
        websocket: WebSocket,
        auth_token: str,
        capabilities: Optional[list[str]] = None,
        workdir: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> RegisteredMessage:
        """Register a new agent connection.

        Args:
            agent_id: Unique identifier for the agent
            websocket: The WebSocket connection
            auth_token: Authentication token from the bridge
            capabilities: List of agent capabilities
            workdir: Working directory on the agent host
            metadata: Additional metadata about the agent

        Returns:
            RegisteredMessage to send back to the agent

        Raises:
            ValueError: If agent_id is already connected
        """
        if agent_id in self._connections:
            # Close existing connection if re-registering
            old_conn = self._connections[agent_id]
            try:
                await old_conn.websocket.close(code=4002, reason="Replaced by new connection")
            except Exception:
                pass

        connection = AgentConnection(
            agent_id=agent_id,
            websocket=websocket,
            auth_token=auth_token,
            capabilities=capabilities or [],
            workdir=workdir,
            metadata=metadata or {},
        )
        self._connections[agent_id] = connection

        if self._on_agent_connected:
            self._on_agent_connected(agent_id, {
                "capabilities": connection.capabilities,
                "workdir": connection.workdir,
                "metadata": connection.metadata,
            })

        # Start heartbeat monitoring if not already running
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())

        # Generate session_id for the connection (could be passed in or generated)
        session_id = metadata.get("session_id") if metadata else None
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())

        return RegisteredMessage(
            session_id=session_id,
            agent_id=agent_id,
            message="Registration successful",
        )

    async def unregister_agent(self, agent_id: str, reason: str = "disconnected") -> None:
        """Unregister an agent connection.

        Args:
            agent_id: The agent to unregister
            reason: Why the agent is being unregistered
        """
        if agent_id not in self._connections:
            return

        connection = self._connections.pop(agent_id)

        # Cancel any pending dispatches for this agent
        for message_id, dispatch in list(self._pending_dispatches.items()):
            if dispatch.agent_id == agent_id:
                dispatch.future.cancel()
                del self._pending_dispatches[message_id]

        if self._on_agent_disconnected:
            self._on_agent_disconnected(agent_id, reason)

        # Stop heartbeat monitor if no more connections
        if not self._connections and self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

    async def dispatch_task(
        self,
        agent_id: str,
        message_id: str,
        content: str,
        context: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
        progress_callback: Optional[Callable[[ProgressMessage], None]] = None,
    ) -> asyncio.Future[ResponseMessage]:
        """Dispatch a task to a connected agent.

        Args:
            agent_id: Target agent
            message_id: Unique ID for this dispatch
            content: Task content/instructions
            context: Additional context for the task
            session_id: Session this dispatch belongs to
            progress_callback: Optional callback for progress updates

        Returns:
            Future that resolves with the ResponseMessage

        Raises:
            ValueError: If agent is not connected
        """
        if agent_id not in self._connections:
            raise ValueError(f"Agent {agent_id} is not connected")

        connection = self._connections[agent_id]

        # Create dispatch message
        dispatch_msg = DispatchMessage(
            message_id=message_id,
            agent_id=agent_id,
            content=content,
            context=context or {},
            session_id=session_id,
        )

        # Create future for response
        loop = asyncio.get_event_loop()
        future: asyncio.Future[ResponseMessage] = loop.create_future()

        # Track pending dispatch
        self._pending_dispatches[message_id] = PendingDispatch(
            message_id=message_id,
            agent_id=agent_id,
            session_id=session_id,
            content=content,
            context=context or {},
            dispatched_at=datetime.now(timezone.utc),
            future=future,
            progress_callback=progress_callback,
        )

        # Send dispatch message
        await connection.websocket.send_json(dispatch_msg.model_dump())

        if self._on_task_dispatched:
            self._on_task_dispatched(agent_id, message_id, content[:100])

        return future

    async def handle_progress(
        self,
        message_id: str,
        agent_id: str,
        status: str,
        progress_text: str = "",
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Handle a progress message from an agent.

        Args:
            message_id: The dispatch this progress is for
            agent_id: The agent reporting progress
            status: Current status
            progress_text: Progress description
            metadata: Additional progress metadata
        """
        if message_id not in self._pending_dispatches:
            return

        dispatch = self._pending_dispatches[message_id]
        if dispatch.agent_id != agent_id:
            return

        progress_msg = ProgressMessage(
            message_id=message_id,
            agent_id=agent_id,
            status=status,
            progress_text=progress_text,
            metadata=metadata or {},
        )

        if dispatch.progress_callback:
            dispatch.progress_callback(progress_msg)

        if self._on_agent_progress:
            self._on_agent_progress(agent_id, message_id, status)

    async def handle_response(
        self,
        message_id: str,
        agent_id: str,
        content: str = "",
        usage: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """Handle a response message from an agent.

        Args:
            message_id: The dispatch this is responding to
            agent_id: The agent responding
            content: Response content
            usage: Token usage stats
            error: Error message if failed
        """
        if message_id not in self._pending_dispatches:
            return

        dispatch = self._pending_dispatches.pop(message_id)
        if dispatch.agent_id != agent_id:
            self._pending_dispatches[message_id] = dispatch
            return

        response_msg = ResponseMessage(
            message_id=message_id,
            agent_id=agent_id,
            content=content,
            usage=usage or {},
            error=error,
        )

        # Resolve the future
        if not dispatch.future.done():
            dispatch.future.set_result(response_msg)

        if self._on_agent_response:
            self._on_agent_response(agent_id, message_id, error)

    async def handle_heartbeat(self, agent_id: str) -> None:
        """Handle a heartbeat message from an agent.

        Args:
            agent_id: The agent sending heartbeat
        """
        if agent_id in self._connections:
            self._connections[agent_id].last_heartbeat = datetime.now(timezone.utc)

    def get_connected_agents(self) -> list[str]:
        """Get list of connected agent IDs."""
        return list(self._connections.keys())

    def is_agent_connected(self, agent_id: str) -> bool:
        """Check if an agent is currently connected."""
        return agent_id in self._connections

    def get_agent_info(self, agent_id: str) -> Optional[dict[str, Any]]:
        """Get information about a connected agent."""
        if agent_id not in self._connections:
            return None

        conn = self._connections[agent_id]
        return {
            "agent_id": conn.agent_id,
            "capabilities": conn.capabilities,
            "workdir": conn.workdir,
            "metadata": conn.metadata,
            "connected_at": conn.connected_at.isoformat(),
            "last_heartbeat": conn.last_heartbeat.isoformat(),
        }

    def get_pending_dispatch(self, message_id: str) -> Optional[dict[str, Any]]:
        """Get information about a pending dispatch."""
        if message_id not in self._pending_dispatches:
            return None

        dispatch = self._pending_dispatches[message_id]
        return {
            "message_id": dispatch.message_id,
            "agent_id": dispatch.agent_id,
            "session_id": dispatch.session_id,
            "content": dispatch.content[:100],
            "dispatched_at": dispatch.dispatched_at.isoformat(),
        }

    async def _heartbeat_monitor(self) -> None:
        """Background task that monitors heartbeats and cleans up stale connections.

        TASK-011: Runs periodically and disconnects agents that haven't sent
        a heartbeat within the configured timeout.
        """
        while True:
            try:
                await asyncio.sleep(self._heartbeat_check_interval)

                now = datetime.now(timezone.utc)
                stale_agents: list[str] = []

                for agent_id, conn in self._connections.items():
                    elapsed = (now - conn.last_heartbeat).total_seconds()
                    if elapsed > self._heartbeat_timeout_seconds:
                        stale_agents.append(agent_id)

                for agent_id in stale_agents:
                    conn = self._connections.get(agent_id)
                    if conn:
                        try:
                            await conn.websocket.close(
                                code=4003, reason="Heartbeat timeout"
                            )
                        except Exception:
                            pass

                    if self._on_heartbeat_lost:
                        self._on_heartbeat_lost(agent_id)

                    await self.unregister_agent(agent_id, reason="heartbeat_timeout")

            except asyncio.CancelledError:
                break
            except Exception:
                # Log but don't crash the monitor
                pass


# Singleton instance
_connection_manager: Optional[RemoteAgentConnectionManager] = None


def get_connection_manager() -> RemoteAgentConnectionManager:
    """Get the singleton connection manager instance."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = RemoteAgentConnectionManager()
    return _connection_manager


def reset_connection_manager() -> None:
    """Reset the singleton (for testing)."""
    global _connection_manager
    if _connection_manager is not None:
        # Cancel heartbeat task if running
        if _connection_manager._heartbeat_task:
            try:
                _connection_manager._heartbeat_task.cancel()
            except RuntimeError:
                # Event loop may already be closed
                pass
        _connection_manager._heartbeat_task = None
        _connection_manager._connections.clear()
        _connection_manager._pending_dispatches.clear()
        _connection_manager._initialized = False
    _connection_manager = None
    RemoteAgentConnectionManager._instance = None
