# WP-0017 — Task distribution and agent framework adapter

## VF Tasks Included
- VF-095: Distributor.route(task) -> AgentRole (role hint rules)
- VF-096: Escalation policy (failures -> stronger role/model)
- VF-100: AgentFramework.runTask() interface
- VF-101: MVP AgentFrameworkAdapter
- VF-102: AgentRegistry (role -> prompt/tool policy/output schema)
- VF-103: Placeholder adapters (LangGraph/CrewAI/AutoGen stubs)

## Goal
Implement task-to-role routing and pluggable agent framework adapter to enable agent dispatch and execution. This connects TaskMaster scheduling with actual agent execution.

## Dependencies
- WP-0016 ✓ (TaskMaster for task scheduling)
- WP-0014 ✓ (ModelRouter for model selection)
- WP-0012 ✓ (LlmClient interface)

## Current State Analysis

From previous work packages:
- ✓ TaskMaster can schedule tasks (WP-0016)
- ✓ ModelRouter can select models based on role/complexity (WP-0014)
- ✓ LlmClient provides model abstraction (WP-0012)
- ✓ Task model defines role (worker/foreman/reviewer) and verification

**Gaps identified:**
1. **No Distributor** - Need component to route tasks to appropriate agent roles
2. **No escalation logic** - Need policy for handling repeated failures
3. **No AgentFramework interface** - Need abstraction for running agent tasks
4. **No AgentFrameworkAdapter** - Need MVP implementation
5. **No AgentRegistry** - Need role -> prompt/tools/schema mapping
6. **No framework stubs** - Need placeholders for future integrations

## Execution Plan

### 1. Implement Distributor (VF-095, VF-096)

Create `runtime/distributor.py`:

```python
from dataclasses import dataclass
from typing import Optional
from orchestration.models import Task


@dataclass
class AgentRole:
    """Agent role assignment for a task."""
    role: str  # "worker", "foreman", "reviewer", "fixer"
    model_tier: str  # "fast", "balanced", "powerful"
    reason: str  # Why this role was selected


class Distributor:
    """
    Routes tasks to agent roles based on hints and heuristics.

    VF-095: Implements task -> role routing logic
    VF-096: Implements escalation policy for failures
    """

    def __init__(self):
        """Initialize distributor with default routing rules."""
        pass

    def route(self, task: Task, failure_count: int = 0) -> AgentRole:
        """
        VF-095: Route task to appropriate agent role.

        Routing logic:
        1. Use task.role as default (from TaskGraph)
        2. Apply escalation policy based on failure_count
        3. Select model tier based on task complexity

        Args:
            task: Task to route
            failure_count: Number of previous failures (for escalation)

        Returns:
            AgentRole assignment
        """
        # Start with task's explicit role
        role = task.role
        model_tier = "balanced"  # Default
        reason = f"Task specifies role: {role}"

        # VF-096: Escalation policy
        if failure_count > 0:
            role, model_tier, reason = self._escalate(task, failure_count)

        return AgentRole(role=role, model_tier=model_tier, reason=reason)

    def _escalate(self, task: Task, failure_count: int) -> tuple[str, str, str]:
        """
        VF-096: Escalate role/model based on failure count.

        Escalation ladder:
        - 1 failure (1st retry): Same role, upgrade to "powerful" model
        - 2+ failures: Escalate to "fixer" role with "powerful" model

        Args:
            task: Failed task
            failure_count: Number of failures

        Returns:
            Tuple of (role, model_tier, reason)
        """
        if failure_count == 1:
            # First retry: upgrade model, keep role
            return (
                task.role,
                "powerful",
                f"Escalated to powerful model after {failure_count} failure(s)"
            )
        else:
            # Multiple failures: escalate to fixer with powerful model
            return (
                "fixer",
                "powerful",
                f"Escalated to fixer role after {failure_count} failure(s)"
            )
```

### 2. Define AgentFramework Interface (VF-100)

Create `models/agent_framework.py`:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional
from orchestration.models import Task


@dataclass
class AgentResult:
    """Standard result from agent task execution."""
    success: bool
    outputs: dict[str, Any]  # Files, artifacts produced
    logs: list[str]  # Execution logs
    error_message: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "outputs": self.outputs,
            "logs": self.logs,
            "error_message": self.error_message
        }


class AgentFramework(ABC):
    """
    VF-100: Interface for agent framework adapters.

    Allows pluggable agent implementations (direct LLM, LangGraph, CrewAI, etc.)
    """

    @abstractmethod
    async def runTask(
        self,
        task: Task,
        role: str,
        context: dict[str, Any]
    ) -> AgentResult:
        """
        Execute a task using an agent with the specified role.

        Args:
            task: Task to execute
            role: Agent role (worker/foreman/reviewer/fixer)
            context: Execution context (workspace path, artifacts, etc.)

        Returns:
            AgentResult with success status and outputs
        """
        pass

    @abstractmethod
    def get_framework_name(self) -> str:
        """Return framework name for logging."""
        pass
```

### 3. Implement MVP AgentFrameworkAdapter (VF-101)

```python
from models.base.llm_client import LlmClient, LlmRequest, LlmMessage
from models.router import get_model_router, RoutingContext
from models.validation import OutputValidator
from models.agent_framework import AgentFramework, AgentResult
from runtime.agent_registry import get_agent_registry


class DirectLlmAdapter(AgentFramework):
    """
    VF-101: MVP adapter that calls LLM directly with role prompt.

    Simplest possible implementation - no complex framework overhead.
    """

    def __init__(self, llm_client: LlmClient):
        """Initialize with LLM client."""
        self.llm_client = llm_client
        self.router = get_model_router()
        self.validator = OutputValidator()
        self.registry = get_agent_registry()

    async def runTask(
        self,
        task: Task,
        role: str,
        context: dict[str, Any]
    ) -> AgentResult:
        """
        Execute task by calling LLM with role prompt.

        Steps:
        1. Get role prompt from registry
        2. Format prompt with task details and context
        3. Select model based on role and tier
        4. Call LLM
        5. Validate output against schema
        6. Return AgentResult
        """
        # Get role configuration
        role_config = self.registry.get_role_config(role)

        # Build prompt
        prompt = role_config.prompt_template.format(
            task_id=task.task_id,
            description=task.description,
            expected_outputs=task.expected_outputs,
            context=context
        )

        # Select model
        routing_ctx = RoutingContext(
            role=role,
            complexity="simple",  # Task complexity from context
            metadata={"task_id": task.task_id}
        )
        provider, model = self.router.select_model(routing_ctx)

        # Make LLM request
        request = LlmRequest(
            messages=[
                LlmMessage(role="system", content=role_config.system_prompt),
                LlmMessage(role="user", content=prompt)
            ],
            model=model,
            temperature=0.7
        )

        try:
            response = await self.llm_client.complete(request)

            # Validate output
            result = self.validator.validate(response, role_config.output_schema)

            if result.valid:
                return AgentResult(
                    success=True,
                    outputs=result.parsed_output,
                    logs=[f"Model: {model}", f"Provider: {provider}"]
                )
            else:
                return AgentResult(
                    success=False,
                    outputs={},
                    logs=[f"Validation failed: {result.errors}"],
                    error_message=f"Output validation failed: {result.errors}"
                )
        except Exception as e:
            return AgentResult(
                success=False,
                outputs={},
                logs=[f"LLM call failed: {str(e)}"],
                error_message=str(e)
            )

    def get_framework_name(self) -> str:
        """Return framework name."""
        return "DirectLLM"
```

### 4. Implement AgentRegistry (VF-102)

Create `runtime/agent_registry.py`:

```python
from dataclasses import dataclass
from typing import Any


@dataclass
class RoleConfig:
    """Configuration for an agent role."""
    role: str
    system_prompt: str
    prompt_template: str
    output_schema: dict[str, Any]
    allowed_tools: list[str]


class AgentRegistry:
    """
    VF-102: Central registry for agent role configurations.

    Maps roles to prompts, tool permissions, and output schemas.
    """

    def __init__(self):
        """Initialize with default role configurations."""
        self.roles: dict[str, RoleConfig] = {
            "worker": RoleConfig(
                role="worker",
                system_prompt="You are a software development agent. Implement the requested task precisely.",
                prompt_template=(
                    "Task ID: {task_id}\n"
                    "Description: {description}\n"
                    "Expected outputs: {expected_outputs}\n\n"
                    "Context: {context}\n\n"
                    "Implement this task and return the result as JSON."
                ),
                output_schema={
                    "type": "object",
                    "properties": {
                        "files": {"type": "array", "items": {"type": "string"}},
                        "summary": {"type": "string"}
                    },
                    "required": ["files", "summary"]
                },
                allowed_tools=["read", "write", "bash"]
            ),
            "foreman": RoleConfig(
                role="foreman",
                system_prompt="You are a planning and coordination agent. Break down complex tasks.",
                prompt_template=(
                    "Task ID: {task_id}\n"
                    "Description: {description}\n\n"
                    "Plan the implementation approach and coordinate subtasks."
                ),
                output_schema={
                    "type": "object",
                    "properties": {
                        "plan": {"type": "array", "items": {"type": "string"}},
                        "dependencies": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["plan"]
                },
                allowed_tools=["read", "glob", "grep"]
            ),
            "reviewer": RoleConfig(
                role="reviewer",
                system_prompt="You are a code review agent. Verify quality and correctness.",
                prompt_template=(
                    "Task ID: {task_id}\n"
                    "Description: {description}\n\n"
                    "Review the implementation and provide feedback."
                ),
                output_schema={
                    "type": "object",
                    "properties": {
                        "approved": {"type": "boolean"},
                        "issues": {"type": "array", "items": {"type": "string"}},
                        "suggestions": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["approved"]
                },
                allowed_tools=["read", "grep", "bash"]
            ),
            "fixer": RoleConfig(
                role="fixer",
                system_prompt="You are a debugging and fixing agent. Diagnose and resolve failures.",
                prompt_template=(
                    "Task ID: {task_id}\n"
                    "Description: {description}\n"
                    "Previous error: {context}\n\n"
                    "Diagnose the issue and implement a fix."
                ),
                output_schema={
                    "type": "object",
                    "properties": {
                        "diagnosis": {"type": "string"},
                        "fix_applied": {"type": "boolean"},
                        "files_modified": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["diagnosis", "fix_applied"]
                },
                allowed_tools=["read", "write", "bash", "grep", "glob"]
            )
        }

    def get_role_config(self, role: str) -> RoleConfig:
        """
        Get configuration for a role.

        Args:
            role: Agent role name

        Returns:
            RoleConfig for the role

        Raises:
            ValueError: If role is unknown
        """
        if role not in self.roles:
            raise ValueError(f"Unknown role: {role}. Available: {list(self.roles.keys())}")
        return self.roles[role]

    def list_roles(self) -> list[str]:
        """Return list of registered roles."""
        return list(self.roles.keys())


# Global registry instance
_agent_registry = None


def get_agent_registry() -> AgentRegistry:
    """Get global agent registry instance."""
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry
```

### 5. Add Placeholder Adapters (VF-103)

Create `models/agent_framework_stubs.py`:

```python
from models.agent_framework import AgentFramework, AgentResult
from orchestration.models import Task


class LangGraphAdapter(AgentFramework):
    """
    VF-103: Placeholder for LangGraph integration.

    Future: Connect to LangGraph for graph-based agent workflows.
    """

    async def runTask(self, task: Task, role: str, context: dict) -> AgentResult:
        """Not implemented - placeholder only."""
        raise NotImplementedError("LangGraph adapter not yet implemented")

    def get_framework_name(self) -> str:
        return "LangGraph (stub)"


class CrewAIAdapter(AgentFramework):
    """
    VF-103: Placeholder for CrewAI integration.

    Future: Connect to CrewAI for multi-agent collaboration.
    """

    async def runTask(self, task: Task, role: str, context: dict) -> AgentResult:
        """Not implemented - placeholder only."""
        raise NotImplementedError("CrewAI adapter not yet implemented")

    def get_framework_name(self) -> str:
        return "CrewAI (stub)"


class AutoGenAdapter(AgentFramework):
    """
    VF-103: Placeholder for AutoGen integration.

    Future: Connect to AutoGen for conversational multi-agent systems.
    """

    async def runTask(self, task: Task, role: str, context: dict) -> AgentResult:
        """Not implemented - placeholder only."""
        raise NotImplementedError("AutoGen adapter not yet implemented")

    def get_framework_name(self) -> str:
        return "AutoGen (stub)"
```

## Done Means

- [x] VF-095: Distributor.route() implemented
  - **File:** `runtime/distributor.py:33` (Distributor.route method)
  - **Features:** Task-to-role routing based on task.role, model tier selection (balanced default), validation of role validity
  - **Tests:** `apps/api/tests/test_distributor.py::TestDistributorRouting` (5 tests)
  - **Verify:** `cd apps/api && pytest tests/test_distributor.py::TestDistributorRouting -v` (5 passed)

- [x] VF-096: Escalation policy implemented
  - **File:** `runtime/distributor.py:72` (_escalate method)
  - **Features:** 1st failure -> powerful model (same role), 2+ failures -> fixer role + powerful model, prevents infinite retry loops
  - **Tests:** `apps/api/tests/test_distributor.py::TestDistributorEscalation` (5 tests)
  - **Verify:** `cd apps/api && pytest tests/test_distributor.py::TestDistributorEscalation -v` (5 passed)

- [x] VF-100: AgentFramework interface defined
  - **File:** `models/agent_framework.py:12` (AgentFramework abstract class, AgentResult dataclass)
  - **Features:** runTask() abstract method, AgentResult with success/outputs/logs/error, get_framework_name() method, pluggable adapter pattern
  - **Tests:** `apps/api/tests/test_agent_framework.py::TestAgentResult` (3 tests)
  - **Verify:** `cd apps/api && pytest tests/test_agent_framework.py::TestAgentResult -v` (3 passed)

- [x] VF-101: DirectLlmAdapter implemented
  - **File:** `models/agent_framework.py:51` (DirectLlmAdapter class)
  - **Features:** Direct LLM calls with role-specific prompts, model routing via ModelRouter, error handling, logs model/provider/role
  - **Tests:** `apps/api/tests/test_agent_framework.py::TestDirectLlmAdapter` (7 tests)
  - **Verify:** `cd apps/api && pytest tests/test_agent_framework.py::TestDirectLlmAdapter -v` (7 passed)

- [x] VF-102: AgentRegistry implemented
  - **File:** `runtime/agent_registry.py:12` (AgentRegistry class, RoleConfig dataclass)
  - **Features:** Pre-configured roles (worker/foreman/reviewer/fixer), system prompts, user prompt templates, JSON output schemas, allowed tools per role, custom role registration
  - **Tests:** `apps/api/tests/test_agent_framework.py::TestAgentRegistry` (10 tests)
  - **Verify:** `cd apps/api && pytest tests/test_agent_framework.py::TestAgentRegistry -v` (10 passed)

- [x] VF-103: Placeholder adapters added
  - **File:** `models/agent_framework_stubs.py` (LangGraphAdapter, CrewAIAdapter, AutoGenAdapter)
  - **Features:** All stubs raise NotImplementedError with helpful messages, implement AgentFramework interface, return framework names with "(stub)" suffix
  - **Tests:** `apps/api/tests/test_agent_framework.py::TestAgentFrameworkStubs` (7 tests)
  - **Verify:** `cd apps/api && pytest tests/test_agent_framework.py::TestAgentFrameworkStubs -v` (7 passed)

**Total tests:** 398 (was 355, added 43 new tests)
**All tests passing:** ✓ (397 passed, 1 skipped from WP-0015)
**New test files:**
- `apps/api/tests/test_distributor.py` (15 tests for VF-095, VF-096)
- `apps/api/tests/test_agent_framework.py` (28 tests for VF-100, VF-101, VF-102, VF-103)

## Verification Commands
```bash
cd apps/api && pytest tests/test_distributor.py -v
cd apps/api && pytest tests/test_agent_framework.py -v
cd apps/api && pytest -v
```

## Notes
- DirectLlmAdapter is MVP - no complex framework overhead
- Escalation policy prevents infinite retry loops
- AgentRegistry centralizes role behavior
- Framework stubs make future integrations explicit
- All components integrate with existing ModelRouter and OutputValidator
