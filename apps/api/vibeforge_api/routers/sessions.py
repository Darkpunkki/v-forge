"""Session API endpoints."""

import asyncio
import json

from fastapi import APIRouter, HTTPException, status

from vibeforge_api.core.session import session_store
from vibeforge_api.core.questionnaire import questionnaire_engine
from vibeforge_api.core.spec_builder import spec_builder
from vibeforge_api.core.app_runner import app_runner
from vibeforge_api.core.workspace import workspace_manager
from vibeforge_api.core.artifacts import artifact_store
from vibeforge_api.core.event_log import EventLog, EventType
from vibeforge_api.core.llm_provider import get_llm_client
from vibeforge_api.models.types import SessionPhase
from vibeforge_api.models.requests import (
    SubmitAnswerRequest,
    PlanDecisionRequest,
    ClarificationAnswerRequest,
)
from vibeforge_api.models.responses import (
    SessionResponse,
    QuestionResponse,
    PlanSummaryResponse,
    ProgressResponse,
    TaskProgress,
    ResultResponse,
    ClarificationResponse,
    ClarificationOption,
)
from orchestration.coordinator import SessionCoordinator
from orchestration.orchestrator import Orchestrator
from orchestration.models import TaskGraph
from models.agent_framework import DirectLlmAdapter

router = APIRouter()

event_log = EventLog(workspace_manager.workspace_root)
llm_client = get_llm_client()
orchestrator = Orchestrator(llm_client, event_log=event_log)
agent_framework = DirectLlmAdapter(llm_client)
session_coordinator = SessionCoordinator(
    session_store,
    workspace_manager,
    questionnaire_engine,
    spec_builder,
    orchestrator,
    agent_framework=agent_framework,
    event_log=event_log,
)

_execution_tasks: dict[str, asyncio.Task] = {}


def _spawn_execution_task(session_id: str) -> None:
    existing = _execution_tasks.get(session_id)
    if existing and not existing.done():
        return

    async def _runner() -> None:
        while True:
            session = session_store.get_session(session_id)
            if not session or session.phase != SessionPhase.EXECUTION:
                break

            try:
                result = await session_coordinator.execute_next_task(session_id)
            except Exception as exc:
                session_coordinator.fail_session(
                    session_id, f"Execution error: {exc}", task_id="execution"
                )
                break

            status = result.get("status")

            if status == "needs_clarification":
                break
            if status == "all_tasks_complete":
                try:
                    await session_coordinator.finalize_session(session_id)
                except Exception as exc:
                    session_coordinator.fail_session(
                        session_id, f"Finalization failed: {exc}", task_id="finalize"
                    )
                break
            if status in {"task_failed_terminal", "blocked"}:
                reason = result.get("error") or result.get("message") or "Execution failed"
                task_id = result.get("task_id") or "execution"
                session_coordinator.fail_session(session_id, reason, task_id=task_id)
                break

            await asyncio.sleep(0)

    loop = asyncio.get_running_loop()
    task = loop.create_task(_runner())
    _execution_tasks[session_id] = task
    task.add_done_callback(lambda _: _execution_tasks.pop(session_id, None))


# VF-021: POST /sessions (startSession)
@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def start_session():
    """Create a new session and initialize workspace."""
    session_id = session_coordinator.start_session()
    session = session_store.get_session(session_id)
    session.add_log("Session created")

    return SessionResponse(
        session_id=session_id,
        phase=session.phase,
    )


# VF-022: GET /sessions/{id}/question (getNextQuestion)
@router.get("/{session_id}/question", response_model=QuestionResponse)
async def get_next_question(session_id: str):
    """Get the next questionnaire question for the session."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.phase != SessionPhase.QUESTIONNAIRE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot get question in phase {session.phase}. Must be in QUESTIONNAIRE phase.",
        )

    question = session_coordinator.get_next_question(session_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No more questions available. Questionnaire is complete.",
        )

    return question


# VF-023: POST /sessions/{id}/answers (submitAnswer)
@router.post("/{session_id}/answers", status_code=status.HTTP_200_OK)
async def submit_answer(session_id: str, request: SubmitAnswerRequest):
    """Submit an answer to a questionnaire question."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.phase != SessionPhase.QUESTIONNAIRE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit answer in phase {session.phase}. Must be in QUESTIONNAIRE phase.",
        )

    try:
        session_coordinator.submit_answer(session_id, request.question_id, request.answer)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # Check if questionnaire is complete
    session = session_store.get_session(session_id)
    if questionnaire_engine.is_questionnaire_complete(session.current_question_index):
        try:
            session_coordinator.finalize_questionnaire(session_id)
            session_coordinator.generate_build_spec(session_id)
            await session_coordinator.generate_concept(session_id)
            await session_coordinator.generate_plan(session_id)
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            ) from exc

    session = session_store.get_session(session_id)

    return {
        "status": "accepted",
        "next_phase": session.phase,
        "is_complete": session.phase != SessionPhase.QUESTIONNAIRE,
    }


# VF-024: GET /sessions/{id}/plan (getPlanSummary)
@router.get("/{session_id}/plan", response_model=PlanSummaryResponse)
async def get_plan_summary(session_id: str):
    """Get the plan summary for review."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.phase != SessionPhase.PLAN_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot get plan in phase {session.phase}. Must be in PLAN_REVIEW phase.",
        )

    task_graph = _load_task_graph(session_id)

    return _build_plan_summary(session, task_graph)


# VF-025: POST /sessions/{id}/plan/decision (approve/reject)
@router.post("/{session_id}/plan/decision", status_code=status.HTTP_200_OK)
async def submit_plan_decision(session_id: str, request: PlanDecisionRequest):
    """Approve or reject the proposed plan."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.phase != SessionPhase.PLAN_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit plan decision in phase {session.phase}. Must be in PLAN_REVIEW phase.",
        )

    if request.approved:
        session_coordinator.approve_plan(session_id)
        _spawn_execution_task(session_id)
    else:
        reason = request.reason or "No reason provided"
        session_coordinator.reject_plan(session_id, reason=reason)

    return {
        "status": "accepted",
        "next_phase": session_store.get_session(session_id).phase,
    }


# VF-026: GET /sessions/{id}/progress (progress/events)
@router.get("/{session_id}/progress", response_model=ProgressResponse)
async def get_progress(session_id: str):
    """Get session progress and event stream."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    event_log = EventLog(workspace_manager.workspace_root)
    events = event_log.get_events(session_id)
    task_graph = _load_task_graph(session_id)
    task_titles = _build_task_title_map(session_id, task_graph)
    active_task, completed_tasks, failed_tasks = _build_task_progress(
        events, task_titles
    )
    logs = _build_event_logs(events)

    return ProgressResponse(
        session_id=session.session_id,
        phase=session.phase,
        active_task=active_task,
        completed_tasks=completed_tasks,
        failed_tasks=failed_tasks,
        logs=logs,
    )


# GET /sessions/{id}/clarification (get pending clarification question)
@router.get("/{session_id}/clarification", response_model=ClarificationResponse)
async def get_clarification(session_id: str):
    """Get pending clarification question from gates/agents."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if not session.pending_clarification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending clarification question for this session",
        )

    # Convert dict format to ClarificationResponse
    clarification = session.pending_clarification
    options = [
        ClarificationOption(
            label=opt.get("label", ""),
            value=opt.get("value", ""),
            description=opt.get("description"),
        )
        for opt in clarification.get("options", [])
    ]

    return ClarificationResponse(
        question=clarification.get("question", ""),
        context=clarification.get("context"),
        options=options,
    )


# VF-027: POST /sessions/{id}/clarification (submit clarification answer)
@router.post("/{session_id}/clarification", status_code=status.HTTP_200_OK)
async def submit_clarification(
    session_id: str, request: ClarificationAnswerRequest
):
    """Submit user's answer to a clarification question."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if not session.pending_clarification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending clarification question for this session",
        )

    # Validate answer is one of the valid options
    clarification = session.pending_clarification
    valid_values = [opt.get("value") for opt in clarification.get("options", [])]
    if request.answer not in valid_values:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid answer. Must be one of: {', '.join(valid_values)}",
        )

    # Store the answer and clear pending clarification
    session.clarification_answer = request.answer
    session.pending_clarification = None
    session.add_log(f"Clarification answered: {request.answer}")

    session_store.update_session(session)
    session_coordinator.resume_execution(session_id)
    _spawn_execution_task(session_id)

    return {
        "status": "accepted",
        "next_phase": SessionPhase.EXECUTION.value,
    }


# VF-028: GET /sessions/{id}/result (final summary)
@router.get("/{session_id}/result", response_model=ResultResponse)
async def get_result(session_id: str):
    """Get the final session result and run instructions."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.phase != SessionPhase.COMPLETE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot get result in phase {session.phase}. Must be in COMPLETE phase.",
        )

    # Get workspace path
    workspace_path = workspace_manager.get_workspace_path(session_id)
    repo_path = workspace_manager.get_repo_path(session_id)

    # List generated files
    generated_files = []
    if repo_path.exists():
        for file_path in repo_path.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(repo_path)
                generated_files.append(str(rel_path))

    # Build run instructions based on BuildSpec
    run_instructions = _build_run_instructions(session.build_spec)

    # Build summary
    summary = _build_summary(session, run_instructions)

    # List artifacts
    artifacts_path = workspace_manager.get_artifacts_path(session_id)
    artifacts = {}
    if artifacts_path.exists():
        for artifact_file in artifacts_path.glob("*.json"):
            artifacts[artifact_file.stem] = str(artifact_file)

    return ResultResponse(
        session_id=session_id,
        status="success",
        workspace_path=str(workspace_path),
        generated_files=sorted(generated_files),
        run_instructions=run_instructions,
        summary=summary,
        artifacts=artifacts,
    )


def _build_run_instructions(build_spec: dict | None) -> str:
    """Build run instructions based on BuildSpec."""
    return app_runner.get_run_instructions(build_spec)


def _build_summary(session, run_instructions: str) -> str:
    """Build session summary."""
    if not session.build_spec:
        return "Session completed but no BuildSpec was generated."

    platform = session.build_spec["target"]["platform"]
    genre = session.build_spec["ideaSeed"]["genre"]
    twists = session.build_spec["ideaSeed"].get("twists", [])

    twist_text = f" with twists: {', '.join(twists)}" if twists else ""

    return f"""Session completed successfully!

Generated a {platform} application with {genre} genre{twist_text}.

Workspace location: {workspace_manager.get_workspace_path(session.session_id)}

Check the generated files and follow the run instructions to start the application.

Run instructions:
{run_instructions}
"""


def _load_task_graph(session_id: str) -> dict | None:
    content = artifact_store.get_artifact(session_id, "task_graph.json")
    if not content:
        return None
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse task graph artifact.",
        ) from exc


def _build_plan_summary(session, task_graph: dict | None) -> PlanSummaryResponse:
    if not task_graph:
        return PlanSummaryResponse(
            features=[],
            task_count=0,
            verification_steps=[],
            estimated_scope="pending",
            constraints=["Plan not generated yet."],
        )

    graph = TaskGraph.from_dict(session.session_id, task_graph)
    features = [task.description for task in graph.tasks]
    verification_steps = sorted(
        {
            task.verification.get("type", "manual")
            for task in graph.tasks
            if task.verification
        }
    )

    return PlanSummaryResponse(
        features=features,
        task_count=len(graph.tasks),
        verification_steps=verification_steps,
        estimated_scope=_format_scope(session.build_spec),
        constraints=_format_constraints(session.build_spec),
    )


def _format_scope(build_spec: dict | None) -> str:
    if not build_spec:
        return "unknown"
    scope = build_spec.get("scopeBudget", {})
    max_files = scope.get("maxTotalFiles")
    max_screens = scope.get("maxScreens")
    parts = []
    if max_files is not None:
        parts.append(f"max files {max_files}")
    if max_screens is not None:
        parts.append(f"max screens {max_screens}")
    return ", ".join(parts) if parts else "unknown"


def _format_constraints(build_spec: dict | None) -> list[str]:
    if not build_spec:
        return []
    constraints: list[str] = []
    stack_preset = build_spec.get("stack", {}).get("preset")
    if stack_preset:
        constraints.append(f"Stack preset: {stack_preset}")
    platform = build_spec.get("target", {}).get("platform")
    if platform:
        constraints.append(f"Platform: {platform}")
    return constraints


def _build_task_title_map(session_id: str, task_graph: dict | None) -> dict[str, str]:
    if not task_graph:
        return {}
    graph = TaskGraph.from_dict(session_id, task_graph)
    return {task.task_id: task.description for task in graph.tasks}


def _build_task_progress(
    events: list, task_titles: dict[str, str]
) -> tuple[TaskProgress | None, list[TaskProgress], list[TaskProgress]]:
    completed_order: list[str] = []
    failed_order: list[str] = []
    active_task_id: str | None = None
    completed_ids: set[str] = set()
    failed_ids: set[str] = set()

    for event in events:
        if event.event_type == EventType.TASK_STARTED and event.task_id:
            active_task_id = event.task_id
        elif event.event_type == EventType.TASK_COMPLETED and event.task_id:
            if event.task_id not in completed_ids:
                completed_order.append(event.task_id)
                completed_ids.add(event.task_id)
            if active_task_id == event.task_id:
                active_task_id = None
        elif event.event_type == EventType.TASK_FAILED and event.task_id:
            if event.task_id not in failed_ids:
                failed_order.append(event.task_id)
                failed_ids.add(event.task_id)
            if active_task_id == event.task_id:
                active_task_id = None

    def _make_task_progress(task_id: str, status: str) -> TaskProgress:
        title = task_titles.get(task_id, f"Task {task_id}")
        return TaskProgress(task_id=task_id, title=title, status=status)

    active_task = (
        _make_task_progress(active_task_id, "in_progress")
        if active_task_id
        else None
    )

    completed_tasks = [
        _make_task_progress(task_id, "completed") for task_id in completed_order
    ]
    failed_tasks = [_make_task_progress(task_id, "failed") for task_id in failed_order]

    return active_task, completed_tasks, failed_tasks


def _build_event_logs(events: list) -> list[str]:
    if not events:
        return ["No events recorded yet."]
    return [
        f"[{event.timestamp.isoformat()}] {event.event_type.value}: {event.message}"
        for event in events[-50:]
    ]
