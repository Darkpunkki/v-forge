# WP-0044 — Agent workflow API endpoints

## Overview

- **VF Tasks:** VF-192, VF-193
- **Goal:** Add Pydantic schemas and 5 control API endpoints for agent initialization, role assignment, task setting, flow configuration, and workflow retrieval.
- **Dependencies:** WP-0043 (agent workflow models)

## Context

With the agent workflow models in place (WP-0043), we can now expose API endpoints for the control panel to configure simulations. These endpoints allow admins to:

1. Initialize N agents for a session
2. Assign roles and models to each agent
3. Set the main orchestration task
4. Configure agent-to-agent communication flows
5. Retrieve current workflow configuration

## Implementation Steps

### Step 1: Create request/response schemas (VF-192)

**File:** `apps/api/vibeforge_api/models/requests.py`

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class InitializeAgentsRequest(BaseModel):
    """Request to initialize agents for a session."""
    count: int = Field(..., ge=1, le=10, description="Number of agents to create (1-10)")

class AssignAgentRoleRequest(BaseModel):
    """Request to assign role and model to an agent."""
    agent_id: str = Field(..., description="Agent ID to configure")
    role: str = Field(..., description="Role: orchestrator, foreman, worker, reviewer, fixer")
    model_id: Optional[str] = Field(None, description="Model ID (e.g., 'gpt-4', 'claude-3')")

class SetMainTaskRequest(BaseModel):
    """Request to set the main orchestration task."""
    description: str = Field(..., min_length=1, description="Task description")
    acceptance_criteria: Optional[List[str]] = Field(None, description="Acceptance criteria")
    verification_commands: Optional[List[str]] = Field(None, description="Verification commands")

class ConfigureAgentFlowRequest(BaseModel):
    """Request to configure agent-to-agent communication graph."""
    edges: List[dict] = Field(..., description="List of {from_agent, to_agent, label?} edges")
```

**File:** `apps/api/vibeforge_api/models/responses.py`

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class AgentInfo(BaseModel):
    """Information about a single agent."""
    agent_id: str
    role: Optional[str] = None
    model_id: Optional[str] = None
    display_name: Optional[str] = None

class InitializeAgentsResponse(BaseModel):
    """Response after initializing agents."""
    session_id: str
    agents: List[AgentInfo]
    message: str

class AssignAgentRoleResponse(BaseModel):
    """Response after assigning role to agent."""
    agent_id: str
    role: str
    model_id: Optional[str] = None
    message: str

class MainTaskResponse(BaseModel):
    """Response after setting main task."""
    session_id: str
    task_set: bool
    description: str
    message: str

class AgentFlowResponse(BaseModel):
    """Response after configuring agent flow."""
    session_id: str
    edge_count: int
    is_valid: bool
    validation_error: Optional[str] = None
    message: str

class WorkflowConfigResponse(BaseModel):
    """Full workflow configuration for a session."""
    session_id: str
    agents: List[AgentInfo]
    agent_roles: Dict[str, str]
    agent_models: Dict[str, str]
    main_task: Optional[str] = None
    flow_edges: List[dict]
    is_configured: bool
```

**File:** `apps/api/vibeforge_api/models/__init__.py` (extend exports)

```python
from .requests import (
    # ... existing ...
    InitializeAgentsRequest,
    AssignAgentRoleRequest,
    SetMainTaskRequest,
    ConfigureAgentFlowRequest,
)
from .responses import (
    # ... existing ...
    AgentInfo,
    InitializeAgentsResponse,
    AssignAgentRoleResponse,
    MainTaskResponse,
    AgentFlowResponse,
    WorkflowConfigResponse,
)
```

### Step 2: Implement control workflow endpoints (VF-193)

**File:** `apps/api/vibeforge_api/routers/control.py`

```python
from vibeforge_api.models import (
    InitializeAgentsRequest, InitializeAgentsResponse,
    AssignAgentRoleRequest, AssignAgentRoleResponse,
    SetMainTaskRequest, MainTaskResponse,
    ConfigureAgentFlowRequest, AgentFlowResponse,
    WorkflowConfigResponse, AgentInfo,
)
from orchestration.models import AgentConfig, AgentRole, AgentFlowGraph, AgentFlowEdge
import uuid

@router.post("/sessions/{session_id}/agents/init", response_model=InitializeAgentsResponse)
async def initialize_agents(session_id: str, request: InitializeAgentsRequest):
    """Initialize N agents for workflow configuration."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Phase guard: only allow in certain phases
    allowed_phases = [SessionPhase.INIT, SessionPhase.QUESTIONNAIRE, SessionPhase.PLAN_REVIEW]
    if session.phase not in allowed_phases:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot initialize agents in phase {session.phase}"
        )

    # Create agent instances
    agents = []
    for i in range(request.count):
        agent = AgentConfig(
            agent_id=f"agent-{uuid.uuid4().hex[:8]}",
            display_name=f"Agent {i + 1}"
        )
        agents.append(agent)

    # Update session
    session.agents = agents
    session.agent_roles = {}
    session.agent_models = {}
    session_store.update_session(session)

    return InitializeAgentsResponse(
        session_id=session_id,
        agents=[AgentInfo(agent_id=a.agent_id, display_name=a.display_name) for a in agents],
        message=f"Initialized {len(agents)} agents"
    )

@router.post("/sessions/{session_id}/agents/assign", response_model=AssignAgentRoleResponse)
async def assign_agent_role(session_id: str, request: AssignAgentRoleRequest):
    """Assign role and model to a specific agent."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate agent exists
    agent_ids = [a.agent_id for a in session.agents]
    if request.agent_id not in agent_ids:
        raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} not found")

    # Validate role
    try:
        role = AgentRole(request.role)
    except ValueError:
        valid_roles = [r.value for r in AgentRole]
        raise HTTPException(status_code=400, detail=f"Invalid role. Valid: {valid_roles}")

    # Update agent config
    for agent in session.agents:
        if agent.agent_id == request.agent_id:
            agent.role = role
            agent.model_id = request.model_id
            break

    session.agent_roles[request.agent_id] = request.role
    if request.model_id:
        session.agent_models[request.agent_id] = request.model_id

    session_store.update_session(session)

    return AssignAgentRoleResponse(
        agent_id=request.agent_id,
        role=request.role,
        model_id=request.model_id,
        message=f"Assigned role {request.role} to agent"
    )

@router.post("/sessions/{session_id}/task", response_model=MainTaskResponse)
async def set_main_task(session_id: str, request: SetMainTaskRequest):
    """Set the main orchestration task for the simulation."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.main_task = request.description
    # Optionally store acceptance_criteria and verification_commands in session artifacts
    session_store.update_session(session)

    return MainTaskResponse(
        session_id=session_id,
        task_set=True,
        description=request.description,
        message="Main task configured"
    )

@router.post("/sessions/{session_id}/flows", response_model=AgentFlowResponse)
async def configure_agent_flow(session_id: str, request: ConfigureAgentFlowRequest):
    """Configure agent-to-agent communication graph."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Build flow graph
    edges = [
        AgentFlowEdge(
            from_agent=e.get("from_agent"),
            to_agent=e.get("to_agent"),
            label=e.get("label")
        )
        for e in request.edges
    ]
    graph = AgentFlowGraph(edges=edges)

    # Validate DAG
    agent_ids = [a.agent_id for a in session.agents]
    is_valid, error = graph.validate_dag(agent_ids)

    if not is_valid:
        return AgentFlowResponse(
            session_id=session_id,
            edge_count=len(edges),
            is_valid=False,
            validation_error=error,
            message="Flow validation failed"
        )

    session.agent_graph = graph
    session_store.update_session(session)

    return AgentFlowResponse(
        session_id=session_id,
        edge_count=len(edges),
        is_valid=True,
        message="Agent flow configured"
    )

@router.get("/sessions/{session_id}/workflow", response_model=WorkflowConfigResponse)
async def get_workflow_config(session_id: str):
    """Get current workflow configuration for a session."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    agents = [
        AgentInfo(
            agent_id=a.agent_id,
            role=a.role.value if a.role else None,
            model_id=a.model_id,
            display_name=a.display_name
        )
        for a in session.agents
    ]

    flow_edges = []
    if session.agent_graph:
        flow_edges = [
            {"from_agent": e.from_agent, "to_agent": e.to_agent, "label": e.label}
            for e in session.agent_graph.edges
        ]

    is_configured = (
        len(session.agents) > 0 and
        len(session.agent_roles) > 0 and
        session.main_task is not None
    )

    return WorkflowConfigResponse(
        session_id=session_id,
        agents=agents,
        agent_roles=session.agent_roles,
        agent_models=session.agent_models,
        main_task=session.main_task,
        flow_edges=flow_edges,
        is_configured=is_configured
    )
```

### Step 3: Add API tests

**File:** `apps/api/tests/test_control_api.py` (extend)

```python
def test_initialize_agents():
    """POST /control/sessions/{id}/agents/init creates agents."""
    # Create session first
    response = client.post("/sessions")
    session_id = response.json()["session_id"]

    # Initialize 3 agents
    response = client.post(
        f"/control/sessions/{session_id}/agents/init",
        json={"count": 3}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["agents"]) == 3
    assert all("agent_id" in a for a in data["agents"])

def test_assign_agent_role():
    """POST /control/sessions/{id}/agents/assign sets role."""
    # Setup: create session and init agents
    session_id = create_session_with_agents(count=2)
    agents = get_session_agents(session_id)

    response = client.post(
        f"/control/sessions/{session_id}/agents/assign",
        json={"agent_id": agents[0]["agent_id"], "role": "worker", "model_id": "gpt-4"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "worker"

def test_assign_invalid_role():
    """Invalid role returns 400."""
    session_id = create_session_with_agents(count=1)
    agents = get_session_agents(session_id)

    response = client.post(
        f"/control/sessions/{session_id}/agents/assign",
        json={"agent_id": agents[0]["agent_id"], "role": "invalid_role"}
    )
    assert response.status_code == 400

def test_set_main_task():
    """POST /control/sessions/{id}/task sets the task."""
    session_id = create_session_with_agents(count=1)

    response = client.post(
        f"/control/sessions/{session_id}/task",
        json={"description": "Build a todo app", "acceptance_criteria": ["Has add button"]}
    )
    assert response.status_code == 200
    assert response.json()["task_set"] is True

def test_configure_agent_flow_valid():
    """POST /control/sessions/{id}/flows accepts valid DAG."""
    session_id = create_session_with_agents(count=3)
    agents = get_session_agents(session_id)

    response = client.post(
        f"/control/sessions/{session_id}/flows",
        json={"edges": [
            {"from_agent": agents[0]["agent_id"], "to_agent": agents[1]["agent_id"]},
            {"from_agent": agents[1]["agent_id"], "to_agent": agents[2]["agent_id"]},
        ]}
    )
    assert response.status_code == 200
    assert response.json()["is_valid"] is True

def test_configure_agent_flow_cycle():
    """POST /control/sessions/{id}/flows rejects cyclic graph."""
    session_id = create_session_with_agents(count=2)
    agents = get_session_agents(session_id)

    response = client.post(
        f"/control/sessions/{session_id}/flows",
        json={"edges": [
            {"from_agent": agents[0]["agent_id"], "to_agent": agents[1]["agent_id"]},
            {"from_agent": agents[1]["agent_id"], "to_agent": agents[0]["agent_id"]},
        ]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert "Cycle" in data["validation_error"]

def test_get_workflow_config():
    """GET /control/sessions/{id}/workflow returns config."""
    session_id = create_session_with_agents(count=2)

    response = client.get(f"/control/sessions/{session_id}/workflow")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert len(data["agents"]) == 2
```

## Verification

```bash
cd apps/api && pytest tests/test_control_api.py -v
cd apps/api && python -c "from vibeforge_api.models import InitializeAgentsRequest, WorkflowConfigResponse"
```

## Files to Touch

- `apps/api/vibeforge_api/models/requests.py` — add 4 request schemas
- `apps/api/vibeforge_api/models/responses.py` — add 6 response schemas
- `apps/api/vibeforge_api/models/__init__.py` — export new models
- `apps/api/vibeforge_api/routers/control.py` — add 5 endpoints
- `apps/api/tests/test_control_api.py` — add endpoint tests

## Done When

- [ ] All 4 request schemas with validation
- [ ] All 6 response schemas
- [ ] 5 endpoints functional with phase guards
- [ ] OpenAPI docs show new endpoints
- [ ] Tests cover happy path and error cases
