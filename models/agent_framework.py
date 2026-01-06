"""
AgentFramework: Interface for pluggable agent implementations.

VF-100: Defines AgentFramework.runTask() interface
VF-101: Implements DirectLlmAdapter (MVP)
"""

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any, Optional

from models.base.llm_client import LlmClient, LlmRequest, LlmMessage, LlmUsage
from models.router import get_model_router, RoutingContext
from models.validation import OutputValidator
from orchestration.models import Task


@dataclass
class AgentResult:
    """Standard result from agent task execution."""

    success: bool
    outputs: dict[str, Any]  # Files, artifacts produced
    logs: list[str]  # Execution logs
    usage: Optional[LlmUsage] = None
    error_message: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "success": self.success,
            "outputs": self.outputs,
            "logs": self.logs,
            "error_message": self.error_message,
        }

        if self.usage:
            result["usage"] = asdict(self.usage)

        return result


class AgentFramework(ABC):
    """
    VF-100: Interface for agent framework adapters.

    Allows pluggable agent implementations (direct LLM, LangGraph, CrewAI, etc.)
    """

    @abstractmethod
    async def runTask(
        self, task: Task, role: str, context: dict[str, Any]
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


class DirectLlmAdapter(AgentFramework):
    """
    VF-101: MVP adapter that calls LLM directly with role prompt.

    Simplest possible implementation - no complex framework overhead.
    """

    def __init__(self, llm_client: LlmClient):
        """
        Initialize with LLM client.

        Args:
            llm_client: LLM client for making model calls
        """
        self.llm_client = llm_client
        self.router = get_model_router()
        self.validator = OutputValidator()

    async def runTask(
        self, task: Task, role: str, context: dict[str, Any]
    ) -> AgentResult:
        """
        Execute task by calling LLM with role prompt.

        Steps:
        1. Get role prompt from hardcoded templates (MVP)
        2. Format prompt with task details and context
        3. Select model based on role
        4. Call LLM
        5. Validate output against simple schema
        6. Return AgentResult

        Args:
            task: Task to execute
            role: Agent role
            context: Execution context

        Returns:
            AgentResult with success/failure and outputs
        """
        # Get role prompts (hardcoded for MVP - VF-102 will externalize)
        system_prompt, user_prompt_template = self._get_role_prompts(role)

        # Format user prompt
        user_prompt = user_prompt_template.format(
            task_id=task.task_id,
            description=task.description,
            expected_outputs=", ".join(task.expected_outputs),
            context=str(context),
        )

        # Select model based on role
        routing_ctx = RoutingContext(
            role=role,
            complexity="simple",  # Default for MVP
            metadata={"task_id": task.task_id},
        )
        provider, model = self.router.select_model(routing_ctx)

        # Make LLM request
        request = LlmRequest(
            messages=[
                LlmMessage(role="system", content=system_prompt),
                LlmMessage(role="user", content=user_prompt),
            ],
            model=model,
            temperature=0.7,
        )

        try:
            response = await self.llm_client.complete(request)

            # For MVP, treat any response as success
            # VF-102 will add proper schema validation
            return AgentResult(
                success=True,
                outputs={"response": response.content, "model": model},
                logs=[
                    f"Model: {model}",
                    f"Provider: {provider}",
                    f"Role: {role}",
                ],
                usage=response.usage,
            )
        except Exception as e:
            return AgentResult(
                success=False,
                outputs={},
                logs=[f"LLM call failed: {str(e)}"],
                error_message=str(e),
            )

    def _get_role_prompts(self, role: str) -> tuple[str, str]:
        """
        Get system and user prompt templates for a role.

        MVP implementation - hardcoded prompts.
        VF-102 will move these to AgentRegistry.

        Args:
            role: Agent role

        Returns:
            Tuple of (system_prompt, user_prompt_template)
        """
        prompts = {
            "worker": (
                "You are a software development agent. Implement the requested task precisely.",
                "Task ID: {task_id}\n"
                "Description: {description}\n"
                "Expected outputs: {expected_outputs}\n\n"
                "Context: {context}\n\n"
                "Implement this task and return the result.",
            ),
            "foreman": (
                "You are a planning and coordination agent. Break down complex tasks.",
                "Task ID: {task_id}\n"
                "Description: {description}\n\n"
                "Plan the implementation approach and coordinate subtasks.",
            ),
            "reviewer": (
                "You are a code review agent. Verify quality and correctness.",
                "Task ID: {task_id}\n"
                "Description: {description}\n\n"
                "Review the implementation and provide feedback.",
            ),
            "fixer": (
                "You are a debugging and fixing agent. Diagnose and resolve failures.",
                "Task ID: {task_id}\n"
                "Description: {description}\n"
                "Previous context: {context}\n\n"
                "Diagnose the issue and implement a fix.",
            ),
        }

        if role not in prompts:
            # Default to worker
            role = "worker"

        return prompts[role]

    def get_framework_name(self) -> str:
        """Return framework name."""
        return "DirectLLM"
