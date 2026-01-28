"""Request models for API endpoints."""

from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


# VF-192: Agent workflow request schemas


class AgentInitConfig(BaseModel):
    """Agent definition for initialization requests."""

    agent_id: str = Field(..., description="Agent identifier")
    display_name: Optional[str] = Field(None, description="Human-readable name")


class InitializeAgentsRequest(BaseModel):
    """Request to initialize agents for a session (VF-192)."""

    agent_count: Optional[int] = Field(
        None, ge=1, le=10, description="Number of agents to initialize"
    )
    agents: Optional[list[AgentInitConfig]] = Field(
        None, description="Explicit agent roster definitions"
    )

    @field_validator("agent_count")
    @classmethod
    def validate_agent_count(cls, v: Optional[int]) -> Optional[int]:
        """Validate agent count is reasonable."""
        if v is None:
            return v
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


class AgentFlowEdgeRequest(BaseModel):
    """Edge definition for agent flow configuration (VF-192)."""

    from_agent: str = Field(..., description="Source agent ID")
    to_agent: str = Field(..., description="Target agent ID")
    label: Optional[str] = Field(None, description="Edge label/description")
    bidirectional: bool = Field(
        False, description="Whether the edge allows traffic both directions"
    )


class ConfigureAgentFlowRequest(BaseModel):
    """Request to configure agent-to-agent communication flow (VF-192)."""

    edges: list[AgentFlowEdgeRequest] = Field(
        ...,
        description="List of edges, each with from_agent/to_agent and optional directionality"
    )


# VF-192: Simulation control request schemas


class SimulationConfigRequest(BaseModel):
    """Request to configure simulation mode (VF-192)."""

    simulation_mode: str = Field(..., description="Simulation mode: 'manual' or 'auto'")
    auto_delay_ms: Optional[int] = Field(None, ge=0, description="Auto-run delay (ms)")
    tick_budget: Optional[int] = Field(None, ge=1, description="Max events per tick")
    use_real_llm: Optional[bool] = Field(None, description="Enable real LLM calls")
    llm_provider: Optional[str] = Field(None, description="LLM provider identifier")
    default_model: Optional[str] = Field(None, description="Default LLM model name")
    default_temperature: Optional[float] = Field(
        None, ge=0, le=1, description="Default LLM temperature"
    )
    max_cost_usd: Optional[float] = Field(None, ge=0, description="Maximum allowed cost (USD)")
    tick_rate_limit_ms: Optional[int] = Field(
        None, ge=0, description="Minimum delay between ticks (ms)"
    )

    @field_validator("simulation_mode")
    @classmethod
    def validate_simulation_mode(cls, v: str) -> str:
        """Validate simulation mode."""
        if v not in {"manual", "auto"}:
            raise ValueError("simulation_mode must be 'manual' or 'auto'")
        return v


class SimulationStartRequest(BaseModel):
    """Request to start simulation (VF-200)."""

    initial_prompt: Optional[str] = Field(
        None, description="Initial prompt to start the simulation"
    )
    first_agent_id: Optional[str] = Field(
        None, description="Agent ID to start the simulation"
    )


class TickRequest(BaseModel):
    """Request to execute one or more ticks (VF-192)."""

    tick_count: int = Field(1, ge=1, le=100, description="Number of ticks to execute")


class SimulationResetRequest(BaseModel):
    """Request to reset simulation state (VF-200)."""

    preserve_workflow: bool = Field(True, description="Keep workflow config (agents/roles/graph), only reset tick state")


# IDEA-0003: Live agent control request schemas


class RegisterAgentRequest(BaseModel):
    """Request to register a remote agent with the control plane."""

    name: str = Field(..., min_length=1, description="Agent display name")
    endpoint_url: str = Field(..., min_length=1, description="Agent bridge endpoint URL")


class DispatchTaskRequest(BaseModel):
    """Request to dispatch a task to a remote agent."""

    content: str = Field(..., min_length=1, description="Task content/instructions")
    context: dict[str, Any] = Field(default_factory=dict, description="Optional task context")


class FollowUpRequest(BaseModel):
    """Request to send a follow-up message to a remote agent."""

    content: str = Field(..., min_length=1, description="Follow-up message content")
