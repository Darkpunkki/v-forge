"""Control panel API endpoints.

Provides observability and monitoring endpoints for the control panel UI.
Separate from the end-user session flow.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
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
)

router = APIRouter(prefix="/control", tags=["control"])


@router.get("/sessions")
async def list_all_sessions():
    """List all sessions with metadata for control panel."""
    from vibeforge_api.core.artifacts import SessionArtifactQuery
    from vibeforge_api.core.workspace import WorkspaceManager
    from vibeforge_api.core.session import session_store

    workspace_manager = WorkspaceManager()
    query = SessionArtifactQuery(workspace_manager.workspace_root)

    session_ids = set(query.list_sessions())
    session_ids.update(session_store.list_sessions())

    sessions = []
    for session_id in session_ids:
        workspace_path = workspace_manager.workspace_root / session_id
        session = session_store.get_session(session_id)

        created_at = session.created_at if session else None
        updated_at = session.updated_at if session else None
        phase = session.phase.value if session else "UNKNOWN"

        if workspace_path.exists():
            stats = workspace_path.stat()
            if not created_at:
                created_at = datetime.fromtimestamp(stats.st_ctime, tz=timezone.utc)
            if not updated_at:
                updated_at = datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc)

        if not created_at:
            created_at = datetime.now(timezone.utc)
        if not updated_at:
            updated_at = created_at

        artifacts = query.get_session_artifacts(session_id)

        sessions.append(
            {
                "session_id": session_id,
                "phase": phase,
                "created_at": created_at.isoformat(),
                "updated_at": updated_at.isoformat(),
                "artifacts": artifacts,
                "_sort_updated_at": updated_at.timestamp(),
            }
        )

    sessions.sort(key=lambda item: item["_sort_updated_at"], reverse=True)
    for session in sessions:
        session.pop("_sort_updated_at", None)

    return {
        "sessions": sessions,
        "total": len(sessions),
    }


@router.get("/sessions/{session_id}/events")
async def stream_session_events(session_id: str):
    """Stream session events via Server-Sent Events (SSE)."""
    from vibeforge_api.core.event_log import EventLog
    from vibeforge_api.core.workspace import WorkspaceManager

    workspace_manager = WorkspaceManager()
    workspace_path = workspace_manager.workspace_root / session_id
    event_log_path = workspace_path / "events.jsonl"

    if not event_log_path.exists():
        raise HTTPException(status_code=404, detail="Event log not found")

    event_log = EventLog(workspace_manager.workspace_root)

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


@router.get("/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    """Get current session status for control panel."""
    from vibeforge_api.core.session import session_store

    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "phase": session.phase.value,
        "active_task_id": session.active_task_id,
        "completed_tasks": len(session.completed_task_ids),
        "failed_tasks": len(session.failed_task_ids),
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }


@router.get("/sessions/{session_id}/bundle")
async def export_run_bundle(session_id: str):
    """Export a run bundle zip archive for a session."""
    from vibeforge_api.core.run_bundle import export_run_bundle as build_bundle
    from vibeforge_api.core.workspace import WorkspaceManager

    workspace_manager = WorkspaceManager()
    try:
        bundle_path = build_bundle(session_id, workspace_manager.workspace_root)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return FileResponse(bundle_path, media_type="application/zip", filename=bundle_path.name)


@router.get("/active")
async def get_active_sessions():
    """Get all active sessions (not in COMPLETE or FAILED state)."""
    from vibeforge_api.core.session import session_store
    from vibeforge_api.models.types import SessionPhase

    all_sessions = session_store.list_sessions()
    active = []

    for session_id in all_sessions:
        session = session_store.get_session(session_id)
        if not session:
            continue
        if session.phase not in {SessionPhase.COMPLETE, SessionPhase.FAILED}:
            active.append({
                "session_id": session.session_id,
                "phase": session.phase.value,
                "active_task_id": session.active_task_id,
                "updated_at": session.updated_at.isoformat(),
            })

    return {
        "active_sessions": active,
        "total": len(active),
    }


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

    # Initialize agents
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
        message=f"Initialized {request.agent_count} agents"
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
    - Flow graph is acyclic
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
        AgentFlowEdge(from_agent=e["from_agent"], to_agent=e["to_agent"])
        for e in request.edges
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
