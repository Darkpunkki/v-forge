"""Session API endpoints."""

from fastapi import APIRouter, HTTPException, status

from vibeforge_api.core.session import session_store
from vibeforge_api.core.questionnaire import questionnaire_engine
from vibeforge_api.core.spec_builder import spec_builder
from vibeforge_api.core.app_runner import app_runner
from vibeforge_api.core.workspace import workspace_manager
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

router = APIRouter()

llm_client = get_llm_client()
orchestrator = Orchestrator(llm_client)
session_coordinator = SessionCoordinator(
    session_store,
    workspace_manager,
    questionnaire_engine,
    spec_builder,
    orchestrator,
)


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

    # MVP: Return mock plan summary
    # In full implementation, this would come from task_graph
    return PlanSummaryResponse(
        features=["User authentication", "Dashboard view", "Data visualization"],
        task_count=5,
        verification_steps=["Build project", "Run tests", "Start dev server"],
        estimated_scope="moderate",
        constraints=["Max 7 screens", "Web platform only", "No external API calls"],
    )


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
        session.update_phase(SessionPhase.EXECUTION)
        session.add_log("Plan approved, moving to EXECUTION phase")
    else:
        session.update_phase(SessionPhase.IDEA)
        reason = request.reason or "No reason provided"
        session.add_log(f"Plan rejected: {reason}, returning to IDEA phase")

    session_store.update_session(session)

    return {
        "status": "accepted",
        "next_phase": session.phase,
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

    # Build task progress lists (MVP: mock data for non-EXECUTION phases)
    completed_tasks = [
        TaskProgress(task_id=tid, title=f"Task {tid}", status="completed")
        for tid in session.completed_task_ids
    ]

    failed_tasks = [
        TaskProgress(task_id=tid, title=f"Task {tid}", status="failed")
        for tid in session.failed_task_ids
    ]

    active_task = None
    if session.active_task_id:
        active_task = TaskProgress(
            task_id=session.active_task_id,
            title=f"Task {session.active_task_id}",
            status="in_progress",
        )

    return ProgressResponse(
        session_id=session.session_id,
        phase=session.phase,
        active_task=active_task,
        completed_tasks=completed_tasks,
        failed_tasks=failed_tasks,
        logs=session.logs[-50:],  # Return last 50 log entries
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

    # For MVP, transition back to EXECUTION phase
    # In future, the coordinator will handle this transition based on the answer
    next_phase = SessionPhase.EXECUTION

    session.update_phase(next_phase)
    session_store.update_session(session)

    return {
        "status": "accepted",
        "next_phase": next_phase.value,
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
