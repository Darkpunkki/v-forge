"""Session API endpoints."""

from fastapi import APIRouter, HTTPException, status

from vibeforge_api.core.session import session_store
from vibeforge_api.core.questionnaire import questionnaire_engine
from vibeforge_api.models.types import SessionPhase
from vibeforge_api.models.requests import SubmitAnswerRequest, PlanDecisionRequest
from vibeforge_api.models.responses import (
    SessionResponse,
    QuestionResponse,
    PlanSummaryResponse,
    ProgressResponse,
    TaskProgress,
)

router = APIRouter()


# VF-021: POST /sessions (startSession)
@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def start_session():
    """Create a new session and initialize workspace."""
    session = session_store.create_session()
    session.add_log("Session created")

    return SessionResponse(
        session_id=session.session_id,
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

    question = questionnaire_engine.get_next_question(session.current_question_index)
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

    # Validate answer
    if not questionnaire_engine.validate_answer(request.question_id, request.answer):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid answer for question {request.question_id}",
        )

    # Store answer
    session.add_answer(request.question_id, request.answer)
    session.current_question_index += 1

    # Check if questionnaire is complete
    if questionnaire_engine.is_questionnaire_complete(session.current_question_index):
        session.update_phase(SessionPhase.BUILD_SPEC)
        session.add_log("Questionnaire complete, moving to BUILD_SPEC phase")

    session_store.update_session(session)

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
