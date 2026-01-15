"""Response models for API endpoints."""

from typing import Any, Optional
from pydantic import BaseModel, Field

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


# VF-192: Agent workflow response schemas


class InitializeAgentsResponse(BaseModel):
    """Response from agent initialization (VF-192)."""

    agent_ids: list[str]
    message: str


class AssignAgentRoleResponse(BaseModel):
    """Response from role/model assignment (VF-192)."""

    agent_id: str
    role: Optional[str]
    model_id: Optional[str]
    message: str


class SetMainTaskResponse(BaseModel):
    """Response from setting main task (VF-192)."""

    main_task: str
    message: str


class ConfigureAgentFlowResponse(BaseModel):
    """Response from configuring agent flow (VF-192)."""

    edge_count: int
    message: str


class WorkflowConfigResponse(BaseModel):
    """Response containing current workflow configuration (VF-192)."""

    agents: list[dict[str, Any]]
    agent_roles: dict[str, str]
    agent_models: dict[str, str]
    agent_graph: Optional[dict[str, Any]]
    main_task: Optional[str]


# VF-192: Simulation control response schemas


class SimulationConfigResponse(BaseModel):
    """Response from simulation configuration (VF-192)."""

    simulation_mode: str
    auto_delay_ms: Optional[int]
    tick_budget: Optional[int]
    message: str


class SimulationStartResponse(BaseModel):
    """Response from starting simulation (VF-192)."""

    tick_index: int
    tick_status: str
    message: str


class TickResponse(BaseModel):
    """Response from executing tick(s) (VF-192)."""

    tick_index: int
    tick_status: str
    events_processed: int
    message: str


class SimulationStateResponse(BaseModel):
    """Response containing current simulation state (VF-192)."""

    initial_prompt: Optional[str]
    first_agent_id: Optional[str]
    simulation_mode: str
    tick_index: int
    tick_status: str
    auto_delay_ms: Optional[int]
    tick_budget: Optional[int]
    pending_work_summary: Optional[str]
    agent_graph: Optional[dict[str, Any]] = None
    agents: list[dict[str, Any]] = Field(default_factory=list)
    available_roles: list[str] = Field(default_factory=list)


class SimulationResetResponse(BaseModel):
    """Response from simulation reset (VF-200)."""

    tick_index: int
    tick_status: str
    workflow_preserved: bool
    message: str


class SimulationPauseResponse(BaseModel):
    """Response from pausing simulation (VF-201)."""

    tick_index: int
    tick_status: str
    message: str
