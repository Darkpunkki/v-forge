"""
Tests for TaskMaster scheduler.

Tests VF-092, VF-093, VF-094 functionality.
"""

import pytest
from orchestration.models import Task, TaskGraph
from runtime.task_master import TaskMaster, TaskStatus, TaskExecution


class TestTaskMasterEnqueue:
    """Test VF-092: TaskMaster.enqueue()."""

    def test_enqueue_accepts_valid_graph(self):
        """Test that enqueue accepts a valid TaskGraph."""
        tasks = [
            Task("task_001", "Task 1", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_002", "Task 2", "worker", ["task_001"], {}, ["out"], {"type": "test"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster()

        master.enqueue(graph)

        assert master.task_graph is graph
        assert len(master.executions) == 2
        assert all(isinstance(ex, TaskExecution) for ex in master.executions.values())

    def test_enqueue_rejects_invalid_graph(self):
        """Test that enqueue rejects invalid TaskGraph."""
        tasks = [
            Task("task_001", "Task 1", "worker", ["task_999"], {}, ["out"], {"type": "build"}, {}),  # Invalid dep
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster()

        with pytest.raises(ValueError) as exc_info:
            master.enqueue(graph)

        assert "Invalid TaskGraph" in str(exc_info.value)

    def test_enqueue_initializes_root_tasks_as_ready(self):
        """Test that tasks with no dependencies start as READY."""
        tasks = [
            Task("task_001", "Root 1", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_002", "Root 2", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_003", "Dependent", "worker", ["task_001"], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster()

        master.enqueue(graph)

        assert master.executions["task_001"].status == TaskStatus.READY
        assert master.executions["task_002"].status == TaskStatus.READY
        assert master.executions["task_003"].status == TaskStatus.PENDING

    def test_enqueue_computes_execution_order(self):
        """Test that enqueue computes topological execution order."""
        tasks = [
            Task("task_003", "Task 3", "worker", ["task_002"], {}, ["out"], {"type": "build"}, {}),
            Task("task_001", "Task 1", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_002", "Task 2", "worker", ["task_001"], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster()

        master.enqueue(graph)

        assert master.execution_order == ["task_001", "task_002", "task_003"]

    def test_enqueue_sets_max_retries(self):
        """Test that enqueue sets max_retries from constructor."""
        tasks = [
            Task("task_001", "Task 1", "worker", [], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster(max_retries=5)

        master.enqueue(graph)

        assert master.executions["task_001"].max_retries == 5


class TestTaskMasterScheduleNext:
    """Test VF-093: TaskMaster.scheduleNext()."""

    def test_schedule_next_returns_ready_task(self):
        """Test that scheduleNext returns first ready task."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_002", "Dependent", "worker", ["task_001"], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster()
        master.enqueue(graph)

        next_task = master.scheduleNext()

        assert next_task is not None
        assert next_task.task_id == "task_001"

    def test_schedule_next_marks_task_as_running(self):
        """Test that scheduleNext marks selected task as RUNNING."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster()
        master.enqueue(graph)

        master.scheduleNext()

        assert master.executions["task_001"].status == TaskStatus.RUNNING

    def test_schedule_next_increments_attempts(self):
        """Test that scheduleNext increments attempt counter."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster()
        master.enqueue(graph)

        master.scheduleNext()

        assert master.executions["task_001"].attempts == 1

    def test_schedule_next_sets_started_at(self):
        """Test that scheduleNext sets started_at timestamp."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster()
        master.enqueue(graph)

        master.scheduleNext()

        assert master.executions["task_001"].started_at is not None

    def test_schedule_next_returns_none_when_no_ready_tasks(self):
        """Test that scheduleNext returns None when no tasks are ready."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_002", "Dependent", "worker", ["task_001"], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster()
        master.enqueue(graph)

        # Schedule task_001
        master.scheduleNext()

        # Now no tasks are ready (task_001 is RUNNING, task_002 is PENDING)
        next_task = master.scheduleNext()

        assert next_task is None

    def test_schedule_next_respects_execution_order(self):
        """Test that scheduleNext picks tasks in topological order."""
        tasks = [
            Task("task_003", "Root C", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_001", "Root A", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_002", "Root B", "worker", [], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster()
        master.enqueue(graph)

        # All 3 are ready, but should pick in execution order (alphabetically)
        task1 = master.scheduleNext()
        master.markDone(task1.task_id)

        task2 = master.scheduleNext()
        master.markDone(task2.task_id)

        task3 = master.scheduleNext()

        assert task1.task_id == "task_001"
        assert task2.task_id == "task_002"
        assert task3.task_id == "task_003"


class TestTaskMasterMarkDone:
    """Test VF-094: TaskMaster.markDone()."""

    def test_mark_done_sets_status_to_done(self):
        """Test that markDone sets task status to DONE."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster()
        master.enqueue(graph)
        master.scheduleNext()

        master.markDone("task_001")

        assert master.executions["task_001"].status == TaskStatus.DONE

    def test_mark_done_sets_completed_at(self):
        """Test that markDone sets completed_at timestamp."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster()
        master.enqueue(graph)
        master.scheduleNext()

        master.markDone("task_001")

        assert master.executions["task_001"].completed_at is not None

    def test_mark_done_stores_result(self):
        """Test that markDone stores optional result data."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster()
        master.enqueue(graph)
        master.scheduleNext()

        result = {"files": ["main.py"], "output": "Build succeeded"}
        master.markDone("task_001", result=result)

        assert master.executions["task_001"].result == result

    def test_mark_done_makes_dependent_tasks_ready(self):
        """Test that markDone triggers dependent tasks to become READY."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_002", "Dependent", "worker", ["task_001"], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster()
        master.enqueue(graph)

        master.scheduleNext()  # task_001 RUNNING
        master.markDone("task_001")

        assert master.executions["task_002"].status == TaskStatus.READY

    def test_mark_done_raises_for_unknown_task(self):
        """Test that markDone raises ValueError for unknown task_id."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster()
        master.enqueue(graph)

        with pytest.raises(ValueError) as exc_info:
            master.markDone("task_999")

        assert "Unknown task_id" in str(exc_info.value)


class TestTaskMasterMarkFailed:
    """Test VF-094: TaskMaster.markFailed() with retry logic."""

    def test_mark_failed_retries_when_attempts_below_max(self):
        """Test that markFailed retries when attempts < max_retries."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster(max_retries=2)
        master.enqueue(graph)
        master.scheduleNext()  # attempts = 1

        should_retry = master.markFailed("task_001", "Build failed")

        assert should_retry is True
        assert master.executions["task_001"].status == TaskStatus.READY
        assert master.executions["task_001"].attempts == 1

    def test_mark_failed_sets_error_message(self):
        """Test that markFailed stores error message."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster()
        master.enqueue(graph)
        master.scheduleNext()

        master.markFailed("task_001", "Compilation error on line 42")

        assert master.executions["task_001"].error_message == "Compilation error on line 42"

    def test_mark_failed_stops_retrying_at_max_attempts(self):
        """Test that markFailed marks task FAILED after max_retries."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster(max_retries=2)
        master.enqueue(graph)

        # Attempt 1
        master.scheduleNext()
        master.markFailed("task_001", "Error 1")

        # Attempt 2
        master.scheduleNext()
        should_retry = master.markFailed("task_001", "Error 2")

        assert should_retry is False
        assert master.executions["task_001"].status == TaskStatus.FAILED
        assert master.executions["task_001"].attempts == 2

    def test_mark_failed_skips_downstream_tasks(self):
        """Test that markFailed marks dependent tasks as SKIPPED."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_002", "Dependent", "worker", ["task_001"], {}, ["out"], {"type": "build"}, {}),
            Task("task_003", "Transitive", "worker", ["task_002"], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster(max_retries=1)
        master.enqueue(graph)

        # Fail task_001 (exceeds retries)
        master.scheduleNext()
        master.markFailed("task_001", "Fatal error")

        # Both downstream tasks should be SKIPPED
        assert master.executions["task_002"].status == TaskStatus.SKIPPED
        assert master.executions["task_003"].status == TaskStatus.SKIPPED

    def test_mark_failed_sets_completed_at_on_final_failure(self):
        """Test that markFailed sets completed_at when max retries exceeded."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster(max_retries=1)
        master.enqueue(graph)

        master.scheduleNext()
        master.markFailed("task_001", "Error")

        assert master.executions["task_001"].completed_at is not None

    def test_force_retry_resets_task_and_downstream(self):
        """Test that forceRetry resets FAILED task and unskips downstream tasks."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task(
                "task_002",
                "Dependent",
                "worker",
                ["task_001"],
                {},
                ["out"],
                {"type": "build"},
                {},
            ),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster(max_retries=1)
        master.enqueue(graph)

        master.scheduleNext()
        master.markFailed("task_001", "Failure")

        assert master.executions["task_001"].status == TaskStatus.FAILED
        assert master.executions["task_002"].status == TaskStatus.SKIPPED

        master.forceRetry("task_001", reset_attempts=True)

        assert master.executions["task_001"].status == TaskStatus.READY
        assert master.executions["task_001"].attempts == 0
        assert master.executions["task_001"].error_message is None
        assert master.executions["task_002"].status == TaskStatus.PENDING

    def test_mark_failed_raises_for_unknown_task(self):
        """Test that markFailed raises ValueError for unknown task_id."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster()
        master.enqueue(graph)

        with pytest.raises(ValueError) as exc_info:
            master.markFailed("task_999", "Error")

        assert "Unknown task_id" in str(exc_info.value)


class TestTaskMasterStatus:
    """Test TaskMaster.get_status()."""

    def test_get_status_before_enqueue(self):
        """Test get_status before enqueuing a graph."""
        master = TaskMaster()

        status = master.get_status()

        assert status["status"] == "not_initialized"

    def test_get_status_after_enqueue(self):
        """Test get_status after enqueuing tasks."""
        tasks = [
            Task("task_001", "Root 1", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_002", "Root 2", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_003", "Dependent", "worker", ["task_001"], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster()
        master.enqueue(graph)

        status = master.get_status()

        assert status["total_tasks"] == 3
        assert status["ready"] == 2  # task_001, task_002
        assert status["pending"] == 1  # task_003
        assert status["completed"] == 0
        assert status["is_complete"] is False
        assert status["has_failures"] is False

    def test_get_status_tracks_running_tasks(self):
        """Test get_status counts RUNNING tasks."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster()
        master.enqueue(graph)

        master.scheduleNext()
        status = master.get_status()

        assert status["running"] == 1
        assert status["ready"] == 0

    def test_get_status_tracks_completion(self):
        """Test get_status tracks completed tasks."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_002", "Dependent", "worker", ["task_001"], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster()
        master.enqueue(graph)

        master.scheduleNext()
        master.markDone("task_001")
        status = master.get_status()

        assert status["completed"] == 1
        assert status["is_complete"] is False

        master.scheduleNext()
        master.markDone("task_002")
        status = master.get_status()

        assert status["completed"] == 2
        assert status["is_complete"] is True

    def test_get_status_tracks_failures(self):
        """Test get_status tracks failed tasks."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster(max_retries=1)
        master.enqueue(graph)

        master.scheduleNext()
        master.markFailed("task_001", "Error")

        status = master.get_status()

        assert status["failed"] == 1
        assert status["has_failures"] is True

    def test_get_status_counts_skipped_as_completed(self):
        """Test get_status counts SKIPPED tasks as completed."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_002", "Dependent", "worker", ["task_001"], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster(max_retries=1)
        master.enqueue(graph)

        master.scheduleNext()
        master.markFailed("task_001", "Error")

        status = master.get_status()

        assert status["skipped"] == 1
        assert status["completed"] == 2  # 1 failed + 1 skipped
        assert status["is_complete"] is True

    def test_get_task_status(self):
        """Test get_task_status returns execution state for specific task."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster()
        master.enqueue(graph)

        exec_state = master.get_task_status("task_001")

        assert exec_state is not None
        assert exec_state.task_id == "task_001"
        assert exec_state.status == TaskStatus.READY


class TestTaskMasterIntegration:
    """Integration tests for complete TaskMaster workflows."""

    def test_complete_execution_flow(self):
        """Test complete execution flow from enqueue to completion."""
        tasks = [
            Task("task_001", "Setup", "worker", [], {}, ["setup.py"], {"type": "build"}, {}),
            Task("task_002", "Build", "worker", ["task_001"], {}, ["app.py"], {"type": "build"}, {}),
            Task("task_003", "Test", "worker", ["task_002"], {}, ["test_results"], {"type": "test"}, {}),
            Task("task_004", "Deploy", "worker", ["task_003"], {}, ["deployed"], {"type": "manual"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster()

        # Enqueue
        master.enqueue(graph)
        assert master.get_status()["total_tasks"] == 4

        # Execute all tasks
        while True:
            task = master.scheduleNext()
            if task is None:
                break
            master.markDone(task.task_id, result={"status": "success"})

        # Verify completion
        status = master.get_status()
        assert status["is_complete"] is True
        assert status["completed"] == 4
        assert status["has_failures"] is False

    def test_execution_with_retries(self):
        """Test execution flow with task retries."""
        tasks = [
            Task("task_001", "Flaky task", "worker", [], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)
        master = TaskMaster(max_retries=3)

        master.enqueue(graph)

        # Fail twice, then succeed
        task1 = master.scheduleNext()
        master.markFailed(task1.task_id, "Temporary error 1")

        task2 = master.scheduleNext()
        master.markFailed(task2.task_id, "Temporary error 2")

        task3 = master.scheduleNext()
        master.markDone(task3.task_id)

        # Verify completion with retries
        assert master.executions["task_001"].attempts == 3
        assert master.executions["task_001"].status == TaskStatus.DONE
        assert master.get_status()["is_complete"] is True
