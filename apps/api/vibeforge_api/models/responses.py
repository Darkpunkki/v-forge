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
