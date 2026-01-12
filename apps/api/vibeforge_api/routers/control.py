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
