# WP-0016 — TaskGraph foundations and task scheduling

## VF Tasks Included
- VF-090: TaskGraph types + parser + schema validation
- VF-091: Validate DAG (no cycles) + dependency resolver
- VF-092: TaskMaster.enqueue(TaskGraph)
- VF-093: TaskMaster.scheduleNext() (ready tasks only)
- VF-094: TaskMaster.markDone/markFailed + retry counters

## Goal
Implement TaskGraph validation, DAG dependency resolution, and TaskMaster scheduling to enable deterministic task execution. TaskMaster will coordinate execution of tasks from an orchestrator-generated TaskGraph.

## Dependencies
- WP-0015 ✓ (Orchestrator generates TaskGraphs with basic DAG validation)

## Current State Analysis

From WP-0015, we have:
- ✓ orchestration/models.py with TaskGraph, Task dataclasses
- ✓ TaskGraph.validate_dag() with cycle detection
- ✓ TaskGraph.from_dict() and to_dict() serialization
- ✓ orchestration/schemas.py with TASKGRAPH_SCHEMA for JSON validation
- ✓ Orchestrator.createTaskGraph() that produces validated TaskGraphs

**Gaps identified:**
1. **No topological sort / dependency resolution** - Need to compute ready tasks
2. **No TaskMaster** - Need scheduler to coordinate task execution
3. **No task status tracking** - Need PENDING/READY/RUNNING/DONE/FAILED states
4. **No retry counters** - Need failure tracking and retry limits
5. **No task selection logic** - Need to pick next runnable task from DAG

## Execution Plan

### 1. Extend TaskGraph with dependency resolution (VF-090, VF-091)

**VF-090: Enhanced validation**
- TaskGraph already has basic validation (validate_dag)
- Extend to check:
  - All task_ids are unique ✓ (already implemented)
  - All dependencies reference existing tasks ✓ (already implemented)
  - No cycles ✓ (already implemented via DFS)
  - Role validation (must be "worker", "foreman", or "reviewer")
  - Verification type validation
- Add comprehensive error messages

**VF-091: Topological sort for dependency resolution**
Add to TaskGraph:
```python
def get_ready_tasks(
    self,
    completed: set[str],
    running: set[str],
    failed: set[str]
) -> list[Task]:
    """
    Return tasks that are ready to run.

    A task is ready if:
    - All dependencies are completed
    - Task is not already running
    - Task is not already completed
    - Task has not failed (unless retrying)

    Returns tasks in topological order (dependency-aware).
    """
    ready = []
    for task in self.tasks:
        if task.task_id in completed or task.task_id in running or task.task_id in failed:
            continue

        # Check if all dependencies are completed
        deps_satisfied = all(dep in completed for dep in task.dependencies)
        if deps_satisfied:
            ready.append(task)

    return ready

def get_execution_order(self) -> list[str]:
    """
    Return task_ids in valid topological sort order.
    Uses Kahn's algorithm for deterministic ordering.
    """
    # Build in-degree map
    in_degree = {task.task_id: 0 for task in self.tasks}
    adj_list = {task.task_id: [] for task in self.tasks}

    for task in self.tasks:
        for dep in task.dependencies:
            adj_list[dep].append(task.task_id)
            in_degree[task.task_id] += 1

    # Queue nodes with no dependencies
    queue = [tid for tid, degree in in_degree.items() if degree == 0]
    result = []

    while queue:
        # Sort for deterministic ordering
        queue.sort()
        current = queue.pop(0)
        result.append(current)

        for neighbor in adj_list[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # If result doesn't contain all tasks, there's a cycle
    if len(result) != len(self.tasks):
        raise ValueError("Cannot compute execution order: graph contains cycles")

    return result
```

### 2. Implement TaskMaster (VF-092, VF-093, VF-094)

Create `runtime/task_master.py`:

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime

from orchestration.models import TaskGraph, Task


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "PENDING"      # Not yet ready (dependencies incomplete)
    READY = "READY"          # Dependencies satisfied, ready to run
    RUNNING = "RUNNING"      # Currently executing
    DONE = "DONE"            # Completed successfully
    FAILED = "FAILED"        # Failed (after retries)
    SKIPPED = "SKIPPED"      # Skipped due to dependency failure


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
    - Load and validate TaskGraph
    - Track task execution state (pending/ready/running/done/failed)
    - Select next runnable task based on dependencies
    - Handle retries and failure escalation

    VF-092: enqueue(TaskGraph)
    VF-093: scheduleNext() -> ready task
    VF-094: markDone/markFailed + retry counters
    """

    def __init__(self, max_retries: int = 2):
        """Initialize TaskMaster."""
        self.task_graph: Optional[TaskGraph] = None
        self.executions: dict[str, TaskExecution] = {}
        self.max_retries = max_retries
        self.execution_order: list[str] = []

    def enqueue(self, task_graph: TaskGraph) -> None:
        """
        VF-092: Load TaskGraph and initialize task statuses.

        Validates the graph and sets up execution tracking.
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
                max_retries=self.max_retries
            )

        # Mark tasks with no dependencies as READY
        self._update_ready_tasks()

    def scheduleNext(self) -> Optional[Task]:
        """
        VF-093: Select next ready task based on dependencies.

        Returns None if no tasks are ready or all tasks complete.
        """
        if not self.task_graph:
            return None

        # Get ready task_ids
        ready_task_ids = [
            tid for tid, exec_state in self.executions.items()
            if exec_state.status == TaskStatus.READY
        ]

        if not ready_task_ids:
            return None

        # Pick first ready task in execution order
        for task_id in self.execution_order:
            if task_id in ready_task_ids:
                # Find task object
                task = next((t for t in self.task_graph.tasks if t.task_id == task_id), None)
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
        """
        if task_id not in self.executions:
            raise ValueError(f"Unknown task_id: {task_id}")

        exec_state = self.executions[task_id]
        exec_state.status = TaskStatus.DONE
        exec_state.completed_at = datetime.utcnow()
        exec_state.result = result

        # Update ready tasks (downstream dependencies may now be satisfied)
        self._update_ready_tasks()

    def markFailed(self, task_id: str, error_message: str) -> bool:
        """
        VF-094: Mark task as failed and handle retries.

        Returns:
            True if task should be retried, False if max retries exceeded.
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
        """Get overall execution status."""
        if not self.task_graph:
            return {"status": "not_initialized"}

        status_counts = {status: 0 for status in TaskStatus}
        for exec_state in self.executions.values():
            status_counts[exec_state.status] += 1

        total = len(self.executions)
        completed = status_counts[TaskStatus.DONE] + status_counts[TaskStatus.SKIPPED]

        return {
            "total_tasks": total,
            "completed": completed,
            "running": status_counts[TaskStatus.RUNNING],
            "ready": status_counts[TaskStatus.READY],
            "pending": status_counts[TaskStatus.PENDING],
            "failed": status_counts[TaskStatus.FAILED],
            "skipped": status_counts[TaskStatus.SKIPPED],
            "is_complete": completed == total,
            "has_failures": status_counts[TaskStatus.FAILED] > 0
        }

    def _update_ready_tasks(self) -> None:
        """Update PENDING tasks to READY if dependencies satisfied."""
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
        """Skip tasks that depend on a failed task."""
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
```

### 3. Write Comprehensive Tests

**test_taskgraph.py:**
- Test TaskGraph.get_ready_tasks() with various dependency scenarios
- Test TaskGraph.get_execution_order() topological sort
- Test execution order is deterministic
- Test handling of empty graph
- Test complex dependency chains

**test_taskmaster.py:**
- Test TaskMaster.enqueue() validation
- Test TaskMaster.scheduleNext() returns tasks in correct order
- Test TaskMaster.markDone() updates downstream ready tasks
- Test TaskMaster.markFailed() retry logic
- Test retry counter limits
- Test downstream task skipping on failure
- Test get_status() summary
- Test complete execution flow

## Done Means

- [x] VF-090: TaskGraph validation enhanced
  - **File:** `orchestration/models.py:110` (TaskGraph.validate_dag extended)
  - **Features:** Enhanced validation for duplicate IDs, missing dependencies, cycles, invalid roles, invalid verification types
  - **Tests:** `apps/api/tests/test_taskgraph.py` (8 validation tests)
  - **Verify:** `cd apps/api && pytest tests/test_taskgraph.py::TestTaskGraphValidation -v` (8 passed)

- [x] VF-091: DAG dependency resolver
  - **File:** `orchestration/models.py:192` (get_execution_order, get_ready_tasks methods)
  - **Features:** Topological sort using Kahn's algorithm with deterministic ordering, ready task selection based on dependencies
  - **Tests:** `apps/api/tests/test_taskgraph.py` (11 dependency resolution tests)
  - **Verify:** `cd apps/api && pytest tests/test_taskgraph.py::TestTaskGraphDependencyResolution -v` (11 passed)

- [x] VF-092: TaskMaster.enqueue()
  - **File:** `runtime/task_master.py:64` (TaskMaster class with enqueue method)
  - **Features:** Load TaskGraph, validate DAG, compute execution order, initialize task execution tracking, mark root tasks as READY
  - **Tests:** `apps/api/tests/test_taskmaster.py` (5 enqueue tests)
  - **Verify:** `cd apps/api && pytest tests/test_taskmaster.py::TestTaskMasterEnqueue -v` (5 passed)

- [x] VF-093: TaskMaster.scheduleNext()
  - **File:** `runtime/task_master.py:99` (scheduleNext method)
  - **Features:** Select next ready task in topological order, mark as RUNNING, increment attempt counter, set timestamps
  - **Tests:** `apps/api/tests/test_taskmaster.py` (6 scheduling tests)
  - **Verify:** `cd apps/api && pytest tests/test_taskmaster.py::TestTaskMasterScheduleNext -v` (6 passed)

- [x] VF-094: TaskMaster.markDone/markFailed
  - **File:** `runtime/task_master.py:142` (markDone, markFailed methods)
  - **Features:** Retry counters (configurable max_retries), failure tracking with error messages, downstream task skipping on failure, completion timestamps, result storage
  - **Tests:** `apps/api/tests/test_taskmaster.py` (11 completion/failure tests + 2 integration tests)
  - **Verify:** `cd apps/api && pytest tests/test_taskmaster.py::TestTaskMasterMarkDone -v` (5 passed), `cd apps/api && pytest tests/test_taskmaster.py::TestTaskMasterMarkFailed -v` (6 passed)

**Total tests:** 355 (was 304, added 50 new tests + 1 skipped)
**All tests passing:** ✓ (354 passed, 1 skipped from WP-0015)
**New test files:**
- `apps/api/tests/test_taskgraph.py` (19 tests for VF-090, VF-091)
- `apps/api/tests/test_taskmaster.py` (31 tests for VF-092, VF-093, VF-094)

## Verification Commands
```bash
cd apps/api && pytest tests/test_taskgraph.py -v
cd apps/api && pytest tests/test_taskmaster.py -v
cd apps/api && pytest -v
```

## Notes
- TaskGraph already has basic DAG validation from WP-0015
- TaskMaster will be used by SessionCoordinator to execute tasks
- Retry logic is configurable (default 2 retries)
- Failed tasks trigger downstream skipping to avoid wasted work
- Topological sort ensures deterministic task ordering
