"""Agent Bridge WebSocket endpoint.

TASK-007: Provides /ws/agent-bridge WebSocket endpoint for remote agent connections.
Remote Agent Bridge services connect here to register agents, receive task dispatches,
and send back progress/responses.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from vibeforge_api.core.connection_manager import get_connection_manager
from vibeforge_api.core.event_log import Event, EventLog, EventType
from vibeforge_api.core.workspace import WorkspaceManager
from vibeforge_api.models.bridge_protocol import (
    HeartbeatMessage,
    ProgressMessage,
    RegisterMessage,
    ResponseMessage,
    parse_bridge_message,
)

router = APIRouter(prefix="/ws", tags=["agent-bridge"])


def _emit_event(
    session_id: str,
    event_type: EventType,
    message: str,
    agent_id: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Emit an event to the event log."""
    workspace_manager = WorkspaceManager()
    event_log = EventLog(workspace_manager.workspace_root)

    event = Event(
        event_type=event_type,
        timestamp=datetime.now(timezone.utc),
        session_id=session_id,
        message=message,
        metadata={"agent_id": agent_id, **(metadata or {})},
    )
    event_log.append(event)


@router.websocket("/agent-bridge")
async def agent_bridge_websocket(websocket: WebSocket):
    """WebSocket endpoint for agent bridge connections.

    Protocol:
    1. Client connects
    2. Client sends RegisterMessage with agent_id and auth_token
    3. Server validates and sends RegisteredMessage
    4. Server can send DispatchMessage for tasks
    5. Client sends ProgressMessage during task execution
    6. Client sends ResponseMessage when task complete
    7. Both sides send HeartbeatMessage to maintain connection

    Close codes:
    - 4001: First message must be register
    - 4002: Replaced by new connection
    - 4003: Heartbeat timeout
    - 4004: Invalid message format
    - 4005: Authentication failed
    """
    await websocket.accept()

    connection_manager = get_connection_manager()
    agent_id: str | None = None
    session_id: str | None = None

    try:
        # First message must be RegisterMessage
        try:
            raw = await websocket.receive_json()
        except Exception as e:
            await websocket.close(code=4004, reason=f"Invalid JSON: {e}")
            return

        try:
            msg = parse_bridge_message(raw)
        except Exception as e:
            await websocket.close(code=4004, reason=f"Invalid message format: {e}")
            return

        if not isinstance(msg, RegisterMessage):
            await websocket.close(code=4001, reason="First message must be register")
            return

        # TODO: Validate auth_token against configured tokens
        # For now, accept any non-empty token
        if not msg.auth_token:
            await websocket.close(code=4005, reason="Authentication failed: empty token")
            return

        # Register the agent
        agent_id = msg.agent_id
        registered_msg = await connection_manager.register_agent(
            agent_id=msg.agent_id,
            websocket=websocket,
            auth_token=msg.auth_token,
            capabilities=msg.capabilities,
            workdir=msg.workdir,
            metadata=msg.metadata,
        )
        session_id = registered_msg.session_id

        # Emit connected event
        _emit_event(
            session_id=session_id,
            event_type=EventType.AGENT_CONNECTED,
            message=f"Agent {agent_id} connected",
            agent_id=agent_id,
            metadata={
                "capabilities": msg.capabilities,
                "workdir": msg.workdir,
            },
        )

        # Send RegisteredMessage back
        await websocket.send_json(registered_msg.model_dump())

        # Main message loop
        while True:
            try:
                raw = await websocket.receive_json()
            except Exception:
                # Connection closed or invalid JSON
                break

            try:
                msg = parse_bridge_message(raw)
            except Exception:
                # Invalid message format, skip but don't disconnect
                continue

            if isinstance(msg, ProgressMessage):
                await connection_manager.handle_progress(
                    message_id=msg.message_id,
                    agent_id=msg.agent_id,
                    status=msg.status,
                    progress_text=msg.progress_text,
                    metadata=msg.metadata,
                )

                # Emit progress event
                _emit_event(
                    session_id=session_id,
                    event_type=EventType.AGENT_PROGRESS,
                    message=f"Agent {msg.agent_id} progress: {msg.status}",
                    agent_id=msg.agent_id,
                    metadata={
                        "message_id": msg.message_id,
                        "status": msg.status,
                        "progress_text": msg.progress_text,
                    },
                )

            elif isinstance(msg, ResponseMessage):
                await connection_manager.handle_response(
                    message_id=msg.message_id,
                    agent_id=msg.agent_id,
                    content=msg.content,
                    usage=msg.usage,
                    error=msg.error,
                )

                # Emit response or error event
                if msg.error:
                    _emit_event(
                        session_id=session_id,
                        event_type=EventType.AGENT_ERROR,
                        message=f"Agent {msg.agent_id} error: {msg.error}",
                        agent_id=msg.agent_id,
                        metadata={
                            "message_id": msg.message_id,
                            "error": msg.error,
                        },
                    )
                else:
                    _emit_event(
                        session_id=session_id,
                        event_type=EventType.AGENT_RESPONSE,
                        message=f"Agent {msg.agent_id} responded",
                        agent_id=msg.agent_id,
                        metadata={
                            "message_id": msg.message_id,
                            "content": msg.content,
                            "content_length": len(msg.content),
                            "usage": msg.usage,
                        },
                    )

            elif isinstance(msg, HeartbeatMessage):
                await connection_manager.handle_heartbeat(msg.agent_id)
                # Echo heartbeat back
                await websocket.send_json(msg.model_dump())

            # Other message types are ignored

    except WebSocketDisconnect:
        pass
    except Exception:
        # Unexpected error
        pass
    finally:
        if agent_id:
            # Emit disconnected event
            if session_id:
                _emit_event(
                    session_id=session_id,
                    event_type=EventType.AGENT_DISCONNECTED,
                    message=f"Agent {agent_id} disconnected",
                    agent_id=agent_id,
                )

            await connection_manager.unregister_agent(agent_id)


@router.get("/agent-bridge/status")
async def get_bridge_status():
    """Get status of all connected agents."""
    connection_manager = get_connection_manager()
    connected = connection_manager.get_connected_agents()

    agents = []
    for agent_id in connected:
        info = connection_manager.get_agent_info(agent_id)
        if info:
            agents.append(info)

    return {
        "connected_count": len(agents),
        "agents": agents,
    }
