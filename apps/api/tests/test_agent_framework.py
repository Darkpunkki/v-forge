"""
Tests for AgentFramework, DirectLlmAdapter, AgentRegistry, and stubs.

Tests VF-100, VF-101, VF-102, VF-103.
"""

import pytest
from unittest.mock import AsyncMock
from orchestration.models import Task
from models.base.llm_client import LlmResponse
from models.agent_framework import (
    AgentFramework,
    AgentResult,
    DirectLlmAdapter,
)
from models.agent_framework_stubs import (
    LangGraphAdapter,
    CrewAIAdapter,
    AutoGenAdapter,
)
from runtime.agent_registry import AgentRegistry, RoleConfig, get_agent_registry


class TestAgentResult:
    """Test AgentResult dataclass (VF-100)."""

    def test_agent_result_success(self):
        """Test creating successful AgentResult."""
        result = AgentResult(
            success=True,
            outputs={"files": ["main.py"], "summary": "Created main.py"},
            logs=["Step 1", "Step 2"],
        )

        assert result.success is True
        assert result.outputs == {"files": ["main.py"], "summary": "Created main.py"}
        assert result.logs == ["Step 1", "Step 2"]
        assert result.error_message is None

    def test_agent_result_failure(self):
        """Test creating failed AgentResult."""
        result = AgentResult(
            success=False,
            outputs={},
            logs=["Attempted step 1", "Failed at step 2"],
            error_message="Build failed",
        )

        assert result.success is False
        assert result.outputs == {}
        assert result.error_message == "Build failed"

    def test_agent_result_to_dict(self):
        """Test converting AgentResult to dictionary."""
        result = AgentResult(
            success=True,
            outputs={"result": "success"},
            logs=["Log entry"],
            error_message=None,
        )

        result_dict = result.to_dict()

        assert result_dict == {
            "success": True,
            "outputs": {"result": "success"},
            "logs": ["Log entry"],
            "error_message": None,
            "needs_clarification": False,
            "clarification": None,
        }


class MockLlmClient:
    """Mock LLM client for testing."""

    def __init__(self, response: LlmResponse):
        self.response = response
        self.requests = []

    async def complete(self, request):
        """Return mock response."""
        self.requests.append(request)
        return self.response


class TestDirectLlmAdapter:
    """Test VF-101: DirectLlmAdapter."""

    @pytest.mark.asyncio
    async def test_run_task_worker_role(self):
        """Test running a worker task."""
        task = Task(
            "task_001",
            "Implement feature",
            "worker",
            [],
            {},
            ["feature.py"],
            {"type": "test"},
            {},
        )

        mock_client = MockLlmClient(
            LlmResponse(content="Implementation complete", model="gpt-4o-mini", finish_reason="stop")
        )
        adapter = DirectLlmAdapter(mock_client)

        result = await adapter.runTask(task, "worker", {"workspace": "/tmp/ws"})

        assert result.success is True
        assert "response" in result.outputs
        assert result.outputs["response"] == "Implementation complete"
        assert any("worker" in log.lower() for log in result.logs)

    @pytest.mark.asyncio
    async def test_run_task_foreman_role(self):
        """Test running a foreman task."""
        task = Task(
            "task_001",
            "Plan implementation",
            "foreman",
            [],
            {},
            ["plan.md"],
            {"type": "manual"},
            {},
        )

        mock_client = MockLlmClient(
            LlmResponse(content="Plan created", model="gpt-4o", finish_reason="stop")
        )
        adapter = DirectLlmAdapter(mock_client)

        result = await adapter.runTask(task, "foreman", {})

        assert result.success is True
        assert result.outputs["model"] == "gpt-4o"

    @pytest.mark.asyncio
    async def test_run_task_reviewer_role(self):
        """Test running a reviewer task."""
        task = Task(
            "task_001",
            "Review code",
            "reviewer",
            [],
            {},
            ["review.md"],
            {"type": "manual"},
            {},
        )

        mock_client = MockLlmClient(
            LlmResponse(content="Review complete", model="gpt-4o-mini", finish_reason="stop")
        )
        adapter = DirectLlmAdapter(mock_client)

        result = await adapter.runTask(task, "reviewer", {})

        assert result.success is True

    @pytest.mark.asyncio
    async def test_run_task_fixer_role(self):
        """Test running a fixer task."""
        task = Task(
            "task_001",
            "Fix bug",
            "fixer",
            [],
            {},
            ["fixed.py"],
            {"type": "test"},
            {},
        )

        mock_client = MockLlmClient(
            LlmResponse(content="Bug fixed", model="gpt-4o", finish_reason="stop")
        )
        adapter = DirectLlmAdapter(mock_client)

        result = await adapter.runTask(task, "fixer", {"error": "TypeError"})

        assert result.success is True

    @pytest.mark.asyncio
    async def test_run_task_handles_llm_failure(self):
        """Test handling LLM client failure."""
        task = Task(
            "task_001",
            "Task",
            "worker",
            [],
            {},
            ["out"],
            {"type": "build"},
            {},
        )

        class FailingClient:
            async def complete(self, request):
                raise RuntimeError("LLM API error")

        adapter = DirectLlmAdapter(FailingClient())

        result = await adapter.runTask(task, "worker", {})

        assert result.success is False
        assert result.error_message == "LLM API error"
        assert any("failed" in log.lower() for log in result.logs)

    @pytest.mark.asyncio
    async def test_run_task_creates_correct_prompt(self):
        """Test that correct prompt is created for task."""
        task = Task(
            "task_001",
            "Test description",
            "worker",
            [],
            {},
            ["output1.py", "output2.py"],
            {"type": "test"},
            {},
        )

        mock_client = MockLlmClient(
            LlmResponse(content="Done", model="gpt-4o-mini", finish_reason="stop")
        )
        adapter = DirectLlmAdapter(mock_client)

        await adapter.runTask(task, "worker", {"workspace": "/test"})

        assert len(mock_client.requests) == 1
        request = mock_client.requests[0]
        assert len(request.messages) == 2
        assert request.messages[0].role == "system"
        assert request.messages[1].role == "user"
        # Check prompt includes task details
        user_prompt = request.messages[1].content
        assert "task_001" in user_prompt
        assert "Test description" in user_prompt

    def test_get_framework_name(self):
        """Test framework name."""
        mock_client = MockLlmClient(
            LlmResponse(content="", model="gpt-4o-mini", finish_reason="stop")
        )
        adapter = DirectLlmAdapter(mock_client)

        assert adapter.get_framework_name() == "DirectLLM"


class TestAgentRegistry:
    """Test VF-102: AgentRegistry."""

    def test_registry_initialization(self):
        """Test that registry initializes with default roles."""
        registry = AgentRegistry()

        assert "worker" in registry.roles
        assert "foreman" in registry.roles
        assert "reviewer" in registry.roles
        assert "fixer" in registry.roles

    def test_get_role_config_worker(self):
        """Test getting worker role configuration."""
        registry = AgentRegistry()

        config = registry.get_role_config("worker")

        assert config.role == "worker"
        assert "software development" in config.system_prompt.lower()
        assert "task_id" in config.prompt_template
        assert "files" in config.output_schema["properties"]
        assert "read" in config.allowed_tools
        assert "write" in config.allowed_tools

    def test_get_role_config_foreman(self):
        """Test getting foreman role configuration."""
        registry = AgentRegistry()

        config = registry.get_role_config("foreman")

        assert config.role == "foreman"
        assert "planning" in config.system_prompt.lower()
        assert "plan" in config.output_schema["properties"]
        assert "read" in config.allowed_tools

    def test_get_role_config_reviewer(self):
        """Test getting reviewer role configuration."""
        registry = AgentRegistry()

        config = registry.get_role_config("reviewer")

        assert config.role == "reviewer"
        assert "review" in config.system_prompt.lower()
        assert "approved" in config.output_schema["properties"]

    def test_get_role_config_fixer(self):
        """Test getting fixer role configuration."""
        registry = AgentRegistry()

        config = registry.get_role_config("fixer")

        assert config.role == "fixer"
        assert "debugging" in config.system_prompt.lower()
        assert "diagnosis" in config.output_schema["properties"]

    def test_get_role_config_unknown_raises(self):
        """Test that unknown role raises ValueError."""
        registry = AgentRegistry()

        with pytest.raises(ValueError) as exc_info:
            registry.get_role_config("unknown_role")

        assert "Unknown role" in str(exc_info.value)
        assert "unknown_role" in str(exc_info.value)

    def test_list_roles(self):
        """Test listing all registered roles."""
        registry = AgentRegistry()

        roles = registry.list_roles()

        assert "worker" in roles
        assert "foreman" in roles
        assert "reviewer" in roles
        assert "fixer" in roles
        assert len(roles) == 4

    def test_register_custom_role(self):
        """Test registering a custom role."""
        registry = AgentRegistry()

        custom_role = RoleConfig(
            role="custom",
            system_prompt="Custom prompt",
            prompt_template="Do: {task_id}",
            output_schema={"type": "object", "properties": {}},
            allowed_tools=["read"],
        )

        registry.register_role(custom_role)

        assert registry.has_role("custom")
        config = registry.get_role_config("custom")
        assert config.role == "custom"
        assert config.system_prompt == "Custom prompt"

    def test_has_role(self):
        """Test checking if role exists."""
        registry = AgentRegistry()

        assert registry.has_role("worker") is True
        assert registry.has_role("foreman") is True
        assert registry.has_role("nonexistent") is False

    def test_get_agent_registry_factory(self):
        """Test get_agent_registry factory function."""
        registry = get_agent_registry()

        assert isinstance(registry, AgentRegistry)
        assert registry.has_role("worker")


class TestAgentFrameworkStubs:
    """Test VF-103: Placeholder adapters."""

    @pytest.mark.asyncio
    async def test_langgraph_stub_raises_not_implemented(self):
        """Test LangGraph stub raises NotImplementedError."""
        adapter = LangGraphAdapter()
        task = Task("t1", "desc", "worker", [], {}, ["out"], {"type": "build"}, {})

        with pytest.raises(NotImplementedError) as exc_info:
            await adapter.runTask(task, "worker", {})

        assert "LangGraph adapter not yet implemented" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_crewai_stub_raises_not_implemented(self):
        """Test CrewAI stub raises NotImplementedError."""
        adapter = CrewAIAdapter()
        task = Task("t1", "desc", "worker", [], {}, ["out"], {"type": "build"}, {})

        with pytest.raises(NotImplementedError) as exc_info:
            await adapter.runTask(task, "worker", {})

        assert "CrewAI adapter not yet implemented" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_autogen_stub_raises_not_implemented(self):
        """Test AutoGen stub raises NotImplementedError."""
        adapter = AutoGenAdapter()
        task = Task("t1", "desc", "worker", [], {}, ["out"], {"type": "build"}, {})

        with pytest.raises(NotImplementedError) as exc_info:
            await adapter.runTask(task, "worker", {})

        assert "AutoGen adapter not yet implemented" in str(exc_info.value)

    def test_langgraph_framework_name(self):
        """Test LangGraph framework name."""
        adapter = LangGraphAdapter()
        assert adapter.get_framework_name() == "LangGraph (stub)"

    def test_crewai_framework_name(self):
        """Test CrewAI framework name."""
        adapter = CrewAIAdapter()
        assert adapter.get_framework_name() == "CrewAI (stub)"

    def test_autogen_framework_name(self):
        """Test AutoGen framework name."""
        adapter = AutoGenAdapter()
        assert adapter.get_framework_name() == "AutoGen (stub)"

    def test_stubs_implement_agent_framework_interface(self):
        """Test that all stubs implement AgentFramework interface."""
        assert isinstance(LangGraphAdapter(), AgentFramework)
        assert isinstance(CrewAIAdapter(), AgentFramework)
        assert isinstance(AutoGenAdapter(), AgentFramework)


class TestRoleConfigDataclass:
    """Test RoleConfig dataclass (VF-102)."""

    def test_role_config_creation(self):
        """Test creating RoleConfig."""
        config = RoleConfig(
            role="test_role",
            system_prompt="Test system prompt",
            prompt_template="Test template: {task_id}",
            output_schema={"type": "object"},
            allowed_tools=["read", "write"],
        )

        assert config.role == "test_role"
        assert config.system_prompt == "Test system prompt"
        assert config.prompt_template == "Test template: {task_id}"
        assert config.output_schema == {"type": "object"}
        assert config.allowed_tools == ["read", "write"]
