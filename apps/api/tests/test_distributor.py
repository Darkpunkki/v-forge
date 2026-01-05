"""
Tests for Distributor (VF-095, VF-096).
"""

import pytest
from orchestration.models import Task
from runtime.distributor import Distributor, AgentRole, get_distributor


class TestDistributorRouting:
    """Test VF-095: Distributor.route() task-to-role routing."""

    def test_route_worker_task(self):
        """Test routing a worker task."""
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
        distributor = Distributor()

        role = distributor.route(task, failure_count=0)

        assert role.role == "worker"
        assert role.model_tier == "balanced"
        assert "worker" in role.reason.lower()

    def test_route_foreman_task(self):
        """Test routing a foreman task."""
        task = Task(
            "task_001",
            "Plan architecture",
            "foreman",
            [],
            {},
            ["design.md"],
            {"type": "manual"},
            {},
        )
        distributor = Distributor()

        role = distributor.route(task, failure_count=0)

        assert role.role == "foreman"
        assert role.model_tier == "balanced"

    def test_route_reviewer_task(self):
        """Test routing a reviewer task."""
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
        distributor = Distributor()

        role = distributor.route(task, failure_count=0)

        assert role.role == "reviewer"
        assert role.model_tier == "balanced"

    def test_route_invalid_role_raises_error(self):
        """Test that invalid task role raises ValueError."""
        task = Task(
            "task_001",
            "Bad task",
            "invalid_role",
            [],
            {},
            ["output"],
            {"type": "build"},
            {},
        )
        distributor = Distributor()

        with pytest.raises(ValueError) as exc_info:
            distributor.route(task, failure_count=0)

        assert "Invalid task role" in str(exc_info.value)

    def test_get_distributor_factory(self):
        """Test get_distributor factory function."""
        distributor = get_distributor()

        assert isinstance(distributor, Distributor)
        assert distributor.valid_roles == {"worker", "foreman", "reviewer", "fixer"}


class TestDistributorEscalation:
    """Test VF-096: Distributor escalation policy."""

    def test_escalate_first_failure_upgrades_model(self):
        """Test that first failure upgrades to powerful model."""
        task = Task(
            "task_001",
            "Failing task",
            "worker",
            [],
            {},
            ["output"],
            {"type": "build"},
            {},
        )
        distributor = Distributor()

        role = distributor.route(task, failure_count=1)

        assert role.role == "worker"  # Same role
        assert role.model_tier == "powerful"  # Upgraded model
        assert "powerful model" in role.reason.lower()
        assert "1 failure" in role.reason.lower()

    def test_escalate_second_failure_switches_to_fixer(self):
        """Test that second failure escalates to fixer role."""
        task = Task(
            "task_001",
            "Repeatedly failing task",
            "worker",
            [],
            {},
            ["output"],
            {"type": "build"},
            {},
        )
        distributor = Distributor()

        role = distributor.route(task, failure_count=2)

        assert role.role == "fixer"  # Escalated role
        assert role.model_tier == "powerful"  # Powerful model
        assert "fixer" in role.reason.lower()
        assert "2 failure" in role.reason.lower()

    def test_escalate_multiple_failures_stays_fixer(self):
        """Test that multiple failures stay on fixer with powerful model."""
        task = Task(
            "task_001",
            "Very broken task",
            "worker",
            [],
            {},
            ["output"],
            {"type": "build"},
            {},
        )
        distributor = Distributor()

        role = distributor.route(task, failure_count=5)

        assert role.role == "fixer"
        assert role.model_tier == "powerful"
        assert "5 failure" in role.reason.lower()

    def test_escalate_from_foreman_to_fixer(self):
        """Test escalation works for foreman tasks too."""
        task = Task(
            "task_001",
            "Failed planning",
            "foreman",
            [],
            {},
            ["plan"],
            {"type": "manual"},
            {},
        )
        distributor = Distributor()

        # First failure: upgrade model, keep foreman
        role1 = distributor.route(task, failure_count=1)
        assert role1.role == "foreman"
        assert role1.model_tier == "powerful"

        # Second failure: escalate to fixer
        role2 = distributor.route(task, failure_count=2)
        assert role2.role == "fixer"
        assert role2.model_tier == "powerful"

    def test_escalate_from_reviewer_to_fixer(self):
        """Test escalation works for reviewer tasks."""
        task = Task(
            "task_001",
            "Failed review",
            "reviewer",
            [],
            {},
            ["review"],
            {"type": "manual"},
            {},
        )
        distributor = Distributor()

        role = distributor.route(task, failure_count=3)

        assert role.role == "fixer"
        assert role.model_tier == "powerful"


class TestDistributorModelTiers:
    """Test Distributor model tier management."""

    def test_get_model_tier_index(self):
        """Test getting index of model tier in hierarchy."""
        distributor = Distributor()

        assert distributor.get_model_tier_index("fast") == 0
        assert distributor.get_model_tier_index("balanced") == 1
        assert distributor.get_model_tier_index("powerful") == 2

    def test_get_model_tier_index_invalid_raises(self):
        """Test that invalid tier raises ValueError."""
        distributor = Distributor()

        with pytest.raises(ValueError) as exc_info:
            distributor.get_model_tier_index("invalid_tier")

        assert "Unknown model tier" in str(exc_info.value)

    def test_model_tiers_hierarchy(self):
        """Test model tier hierarchy is defined correctly."""
        distributor = Distributor()

        assert distributor.model_tiers == ["fast", "balanced", "powerful"]


class TestDistributorIntegration:
    """Integration tests for Distributor."""

    def test_complete_escalation_ladder(self):
        """Test complete escalation ladder from worker to fixer."""
        task = Task(
            "task_001",
            "Difficult task",
            "worker",
            [],
            {},
            ["result"],
            {"type": "build"},
            {},
        )
        distributor = Distributor()

        # No failures: balanced worker
        role0 = distributor.route(task, failure_count=0)
        assert (role0.role, role0.model_tier) == ("worker", "balanced")

        # 1 failure: powerful worker
        role1 = distributor.route(task, failure_count=1)
        assert (role1.role, role1.model_tier) == ("worker", "powerful")

        # 2+ failures: powerful fixer
        role2 = distributor.route(task, failure_count=2)
        assert (role2.role, role2.model_tier) == ("fixer", "powerful")

        role5 = distributor.route(task, failure_count=5)
        assert (role5.role, role5.model_tier) == ("fixer", "powerful")

    def test_route_returns_agent_role_dataclass(self):
        """Test that route returns properly structured AgentRole."""
        task = Task(
            "task_001",
            "Test task",
            "worker",
            [],
            {},
            ["out"],
            {"type": "build"},
            {},
        )
        distributor = Distributor()

        role = distributor.route(task, failure_count=0)

        assert isinstance(role, AgentRole)
        assert hasattr(role, "role")
        assert hasattr(role, "model_tier")
        assert hasattr(role, "reason")
        assert isinstance(role.role, str)
        assert isinstance(role.model_tier, str)
        assert isinstance(role.reason, str)
