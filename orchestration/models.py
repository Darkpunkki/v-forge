"""Data models for orchestration layer."""

from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator


@dataclass
class ConceptDoc:
    """Structured concept document for a build (output of VF-073)."""

    session_id: str
    idea_description: str
    features: list[str]
    tech_stack: dict[str, str]
    file_structure: dict[str, str]
    verification_steps: list[str]
    constraints: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (excluding session_id for serialization)."""
        return {
            "idea_description": self.idea_description,
            "features": self.features,
            "tech_stack": self.tech_stack,
            "file_structure": self.file_structure,
            "verification_steps": self.verification_steps,
            "constraints": self.constraints,
        }

    @classmethod
    def from_dict(cls, session_id: str, data: dict[str, Any]) -> "ConceptDoc":
        """Create ConceptDoc from dictionary."""
        return cls(
            session_id=session_id,
            idea_description=data["idea_description"],
            features=data["features"],
            tech_stack=data["tech_stack"],
            file_structure=data["file_structure"],
            verification_steps=data["verification_steps"],
            constraints=data["constraints"],
        )


@dataclass
class Task:
    """Single task in a task graph."""

    task_id: str
    description: str
    role: str  # "worker", "foreman", "reviewer"
    dependencies: list[str]
    inputs: dict[str, Any]
    expected_outputs: list[str]
    verification: dict[str, Any]
    constraints: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "description": self.description,
            "role": self.role,
            "dependencies": self.dependencies,
            "inputs": self.inputs,
            "expected_outputs": self.expected_outputs,
            "verification": self.verification,
            "constraints": self.constraints,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        """Create Task from dictionary."""
        return cls(
            task_id=data["task_id"],
            description=data["description"],
            role=data["role"],
            dependencies=data.get("dependencies", []),
            inputs=data.get("inputs", {}),
            expected_outputs=data.get("expected_outputs", []),
            verification=data.get("verification", {}),
            constraints=data.get("constraints", {}),
        )


@dataclass
class TaskGraph:
    """DAG of tasks for executing a build (output of VF-074)."""

    session_id: str
    tasks: list[Task]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (excluding session_id for serialization)."""
        return {
            "tasks": [task.to_dict() for task in self.tasks],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, session_id: str, data: dict[str, Any]) -> "TaskGraph":
        """Create TaskGraph from dictionary."""
        tasks = [Task.from_dict(task_data) for task_data in data["tasks"]]
        return cls(
            session_id=session_id,
            tasks=tasks,
            metadata=data.get("metadata", {}),
        )

    def validate_dag(self) -> tuple[bool, list[str]]:
        """
        VF-090: Validate that task dependencies form a valid DAG.

        Checks:
        - All task_ids are unique
        - All dependencies reference existing tasks
        - No cycles exist
        - Roles are valid (worker/foreman/reviewer)
        - Verification types are valid

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        task_ids = {task.task_id for task in self.tasks}

        # Check all task_ids are unique
        if len(task_ids) != len(self.tasks):
            errors.append("Duplicate task IDs found")

        # Check all dependencies reference existing tasks
        for task in self.tasks:
            for dep in task.dependencies:
                if dep not in task_ids:
                    errors.append(
                        f"Task {task.task_id} depends on non-existent task {dep}"
                    )

            # Validate role
            valid_roles = {"worker", "foreman", "reviewer"}
            if task.role not in valid_roles:
                errors.append(
                    f"Task {task.task_id} has invalid role '{task.role}'. "
                    f"Must be one of: {valid_roles}"
                )

            # Validate verification type if present
            if task.verification:
                ver_type = task.verification.get("type")
                valid_types = {"build", "test", "lint", "manual", "integration"}
                if ver_type and ver_type not in valid_types:
                    errors.append(
                        f"Task {task.task_id} has invalid verification type '{ver_type}'. "
                        f"Must be one of: {valid_types}"
                    )

        # Check for cycles using DFS
        def has_cycle() -> bool:
            visited = set()
            rec_stack = set()

            def visit(task_id: str) -> bool:
                if task_id in rec_stack:
                    return True  # Cycle detected
                if task_id in visited:
                    return False

                visited.add(task_id)
                rec_stack.add(task_id)

                # Get task
                task = next((t for t in self.tasks if t.task_id == task_id), None)
                if task:
                    for dep in task.dependencies:
                        if visit(dep):
                            return True

                rec_stack.remove(task_id)
                return False

            for task in self.tasks:
                if task.task_id not in visited:
                    if visit(task.task_id):
                        return True
            return False

        if has_cycle():
            errors.append("DAG validation failed: task graph contains cycles")

        return (len(errors) == 0, errors)

    def get_execution_order(self) -> list[str]:
        """
        VF-091: Return task_ids in valid topological sort order.

        Uses Kahn's algorithm for deterministic ordering.
        Tasks with equal priority are sorted alphabetically by task_id.

        Returns:
            List of task_ids in execution order

        Raises:
            ValueError: If graph contains cycles
        """
        # Build in-degree map and adjacency list
        in_degree = {task.task_id: 0 for task in self.tasks}
        adj_list = {task.task_id: [] for task in self.tasks}

        for task in self.tasks:
            for dep in task.dependencies:
                adj_list[dep].append(task.task_id)
                in_degree[task.task_id] += 1

        # Queue nodes with no dependencies (in-degree 0)
        queue = [tid for tid, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            # Sort for deterministic ordering
            queue.sort()
            current = queue.pop(0)
            result.append(current)

            # Reduce in-degree for neighbors
            for neighbor in adj_list[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # If result doesn't contain all tasks, there's a cycle
        if len(result) != len(self.tasks):
            raise ValueError(
                "Cannot compute execution order: graph contains cycles"
            )

        return result

    def get_ready_tasks(
        self,
        completed: set[str],
        running: set[str],
        failed: set[str],
    ) -> list[Task]:
        """
        VF-091: Return tasks that are ready to run.

        A task is ready if:
        - All dependencies are completed
        - Task is not already running
        - Task is not already completed
        - Task has not failed

        Args:
            completed: Set of task_ids that are completed
            running: Set of task_ids currently running
            failed: Set of task_ids that have failed

        Returns:
            List of Task objects ready to run (in execution order)
        """
        ready = []
        for task in self.tasks:
            # Skip if already in a terminal or active state
            if (
                task.task_id in completed
                or task.task_id in running
                or task.task_id in failed
            ):
                continue

            # Check if all dependencies are completed
            deps_satisfied = all(dep in completed for dep in task.dependencies)
            if deps_satisfied:
                ready.append(task)

        # Return in execution order
        if not ready:
            return []

        # Sort by execution order
        try:
            execution_order = self.get_execution_order()
            ready.sort(key=lambda t: execution_order.index(t.task_id))
        except ValueError:
            # If we can't get execution order, just return alphabetically
            ready.sort(key=lambda t: t.task_id)

        return ready


@dataclass
class RunSummary:
    """Summary of completed build execution (output of VF-075)."""

    session_id: str
    status: str  # "success", "partial", "failed"
    summary: str
    files_generated: list[str]
    verification_results: dict[str, str]
    how_to_run: list[str]
    limitations: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (excluding session_id for serialization)."""
        return {
            "status": self.status,
            "summary": self.summary,
            "files_generated": self.files_generated,
            "verification_results": self.verification_results,
            "how_to_run": self.how_to_run,
            "limitations": self.limitations,
        }

    @classmethod
    def from_dict(cls, session_id: str, data: dict[str, Any]) -> "RunSummary":
        """Create RunSummary from dictionary."""
        return cls(
            session_id=session_id,
            status=data["status"],
            summary=data["summary"],
            files_generated=data["files_generated"],
            verification_results=data["verification_results"],
            how_to_run=data["how_to_run"],
            limitations=data["limitations"],
        )


# VF-191: Agent workflow models (for control panel simulation mode)


class AgentRole(str, Enum):
    """Enumeration of valid agent roles."""

    ORCHESTRATOR = "orchestrator"
    FOREMAN = "foreman"
    WORKER = "worker"
    REVIEWER = "reviewer"
    FIXER = "fixer"


class AgentConfig(BaseModel):
    """Configuration for a single agent instance (VF-191).

    Used by the control panel simulation mode to configure agents
    before running custom multi-agent workflows.
    """

    agent_id: str = Field(..., description="Unique identifier for this agent")
    role: Optional[AgentRole] = Field(None, description="Assigned role")
    model_id: Optional[str] = Field(
        None, description="Model to use (e.g., 'gpt-4', 'claude-3')"
    )
    display_name: Optional[str] = Field(None, description="Human-readable name")

    @field_validator("agent_id")
    @classmethod
    def validate_agent_id(cls, v: str) -> str:
        """Validate that agent_id is non-empty."""
        if not v or not v.strip():
            raise ValueError("agent_id cannot be empty")
        return v.strip()


class AgentFlowEdge(BaseModel):
    """Edge in agent communication graph (VF-191)."""

    from_agent: str = Field(..., description="Source agent ID")
    to_agent: str = Field(..., description="Target agent ID")
    label: Optional[str] = Field(None, description="Edge label/description")
    bidirectional: bool = Field(
        False, description="Whether the edge allows traffic both directions"
    )


class AgentFlowGraph(BaseModel):
    """Graph representing agent-to-agent communication topology (VF-191).

    Used by the control panel simulation mode to define which agents
    can communicate with each other. Messages are only allowed along
    configured edges (graph-gated messaging).
    """

    edges: list[AgentFlowEdge] = Field(default_factory=list)

    def validate_dag(self, agent_ids: list[str]) -> tuple[bool, Optional[str]]:
        """Validate graph references valid agents.

        Args:
            agent_ids: List of valid agent IDs to check against

        Returns:
            (is_valid, error_message) tuple
        """
        # Check all referenced agents exist
        unknown_sources = sorted(
            {
                edge.from_agent
                for edge in self.edges
                if edge.from_agent not in agent_ids
            }
        )
        unknown_targets = sorted(
            {
                edge.to_agent
                for edge in self.edges
                if edge.to_agent not in agent_ids
            }
        )

        if unknown_sources or unknown_targets:
            messages = []
            if unknown_sources:
                messages.append(
                    f"Unknown source agent(s): {', '.join(unknown_sources)}"
                )
            if unknown_targets:
                messages.append(
                    f"Unknown target agent(s): {', '.join(unknown_targets)}"
                )
            return False, "; ".join(messages)

        return True, None

    def get_predecessors(self, agent_id: str) -> list[str]:
        """Get agents that feed into this agent.

        Args:
            agent_id: Target agent ID

        Returns:
            List of agent IDs that have edges pointing to this agent
        """
        predecessors = [e.from_agent for e in self.edges if e.to_agent == agent_id]
        predecessors.extend(
            e.to_agent
            for e in self.edges
            if e.bidirectional and e.from_agent == agent_id
        )
        return predecessors

    def get_successors(self, agent_id: str) -> list[str]:
        """Get agents this agent feeds into.

        Args:
            agent_id: Source agent ID

        Returns:
            List of agent IDs that this agent points to
        """
        successors = [e.to_agent for e in self.edges if e.from_agent == agent_id]
        successors.extend(
            e.from_agent
            for e in self.edges
            if e.bidirectional and e.to_agent == agent_id
        )
        return successors


class SimulationConfig(BaseModel):
    """Configuration for tick-based simulation mode (VF-191)."""

    simulation_mode: str = Field(
        "manual", description="Simulation mode: 'manual' or 'auto'"
    )
    auto_delay_ms: Optional[int] = Field(
        None, description="Auto-run delay between ticks (milliseconds)"
    )
    tick_budget: Optional[int] = Field(
        None, description="Maximum events/messages per tick (safety limit)"
    )


class TickState(BaseModel):
    """Current state of tick-based simulation (VF-191)."""

    tick_index: int = Field(0, description="Current tick number (starts at 0)")
    tick_status: str = Field(
        "idle",
        description="Tick status: 'idle' | 'running' | 'blocked' | 'completed'",
    )
    pending_work_summary: Optional[str] = Field(
        None, description="Summary of pending work for next tick"
    )
