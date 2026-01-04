"""Core types and enums for VibeForge."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class SessionPhase(str, Enum):
    """Session lifecycle phases."""

    QUESTIONNAIRE = "QUESTIONNAIRE"
    BUILD_SPEC = "BUILD_SPEC"
    IDEA = "IDEA"
    PLAN_REVIEW = "PLAN_REVIEW"
    EXECUTION = "EXECUTION"
    VERIFICATION = "VERIFICATION"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class AgentRole(str, Enum):
    """Agent roles for task execution."""

    ORCHESTRATOR = "ORCHESTRATOR"
    WORKER = "WORKER"
    FIXER = "FIXER"
    REVIEWER = "REVIEWER"


class GateResultStatus(str, Enum):
    """Gate evaluation result status."""

    OK = "OK"
    WARN = "WARN"
    BLOCK = "BLOCK"


class GateResult(BaseModel):
    """Result from a gate evaluation."""

    status: GateResultStatus
    message: str
    details: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Standard error response format."""

    code: str
    message: str
    detail: Optional[str] = None
