"""Request models for API endpoints."""

from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class SubmitAnswerRequest(BaseModel):
    """Request to submit an answer to a questionnaire question."""

    question_id: str
    answer: Any


class PlanDecisionRequest(BaseModel):
    """Request to approve or reject a plan."""

    approved: bool
    reason: str | None = None


class ClarificationAnswerRequest(BaseModel):
    """Request to submit an answer to a clarification question."""

    answer: str


# VF-192: Agent workflow request schemas


class InitializeAgentsRequest(BaseModel):
    """Request to initialize agents for a session (VF-192)."""

    agent_count: int = Field(..., ge=1, le=10, description="Number of agents to initialize")

    @field_validator("agent_count")
    @classmethod
    def validate_agent_count(cls, v: int) -> int:
        """Validate agent count is reasonable."""
        if v < 1:
            raise ValueError("agent_count must be at least 1")
        if v > 10:
            raise ValueError("agent_count cannot exceed 10 (safety limit)")
        return v


class AssignAgentRoleRequest(BaseModel):
    """Request to assign role and model to an agent (VF-192)."""

    agent_id: str = Field(..., description="Agent identifier")
    role: Optional[str] = Field(None, description="Agent role (orchestrator/foreman/worker/reviewer/fixer)")
    model_id: Optional[str] = Field(None, description="Model ID (e.g., gpt-4, claude-3)")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        """Validate role is supported."""
        if v is None:
            return v
        valid_roles = {"orchestrator", "foreman", "worker", "reviewer", "fixer"}
        if v not in valid_roles:
            raise ValueError(f"role must be one of: {valid_roles}")
        return v


class SetMainTaskRequest(BaseModel):
    """Request to set main orchestration task (VF-192)."""

    main_task: str = Field(..., min_length=1, description="Main task description/goal")


class ConfigureAgentFlowRequest(BaseModel):
    """Request to configure agent-to-agent communication flow (VF-192)."""

    edges: list[dict[str, str]] = Field(
        ...,
        description="List of edges, each with 'from_agent' and 'to_agent' keys"
    )


# VF-192: Simulation control request schemas


class SimulationConfigRequest(BaseModel):
    """Request to configure simulation mode (VF-192)."""

    simulation_mode: str = Field(..., description="Simulation mode: 'manual' or 'auto'")
    auto_delay_ms: Optional[int] = Field(None, ge=0, description="Auto-run delay (ms)")
    tick_budget: Optional[int] = Field(None, ge=1, description="Max events per tick")

    @field_validator("simulation_mode")
    @classmethod
    def validate_simulation_mode(cls, v: str) -> str:
        """Validate simulation mode."""
        if v not in {"manual", "auto"}:
            raise ValueError("simulation_mode must be 'manual' or 'auto'")
        return v


class TickRequest(BaseModel):
    """Request to execute one or more ticks (VF-192)."""

    tick_count: int = Field(1, ge=1, le=100, description="Number of ticks to execute")
