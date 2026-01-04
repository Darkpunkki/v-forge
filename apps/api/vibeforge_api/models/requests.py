"""Request models for API endpoints."""

from typing import Any
from pydantic import BaseModel


class SubmitAnswerRequest(BaseModel):
    """Request to submit an answer to a questionnaire question."""

    question_id: str
    answer: Any


class PlanDecisionRequest(BaseModel):
    """Request to approve or reject a plan."""

    approved: bool
    reason: str | None = None
