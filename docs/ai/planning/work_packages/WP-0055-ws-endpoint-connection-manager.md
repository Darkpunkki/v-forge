# WP-0055 — WebSocket Endpoint + Connection Manager

## Metadata
- **Status:** Done
- **Completed:** 2026-01-28
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Epic:** EPIC-002 (Real-Time Control Bridge)
- **Tasks:** TASK-007, TASK-010, TASK-011, TASK-008, TASK-012
- **Dependencies:** WP-0054 ✓ (bridge protocol models + event types)

## Goal

Build the WebSocket infrastructure that allows remote Agent Bridge services to connect to VibeForge, register agents, receive task dispatches, and send back progress/responses. This is the server-side control channel for real agent orchestration.

## Prerequisites (from WP-0054)

- `apps/api/vibeforge_api/models/bridge_protocol.py`: 6 message types (RegisterMessage, RegisteredMessage, DispatchMessage, ProgressMessage, ResponseMessage, HeartbeatMessage)
- `apps/api/vibeforge_api/core/event_log.py`: 7 agent bridge event types (AGENT_CONNECTED, AGENT_DISCONNECTED, TASK_DISPATCHED, AGENT_PROGRESS, AGENT_RESPONSE, AGENT_ERROR, AGENT_HEARTBEAT_LOST)
- `apps/api/vibeforge_api/core/session.py`: agent_connections, pending_dispatches, response_buffer fields

## Implementation Steps

### Step 1: TASK-010 — RemoteAgentConnectionManager

Create `apps/api/vibeforge_api/core/connection_manager.py`:

```python
class RemoteAgentConnectionManager:
    """Singleton that manages WebSocket connections to remote agent bridges."""

    def __init__(self):
        self._connections: dict[str, WebSocket] = {}  # agent_id -> websocket
        self._agent_metadata: dict[str, dict] = {}    # agent_id -> metadata
        self._pending_dispatches: dict[str, asyncio.Future] = {}  # message_id -> future
        self._last_heartbeat: dict[str, datetime] = {}  # agent_id -> timestamp
        self._heartbeat_timeout_seconds: float = 30.0

    async def register_agent(agent_id, websocket, auth_token, capabilities, workdir, metadata)
    async def unregister_agent(agent_id)
    async def dispatch_task(agent_id, message_id, content, context, session_id) -> asyncio.Future
    async def handle_progress(message_id, agent_id, status, progress_text, metadata)
    async def handle_response(message_id, agent_id, content, usage, error)
    async def handle_heartbeat(agent_id)
    def get_connected_agents() -> list[str]
    def is_agent_connected(agent_id) -> bool
```

### Step 2: TASK-011 — Heartbeat Monitoring

Add background task that checks `_last_heartbeat` against configurable timeout:
- If agent hasn't sent heartbeat in `heartbeat_timeout_seconds`, mark as disconnected
- Emit AGENT_HEARTBEAT_LOST event
- Clean up connection state

### Step 3: TASK-007 — WebSocket Endpoint

Create `apps/api/vibeforge_api/routers/agent_bridge.py`:

```python
router = APIRouter(prefix="/ws", tags=["agent-bridge"])

@router.websocket("/agent-bridge")
async def agent_bridge_websocket(websocket: WebSocket):
    """WebSocket endpoint for agent bridge connections."""
    await websocket.accept()
    agent_id = None

    try:
        # First message must be RegisterMessage
        raw = await websocket.receive_json()
        msg = parse_bridge_message(raw)
        if not isinstance(msg, RegisterMessage):
            await websocket.close(code=4001, reason="First message must be register")
            return

        # Validate auth_token (placeholder for now)
        # Register agent
        agent_id = msg.agent_id
        await connection_manager.register_agent(...)

        # Send RegisteredMessage back
        await websocket.send_json(RegisteredMessage(...).model_dump())

        # Main message loop
        while True:
            raw = await websocket.receive_json()
            msg = parse_bridge_message(raw)

            if isinstance(msg, ProgressMessage):
                await connection_manager.handle_progress(...)
            elif isinstance(msg, ResponseMessage):
                await connection_manager.handle_response(...)
            elif isinstance(msg, HeartbeatMessage):
                await connection_manager.handle_heartbeat(msg.agent_id)
                # Echo heartbeat back
                await websocket.send_json(msg.model_dump())
            else:
                # Unknown message type
                pass

    except WebSocketDisconnect:
        pass
    finally:
        if agent_id:
            await connection_manager.unregister_agent(agent_id)
```

### Step 4: TASK-008 — Integration

- Mount `agent_bridge.router` in `main.py`
- Add `get_connection_manager()` helper for dependency injection
- Wire event logging for all connection events

### Step 5: TASK-012 — Unit Tests

Create `apps/api/tests/test_agent_bridge_ws.py`:
- Test WebSocket connection lifecycle (connect → register → disconnect)
- Test registration validation (must register first, auth token)
- Test heartbeat monitoring (timeout detection)
- Test dispatch → progress → response flow
- Test multiple agents connected simultaneously

## Verification

```bash
cd apps/api && python -m pytest tests/test_agent_bridge_ws.py -v
```

## Files to Create/Modify

- `apps/api/vibeforge_api/core/connection_manager.py` (new)
- `apps/api/vibeforge_api/routers/agent_bridge.py` (new)
- `apps/api/vibeforge_api/main.py` (add router)
- `apps/api/tests/test_agent_bridge_ws.py` (new)

## Done Means

- [x] RemoteAgentConnectionManager singleton implemented with register/unregister/dispatch/response handling
- [x] Heartbeat monitoring with configurable timeout
- [x] /ws/agent-bridge WebSocket endpoint accepts connections
- [x] Protocol messages parsed and handled correctly
- [x] Event logging for all connection events
- [x] All tests pass (29 new tests)
