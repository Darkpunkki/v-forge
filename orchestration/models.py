"""Data models for orchestration layer."""

from dataclasses import dataclass, field
from typing import Any, Optional


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
        Validate that task dependencies form a valid DAG.

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
                    errors.append(f"Task {task.task_id} depends on non-existent task {dep}")

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
            errors.append("Task graph contains cycles - must be a DAG")

        return (len(errors) == 0, errors)


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
