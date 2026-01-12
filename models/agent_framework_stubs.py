"""
Agent Framework Stubs: Placeholder adapters for future integrations.

VF-103: Stub implementations for LangGraph, CrewAI, and AutoGen

Upgrade Path: docs/ai/design/agent-local-stub-upgrade-path.md
- LangGraphAdapter: VF-310 through VF-312 (High priority)
- CrewAIAdapter: VF-315 through VF-316 (Medium priority)
- AutoGenAdapter: VF-320 through VF-321 (Low priority, deferred)

See MVP Placeholder Audit (MP-005) for remediation guidance.
"""

from typing import Any
from models.agent_framework import AgentFramework, AgentResult
from orchestration.models import Task


class LangGraphAdapter(AgentFramework):
    """
    VF-103: Placeholder for LangGraph integration.

    Future: Connect to LangGraph for graph-based agent workflows.
    LangGraph enables complex, stateful agent workflows with cycles.
    """

    async def runTask(
        self, task: Task, role: str, context: dict[str, Any]
    ) -> AgentResult:
        """
        Not implemented - placeholder only.

        Args:
            task: Task to execute
            role: Agent role
            context: Execution context

        Raises:
            NotImplementedError: Always - stub only
        """
        raise NotImplementedError(
            "LangGraph adapter not yet implemented. "
            "This is a placeholder for future LangGraph integration."
        )

    def get_framework_name(self) -> str:
        """Return framework name."""
        return "LangGraph (stub)"


class CrewAIAdapter(AgentFramework):
    """
    VF-103: Placeholder for CrewAI integration.

    Future: Connect to CrewAI for multi-agent collaboration.
    CrewAI enables role-based multi-agent systems with process orchestration.
    """

    async def runTask(
        self, task: Task, role: str, context: dict[str, Any]
    ) -> AgentResult:
        """
        Not implemented - placeholder only.

        Args:
            task: Task to execute
            role: Agent role
            context: Execution context

        Raises:
            NotImplementedError: Always - stub only
        """
        raise NotImplementedError(
            "CrewAI adapter not yet implemented. "
            "This is a placeholder for future CrewAI integration."
        )

    def get_framework_name(self) -> str:
        """Return framework name."""
        return "CrewAI (stub)"


class AutoGenAdapter(AgentFramework):
    """
    VF-103: Placeholder for AutoGen integration.

    Future: Connect to AutoGen for conversational multi-agent systems.
    AutoGen enables autonomous agent conversations and code execution.
    """

    async def runTask(
        self, task: Task, role: str, context: dict[str, Any]
    ) -> AgentResult:
        """
        Not implemented - placeholder only.

        Args:
            task: Task to execute
            role: Agent role
            context: Execution context

        Raises:
            NotImplementedError: Always - stub only
        """
        raise NotImplementedError(
            "AutoGen adapter not yet implemented. "
            "This is a placeholder for future AutoGen integration."
        )

    def get_framework_name(self) -> str:
        """Return framework name."""
        return "AutoGen (stub)"
