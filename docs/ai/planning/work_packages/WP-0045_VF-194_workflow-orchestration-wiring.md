# WP-0045 — Wire workflow config into orchestration

## Overview

- **VF Tasks:** VF-194
- **Goal:** Update SessionCoordinator to consume AgentConfig and add forced model override to ModelRouter for per-agent model enforcement.
- **Dependencies:** WP-0043 (models), WP-0044 (endpoints to set config)

## Context

With workflow configuration stored in the session (WP-0043) and API endpoints to set it (WP-0044), we now need to wire this configuration into the orchestration layer so that:

1. SessionCoordinator respects the configured agents and their roles
2. ModelRouter can be forced to use a specific model for an agent
3. Events include workflow configuration metadata

## Implementation Steps

### Step 1: Add forced_model to ModelRouter

**File:** `models/router.py`

```python
class RoutingContext(BaseModel):
    """Context for model routing decisions."""
    role: str
    complexity: str = "medium"  # low, medium, high
    retry_count: int = 0
    forced_model: Optional[str] = None  # NEW: override model selection

class ModelRouter:
    """Routes requests to appropriate models based on context."""

    def select_model(self, context: RoutingContext) -> str:
        """Select model based on routing rules.

        If forced_model is set, use it directly (for workflow simulation mode).
        Otherwise, apply normal routing logic.
        """
        # Check for forced model override
        if context.forced_model:
            # Validate the model exists
            if self._is_valid_model(context.forced_model):
                return context.forced_model
            else:
                # Fall back to default if invalid
                logger.warning(f"Invalid forced_model {context.forced_model}, using default")

        # Normal routing logic
        return self._route_by_rules(context)

    def _is_valid_model(self, model_id: str) -> bool:
        """Check if model ID is valid."""
        valid_models = self.config.get("valid_models", [
            "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo",
            "claude-3-opus", "claude-3-sonnet", "claude-3-haiku",
            "local-llama", "local-mixtral"
        ])
        return model_id in valid_models
```

**Tests:** `apps/api/tests/test_model_router.py`

```python
def test_forced_model_override():
    """Forced model bypasses routing rules."""
    router = get_model_router()
    context = RoutingContext(role="worker", forced_model="gpt-4-turbo")

    model = router.select_model(context)
    assert model == "gpt-4-turbo"

def test_forced_model_invalid_falls_back():
    """Invalid forced model falls back to default routing."""
    router = get_model_router()
    context = RoutingContext(role="worker", forced_model="nonexistent-model")

    model = router.select_model(context)
    assert model != "nonexistent-model"  # Should use default
```

### Step 2: Update SessionCoordinator to consume AgentConfig

**File:** `orchestration/coordinator/session_coordinator.py`

```python
from orchestration.models import AgentConfig, AgentFlowGraph

class SessionCoordinator:
    """Coordinates session lifecycle and agent execution."""

    def __init__(
        self,
        session: Session,
        orchestrator: Optional[Orchestrator] = None,
        agent_framework: Optional[AgentFrameworkAdapter] = None,
        workflow_config: Optional[dict] = None,  # NEW: explicit workflow config
    ):
        self.session = session
        self.orchestrator = orchestrator
        self.agent_framework = agent_framework
        self._workflow_config = workflow_config

    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Get configuration for a specific agent."""
        for agent in self.session.agents:
            if agent.agent_id == agent_id:
                return agent
        return None

    def get_forced_model(self, agent_id: str) -> Optional[str]:
        """Get forced model for agent if configured."""
        return self.session.agent_models.get(agent_id)

    async def execute_next_task(self) -> ExecutionResult:
        """Execute next task respecting workflow configuration."""
        # ... existing task retrieval logic ...

        # Get agent assignment for this task's role
        task_role = task.role
        assigned_agent = self._get_agent_for_role(task_role)

        # Build routing context with potential forced model
        forced_model = None
        if assigned_agent:
            forced_model = self.get_forced_model(assigned_agent.agent_id)

        routing_context = RoutingContext(
            role=task_role,
            complexity=self._assess_complexity(task),
            retry_count=failure_count,
            forced_model=forced_model,  # Pass forced model if configured
        )

        # Select model (will use forced_model if set)
        model = self.model_router.select_model(routing_context)

        # Emit event with workflow metadata
        self.event_log.emit(
            EventType.AGENT_INVOKED,
            session_id=self.session.session_id,
            metadata={
                "agent_role": task_role,
                "model": model,
                "forced_model": forced_model,
                "agent_id": assigned_agent.agent_id if assigned_agent else None,
                "workflow_configured": self._is_workflow_configured(),
            }
        )

        # ... rest of execution logic ...

    def _get_agent_for_role(self, role: str) -> Optional[AgentConfig]:
        """Find agent assigned to the given role."""
        for agent_id, assigned_role in self.session.agent_roles.items():
            if assigned_role == role:
                return self.get_agent_config(agent_id)
        return None

    def _is_workflow_configured(self) -> bool:
        """Check if simulation workflow is configured."""
        return (
            len(self.session.agents) > 0 and
            len(self.session.agent_roles) > 0 and
            self.session.main_task is not None
        )
```

### Step 3: Emit workflow metadata in events

Update event emission to include workflow configuration data:

```python
# In execute_next_task and other methods

metadata = {
    # Existing fields
    "agent_role": agent_role.role,
    "model_tier": agent_role.model_tier,
    "task_id": task.id,

    # Workflow configuration fields
    "workflow_mode": "simulation" if self._is_workflow_configured() else "normal",
    "configured_agents": len(self.session.agents),
    "agent_id": assigned_agent.agent_id if assigned_agent else None,
    "forced_model": forced_model,
    "main_task": self.session.main_task if self._is_workflow_configured() else None,
}
```

### Step 4: Add tests

**File:** `apps/api/tests/test_session_coordinator.py` (extend)

```python
class TestSessionCoordinatorWorkflow:
    """Tests for workflow configuration in SessionCoordinator."""

    def test_get_agent_config(self):
        """Coordinator can retrieve agent config by ID."""
        session = Session(session_id="test-1")
        session.agents = [
            AgentConfig(agent_id="agent-1", role=AgentRole.WORKER),
            AgentConfig(agent_id="agent-2", role=AgentRole.REVIEWER),
        ]

        coordinator = SessionCoordinator(session=session)
        agent = coordinator.get_agent_config("agent-1")
        assert agent is not None
        assert agent.role == AgentRole.WORKER

    def test_get_forced_model(self):
        """Coordinator returns forced model if configured."""
        session = Session(session_id="test-1")
        session.agent_models = {"agent-1": "gpt-4-turbo"}

        coordinator = SessionCoordinator(session=session)
        model = coordinator.get_forced_model("agent-1")
        assert model == "gpt-4-turbo"

    def test_is_workflow_configured(self):
        """Workflow is configured when agents, roles, and task set."""
        session = Session(session_id="test-1")
        coordinator = SessionCoordinator(session=session)

        # Not configured initially
        assert not coordinator._is_workflow_configured()

        # Configure workflow
        session.agents = [AgentConfig(agent_id="agent-1")]
        session.agent_roles = {"agent-1": "worker"}
        session.main_task = "Build a todo app"

        assert coordinator._is_workflow_configured()
```

## Verification

```bash
cd apps/api && pytest tests/test_session_coordinator.py tests/test_model_router.py -v
```

## Files to Touch

- `models/router.py` — add forced_model to RoutingContext and select_model
- `orchestration/coordinator/session_coordinator.py` — consume AgentConfig, emit workflow metadata
- `apps/api/tests/test_model_router.py` — add forced model tests
- `apps/api/tests/test_session_coordinator.py` — add workflow config tests

## Done When

- [x] ModelRouter respects forced_model override
- [x] SessionCoordinator retrieves agent config for tasks
- [x] Events include workflow_mode and agent metadata
- [x] Tests cover forced model and workflow configuration

## Completion Summary

**Status:** Complete ✓
**Date:** 2026-01-13

### Implementation Details:

1. **ModelRouter forced_model (VF-194)**
   - Added `forced_model: Optional[str]` to `RoutingContext` dataclass
   - Implemented `_validate_forced_model()` with provider:model parsing
   - Implemented `_infer_provider()` to detect provider from model name
   - Implemented `_is_valid_model()` with known model catalog
   - Updated `select_model()` to check forced_model first
   - Added 14 comprehensive tests in TestForcedModelRouting class
   - All 31 ModelRouter tests pass

2. **SessionCoordinator workflow configuration (VF-194)**
   - Added `get_agent_config(session, agent_id)` helper method
   - Added `get_forced_model(session, agent_id)` helper method
   - Added `get_agent_for_role(session, role)` helper method
   - Added `is_workflow_configured(session)` helper method
   - Updated `execute_next_task()` to detect workflow mode and retrieve forced_model
   - Added workflow metadata to context: forced_model, agent_id, workflow_mode, main_task
   - Enhanced AGENT_INVOKED event metadata with workflow configuration
   - Added 10 comprehensive tests in TestVF194_WorkflowConfiguration class

3. **DirectLlmAdapter integration (VF-194)**
   - Updated `runTask()` to extract forced_model from context
   - Pass forced_model to RoutingContext when calling select_model()

### Verification Results:

```bash
cd apps/api && pytest tests/test_model_router.py -v
# 31 passed (17 existing + 14 new forced_model tests)

cd apps/api && pytest tests/test_session_coordinator.py::TestVF194_WorkflowConfiguration -v
# 10 passed (all new workflow configuration tests)
```

### Files Modified:

- `models/router.py` - added forced_model parameter + validation (70 lines)
- `orchestration/coordinator/session_coordinator.py` - added workflow helpers + metadata (65 lines)
- `models/agent_framework.py` - consume forced_model from context (3 lines)
- `apps/api/tests/test_model_router.py` - added TestForcedModelRouting (218 lines, 14 tests)
- `apps/api/tests/test_session_coordinator.py` - added TestVF194_WorkflowConfiguration (138 lines, 10 tests)
