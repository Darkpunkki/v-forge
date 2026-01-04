"""Session API endpoints."""

from fastapi import APIRouter, HTTPException, status

from vibeforge_api.core.session import session_store
from vibeforge_api.core.questionnaire import questionnaire_engine
from vibeforge_api.core.spec_builder import spec_builder
from vibeforge_api.core.workspace import workspace_manager
from vibeforge_api.core.artifacts import artifact_store
from vibeforge_api.core.mock_generator import mock_generator
from vibeforge_api.models.types import SessionPhase
from vibeforge_api.models.requests import SubmitAnswerRequest, PlanDecisionRequest
from vibeforge_api.models.responses import (
    SessionResponse,
    QuestionResponse,
    PlanSummaryResponse,
    ProgressResponse,
    TaskProgress,
    ResultResponse,
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
        # Initialize workspace first (needed for artifacts)
        workspace_manager.init_repo(session.session_id)
        session.add_log("Workspace initialized")

        # Generate IntentProfile
        intent_profile = questionnaire_engine.finalize(session.session_id, session.answers)
        session.intent_profile = intent_profile
        session.add_log("IntentProfile generated")

        # Store IntentProfile artifact
        artifact_store.save_artifact(session.session_id, "intent_profile.json", intent_profile)

        # Generate BuildSpec
        build_spec = spec_builder.fromIntent(intent_profile)
        session.build_spec = build_spec
        session.add_log("BuildSpec generated")

        # Store BuildSpec artifact
        artifact_store.save_artifact(session.session_id, "build_spec.json", build_spec)

        # Generate mock files (MVP demo)
        workspace_path = workspace_manager.get_workspace_path(session.session_id)
        generated_files = mock_generator.generate(session.session_id, build_spec, workspace_path)
        session.add_log(f"Generated {len(generated_files)} demo files")

        # Transition to IDEA phase (concept generation would happen next)
        # For MVP demo, skip directly to COMPLETE with mock generation
        session.update_phase(SessionPhase.COMPLETE)
        session.add_log("Session complete (MVP demo mode)")

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
    summary = _build_summary(session)

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
    if not build_spec:
        return "No build specification available."

    preset = build_spec["stack"]["preset"]

    if preset == "WEB_VITE_REACT_TS":
        return """# Run Instructions

1. Install dependencies:
   ```
   npm install
   ```

2. Start development server:
   ```
   npm run dev
   ```

3. Open http://localhost:5173 in your browser

4. Build for production:
   ```
   npm run build
   ```

5. Run tests:
   ```
   npm test
   ```
"""
    elif preset == "CLI_PYTHON":
        return """# Run Instructions

1. Install dependencies (if any):
   ```
   pip install -r requirements.txt
   ```

2. Run the CLI:
   ```
   python main.py --help
   ```

3. Run tests:
   ```
   python -m pytest
   ```
"""
    else:
        return "See README.md for run instructions."


def _build_summary(session) -> str:
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
"""
