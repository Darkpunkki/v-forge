"""Control panel API endpoints.

Provides observability and monitoring endpoints for the control panel UI.
Separate from the end-user session flow.
"""

from typing import Optional
from collections import Counter
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from datetime import datetime, timezone

# VF-193: Import workflow request/response models
from vibeforge_api.models import (
    InitializeAgentsRequest,
    AssignAgentRoleRequest,
    SetMainTaskRequest,
    ConfigureAgentFlowRequest,
    # VF-200/VF-201: Simulation request/response models
    SimulationConfigRequest,
    SimulationStartRequest,
    SimulationResetRequest,
    TickRequest,
    RegisterAgentRequest,
    DispatchTaskRequest,
    FollowUpRequest,
    AgentListResponse,
    AgentDetailResponse,
    TaskDispatchResponse,
    TaskStatusResponse,
)

from vibeforge_api.core.auth import require_auth

router = APIRouter(
    prefix="/control",
    tags=["control"],
    dependencies=[Depends(require_auth)],
)

_MAX_TASK_CONTENT_LENGTH = 10_000
_AGENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]{1,64}$")
_DISALLOWED_CONTENT_PATTERN = re.compile(r"[\x00]")


def _validate_agent_id(agent_id: str) -> str:
    if not _AGENT_ID_PATTERN.fullmatch(agent_id or ""):
        raise HTTPException(
            status_code=400,
            detail="Invalid agent_id format. Use alphanumeric characters and hyphens only.",
        )
    return agent_id


def _sanitize_task_content(content: str) -> str:
    if content is None:
        raise HTTPException(status_code=400, detail="content is required")

    cleaned = _DISALLOWED_CONTENT_PATTERN.sub("", content).strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="content must not be empty")
    if len(cleaned) > _MAX_TASK_CONTENT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"content must be <= {_MAX_TASK_CONTENT_LENGTH} characters",
        )
    return cleaned

_control_context_session_id: str | None = None
_control_context_lock = asyncio.Lock()


async def _get_control_context_session_id() -> str:
    global _control_context_session_id
    from vibeforge_api.core.session import session_store

    if _control_context_session_id:
        session = session_store.get_session(_control_context_session_id)
        if session:
            return _control_context_session_id

    async with _control_context_lock:
        if _control_context_session_id:
            session = session_store.get_session(_control_context_session_id)
            if session:
                return _control_context_session_id

        session = session_store.create_session()
        _control_context_session_id = session.session_id
        return _control_context_session_id


def _slugify_agent_name(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return cleaned or "agent"


def _generate_agent_id(name: str, manager) -> str:
    base = _slugify_agent_name(name)
    agent_id = f"{base}-{uuid.uuid4().hex[:6]}"
    while manager.get_registered_agent(agent_id):
        agent_id = f"{base}-{uuid.uuid4().hex[:6]}"
    return agent_id


def _build_agent_view(
    agent_id: str,
    registered: Optional[dict],
    connection_info: Optional[dict],
) -> dict:
    name = registered.get("name") if registered else agent_id
    endpoint_url = registered.get("endpoint_url") if registered else ""
    status = "connected" if connection_info else "disconnected"

    return {
        "agent_id": agent_id,
        "name": name,
        "endpoint_url": endpoint_url,
        "status": status,
        "capabilities": (connection_info or {}).get("capabilities", []),
        "workdir": (connection_info or {}).get("workdir"),
        "metadata": (connection_info or {}).get("metadata", {}),
        "connected_at": (connection_info or {}).get("connected_at"),
        "last_heartbeat": (connection_info or {}).get("last_heartbeat"),
    }


def _emit_control_event(
    session_id: str,
    event_type,
    message: str,
    agent_id: str,
    metadata: Optional[dict] = None,
) -> None:
    from vibeforge_api.core.event_log import Event, EventLog
    from vibeforge_api.core.workspace import WorkspaceManager

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


@router.post("/sessions")
async def create_session():
    """Create a new session for control/simulation use."""
    from vibeforge_api.core.session import session_store

    session = session_store.create_session()
    return {"session_id": session.session_id, "phase": session.phase.value}


@router.get("/context")
async def get_control_context():
    """Get or create a stable control context session id."""
    session_id = await _get_control_context_session_id()
    return {"control_session_id": session_id}


@router.post("/agents/register", response_model=AgentDetailResponse)
async def register_agent(request: RegisterAgentRequest):
    """Register a remote agent with name + endpoint URL."""
    from vibeforge_api.core.connection_manager import get_connection_manager

    manager = get_connection_manager()
    name = request.name.strip()
    endpoint_url = request.endpoint_url.strip()

    if not name or not endpoint_url:
        raise HTTPException(status_code=400, detail="name and endpoint_url are required")

    agent_id = _generate_agent_id(name, manager)
    registered = manager.register_agent_info(agent_id, name, endpoint_url)
    connection_info = manager.get_agent_info(agent_id)
    agent_view = _build_agent_view(agent_id, registered, connection_info)

    return AgentDetailResponse(agent=agent_view)


@router.get("/agents", response_model=AgentListResponse)
async def list_agents():
    """List all registered agents with connection status."""
    from vibeforge_api.core.connection_manager import get_connection_manager

    manager = get_connection_manager()
    agents = []
    seen: set[str] = set()

    for entry in manager.get_registered_agents():
        agent_id = entry["agent_id"]
        connection_info = manager.get_agent_info(agent_id)
        agents.append(_build_agent_view(agent_id, entry, connection_info))
        seen.add(agent_id)

    for agent_id in manager.get_connected_agents():
        if agent_id in seen:
            continue
        connection_info = manager.get_agent_info(agent_id)
        agents.append(_build_agent_view(agent_id, None, connection_info))
        seen.add(agent_id)

    return AgentListResponse(agents=agents, total=len(agents))


@router.get("/agents/{agent_id}", response_model=AgentDetailResponse)
async def get_agent_detail(agent_id: str):
    """Get agent details and connection status."""
    from vibeforge_api.core.connection_manager import get_connection_manager

    agent_id = _validate_agent_id(agent_id)
    manager = get_connection_manager()
    registered = manager.get_registered_agent(agent_id)
    connection_info = manager.get_agent_info(agent_id)

    if not registered and not connection_info:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent_view = _build_agent_view(agent_id, registered, connection_info)
    return AgentDetailResponse(agent=agent_view)


@router.post("/agents/{agent_id}/dispatch", response_model=TaskDispatchResponse)
async def dispatch_agent_task(agent_id: str, request: DispatchTaskRequest):
    """Dispatch a task to a connected remote agent."""
    from vibeforge_api.core.connection_manager import get_connection_manager
    from vibeforge_api.core.event_log import EventType

    agent_id = _validate_agent_id(agent_id)
    content = _sanitize_task_content(request.content)

    manager = get_connection_manager()
    registered = manager.get_registered_agent(agent_id)
    if not registered and not manager.is_agent_connected(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")

    if not manager.is_agent_connected(agent_id):
        raise HTTPException(status_code=409, detail="Agent is not connected")

    message_id = str(uuid.uuid4())
    session_id = await _get_control_context_session_id()

    try:
        await manager.dispatch_task(
            agent_id=agent_id,
            message_id=message_id,
            content=content,
            context=request.context,
            session_id=session_id,
        )
    except ValueError:
        raise HTTPException(status_code=409, detail="Agent is not connected")

    _emit_control_event(
        session_id=session_id,
        event_type=EventType.TASK_DISPATCHED,
        message=f"Dispatched task to agent {agent_id}",
        agent_id=agent_id,
        metadata={"message_id": message_id},
    )

    return TaskDispatchResponse(
        agent_id=agent_id,
        message_id=message_id,
        status="dispatched",
        message="Task dispatched",
    )


@router.post("/agents/{agent_id}/followup", response_model=TaskDispatchResponse)
async def send_followup(agent_id: str, request: FollowUpRequest):
    """Send a follow-up message to an agent's active task."""
    from vibeforge_api.core.connection_manager import get_connection_manager
    from vibeforge_api.core.event_log import EventType

    agent_id = _validate_agent_id(agent_id)
    content = _sanitize_task_content(request.content)

    manager = get_connection_manager()
    registered = manager.get_registered_agent(agent_id)
    if not registered and not manager.is_agent_connected(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")

    if not manager.is_agent_connected(agent_id):
        raise HTTPException(status_code=409, detail="Agent is not connected")

    status_info = manager.get_agent_task_status(agent_id) or {}
    current_status = status_info.get("status", "idle")
    followup_to = status_info.get("message_id")

    if current_status in {"idle", "completed", "error"} or not followup_to:
        raise HTTPException(status_code=409, detail="No active task to follow up")

    message_id = str(uuid.uuid4())
    session_id = await _get_control_context_session_id()

    context = {
        "is_followup": True,
        "followup_to": followup_to,
    }

    try:
        await manager.dispatch_task(
            agent_id=agent_id,
            message_id=message_id,
            content=content,
            context=context,
            session_id=session_id,
        )
    except ValueError:
        raise HTTPException(status_code=409, detail="Agent is not connected")

    _emit_control_event(
        session_id=session_id,
        event_type=EventType.TASK_DISPATCHED,
        message=f"Sent follow-up to agent {agent_id}",
        agent_id=agent_id,
        metadata={"message_id": message_id, "followup_to": followup_to, "is_followup": True},
    )

    return TaskDispatchResponse(
        agent_id=agent_id,
        message_id=message_id,
        status="dispatched",
        message="Follow-up dispatched",
    )


@router.get("/agents/{agent_id}/task", response_model=TaskStatusResponse)
async def get_agent_task_status(agent_id: str):
    """Get current task status for an agent."""
    from vibeforge_api.core.connection_manager import get_connection_manager

    agent_id = _validate_agent_id(agent_id)
    manager = get_connection_manager()
    registered = manager.get_registered_agent(agent_id)
    connected = manager.is_agent_connected(agent_id)

    if not registered and not connected:
        raise HTTPException(status_code=404, detail="Agent not found")

    status_info = manager.get_agent_task_status(agent_id) or {}

    return TaskStatusResponse(
        agent_id=agent_id,
        status=status_info.get("status", "idle"),
        message_id=status_info.get("message_id"),
        error=status_info.get("error"),
    )


@router.get("/agents/{agent_id}/events")
async def stream_agent_events(agent_id: str):
    """Stream agent-specific events via SSE."""
    from vibeforge_api.core.connection_manager import get_connection_manager
    from vibeforge_api.core.event_log import EventLog
    from vibeforge_api.core.session import session_store
    from vibeforge_api.core.workspace import WorkspaceManager

    agent_id = _validate_agent_id(agent_id)
    manager = get_connection_manager()
    registered = manager.get_registered_agent(agent_id)
    connection_info = manager.get_agent_info(agent_id)

    if not registered and not connection_info:
        raise HTTPException(status_code=404, detail="Agent not found")

    session_id = None
    if connection_info:
        session_id = connection_info.get("session_id")
    if not session_id:
        session_id = await _get_control_context_session_id()

    workspace_manager = WorkspaceManager()
    event_log_path = workspace_manager.workspace_root / session_id / "events.jsonl"

    session = session_store.get_session(session_id)
    if not session and not event_log_path.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    event_log = EventLog(workspace_manager.workspace_root, use_cache=False)

    async def event_generator():
        events = event_log.get_events_filtered(session_id=session_id, agent_id=agent_id)
        for event in events:
            yield {
                "event": "agent_event",
                "data": json.dumps(event.to_dict()),
            }

        last_count = len(events)
        while True:
            await asyncio.sleep(1)
            current_events = event_log.get_events_filtered(
                session_id=session_id,
                agent_id=agent_id,
            )
            if len(current_events) > last_count:
                new_events = current_events[last_count:]
                for event in new_events:
                    yield {
                        "event": "agent_event",
                        "data": json.dumps(event.to_dict()),
                    }
                last_count = len(current_events)

    return EventSourceResponse(event_generator())


@router.get("/sessions/{session_id}/events")
async def stream_session_events(session_id: str):
    """Stream session events via Server-Sent Events (SSE)."""
    from vibeforge_api.core.event_log import EventLog
    from vibeforge_api.core.session import session_store
    from vibeforge_api.core.workspace import WorkspaceManager

    workspace_manager = WorkspaceManager()
    event_log_path = workspace_manager.workspace_root / session_id / "events.jsonl"

    # Allow streaming if session exists or there is an event log on disk.
    session = session_store.get_session(session_id)
    if not session and not event_log_path.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    # Disable cache so we always read fresh events from disk
    event_log = EventLog(workspace_manager.workspace_root, use_cache=False)

    async def event_generator():
        """Generate SSE events."""
        # Send existing events first
        events = event_log.get_events(session_id)
        for event in events:
            yield {
                "event": "session_event",
                "data": json.dumps(event.to_dict()),
            }

        # Then stream new events (poll for updates)
        last_count = len(events)
        while True:
            await asyncio.sleep(1)  # Poll every second

            # Check for new events
            current_events = event_log.get_events(session_id)
            if len(current_events) > last_count:
                new_events = current_events[last_count:]
                for event in new_events:
                    yield {
                        "event": "session_event",
                        "data": json.dumps(event.to_dict()),
                    }
                last_count = len(current_events)

    return EventSourceResponse(event_generator())


@router.get("/sessions/{session_id}/events/filter")
async def get_filtered_events(
    session_id: str,
    event_type: Optional[str] = None,
    tick_index: Optional[int] = None,
    tick_min: Optional[int] = None,
    tick_max: Optional[int] = None,
    agent_id: Optional[str] = None,
    limit: Optional[int] = None,
):
    """Get filtered events for a session (VF-206).

    Query params:
        event_type: Filter by event type (e.g., "tick_advanced", "message_sent")
        tick_index: Filter by exact tick index
        tick_min: Filter by minimum tick index (inclusive)
        tick_max: Filter by maximum tick index (inclusive)
        agent_id: Filter by agent ID
        limit: Maximum number of events to return (most recent)
    """
    from vibeforge_api.core.event_log import EventLog
    from vibeforge_api.core.workspace import WorkspaceManager

    workspace_manager = WorkspaceManager()
    workspace_path = workspace_manager.workspace_root / session_id

    if not workspace_path.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    event_log = EventLog(workspace_manager.workspace_root)
    events = event_log.get_events_filtered(
        session_id=session_id,
        event_type=event_type,
        tick_index=tick_index,
        tick_min=tick_min,
        tick_max=tick_max,
        agent_id=agent_id,
        limit=limit,
    )

    return {
        "events": [e.to_dict() for e in events],
        "total": len(events),
        "filters_applied": {
            "event_type": event_type,
            "tick_index": tick_index,
            "tick_min": tick_min,
            "tick_max": tick_max,
            "agent_id": agent_id,
            "limit": limit,
        },
    }


@router.get("/sessions/{session_id}/prompts")
async def get_session_prompts(session_id: str):
    """Get prompts sent during a session."""
    from vibeforge_api.core.event_log import EventLog, EventType
    from vibeforge_api.core.workspace import WorkspaceManager

    workspace_manager = WorkspaceManager()
    workspace_path = workspace_manager.workspace_root / session_id
    event_log_path = workspace_path / "events.jsonl"

    if not event_log_path.exists():
        raise HTTPException(status_code=404, detail="Event log not found")

    event_log = EventLog(workspace_manager.workspace_root)
    events = event_log.get_events(session_id, event_type=EventType.LLM_REQUEST_SENT)

    prompts = []
    for event in events:
        metadata = event.metadata or {}
        prompts.append({
            "timestamp": event.timestamp.isoformat(),
            "task_id": event.task_id,
            "agent_role": metadata.get("agent_role"),
            "model": metadata.get("model"),
            "prompt": metadata.get("prompt", ""),
            "system_message": metadata.get("system_message", ""),
            "max_tokens": metadata.get("max_tokens"),
            "temperature": metadata.get("temperature"),
        })

    return {"prompts": prompts, "total": len(prompts)}


@router.get("/sessions/{session_id}/llm-trace")
async def get_session_llm_trace(session_id: str):
    """Get prompts and responses for a session."""
    from vibeforge_api.core.event_log import EventLog, EventType
    from vibeforge_api.core.workspace import WorkspaceManager

    workspace_manager = WorkspaceManager()
    workspace_path = workspace_manager.workspace_root / session_id
    event_log_path = workspace_path / "events.jsonl"

    if not event_log_path.exists():
        raise HTTPException(status_code=404, detail="Event log not found")

    event_log = EventLog(workspace_manager.workspace_root)
    events = event_log.get_events(session_id)

    traces: dict[str, dict] = {}

    def ensure_entry(key: str, timestamp: datetime) -> dict:
        if key not in traces:
            traces[key] = {
                "request_id": key,
                "timestamp": timestamp.isoformat(),
                "task_id": None,
                "agent_role": None,
                "model": None,
                "prompt": "",
                "system_message": "",
                "max_tokens": None,
                "temperature": None,
                "response": None,
                "response_model": None,
                "response_timestamp": None,
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None,
            }
        return traces[key]

    for event in events:
        if event.event_type == EventType.LLM_REQUEST_SENT:
            metadata = event.metadata or {}
            request_id = metadata.get("request_id") or f"request::{event.timestamp.isoformat()}"
            entry = ensure_entry(request_id, event.timestamp)
            entry.update(
                {
                    "request_id": request_id,
                    "timestamp": event.timestamp.isoformat(),
                    "task_id": event.task_id,
                    "agent_role": metadata.get("agent_role"),
                    "model": metadata.get("model"),
                    "prompt": metadata.get("prompt", ""),
                    "system_message": metadata.get("system_message", ""),
                    "max_tokens": metadata.get("max_tokens"),
                    "temperature": metadata.get("temperature"),
                }
            )
        if event.event_type == EventType.LLM_RESPONSE_RECEIVED:
            metadata = event.metadata or {}
            request_id = metadata.get("request_id") or f"response::{event.timestamp.isoformat()}"
            entry = ensure_entry(request_id, event.timestamp)
            entry.update(
                {
                    "request_id": request_id,
                    "task_id": entry.get("task_id") or event.task_id,
                    "agent_role": entry.get("agent_role") or metadata.get("agent_role"),
                    "response": metadata.get("response"),
                    "response_model": metadata.get("model"),
                    "response_timestamp": event.timestamp.isoformat(),
                    "prompt_tokens": metadata.get("prompt_tokens"),
                    "completion_tokens": metadata.get("completion_tokens"),
                    "total_tokens": metadata.get("total_tokens"),
                }
            )

    def sort_key(item: dict) -> str:
        return item.get("response_timestamp") or item.get("timestamp")

    trace_list = sorted(traces.values(), key=sort_key, reverse=True)
    return {"traces": trace_list, "total": len(trace_list)}


# VF-193: Agent workflow API endpoints


@router.post("/sessions/{session_id}/agents/init")
async def initialize_agents(session_id: str, request: InitializeAgentsRequest):
    """Initialize N agents for a session (VF-193).

    Validates:
    - Session exists
    - Session phase allows agent initialization (e.g., not COMPLETE/FAILED)
    - Agent count is within limits
    """
    from vibeforge_api.core.session import session_store
    from vibeforge_api.models import InitializeAgentsRequest, InitializeAgentsResponse
    from vibeforge_api.models.types import SessionPhase
    from orchestration.models import AgentConfig

    # Get session
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Phase guardrail: don't allow agent initialization if session is terminal
    terminal_phases = {SessionPhase.COMPLETE, SessionPhase.FAILED}
    if session.phase in terminal_phases:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot initialize agents in {session.phase.value} phase"
        )

    if request.agent_count is not None and request.agents is not None:
        raise HTTPException(
            status_code=400,
            detail="Provide either agent_count or agents, not both."
        )
    if request.agent_count is None and request.agents is None:
        raise HTTPException(
            status_code=400,
            detail="Provide agent_count or agents to initialize."
        )

    if request.agents is not None:
        empty_ids: list[str] = []
        agent_ids: list[str] = []
        display_names: dict[str, Optional[str]] = {}

        for agent in request.agents:
            raw_id = agent.agent_id
            normalized_id = raw_id.strip() if raw_id else ""
            if not normalized_id:
                empty_ids.append(raw_id or "")
                continue
            agent_ids.append(normalized_id)
            display_name = agent.display_name.strip() if agent.display_name else None
            display_names[normalized_id] = display_name

        if empty_ids:
            raise HTTPException(
                status_code=400,
                detail="Agent IDs cannot be empty or whitespace."
            )

        duplicates = sorted(
            agent_id for agent_id, count in Counter(agent_ids).items() if count > 1
        )
        if duplicates:
            raise HTTPException(
                status_code=400,
                detail=f"Duplicate agent IDs: {', '.join(duplicates)}"
            )

        agents = [
            AgentConfig(
                agent_id=agent_id,
                display_name=display_names.get(agent_id),
            ).model_dump()
            for agent_id in agent_ids
        ]
    else:
        agent_ids = [f"agent-{i+1}" for i in range(request.agent_count)]
        agents = [
            AgentConfig(agent_id=aid).model_dump() for aid in agent_ids
        ]

    session.agents = agents
    session.agent_roles = {}
    session.agent_models = {}
    session_store.update_session(session)

    return InitializeAgentsResponse(
        agent_ids=agent_ids,
        message=f"Initialized {len(agent_ids)} agents"
    )


@router.post("/sessions/{session_id}/agents/assign")
async def assign_agent_role(session_id: str, request: AssignAgentRoleRequest):
    """Assign role and model to an agent (VF-193).

    Validates:
    - Session exists
    - Agent exists in session
    - Role is valid (if provided)
    """
    from vibeforge_api.core.session import session_store
    from vibeforge_api.models import AssignAgentRoleRequest, AssignAgentRoleResponse
    from vibeforge_api.models.types import SessionPhase

    # Get session
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Phase guardrail
    terminal_phases = {SessionPhase.COMPLETE, SessionPhase.FAILED}
    if session.phase in terminal_phases:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot assign roles in {session.phase.value} phase"
        )

    # Check agent exists
    agent_ids = [a.get("agent_id") for a in session.agents]
    if request.agent_id not in agent_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Agent {request.agent_id} not found in session"
        )

    # Assign role and model
    if request.role:
        session.agent_roles[request.agent_id] = request.role
    if request.model_id:
        session.agent_models[request.agent_id] = request.model_id

    session_store.update_session(session)

    return AssignAgentRoleResponse(
        agent_id=request.agent_id,
        role=request.role,
        model_id=request.model_id,
        message=f"Assigned role/model to {request.agent_id}"
    )


@router.post("/sessions/{session_id}/task")
async def set_main_task(session_id: str, request: SetMainTaskRequest):
    """Set the main orchestration task (VF-193).

    Validates:
    - Session exists
    - Task is non-empty
    """
    from vibeforge_api.core.session import session_store
    from vibeforge_api.models import SetMainTaskRequest, SetMainTaskResponse
    from vibeforge_api.models.types import SessionPhase

    # Get session
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Phase guardrail
    terminal_phases = {SessionPhase.COMPLETE, SessionPhase.FAILED}
    if session.phase in terminal_phases:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot set task in {session.phase.value} phase"
        )

    session.main_task = request.main_task
    session_store.update_session(session)

    return SetMainTaskResponse(
        main_task=request.main_task,
        message="Main task set successfully"
    )


@router.post("/sessions/{session_id}/flows")
async def configure_agent_flow(session_id: str, request: ConfigureAgentFlowRequest):
    """Configure agent-to-agent communication flow (VF-193).

    Validates:
    - Session exists
    - All referenced agents exist
    """
    from vibeforge_api.core.session import session_store
    from vibeforge_api.models import ConfigureAgentFlowRequest, ConfigureAgentFlowResponse
    from vibeforge_api.models.types import SessionPhase
    from orchestration.models import AgentFlowGraph, AgentFlowEdge

    # Get session
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Phase guardrail
    terminal_phases = {SessionPhase.COMPLETE, SessionPhase.FAILED}
    if session.phase in terminal_phases:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot configure flow in {session.phase.value} phase"
        )

    # Build flow graph
    edges = [
        AgentFlowEdge(
            from_agent=edge.from_agent,
            to_agent=edge.to_agent,
            label=edge.label,
            bidirectional=edge.bidirectional,
        )
        for edge in request.edges
    ]
    flow_graph = AgentFlowGraph(edges=edges)

    # Validate graph
    agent_ids = [a.get("agent_id") for a in session.agents]
    is_valid, error = flow_graph.validate_dag(agent_ids)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid flow graph: {error}")

    session.agent_graph = flow_graph.model_dump()
    session_store.update_session(session)

    return ConfigureAgentFlowResponse(
        edge_count=len(request.edges),
        message=f"Configured flow with {len(request.edges)} edges"
    )


@router.get("/sessions/{session_id}/workflow")
async def get_workflow_config(session_id: str):
    """Get current workflow configuration (VF-193).

    Returns:
    - All agent configs
    - Agent role assignments
    - Agent model assignments
    - Agent flow graph
    - Main task
    """
    from vibeforge_api.core.session import session_store
    from vibeforge_api.models import WorkflowConfigResponse

    # Get session
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return WorkflowConfigResponse(
        agents=session.agents,
        agent_roles=session.agent_roles,
        agent_models=session.agent_models,
        agent_graph=session.agent_graph,
        main_task=session.main_task,
    )


# VF-200: Simulation lifecycle endpoints


@router.post("/sessions/{session_id}/simulation/config")
async def configure_simulation(session_id: str, request: SimulationConfigRequest):
    """Configure simulation mode and parameters (VF-200).

    Sets simulation_mode (manual/auto), auto_delay_ms, and tick_budget.
    Cannot configure if simulation is already running.
    """
    from vibeforge_api.core.session import session_store
    from vibeforge_api.models import SimulationConfigRequest, SimulationConfigResponse
    from vibeforge_api.models.types import SessionPhase

    # Get session
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Phase guardrail: don't allow config in terminal phases
    terminal_phases = {SessionPhase.COMPLETE, SessionPhase.FAILED}
    if session.phase in terminal_phases:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot configure simulation in {session.phase.value} phase"
        )

    # Running guardrail: cannot configure if simulation is already running
    if session.tick_status == "running":
        raise HTTPException(
            status_code=400,
            detail="Cannot configure simulation while it is running. Pause or reset first."
        )

    # Update simulation config
    session.simulation_mode = request.simulation_mode
    session.auto_delay_ms = request.auto_delay_ms
    if request.tick_budget is not None:
        session.tick_budget = request.tick_budget
    if request.use_real_llm is not None:
        session.use_real_llm = request.use_real_llm
    if request.llm_provider is not None:
        session.llm_provider = request.llm_provider
    if request.default_model is not None:
        session.default_model = request.default_model
    if request.default_temperature is not None:
        session.default_temperature = request.default_temperature
    if request.max_cost_usd is not None:
        session.max_cost_usd = request.max_cost_usd
    if request.tick_rate_limit_ms is not None:
        session.tick_rate_limit_ms = request.tick_rate_limit_ms

    session_store.update_session(session)

    return SimulationConfigResponse(
        simulation_mode=session.simulation_mode,
        auto_delay_ms=session.auto_delay_ms,
        tick_budget=session.tick_budget,
        message="Simulation configuration updated"
    )


@router.post("/sessions/{session_id}/simulation/start")
async def start_simulation(
    session_id: str, request: SimulationStartRequest | None = None
):
    """Start simulation - validates workflow is complete (VF-200).

    Validates:
    - Agents initialized
    - All agents have roles assigned
    - Agent flow graph is configured
    - Main task is set

    After validation, sets tick_status to "running" and locks configuration.
    """
    from vibeforge_api.core.session import session_store
    from vibeforge_api.models import SimulationStartResponse
    from vibeforge_api.models.types import SessionPhase

    # Get session
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Phase guardrail
    terminal_phases = {SessionPhase.COMPLETE, SessionPhase.FAILED}
    if session.phase in terminal_phases:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start simulation in {session.phase.value} phase"
        )

    # Already running check
    if session.tick_status == "running":
        raise HTTPException(
            status_code=400,
            detail="Simulation is already running"
        )

    missing: list[str] = []

    # Workflow validation: agents initialized
    if not session.agents:
        missing.append("agents")

    # Workflow validation: all agents have roles
    agent_ids = [a.get("agent_id") for a in session.agents if a.get("agent_id")]
    agents_without_roles = [aid for aid in agent_ids if aid not in session.agent_roles]
    if session.agents and agents_without_roles:
        missing.append(f"roles (missing for {', '.join(agents_without_roles)})")

    # Workflow validation: agent flow graph configured
    if not session.agent_graph or not session.agent_graph.get("edges"):
        missing.append("flow graph")

    # Workflow validation: main task set
    if not session.main_task:
        missing.append("main task")

    initial_prompt = ""
    first_agent_id = ""
    if request is not None:
        initial_prompt = request.initial_prompt or ""
        first_agent_id = request.first_agent_id or ""

    if not initial_prompt.strip():
        missing.append("initial_prompt")
    if not first_agent_id.strip():
        missing.append("first_agent_id")

    if missing:
        raise HTTPException(
            status_code=400,
            detail="Cannot start simulation: missing prerequisites: " + ", ".join(missing),
        )

    initial_prompt = initial_prompt.strip()
    first_agent_id = first_agent_id.strip()
    if first_agent_id not in agent_ids:
        raise HTTPException(
            status_code=400,
            detail=f"first_agent_id '{first_agent_id}' is not in agent roster"
        )

    session.initial_prompt = initial_prompt
    session.first_agent_id = first_agent_id

    # Start simulation
    session.tick_status = "running"
    session.tick_index = 0  # Reset tick index on start
    session.simulation_expected_responses = []
    session.simulation_final_answer = None
    session_store.update_session(session)

    return SimulationStartResponse(
        tick_index=session.tick_index,
        tick_status=session.tick_status,
        message="Simulation started"
    )


@router.post("/sessions/{session_id}/simulation/reset")
async def reset_simulation(session_id: str, request: SimulationResetRequest):
    """Reset simulation state (VF-200).

    Resets tick_index to 0 and tick_status to "idle".
    Optionally clears workflow config based on preserve_workflow flag.
    """
    from vibeforge_api.core.session import session_store
    from vibeforge_api.core.workspace import WorkspaceManager
    from vibeforge_api.models import SimulationResetRequest, SimulationResetResponse
    from vibeforge_api.models.types import SessionPhase

    # Get session
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Phase guardrail
    terminal_phases = {SessionPhase.COMPLETE, SessionPhase.FAILED}
    if session.phase in terminal_phases:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reset simulation in {session.phase.value} phase"
        )

    # Reset tick state
    session.tick_index = 0
    session.tick_status = "idle"
    session.initial_prompt = None
    session.first_agent_id = None
    session.simulation_message_queue = []
    session.simulation_message_counter = 0
    session.simulation_expected_responses = []
    session.simulation_final_answer = None

    workspace_manager = WorkspaceManager()
    event_log_path = workspace_manager.workspace_root / session_id / "events.jsonl"
    if event_log_path.exists():
        try:
            event_log_path.unlink()
        except PermissionError:
            event_log_path.write_text("")

    # Optionally clear workflow config
    if not request.preserve_workflow:
        session.agents = []
        session.agent_roles = {}
        session.agent_models = {}
        session.agent_graph = None
        session.main_task = None

    session_store.update_session(session)

    return SimulationResetResponse(
        tick_index=session.tick_index,
        tick_status=session.tick_status,
        workflow_preserved=request.preserve_workflow,
        message="Simulation reset" + (" (workflow preserved)" if request.preserve_workflow else " (workflow cleared)")
    )


# VF-201: Tick control endpoints


def _enforce_tick_guardrails(session) -> None:
    if session.simulation_cost_usd >= session.max_cost_usd:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Cost budget exceeded: ${session.simulation_cost_usd:.2f} / "
                f"${session.max_cost_usd:.2f}"
            ),
        )

    if not session.use_real_llm:
        return

    if session.last_tick_timestamp and session.tick_rate_limit_ms is not None:
        elapsed_ms = (
            datetime.now(timezone.utc) - session.last_tick_timestamp
        ).total_seconds() * 1000
        if elapsed_ms < session.tick_rate_limit_ms:
            remaining_ms = int(session.tick_rate_limit_ms - elapsed_ms)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit: wait {remaining_ms}ms",
            )


@router.post("/sessions/{session_id}/simulation/tick")
async def advance_tick(session_id: str):
    """Advance simulation by exactly one tick (VF-201).

    Validates simulation is running (tick_status == "running").
    Increments tick_index by 1.
    Returns tick engine event summary for the tick.
    """
    from vibeforge_api.core.event_log import EventLog
    from vibeforge_api.core.session import session_store
    from vibeforge_api.core.workspace import WorkspaceManager
    from vibeforge_api.models import TickResponse
    from orchestration.coordinator.tick_engine import TickEngine

    # Get session
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Must be started to tick
    if session.tick_status != "running":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot advance tick: simulation not running (status: {session.tick_status})."
        )

    _enforce_tick_guardrails(session)

    workspace_manager = WorkspaceManager()
    event_log = EventLog(workspace_manager.workspace_root)

    # Create TickEngine
    engine = TickEngine(session, event_log=event_log)

    # Queue initial prompt as first message if this is the first tick
    # and initial_prompt exists but message queue is empty
    if (
        session.tick_index == 0
        and session.initial_prompt
        and session.first_agent_id
        and not engine.message_queue
    ):
        engine.send_message(
            from_agent="user",
            to_agent=session.first_agent_id,
            content={
                "text": session.initial_prompt,
                "expect_response": True,
            },
            bypass_validation=True,  # System message bypasses graph validation
        )

    # Advance tick using TickEngine
    result = await engine.advance_tick()
    engine.sync_session_state()

    session.last_tick_timestamp = datetime.now(timezone.utc)
    processed_events = [event.to_dict() for event in result.events]

    session_store.update_session(session)

    tick_summary = {
        "new_tick_index": result.tick_index,
        "processed_event_count": len(processed_events),
        "processed_events": processed_events,
        "messages_sent": len(result.messages_delivered),
        "messages_blocked": result.messages_blocked,
    }

    return TickResponse(
        tick_index=session.tick_index,
        new_tick_index=result.tick_index,
        tick_status=session.tick_status,
        events_processed=len(processed_events),
        processed_event_count=len(processed_events),
        processed_events=processed_events,
        messages_sent=len(result.messages_delivered),
        messages_blocked=result.messages_blocked,
        tick_summaries=[tick_summary],
        message=f"Advanced to tick {session.tick_index}"
    )


@router.post("/sessions/{session_id}/simulation/ticks")
async def advance_ticks(session_id: str, request: TickRequest):
    """Advance simulation by N ticks (VF-201).

    Validates simulation is running.
    Advances tick_index by N (with safety limit of 100).
    Returns per-tick summaries and aggregated events.
    """
    from vibeforge_api.core.event_log import EventLog
    from vibeforge_api.core.session import session_store
    from vibeforge_api.core.workspace import WorkspaceManager
    from vibeforge_api.models import TickRequest, TickResponse
    from orchestration.coordinator.tick_engine import TickEngine

    # Get session
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Must be started to tick
    if session.tick_status != "running":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot advance ticks: simulation not running (status: {session.tick_status})."
        )

    _enforce_tick_guardrails(session)

    # Advance ticks using TickEngine
    starting_tick = session.tick_index
    workspace_manager = WorkspaceManager()
    event_log = EventLog(workspace_manager.workspace_root)
    engine = TickEngine(session, event_log=event_log)

    # Queue initial prompt as first message if this is the first tick
    # and initial_prompt exists but message queue is empty
    if (
        session.tick_index == 0
        and session.initial_prompt
        and session.first_agent_id
        and not engine.message_queue
    ):
        engine.send_message(
            from_agent="user",
            to_agent=session.first_agent_id,
            content={
                "text": session.initial_prompt,
                "expect_response": True,
            },
            bypass_validation=True,  # System message bypasses graph validation
        )

    tick_summaries = []
    processed_events: list[dict] = []
    messages_sent_total = 0
    messages_blocked_total = 0

    for _ in range(request.tick_count):
        result = await engine.advance_tick()
        tick_events = [event.to_dict() for event in result.events]
        processed_events.extend(tick_events)

        tick_summaries.append(
            {
                "new_tick_index": result.tick_index,
                "processed_event_count": len(tick_events),
                "processed_events": tick_events,
                "messages_sent": len(result.messages_delivered),
                "messages_blocked": result.messages_blocked,
            }
        )
        messages_sent_total += len(result.messages_delivered)
        messages_blocked_total += result.messages_blocked

    engine.sync_session_state()
    session.last_tick_timestamp = datetime.now(timezone.utc)
    session_store.update_session(session)

    return TickResponse(
        tick_index=session.tick_index,
        new_tick_index=session.tick_index,
        tick_status=session.tick_status,
        events_processed=len(processed_events),
        processed_event_count=len(processed_events),
        processed_events=processed_events,
        messages_sent=messages_sent_total,
        messages_blocked=messages_blocked_total,
        tick_summaries=tick_summaries,
        message=f"Advanced {request.tick_count} ticks ({starting_tick} -> {session.tick_index})"
    )


@router.post("/sessions/{session_id}/simulation/pause")
async def pause_simulation(session_id: str):
    """Pause auto-run simulation (VF-201).

    Only valid if tick_status == "running".
    Sets tick_status to "paused".
    """
    from vibeforge_api.core.session import session_store
    from vibeforge_api.models import SimulationPauseResponse

    # Get session
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Must be running to pause
    if session.tick_status == "paused":
        raise HTTPException(
            status_code=400,
            detail="Cannot pause: simulation already paused"
        )
    if session.tick_status == "completed":
        raise HTTPException(
            status_code=400,
            detail="Cannot pause: simulation already completed"
        )
    if session.tick_status != "running":
        raise HTTPException(
            status_code=400,
            detail="Cannot pause: simulation not running"
        )

    # Pause simulation
    session.tick_status = "paused"
    session_store.update_session(session)

    return SimulationPauseResponse(
        tick_index=session.tick_index,
        tick_status=session.tick_status,
        message="Simulation paused"
    )


@router.post("/sessions/{session_id}/simulation/stop")
async def stop_simulation(session_id: str):
    """Stop simulation (VF-201).

    Transitions tick_status to "completed" to prevent further ticks.
    """
    from vibeforge_api.core.session import session_store
    from vibeforge_api.models import SimulationStopResponse
    from vibeforge_api.models.types import SessionPhase

    # Get session
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Phase guardrail
    terminal_phases = {SessionPhase.COMPLETE, SessionPhase.FAILED}
    if session.phase in terminal_phases:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot stop simulation in {session.phase.value} phase"
        )

    if session.tick_status == "idle":
        raise HTTPException(status_code=400, detail="Cannot stop: simulation not running")
    if session.tick_status == "completed":
        raise HTTPException(status_code=400, detail="Cannot stop: simulation already completed")

    session.tick_status = "completed"
    session_store.update_session(session)

    return SimulationStopResponse(
        tick_index=session.tick_index,
        tick_status=session.tick_status,
        message="Simulation stopped"
    )


@router.get("/sessions/{session_id}/simulation/state")
async def get_simulation_state(session_id: str):
    """Get current simulation state (VF-201).

    Returns tick_index, simulation_mode, tick_status, and queued work summary.
    """
    from vibeforge_api.core.session import session_store
    from vibeforge_api.models import SimulationStateResponse
    from orchestration.models import AgentRole

    # Get session
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Build roster with labels
    agents = []
    for agent in session.agents:
        agent_id = agent.get("agent_id")
        if not agent_id:
            continue
        agents.append(
            {
                "agent_id": agent_id,
                "display_name": agent.get("display_name"),
                "role": session.agent_roles.get(agent_id) or agent.get("role"),
                "model_id": session.agent_models.get(agent_id) or agent.get("model_id"),
            }
        )

    available_roles = [role.value for role in AgentRole]

    # Build pending work summary
    pending_work_summary = None
    if session.agents:
        pending_work_summary = f"{len(session.agents)} agents configured"

    return SimulationStateResponse(
        initial_prompt=session.initial_prompt,
        first_agent_id=session.first_agent_id,
        simulation_mode=session.simulation_mode,
        tick_index=session.tick_index,
        tick_status=session.tick_status,
        auto_delay_ms=session.auto_delay_ms,
        tick_budget=session.tick_budget,
        pending_work_summary=pending_work_summary,
        simulation_expected_responses=getattr(
            session, "simulation_expected_responses", []
        ),
        simulation_final_answer=session.simulation_final_answer,
        use_real_llm=session.use_real_llm,
        llm_provider=session.llm_provider,
        default_model=session.default_model,
        default_temperature=session.default_temperature,
        simulation_cost_usd=session.simulation_cost_usd,
        max_history_depth=session.max_history_depth,
        max_cost_usd=session.max_cost_usd,
        tick_rate_limit_ms=session.tick_rate_limit_ms,
        last_tick_timestamp=session.last_tick_timestamp,
        agent_graph=session.agent_graph,
        agents=agents,
        available_roles=available_roles,
    )


@router.get("/sessions/{session_id}/debug/messages")
async def get_debug_message_log(session_id: str):
    """Get a human-readable message log for debugging.

    Returns messages in chronological order with full content for analysis.
    """
    from vibeforge_api.core.event_log import EventLog, EventType
    from vibeforge_api.core.session import session_store
    from vibeforge_api.core.workspace import WorkspaceManager

    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    workspace_manager = WorkspaceManager()
    event_log = EventLog(workspace_manager.workspace_root, use_cache=False)

    events = event_log.get_events(session_id)
    messages = []

    for event in events:
        if event.event_type in (EventType.MESSAGE_SENT, EventType.MESSAGE_BLOCKED_BY_GRAPH):
            meta = event.metadata or {}
            content = meta.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else str(content)
            is_stub = content.get("is_stub", False) if isinstance(content, dict) else False
            is_delegation = content.get("delegation", False) if isinstance(content, dict) else False
            expect_response = content.get("expect_response", False) if isinstance(content, dict) else False

            messages.append({
                "tick": meta.get("tick_index"),
                "from": meta.get("from_agent"),
                "to": meta.get("to_agent"),
                "type": "BLOCKED" if event.event_type == EventType.MESSAGE_BLOCKED_BY_GRAPH else (
                    "STUB" if is_stub else ("DELEGATION" if is_delegation else "MESSAGE")
                ),
                "expect_response": expect_response,
                "text_preview": text[:200] + "..." if len(text) > 200 else text,
                "full_text": text,
                "message_id": meta.get("message_id"),
                "in_response_to": content.get("in_response_to") if isinstance(content, dict) else None,
            })

    # Also include delegation tracking state
    delegation_tracking = getattr(session, "simulation_delegation_tracking", {})

    return {
        "session_id": session_id,
        "tick_index": session.tick_index,
        "tick_status": session.tick_status,
        "use_real_llm": session.use_real_llm,
        "delegation_tracking": delegation_tracking,
        "expected_responses": session.simulation_expected_responses,
        "final_answer": session.simulation_final_answer,
        "message_count": len(messages),
        "messages": messages,
    }
