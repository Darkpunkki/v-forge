"""
Distributor: Routes tasks to agent roles with escalation policy.

VF-095: Task-to-role routing based on hints and heuristics
VF-096: Escalation policy for handling repeated failures
"""

from dataclasses import dataclass
from orchestration.models import Task


@dataclass
class AgentRole:
    """Agent role assignment for a task."""

    role: str  # "worker", "foreman", "reviewer", "fixer"
    model_tier: str  # "fast", "balanced", "powerful"
    reason: str  # Why this role was selected


class Distributor:
    """
    Routes tasks to agent roles based on hints and heuristics.

    VF-095: Implements task -> role routing logic
    VF-096: Implements escalation policy for failures
    """

    def __init__(self):
        """Initialize distributor with default routing rules."""
        # Valid roles for validation
        self.valid_roles = {"worker", "foreman", "reviewer", "fixer"}

        # Model tier hierarchy for escalation
        self.model_tiers = ["fast", "balanced", "powerful"]

    def route(self, task: Task, failure_count: int = 0) -> AgentRole:
        """
        VF-095: Route task to appropriate agent role.

        Routing logic:
        1. Use task.role as default (from TaskGraph)
        2. Apply escalation policy based on failure_count
        3. Select model tier based on task complexity and failures

        Args:
            task: Task to route
            failure_count: Number of previous failures (for escalation)

        Returns:
            AgentRole assignment

        Raises:
            ValueError: If task role is invalid
        """
        # Validate task role
        if task.role not in self.valid_roles and task.role != "fixer":
            # Allow fixer even if not in original valid set
            if task.role not in {"worker", "foreman", "reviewer"}:
                raise ValueError(
                    f"Invalid task role: {task.role}. "
                    f"Must be one of: worker, foreman, reviewer"
                )

        # Start with task's explicit role
        role = task.role
        model_tier = "balanced"  # Default
        reason = f"Task specifies role: {role}"

        # VF-096: Escalation policy
        if failure_count > 0:
            role, model_tier, reason = self._escalate(task, failure_count)

        return AgentRole(role=role, model_tier=model_tier, reason=reason)

    def _escalate(
        self, task: Task, failure_count: int
    ) -> tuple[str, str, str]:
        """
        VF-096: Escalate role/model based on failure count.

        Escalation ladder:
        - 1 failure (1st retry): Same role, upgrade to "powerful" model
        - 2+ failures: Escalate to "fixer" role with "powerful" model

        Args:
            task: Failed task
            failure_count: Number of failures

        Returns:
            Tuple of (role, model_tier, reason)
        """
        if failure_count == 1:
            # First retry: upgrade model, keep role
            return (
                task.role,
                "powerful",
                f"Escalated to powerful model after {failure_count} failure(s)",
            )
        else:
            # Multiple failures: escalate to fixer with powerful model
            return (
                "fixer",
                "powerful",
                f"Escalated to fixer role after {failure_count} failure(s)",
            )

    def get_model_tier_index(self, tier: str) -> int:
        """
        Get index of model tier in hierarchy.

        Args:
            tier: Model tier name

        Returns:
            Index in model_tiers list

        Raises:
            ValueError: If tier is unknown
        """
        if tier not in self.model_tiers:
            raise ValueError(
                f"Unknown model tier: {tier}. "
                f"Must be one of: {self.model_tiers}"
            )
        return self.model_tiers.index(tier)


# Global distributor instance
_distributor = None


def get_distributor() -> Distributor:
    """Get global distributor instance."""
    global _distributor
    if _distributor is None:
        _distributor = Distributor()
    return _distributor
