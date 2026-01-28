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
    # IDEA-0003: Live agent control requests
    RegisterAgentRequest,
    DispatchTaskRequest,
    FollowUpRequest,
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
    # IDEA-0003: Live agent control responses
    AgentConnectionInfo,
    AgentListResponse,
    AgentDetailResponse,
    TaskDispatchResponse,
    TaskStatusResponse,
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
    "RegisterAgentRequest",
    "DispatchTaskRequest",
    "FollowUpRequest",
    "SimulationConfigResponse",
    "SimulationStartResponse",
    "TickResponse",
    "SimulationStateResponse",
    "SimulationResetResponse",
    "SimulationPauseResponse",
    "SimulationStopResponse",
    "AgentConnectionInfo",
    "AgentListResponse",
    "AgentDetailResponse",
    "TaskDispatchResponse",
    "TaskStatusResponse",
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
