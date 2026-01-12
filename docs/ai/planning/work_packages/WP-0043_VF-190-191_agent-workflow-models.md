# WP-0043 — Session model + orchestration models for agent workflow

## Overview

- **VF Tasks:** VF-190, VF-191
- **Goal:** Extend Session model with agent workflow fields and create AgentConfig/AgentFlowGraph orchestration models to enable workflow state persistence.
- **Dependencies:** WP-0013 ✓ (Session model foundations)

## Context

The control panel currently supports monitoring and visualization of agent execution (VF-170 through VF-186 complete). To enable simulation mode where admins can configure and run custom agent workflows, we need to extend the data models to store:

1. **Agent instances** — initialized agents for a simulation
2. **Role assignments** — which agent plays which role
3. **Model assignments** — which model each agent uses
4. **Communication graph** — agent-to-agent flow topology
5. **Main task** — the orchestration goal

## Implementation Steps

### Step 1: Extend Session model (VF-190)

**File:** `apps/api/vibeforge_api/core/session.py`

Add these fields to the `Session` dataclass:

```python
from typing import List, Dict, Optional
from orchestration.models import AgentConfig, AgentFlowGraph

@dataclass
class Session:
    # ... existing fields ...

    # Agent workflow fields (for control panel simulation mode)
    agents: List[AgentConfig] = field(default_factory=list)
    agent_roles: Dict[str, str] = field(default_factory=dict)  # agent_id -> role
    agent_models: Dict[str, str] = field(default_factory=dict)  # agent_id -> model_id
    agent_graph: Optional[AgentFlowGraph] = None
    main_task: Optional[str] = None
```

**Acceptance criteria:**
- [ ] All 5 workflow fields added with proper types
- [ ] Default values prevent None errors
- [ ] `SessionStore.update_session()` persists these fields
- [ ] Existing session tests still pass

### Step 2: Create AgentConfig model (VF-191)

**File:** `orchestration/models.py`

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum

class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    FOREMAN = "foreman"
    WORKER = "worker"
    REVIEWER = "reviewer"
    FIXER = "fixer"

class AgentConfig(BaseModel):
    """Configuration for a single agent instance."""
    agent_id: str = Field(..., description="Unique identifier for this agent")
    role: Optional[AgentRole] = Field(None, description="Assigned role")
    model_id: Optional[str] = Field(None, description="Model to use (e.g., 'gpt-4', 'claude-3')")
    display_name: Optional[str] = Field(None, description="Human-readable name")

    @field_validator('agent_id')
    @classmethod
    def validate_agent_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("agent_id cannot be empty")
        return v.strip()
```

**Acceptance criteria:**
- [ ] AgentConfig model with id, role, model_id, display_name
- [ ] AgentRole enum with all 5 roles
- [ ] Validation for non-empty agent_id

### Step 3: Create AgentFlowGraph model (VF-191)

**File:** `orchestration/models.py`

```python
class AgentFlowEdge(BaseModel):
    """Edge in agent communication graph."""
    from_agent: str = Field(..., description="Source agent ID")
    to_agent: str = Field(..., description="Target agent ID")
    label: Optional[str] = Field(None, description="Edge label/description")

class AgentFlowGraph(BaseModel):
    """DAG representing agent-to-agent communication topology."""
    edges: List[AgentFlowEdge] = Field(default_factory=list)

    def validate_dag(self, agent_ids: List[str]) -> tuple[bool, Optional[str]]:
        """Validate graph is acyclic and references valid agents.

        Returns:
            (is_valid, error_message) tuple
        """
        # Check all referenced agents exist
        for edge in self.edges:
            if edge.from_agent not in agent_ids:
                return False, f"Unknown agent: {edge.from_agent}"
            if edge.to_agent not in agent_ids:
                return False, f"Unknown agent: {edge.to_agent}"

        # Check for cycles using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for edge in self.edges:
                if edge.from_agent == node:
                    neighbor = edge.to_agent
                    if neighbor not in visited:
                        if has_cycle(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        return True

            rec_stack.remove(node)
            return False

        for agent_id in agent_ids:
            if agent_id not in visited:
                if has_cycle(agent_id):
                    return False, "Cycle detected in agent flow graph"

        return True, None

    def get_predecessors(self, agent_id: str) -> List[str]:
        """Get agents that feed into this agent."""
        return [e.from_agent for e in self.edges if e.to_agent == agent_id]

    def get_successors(self, agent_id: str) -> List[str]:
        """Get agents this agent feeds into."""
        return [e.to_agent for e in self.edges if e.from_agent == agent_id]
```

**Acceptance criteria:**
- [ ] AgentFlowEdge with from/to/label
- [ ] AgentFlowGraph with edges list
- [ ] `validate_dag()` checks for cycles and unknown agents
- [ ] Helper methods for graph traversal

### Step 4: Add unit tests

**File:** `apps/api/tests/test_session_model.py` (extend)

```python
def test_session_workflow_fields_default():
    """Workflow fields should default to empty/None."""
    session = Session(session_id="test-123")
    assert session.agents == []
    assert session.agent_roles == {}
    assert session.agent_models == {}
    assert session.agent_graph is None
    assert session.main_task is None

def test_session_with_agent_config():
    """Session can store agent configurations."""
    from orchestration.models import AgentConfig, AgentRole

    agent = AgentConfig(
        agent_id="agent-1",
        role=AgentRole.WORKER,
        model_id="gpt-4"
    )
    session = Session(session_id="test-123", agents=[agent])
    assert len(session.agents) == 1
    assert session.agents[0].role == AgentRole.WORKER
```

**File:** `apps/api/tests/test_orchestration_models.py` (extend)

```python
def test_agent_config_validation():
    """AgentConfig requires non-empty agent_id."""
    with pytest.raises(ValidationError):
        AgentConfig(agent_id="")

def test_agent_flow_graph_valid():
    """Valid DAG passes validation."""
    graph = AgentFlowGraph(edges=[
        AgentFlowEdge(from_agent="a", to_agent="b"),
        AgentFlowEdge(from_agent="b", to_agent="c"),
    ])
    is_valid, error = graph.validate_dag(["a", "b", "c"])
    assert is_valid
    assert error is None

def test_agent_flow_graph_cycle_detection():
    """Cyclic graph fails validation."""
    graph = AgentFlowGraph(edges=[
        AgentFlowEdge(from_agent="a", to_agent="b"),
        AgentFlowEdge(from_agent="b", to_agent="a"),  # cycle!
    ])
    is_valid, error = graph.validate_dag(["a", "b"])
    assert not is_valid
    assert "Cycle" in error

def test_agent_flow_graph_unknown_agent():
    """Unknown agent reference fails validation."""
    graph = AgentFlowGraph(edges=[
        AgentFlowEdge(from_agent="a", to_agent="unknown"),
    ])
    is_valid, error = graph.validate_dag(["a", "b"])
    assert not is_valid
    assert "Unknown agent" in error
```

## Verification

```bash
cd apps/api && pytest tests/test_session_model.py tests/test_session_store.py tests/test_orchestration_models.py -v
```

## Files to Touch

- `apps/api/vibeforge_api/core/session.py` — add workflow fields
- `orchestration/models.py` — add AgentConfig, AgentRole, AgentFlowEdge, AgentFlowGraph
- `apps/api/tests/test_session_model.py` — extend with workflow field tests
- `apps/api/tests/test_orchestration_models.py` — add AgentConfig/FlowGraph tests

## Done When

- [x] Session model includes all 5 workflow fields (+ 5 simulation fields)
- [x] AgentConfig model with validation
- [x] AgentFlowGraph model with DAG validation
- [x] SimulationConfig and TickState models created
- [x] All existing tests pass (67 passed, 1 warning)
- [x] New tests cover edge cases (4 session tests + 13 orchestration tests)
