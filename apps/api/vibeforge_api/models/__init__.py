"""Data models and types for VibeForge API."""

from models.base import LlmClient, LlmMessage, LlmRequest, LlmResponse, LlmUsage
from vibeforge_api.models.types import (
    SessionPhase,
    AgentRole,
    GateResult,
    ErrorResponse,
)
from vibeforge_api.models.requests import (
    # VF-192: Agent workflow requests
    InitializeAgentsRequest,
    AssignAgentRoleRequest,
    SetMainTaskRequest,
    ConfigureAgentFlowRequest,
    # VF-192/VF-200: Simulation requests
    SimulationConfigRequest,
    SimulationStartRequest,
    TickRequest,
    SimulationResetRequest,
)
from vibeforge_api.models.bridge_protocol import (
    RegisterMessage,
    RegisteredMessage,
    DispatchMessage,
    ProgressMessage,
    ResponseMessage,
    HeartbeatMessage,
    BridgeMessage,
    parse_bridge_message,
)
from vibeforge_api.models.responses import (
    # VF-192: Agent workflow responses
    InitializeAgentsResponse,
    AssignAgentRoleResponse,
    SetMainTaskResponse,
    ConfigureAgentFlowResponse,
    WorkflowConfigResponse,
    # VF-192/VF-200/VF-201: Simulation responses
    SimulationConfigResponse,
    SimulationStartResponse,
    TickResponse,
    SimulationStateResponse,
    SimulationResetResponse,
    SimulationPauseResponse,
    SimulationStopResponse,
)

__all__ = [
    "SessionPhase",
    "AgentRole",
    "GateResult",
    "ErrorResponse",
    "LlmClient",
    "LlmMessage",
    "LlmRequest",
    "LlmResponse",
    "LlmUsage",
    # VF-192: Agent workflow
    "InitializeAgentsRequest",
    "AssignAgentRoleRequest",
    "SetMainTaskRequest",
    "ConfigureAgentFlowRequest",
    "InitializeAgentsResponse",
    "AssignAgentRoleResponse",
    "SetMainTaskResponse",
    "ConfigureAgentFlowResponse",
    "WorkflowConfigResponse",
    # VF-192/VF-200/VF-201: Simulation
    "SimulationConfigRequest",
    "SimulationStartRequest",
    "TickRequest",
    "SimulationResetRequest",
    "SimulationConfigResponse",
    "SimulationStartResponse",
    "TickResponse",
    "SimulationStateResponse",
    "SimulationResetResponse",
    "SimulationPauseResponse",
    "SimulationStopResponse",
    # Agent bridge protocol
    "RegisterMessage",
    "RegisteredMessage",
    "DispatchMessage",
    "ProgressMessage",
    "ResponseMessage",
    "HeartbeatMessage",
    "BridgeMessage",
    "parse_bridge_message",
]
