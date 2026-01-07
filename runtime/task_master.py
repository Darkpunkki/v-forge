"""
TaskMaster: Task scheduler and coordinator.

VF-092: TaskMaster.enqueue(TaskGraph)
VF-093: TaskMaster.scheduleNext() -> ready task
VF-094: TaskMaster.markDone/markFailed + retry counters
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from orchestration.models import Task, TaskGraph


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "PENDING"  # Not yet ready (dependencies incomplete)
    READY = "READY"  # Dependencies satisfied, ready to run
    RUNNING = "RUNNING"  # Currently executing
    DONE = "DONE"  # Completed successfully
    FAILED = "FAILED"  # Failed (after retries)
    SKIPPED = "SKIPPED"  # Skipped due to dependency failure


@dataclass
class TaskExecution:
    """Tracks execution state for a single task."""

    task_id: str
    status: TaskStatus
    attempts: int = 0
    max_retries: int = 2
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[dict] = None


class TaskMaster:
    """
    Task scheduler and coordinator.

    Responsibilities:
    - Load and validate TaskGraph (VF-092)
    - Track task execution state (pending/ready/running/done/failed)
    - Select next runnable task based on dependencies (VF-093)
    - Handle retries and failure escalation (VF-094)
    """

    def __init__(self, max_retries: int = 2):
        """
        Initialize TaskMaster.

        Args:
            max_retries: Maximum number of retry attempts per task
        """
        self.task_graph: Optional[TaskGraph] = None
        self.executions: dict[str, TaskExecution] = {}
        self.max_retries = max_retries
        self.execution_order: list[str] = []

    def enqueue(self, task_graph: TaskGraph) -> None:
        """
        VF-092: Load TaskGraph and initialize task statuses.

        Validates the graph and sets up execution tracking.

        Args:
            task_graph: TaskGraph to execute

        Raises:
            ValueError: If TaskGraph validation fails
        """
        # Validate DAG
        is_valid, errors = task_graph.validate_dag()
        if not is_valid:
            raise ValueError(f"Invalid TaskGraph: {errors}")

        # Store graph
        self.task_graph = task_graph

        # Compute execution order
        self.execution_order = task_graph.get_execution_order()

        # Initialize execution tracking
        self.executions = {}
        for task in task_graph.tasks:
            self.executions[task.task_id] = TaskExecution(
                task_id=task.task_id,
                status=TaskStatus.PENDING,
                max_retries=self.max_retries,
            )

        # Mark tasks with no dependencies as READY
        self._update_ready_tasks()

    def scheduleNext(self) -> Optional[Task]:
        """
        VF-093: Select next ready task based on dependencies.

        Returns the first task in execution order that is READY.
        Marks selected task as RUNNING.

        Returns:
            Next Task to execute, or None if no tasks are ready
        """
        if not self.task_graph:
            return None

        # Get ready task_ids
        ready_task_ids = [
            tid
            for tid, exec_state in self.executions.items()
            if exec_state.status == TaskStatus.READY
        ]

        if not ready_task_ids:
            return None

        # Pick first ready task in execution order
        for task_id in self.execution_order:
            if task_id in ready_task_ids:
                # Find task object
                task = next(
                    (t for t in self.task_graph.tasks if t.task_id == task_id), None
                )
                if task:
                    # Mark as RUNNING
                    self.executions[task_id].status = TaskStatus.RUNNING
                    self.executions[task_id].started_at = datetime.utcnow()
                    self.executions[task_id].attempts += 1
                    return task

        return None

    def markDone(self, task_id: str, result: Optional[dict] = None) -> None:
        """
        VF-094: Mark task as successfully completed.

        Updates task status to DONE and triggers downstream dependency updates.

        Args:
            task_id: ID of completed task
            result: Optional result data from task execution

        Raises:
            ValueError: If task_id is unknown
        """
        if task_id not in self.executions:
            raise ValueError(f"Unknown task_id: {task_id}")

        exec_state = self.executions[task_id]
        exec_state.status = TaskStatus.DONE
        exec_state.completed_at = datetime.utcnow()
        exec_state.result = result

        # Update ready tasks (downstream dependencies may now be satisfied)
        self._update_ready_tasks()

    def markNeedsClarification(self, task_id: str) -> None:
        """
        Mark task as awaiting clarification without counting as a failure.

        Resets task to READY so it can be re-run after clarification is provided.

        Args:
            task_id: ID of task awaiting clarification

        Raises:
            ValueError: If task_id is unknown
        """
        if task_id not in self.executions:
            raise ValueError(f"Unknown task_id: {task_id}")

        exec_state = self.executions[task_id]
        exec_state.status = TaskStatus.READY
        exec_state.started_at = None
        if exec_state.attempts > 0:
            exec_state.attempts -= 1

    def markFailed(self, task_id: str, error_message: str) -> bool:
        """
        VF-094: Mark task as failed and handle retries.

        If retries are available, resets task to READY.
        If max retries exceeded, marks task as FAILED and skips downstream tasks.

        Args:
            task_id: ID of failed task
            error_message: Error description

        Returns:
            True if task should be retried, False if max retries exceeded

        Raises:
            ValueError: If task_id is unknown
        """
        if task_id not in self.executions:
            raise ValueError(f"Unknown task_id: {task_id}")

        exec_state = self.executions[task_id]
        exec_state.error_message = error_message

        # Check if retries available
        if exec_state.attempts < exec_state.max_retries:
            # Reset to READY for retry
            exec_state.status = TaskStatus.READY
            return True
        else:
            # Max retries exceeded - mark FAILED
            exec_state.status = TaskStatus.FAILED
            exec_state.completed_at = datetime.utcnow()

            # Mark downstream tasks as SKIPPED
            self._skip_downstream_tasks(task_id)
            return False

    def get_status(self) -> dict:
        """
        Get overall execution status.

        Returns:
            Dictionary with execution statistics and completion status
        """
        if not self.task_graph:
            return {"status": "not_initialized"}

        status_counts = {status: 0 for status in TaskStatus}
        for exec_state in self.executions.values():
            status_counts[exec_state.status] += 1

        total = len(self.executions)
        # Completed includes DONE, FAILED, and SKIPPED (all terminal states)
        completed = (
            status_counts[TaskStatus.DONE]
            + status_counts[TaskStatus.FAILED]
            + status_counts[TaskStatus.SKIPPED]
        )

        return {
            "total_tasks": total,
            "completed": completed,
            "running": status_counts[TaskStatus.RUNNING],
            "ready": status_counts[TaskStatus.READY],
            "pending": status_counts[TaskStatus.PENDING],
            "failed": status_counts[TaskStatus.FAILED],
            "skipped": status_counts[TaskStatus.SKIPPED],
            "is_complete": completed == total,
            "has_failures": status_counts[TaskStatus.FAILED] > 0,
        }

    def get_task_status(self, task_id: str) -> Optional[TaskExecution]:
        """
        Get execution status for a specific task.

        Args:
            task_id: Task ID to query

        Returns:
            TaskExecution state or None if task not found
        """
        return self.executions.get(task_id)

    def _update_ready_tasks(self) -> None:
        """
        Update PENDING tasks to READY if dependencies satisfied.

        Called after markDone to propagate readiness downstream.
        """
        if not self.task_graph:
            return

        for task in self.task_graph.tasks:
            exec_state = self.executions[task.task_id]

            # Only update PENDING tasks
            if exec_state.status != TaskStatus.PENDING:
                continue

            # Check if all dependencies are DONE
            all_deps_done = all(
                self.executions[dep].status == TaskStatus.DONE
                for dep in task.dependencies
            )

            if all_deps_done:
                exec_state.status = TaskStatus.READY

    def _skip_downstream_tasks(self, failed_task_id: str) -> None:
        """
        Skip tasks that depend on a failed task.

        Recursively marks all dependent tasks as SKIPPED.

        Args:
            failed_task_id: ID of the failed task
        """
        if not self.task_graph:
            return

        # Find all tasks that depend on failed task (directly or transitively)
        to_skip = set()

        def mark_dependent(task_id: str):
            for task in self.task_graph.tasks:
                if task_id in task.dependencies and task.task_id not in to_skip:
                    to_skip.add(task.task_id)
                    mark_dependent(task.task_id)

        mark_dependent(failed_task_id)

        # Mark as SKIPPED
        for task_id in to_skip:
            exec_state = self.executions[task_id]
            if exec_state.status in [TaskStatus.PENDING, TaskStatus.READY]:
                exec_state.status = TaskStatus.SKIPPED
                exec_state.completed_at = datetime.utcnow()
