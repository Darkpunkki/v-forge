"""Control panel API endpoints.

Provides observability and monitoring endpoints for the control panel UI.
Separate from the end-user session flow.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from datetime import datetime

router = APIRouter(prefix="/control", tags=["control"])


@router.get("/sessions")
async def list_all_sessions():
    """List all sessions with metadata for control panel."""
    from vibeforge_api.core.artifacts import SessionArtifactQuery
    from vibeforge_api.core.workspace import WorkspaceManager

    workspace_manager = WorkspaceManager()
    query = SessionArtifactQuery(workspace_manager.workspace_root)

    sessions = query.query_sessions_by_date()

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

    for session in all_sessions:
        if session.phase not in {SessionPhase.COMPLETE, SessionPhase.FAILED}:
            active.append({
                "session_id": session.id,
                "phase": session.phase.value,
                "active_task_id": session.active_task_id,
                "updated_at": session.updated_at.isoformat(),
            })

    return {
        "active_sessions": active,
        "total": len(active),
    }
