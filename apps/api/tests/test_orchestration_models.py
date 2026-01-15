"""Tests for orchestration models (ConceptDoc, TaskGraph, RunSummary)."""

import pytest
from orchestration.models import ConceptDoc, Task, TaskGraph, RunSummary


class TestConceptDoc:
    """Test ConceptDoc model."""

    def test_concept_doc_creation(self):
        """Test creating ConceptDoc instance."""
        concept = ConceptDoc(
            session_id="test-123",
            idea_description="A task manager application",
            features=["Create tasks", "Delete tasks"],
            tech_stack={"framework": "React", "language": "TypeScript", "testing": "Vitest", "build": "Vite", "runtime": "Node"},
            file_structure={"src/App.tsx": "Main app"},
            verification_steps=["npm test"],
            constraints=["Simple scope"]
        )

        assert concept.session_id == "test-123"
        assert "task manager" in concept.idea_description
        assert len(concept.features) == 2
        assert concept.tech_stack["framework"] == "React"

    def test_concept_doc_to_dict(self):
        """Test ConceptDoc serialization."""
        concept = ConceptDoc(
            session_id="test-123",
            idea_description="Test app",
            features=["F1", "F2"],
            tech_stack={"framework": "React", "language": "TS", "testing": "Vitest", "build": "Vite", "runtime": "Node"},
            file_structure={"src/main.ts": "Entry"},
            verification_steps=["npm test"],
            constraints=["C1"]
        )

        data = concept.to_dict()

        assert "session_id" not in data  # Excluded from serialization
        assert data["idea_description"] == "Test app"
        assert data["features"] == ["F1", "F2"]

    def test_concept_doc_from_dict(self):
        """Test ConceptDoc deserialization."""
        data = {
            "idea_description": "Test app description",
            "features": ["Feature 1", "Feature 2"],
            "tech_stack": {"framework": "React", "language": "TS", "testing": "Vitest", "build": "Vite", "runtime": "Node"},
            "file_structure": {"src/App.tsx": "Main"},
            "verification_steps": ["npm test"],
            "constraints": ["Constraint 1"]
        }

        concept = ConceptDoc.from_dict("session-456", data)

        assert concept.session_id == "session-456"
        assert concept.idea_description == "Test app description"
        assert len(concept.features) == 2


class TestTask:
    """Test Task model."""

    def test_task_creation(self):
        """Test creating Task instance."""
        task = Task(
            task_id="task_001",
            description="Set up project",
            role="worker",
            dependencies=[],
            inputs={"concept": "doc"},
            expected_outputs=["package.json"],
            verification={"type": "build", "commands": ["npm install"]},
            constraints={"max_files": 10}
        )

        assert task.task_id == "task_001"
        assert task.role == "worker"
        assert len(task.dependencies) == 0

    def test_task_to_dict(self):
        """Test Task serialization."""
        task = Task(
            task_id="task_001",
            description="Test task",
            role="foreman",
            dependencies=["task_000"],
            inputs={},
            expected_outputs=["output.txt"],
            verification={"type": "manual"},
            constraints={}
        )

        data = task.to_dict()

        assert data["task_id"] == "task_001"
        assert data["role"] == "foreman"
        assert data["dependencies"] == ["task_000"]

    def test_task_from_dict(self):
        """Test Task deserialization."""
        data = {
            "task_id": "task_002",
            "description": "Implement feature",
            "role": "worker",
            "dependencies": ["task_001"],
            "inputs": {"previous": "data"},
            "expected_outputs": ["feature.ts"],
            "verification": {"type": "test", "commands": ["npm test"]},
            "constraints": {"timeout_seconds": 300}
        }

        task = Task.from_dict(data)

        assert task.task_id == "task_002"
        assert task.role == "worker"
        assert task.dependencies == ["task_001"]


class TestTaskGraph:
    """Test TaskGraph model and DAG validation."""

    def test_task_graph_creation(self):
        """Test creating TaskGraph instance."""
        tasks = [
            Task("task_001", "Setup", "worker", [], {}, ["package.json"], {"type": "build"}, {}),
            Task("task_002", "Implement", "worker", ["task_001"], {}, ["src/app.ts"], {"type": "test"}, {})
        ]

        graph = TaskGraph(
            session_id="test-123",
            tasks=tasks,
            metadata={"total_tasks": 2}
        )

        assert graph.session_id == "test-123"
        assert len(graph.tasks) == 2
        assert graph.metadata["total_tasks"] == 2

    def test_task_graph_to_dict(self):
        """Test TaskGraph serialization."""
        tasks = [
            Task("task_001", "Setup", "worker", [], {}, ["out"], {"type": "build"}, {})
        ]
        graph = TaskGraph("test-123", tasks, {"total_tasks": 1})

        data = graph.to_dict()

        assert "session_id" not in data
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["task_id"] == "task_001"
        assert data["metadata"]["total_tasks"] == 1

    def test_task_graph_from_dict(self):
        """Test TaskGraph deserialization."""
        data = {
            "tasks": [
                {
                    "task_id": "task_001",
                    "description": "Task 1",
                    "role": "worker",
                    "dependencies": [],
                    "inputs": {},
                    "expected_outputs": ["output1"],
                    "verification": {"type": "build"},
                    "constraints": {}
                }
            ],
            "metadata": {"total_tasks": 1}
        }

        graph = TaskGraph.from_dict("session-789", data)

        assert graph.session_id == "session-789"
        assert len(graph.tasks) == 1
        assert graph.tasks[0].task_id == "task_001"

    def test_validate_dag_valid_graph(self):
        """Test DAG validation passes for valid graph."""
        tasks = [
            Task("task_001", "Setup", "worker", [], {}, ["out1"], {"type": "build"}, {}),
            Task("task_002", "Build", "worker", ["task_001"], {}, ["out2"], {"type": "build"}, {}),
            Task("task_003", "Test", "reviewer", ["task_002"], {}, ["out3"], {"type": "test"}, {})
        ]
        graph = TaskGraph("test-123", tasks)

        is_valid, errors = graph.validate_dag()

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_dag_detects_duplicate_task_ids(self):
        """Test DAG validation detects duplicate task IDs."""
        tasks = [
            Task("task_001", "Setup", "worker", [], {}, ["out1"], {"type": "build"}, {}),
            Task("task_001", "Duplicate", "worker", [], {}, ["out2"], {"type": "build"}, {})
        ]
        graph = TaskGraph("test-123", tasks)

        is_valid, errors = graph.validate_dag()

        assert is_valid is False
        assert any("Duplicate task IDs" in error for error in errors)

    def test_validate_dag_detects_nonexistent_dependencies(self):
        """Test DAG validation detects dependencies on non-existent tasks."""
        tasks = [
            Task("task_001", "Setup", "worker", [], {}, ["out1"], {"type": "build"}, {}),
            Task("task_002", "Build", "worker", ["task_999"], {}, ["out2"], {"type": "build"}, {})
        ]
        graph = TaskGraph("test-123", tasks)

        is_valid, errors = graph.validate_dag()

        assert is_valid is False
        assert any("non-existent task" in error for error in errors)

    def test_validate_dag_detects_cycles(self):
        """Test DAG validation detects cycles."""
        # Create a cycle: task_001 -> task_002 -> task_003 -> task_001
        tasks = [
            Task("task_001", "Task 1", "worker", ["task_003"], {}, ["out1"], {"type": "build"}, {}),
            Task("task_002", "Task 2", "worker", ["task_001"], {}, ["out2"], {"type": "build"}, {}),
            Task("task_003", "Task 3", "worker", ["task_002"], {}, ["out3"], {"type": "build"}, {})
        ]
        graph = TaskGraph("test-123", tasks)

        is_valid, errors = graph.validate_dag()

        assert is_valid is False
        assert any("cycles" in error.lower() or "cycle" in error.lower() for error in errors)

    def test_validate_dag_allows_parallel_tasks(self):
        """Test DAG validation allows parallel tasks (no dependencies)."""
        tasks = [
            Task("task_001", "Setup", "worker", [], {}, ["out1"], {"type": "build"}, {}),
            Task("task_002", "Feature A", "worker", ["task_001"], {}, ["featureA"], {"type": "build"}, {}),
            Task("task_003", "Feature B", "worker", ["task_001"], {}, ["featureB"], {"type": "build"}, {}),
            Task("task_004", "Integrate", "worker", ["task_002", "task_003"], {}, ["integrated"], {"type": "test"}, {})
        ]
        graph = TaskGraph("test-123", tasks)

        is_valid, errors = graph.validate_dag()

        assert is_valid is True
        assert len(errors) == 0


class TestRunSummary:
    """Test RunSummary model."""

    def test_run_summary_creation(self):
        """Test creating RunSummary instance."""
        summary = RunSummary(
            session_id="test-123",
            status="success",
            summary="Built a task manager app",
            files_generated=["src/App.tsx", "package.json"],
            verification_results={"test": "✓ Passed"},
            how_to_run=["npm install", "npm run dev"],
            limitations=["No backend", "Local only"]
        )

        assert summary.session_id == "test-123"
        assert summary.status == "success"
        assert len(summary.files_generated) == 2

    def test_run_summary_to_dict(self):
        """Test RunSummary serialization."""
        summary = RunSummary(
            session_id="test-123",
            status="partial",
            summary="Partially completed build",
            files_generated=["file1.ts"],
            verification_results={"build": "✓ Pass", "test": "✗ Fail"},
            how_to_run=["npm run dev"],
            limitations=["Tests incomplete"]
        )

        data = summary.to_dict()

        assert "session_id" not in data
        assert data["status"] == "partial"
        assert data["summary"] == "Partially completed build"

    def test_run_summary_from_dict(self):
        """Test RunSummary deserialization."""
        data = {
            "status": "failed",
            "summary": "Build failed due to errors",
            "files_generated": [],
            "verification_results": {"build": "✗ Failed"},
            "how_to_run": ["Fix errors first"],
            "limitations": ["Build incomplete", "No runnable output"]
        }

        summary = RunSummary.from_dict("session-456", data)

        assert summary.session_id == "session-456"
        assert summary.status == "failed"
        assert len(summary.files_generated) == 0


class TestAgentWorkflowModels:
    """Tests for VF-191: Agent workflow models."""

    def test_agent_config_validation(self):
        """AgentConfig requires non-empty agent_id."""
        from pydantic import ValidationError
        from orchestration.models import AgentConfig

        # Valid agent config
        agent = AgentConfig(agent_id="agent-1")
        assert agent.agent_id == "agent-1"

        # Empty agent_id should fail
        with pytest.raises(ValidationError):
            AgentConfig(agent_id="")

        # Whitespace-only agent_id should fail
        with pytest.raises(ValidationError):
            AgentConfig(agent_id="   ")

    def test_agent_config_with_role_and_model(self):
        """AgentConfig can store role and model_id."""
        from orchestration.models import AgentConfig, AgentRole

        agent = AgentConfig(
            agent_id="agent-1",
            role=AgentRole.WORKER,
            model_id="gpt-4",
            display_name="Worker Agent 1",
        )

        assert agent.agent_id == "agent-1"
        assert agent.role == AgentRole.WORKER
        assert agent.model_id == "gpt-4"
        assert agent.display_name == "Worker Agent 1"

    def test_agent_role_enum_values(self):
        """AgentRole enum has expected values."""
        from orchestration.models import AgentRole

        assert AgentRole.ORCHESTRATOR.value == "orchestrator"
        assert AgentRole.FOREMAN.value == "foreman"
        assert AgentRole.WORKER.value == "worker"
        assert AgentRole.REVIEWER.value == "reviewer"
        assert AgentRole.FIXER.value == "fixer"

    def test_agent_flow_graph_valid(self):
        """Valid DAG passes validation."""
        from orchestration.models import AgentFlowGraph, AgentFlowEdge

        graph = AgentFlowGraph(
            edges=[
                AgentFlowEdge(from_agent="a", to_agent="b"),
                AgentFlowEdge(from_agent="b", to_agent="c"),
            ]
        )
        is_valid, error = graph.validate_dag(["a", "b", "c"])
        assert is_valid
        assert error is None

    def test_agent_flow_graph_cycle_allowed(self):
        """Cyclic graph passes validation."""
        from orchestration.models import AgentFlowGraph, AgentFlowEdge

        graph = AgentFlowGraph(
            edges=[
                AgentFlowEdge(from_agent="a", to_agent="b"),
                AgentFlowEdge(from_agent="b", to_agent="c"),
                AgentFlowEdge(from_agent="c", to_agent="a"),  # cycle!
            ]
        )
        is_valid, error = graph.validate_dag(["a", "b", "c"])
        assert is_valid
        assert error is None

    def test_agent_flow_graph_bidirectional_links_allowed(self):
        """Bidirectional links pass validation."""
        from orchestration.models import AgentFlowGraph, AgentFlowEdge

        graph = AgentFlowGraph(
            edges=[
                AgentFlowEdge(from_agent="a", to_agent="b"),
                AgentFlowEdge(from_agent="b", to_agent="a"),
            ]
        )
        is_valid, error = graph.validate_dag(["a", "b"])
        assert is_valid
        assert error is None

    def test_agent_flow_graph_unknown_agent(self):
        """Unknown agent reference fails validation."""
        from orchestration.models import AgentFlowGraph, AgentFlowEdge

        graph = AgentFlowGraph(
            edges=[
                AgentFlowEdge(from_agent="a", to_agent="unknown"),
            ]
        )
        is_valid, error = graph.validate_dag(["a", "b"])
        assert not is_valid
        assert "Unknown target agent" in error
        assert "unknown" in error

    def test_agent_flow_graph_get_predecessors(self):
        """get_predecessors returns agents that feed into target."""
        from orchestration.models import AgentFlowGraph, AgentFlowEdge

        graph = AgentFlowGraph(
            edges=[
                AgentFlowEdge(from_agent="a", to_agent="c"),
                AgentFlowEdge(from_agent="b", to_agent="c"),
            ]
        )

        predecessors = graph.get_predecessors("c")
        assert set(predecessors) == {"a", "b"}

        predecessors = graph.get_predecessors("a")
        assert predecessors == []

    def test_agent_flow_graph_get_successors(self):
        """get_successors returns agents that target feeds into."""
        from orchestration.models import AgentFlowGraph, AgentFlowEdge

        graph = AgentFlowGraph(
            edges=[
                AgentFlowEdge(from_agent="a", to_agent="b"),
                AgentFlowEdge(from_agent="a", to_agent="c"),
            ]
        )

        successors = graph.get_successors("a")
        assert set(successors) == {"b", "c"}

        successors = graph.get_successors("c")
        assert successors == []

    def test_simulation_config_defaults(self):
        """SimulationConfig has correct defaults."""
        from orchestration.models import SimulationConfig

        config = SimulationConfig()
        assert config.simulation_mode == "manual"
        assert config.auto_delay_ms is None
        assert config.tick_budget is None

    def test_simulation_config_with_values(self):
        """SimulationConfig stores custom values."""
        from orchestration.models import SimulationConfig

        config = SimulationConfig(
            simulation_mode="auto", auto_delay_ms=1000, tick_budget=100
        )
        assert config.simulation_mode == "auto"
        assert config.auto_delay_ms == 1000
        assert config.tick_budget == 100

    def test_tick_state_defaults(self):
        """TickState has correct defaults."""
        from orchestration.models import TickState

        state = TickState()
        assert state.tick_index == 0
        assert state.tick_status == "idle"
        assert state.pending_work_summary is None

    def test_tick_state_with_values(self):
        """TickState stores custom values."""
        from orchestration.models import TickState

        state = TickState(
            tick_index=5,
            tick_status="running",
            pending_work_summary="3 tasks queued",
        )
        assert state.tick_index == 5
        assert state.tick_status == "running"
        assert state.pending_work_summary == "3 tasks queued"
