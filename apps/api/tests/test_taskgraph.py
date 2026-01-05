"""
Tests for TaskGraph validation and dependency resolution.

Tests VF-090 and VF-091 functionality.
"""

import pytest
from orchestration.models import Task, TaskGraph


class TestTaskGraphValidation:
    """Test VF-090: TaskGraph validation."""

    def test_validate_dag_accepts_valid_graph(self):
        """Test that a valid DAG passes validation."""
        tasks = [
            Task(
                "task_001",
                "First task",
                "worker",
                [],
                {},
                ["output1"],
                {"type": "build"},
                {},
            ),
            Task(
                "task_002",
                "Second task",
                "worker",
                ["task_001"],
                {},
                ["output2"],
                {"type": "test"},
                {},
            ),
            Task(
                "task_003",
                "Third task",
                "reviewer",
                ["task_002"],
                {},
                ["output3"],
                {"type": "integration"},
                {},
            ),
        ]
        graph = TaskGraph("test-session", tasks)

        is_valid, errors = graph.validate_dag()

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_dag_detects_duplicate_task_ids(self):
        """Test that duplicate task IDs are detected."""
        tasks = [
            Task("task_001", "Task 1", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_001", "Task 2", "worker", [], {}, ["out"], {"type": "build"}, {}),  # Duplicate ID
        ]
        graph = TaskGraph("test-session", tasks)

        is_valid, errors = graph.validate_dag()

        assert is_valid is False
        assert any("Duplicate task IDs" in err for err in errors)

    def test_validate_dag_detects_nonexistent_dependency(self):
        """Test that dependencies to non-existent tasks are detected."""
        tasks = [
            Task("task_001", "Task 1", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task(
                "task_002",
                "Task 2",
                "worker",
                ["task_999"],  # Non-existent dependency
                {},
                ["out"],
                {"type": "build"},
                {},
            ),
        ]
        graph = TaskGraph("test-session", tasks)

        is_valid, errors = graph.validate_dag()

        assert is_valid is False
        assert any("non-existent task" in err for err in errors)

    def test_validate_dag_detects_cycles(self):
        """Test that cyclical dependencies are detected."""
        tasks = [
            Task(
                "task_001",
                "Task 1",
                "worker",
                ["task_003"],  # Depends on task_003
                {},
                ["out"],
                {"type": "build"},
                {},
            ),
            Task(
                "task_002",
                "Task 2",
                "worker",
                ["task_001"],
                {},
                ["out"],
                {"type": "build"},
                {},
            ),
            Task(
                "task_003",
                "Task 3",
                "worker",
                ["task_002"],  # Cycle: 1->3->2->1
                {},
                ["out"],
                {"type": "build"},
                {},
            ),
        ]
        graph = TaskGraph("test-session", tasks)

        is_valid, errors = graph.validate_dag()

        assert is_valid is False
        assert any("cycles" in err.lower() for err in errors)

    def test_validate_dag_detects_invalid_role(self):
        """Test that invalid roles are detected."""
        tasks = [
            Task(
                "task_001",
                "Task 1",
                "invalid_role",  # Invalid role
                [],
                {},
                ["out"],
                {"type": "build"},
                {},
            ),
        ]
        graph = TaskGraph("test-session", tasks)

        is_valid, errors = graph.validate_dag()

        assert is_valid is False
        assert any("invalid role" in err.lower() for err in errors)

    def test_validate_dag_detects_invalid_verification_type(self):
        """Test that invalid verification types are detected."""
        tasks = [
            Task(
                "task_001",
                "Task 1",
                "worker",
                [],
                {},
                ["out"],
                {"type": "invalid_verification"},  # Invalid verification type
                {},
            ),
        ]
        graph = TaskGraph("test-session", tasks)

        is_valid, errors = graph.validate_dag()

        assert is_valid is False
        assert any("invalid verification type" in err.lower() for err in errors)

    def test_validate_dag_accepts_all_valid_roles(self):
        """Test that all valid roles are accepted."""
        for role in ["worker", "foreman", "reviewer"]:
            tasks = [
                Task("task_001", "Task 1", role, [], {}, ["out"], {"type": "build"}, {})
            ]
            graph = TaskGraph("test-session", tasks)

            is_valid, errors = graph.validate_dag()

            assert is_valid is True, f"Role '{role}' should be valid"

    def test_validate_dag_accepts_all_valid_verification_types(self):
        """Test that all valid verification types are accepted."""
        for ver_type in ["build", "test", "lint", "manual", "integration"]:
            tasks = [
                Task(
                    "task_001",
                    "Task 1",
                    "worker",
                    [],
                    {},
                    ["out"],
                    {"type": ver_type},
                    {},
                )
            ]
            graph = TaskGraph("test-session", tasks)

            is_valid, errors = graph.validate_dag()

            assert is_valid is True, f"Verification type '{ver_type}' should be valid"


class TestTaskGraphDependencyResolution:
    """Test VF-091: DAG dependency resolution."""

    def test_get_execution_order_simple_linear(self):
        """Test execution order for simple linear dependency chain."""
        tasks = [
            Task("task_003", "Task 3", "worker", ["task_002"], {}, ["out"], {"type": "build"}, {}),
            Task("task_001", "Task 1", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_002", "Task 2", "worker", ["task_001"], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)

        execution_order = graph.get_execution_order()

        assert execution_order == ["task_001", "task_002", "task_003"]

    def test_get_execution_order_parallel_branches(self):
        """Test execution order for parallel branches."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_002", "Branch A", "worker", ["task_001"], {}, ["out"], {"type": "build"}, {}),
            Task("task_003", "Branch B", "worker", ["task_001"], {}, ["out"], {"type": "build"}, {}),
            Task("task_004", "Merge", "worker", ["task_002", "task_003"], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)

        execution_order = graph.get_execution_order()

        # Root must be first, merge must be last
        assert execution_order[0] == "task_001"
        assert execution_order[-1] == "task_004"
        # Branches can be in any order, but both must come before merge
        assert execution_order.index("task_002") < execution_order.index("task_004")
        assert execution_order.index("task_003") < execution_order.index("task_004")

    def test_get_execution_order_complex_dag(self):
        """Test execution order for complex DAG."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_002", "A", "worker", ["task_001"], {}, ["out"], {"type": "build"}, {}),
            Task("task_003", "B", "worker", ["task_001"], {}, ["out"], {"type": "build"}, {}),
            Task("task_004", "C", "worker", ["task_002"], {}, ["out"], {"type": "build"}, {}),
            Task("task_005", "D", "worker", ["task_002", "task_003"], {}, ["out"], {"type": "build"}, {}),
            Task("task_006", "E", "worker", ["task_004", "task_005"], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)

        execution_order = graph.get_execution_order()

        # Verify all dependencies are satisfied
        task_map = {t.task_id: t for t in tasks}
        for i, task_id in enumerate(execution_order):
            task = task_map[task_id]
            for dep in task.dependencies:
                dep_index = execution_order.index(dep)
                assert dep_index < i, f"{dep} must come before {task_id}"

    def test_get_execution_order_is_deterministic(self):
        """Test that execution order is deterministic (same graph returns same order)."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_002", "A", "worker", ["task_001"], {}, ["out"], {"type": "build"}, {}),
            Task("task_003", "B", "worker", ["task_001"], {}, ["out"], {"type": "build"}, {}),
        ]

        graph1 = TaskGraph("test-session", tasks.copy())
        graph2 = TaskGraph("test-session", tasks.copy())

        order1 = graph1.get_execution_order()
        order2 = graph2.get_execution_order()

        assert order1 == order2

    def test_get_execution_order_raises_on_cycle(self):
        """Test that get_execution_order raises on cyclical graph."""
        tasks = [
            Task("task_001", "Task 1", "worker", ["task_002"], {}, ["out"], {"type": "build"}, {}),
            Task("task_002", "Task 2", "worker", ["task_001"], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)

        with pytest.raises(ValueError) as exc_info:
            graph.get_execution_order()

        assert "cycles" in str(exc_info.value).lower()

    def test_get_ready_tasks_returns_root_tasks(self):
        """Test that get_ready_tasks returns tasks with no dependencies initially."""
        tasks = [
            Task("task_001", "Root 1", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_002", "Root 2", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_003", "Dependent", "worker", ["task_001"], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)

        ready = graph.get_ready_tasks(completed=set(), running=set(), failed=set())

        ready_ids = {t.task_id for t in ready}
        assert ready_ids == {"task_001", "task_002"}

    def test_get_ready_tasks_respects_completed(self):
        """Test that get_ready_tasks excludes completed tasks."""
        tasks = [
            Task("task_001", "Root", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_002", "Dep", "worker", ["task_001"], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)

        # task_001 is completed
        ready = graph.get_ready_tasks(completed={"task_001"}, running=set(), failed=set())

        ready_ids = {t.task_id for t in ready}
        assert ready_ids == {"task_002"}

    def test_get_ready_tasks_respects_running(self):
        """Test that get_ready_tasks excludes running tasks."""
        tasks = [
            Task("task_001", "Root 1", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_002", "Root 2", "worker", [], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)

        # task_001 is running
        ready = graph.get_ready_tasks(completed=set(), running={"task_001"}, failed=set())

        ready_ids = {t.task_id for t in ready}
        assert ready_ids == {"task_002"}

    def test_get_ready_tasks_respects_failed(self):
        """Test that get_ready_tasks excludes failed tasks."""
        tasks = [
            Task("task_001", "Root 1", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_002", "Root 2", "worker", [], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)

        # task_001 failed
        ready = graph.get_ready_tasks(completed=set(), running=set(), failed={"task_001"})

        ready_ids = {t.task_id for t in ready}
        assert ready_ids == {"task_002"}

    def test_get_ready_tasks_waits_for_all_dependencies(self):
        """Test that tasks wait for ALL dependencies to complete."""
        tasks = [
            Task("task_001", "Root 1", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_002", "Root 2", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_003", "Merge", "worker", ["task_001", "task_002"], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)

        # Only task_001 completed (task_002 still pending)
        ready = graph.get_ready_tasks(completed={"task_001"}, running=set(), failed=set())

        ready_ids = {t.task_id for t in ready}
        assert "task_003" not in ready_ids  # Still waiting for task_002

        # Both dependencies completed
        ready = graph.get_ready_tasks(
            completed={"task_001", "task_002"}, running=set(), failed=set()
        )

        ready_ids = {t.task_id for t in ready}
        assert "task_003" in ready_ids  # Now ready

    def test_get_ready_tasks_returns_in_execution_order(self):
        """Test that get_ready_tasks returns tasks in execution order."""
        tasks = [
            Task("task_003", "Root C", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_001", "Root A", "worker", [], {}, ["out"], {"type": "build"}, {}),
            Task("task_002", "Root B", "worker", [], {}, ["out"], {"type": "build"}, {}),
        ]
        graph = TaskGraph("test-session", tasks)

        ready = graph.get_ready_tasks(completed=set(), running=set(), failed=set())

        # Should be sorted alphabetically (task_001, task_002, task_003)
        assert [t.task_id for t in ready] == ["task_001", "task_002", "task_003"]
