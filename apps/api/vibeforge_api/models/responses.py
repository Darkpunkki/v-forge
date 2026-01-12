"""Response models for API endpoints."""

from typing import Any, Optional
from pydantic import BaseModel

from vibeforge_api.models.types import SessionPhase


class SessionResponse(BaseModel):
    """Response from session creation."""

    session_id: str
    phase: SessionPhase


class QuestionOption(BaseModel):
    """A single option for a question."""

    value: str
    label: str


class QuestionResponse(BaseModel):
    """Response containing next questionnaire question."""

    question_id: str
    text: str
    question_type: str  # radio, checkbox, select, slider
    options: list[QuestionOption] | None = None
    min_value: int | None = None
    max_value: int | None = None
    is_final: bool = False


class PlanSummaryResponse(BaseModel):
    """Response containing plan summary for review."""

    features: list[str]
    task_count: int
    verification_steps: list[str]
    estimated_scope: str
    constraints: list[str]


class TaskProgress(BaseModel):
    """Progress information for a single task."""

    task_id: str
    title: str
    status: str  # pending, in_progress, completed, failed


class ProgressResponse(BaseModel):
    """Response containing session progress information."""

    session_id: str
    phase: SessionPhase
    active_task: Optional[TaskProgress] = None
    completed_tasks: list[TaskProgress] = []
    failed_tasks: list[TaskProgress] = []
    logs: list[str] = []


class ResultResponse(BaseModel):
    """Response containing final session result and summary."""

    session_id: str
    status: str  # success, failed
    workspace_path: str
    generated_files: list[str]
    run_instructions: str
    summary: str
    artifacts: dict[str, str]  # artifact_name -> artifact_path


class ClarificationOption(BaseModel):
    """A single option for a clarification question."""

    label: str
    value: str
    description: Optional[str] = None


class ClarificationResponse(BaseModel):
    """Response containing clarification question from gates/agents."""

    question: str
    context: Optional[str | dict[str, Any]] = None
    options: list[ClarificationOption]
