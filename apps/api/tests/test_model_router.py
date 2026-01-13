"""Tests for ModelRouter (VF-063)."""

import pytest
from pathlib import Path

from models.router import ModelRouter, RoutingContext, get_model_router


class TestRoutingContext:
    """Test RoutingContext dataclass."""

    def test_routing_context_creation(self):
        """Test creating routing context."""
        context = RoutingContext(
            role="worker",
            complexity="simple",
            failure_count=0
        )

        assert context.role == "worker"
        assert context.complexity == "simple"
        assert context.failure_count == 0
        assert context.metadata is None

    def test_routing_context_with_metadata(self):
        """Test routing context with metadata."""
        context = RoutingContext(
            role="orchestrator",
            complexity="complex",
            failure_count=2,
            metadata={"task_id": "task-123"}
        )

        assert context.metadata == {"task_id": "task-123"}

    def test_routing_context_defaults(self):
        """Test routing context default values."""
        context = RoutingContext(role="fixer")

        assert context.role == "fixer"
        assert context.complexity == "medium"  # Default
        assert context.failure_count == 0  # Default


class TestModelRouter:
    """Test ModelRouter implementation."""

    def test_router_initialization_with_config(self):
        """Test router initialization with explicit config."""
        config = {
            "routing_rules": {
                "worker": {
                    "simple": {"provider": "openai", "model": "gpt-4o-mini"}
                }
            },
            "escalation_rules": {},
            "default_provider": "openai",
            "default_model": "gpt-4o-mini"
        }

        router = ModelRouter(routing_config=config)

        assert router.default_provider == "openai"
        assert router.default_model == "gpt-4o-mini"

    def test_router_initialization_from_file(self):
        """Test router initialization from config file."""
        config_path = Path(__file__).parent.parent.parent.parent / "configs" / "models" / "routing.json"

        if config_path.exists():
            router = ModelRouter(config_path=config_path)
            assert router.routing_rules is not None
            assert "orchestrator" in router.routing_rules

    def test_select_model_for_worker_simple(self):
        """Test VF-063: routing for worker role with simple complexity."""
        config = {
            "routing_rules": {
                "worker": {
                    "simple": {"provider": "openai", "model": "gpt-4o-mini"},
                    "complex": {"provider": "openai", "model": "gpt-4o"}
                }
            },
            "escalation_rules": {},
            "default_provider": "openai",
            "default_model": "gpt-4o-mini"
        }

        router = ModelRouter(routing_config=config)
        context = RoutingContext(role="worker", complexity="simple")

        provider, model = router.select_model(context)

        assert provider == "openai"
        assert model == "gpt-4o-mini"

    def test_select_model_for_worker_complex(self):
        """Test routing for worker role with complex complexity."""
        config = {
            "routing_rules": {
                "worker": {
                    "simple": {"provider": "openai", "model": "gpt-4o-mini"},
                    "complex": {"provider": "openai", "model": "gpt-4o"}
                }
            },
            "escalation_rules": {},
            "default_provider": "openai",
            "default_model": "gpt-4o-mini"
        }

        router = ModelRouter(routing_config=config)
        context = RoutingContext(role="worker", complexity="complex")

        provider, model = router.select_model(context)

        assert provider == "openai"
        assert model == "gpt-4o"

    def test_select_model_for_orchestrator(self):
        """Test routing for orchestrator role."""
        config = {
            "routing_rules": {
                "orchestrator": {
                    "medium": {"provider": "openai", "model": "gpt-4o"}
                }
            },
            "escalation_rules": {},
            "default_provider": "openai",
            "default_model": "gpt-4o-mini"
        }

        router = ModelRouter(routing_config=config)
        context = RoutingContext(role="orchestrator", complexity="medium")

        provider, model = router.select_model(context)

        assert provider == "openai"
        assert model == "gpt-4o"

    def test_select_model_for_reviewer(self):
        """Test routing for reviewer role (should use stronger model)."""
        config = {
            "routing_rules": {
                "reviewer": {
                    "simple": {"provider": "openai", "model": "gpt-4o"}
                }
            },
            "escalation_rules": {},
            "default_provider": "openai",
            "default_model": "gpt-4o-mini"
        }

        router = ModelRouter(routing_config=config)
        context = RoutingContext(role="reviewer", complexity="simple")

        provider, model = router.select_model(context)

        assert provider == "openai"
        assert model == "gpt-4o"

    def test_select_model_fallback_to_default(self):
        """Test fallback to default when no routing rule matches."""
        config = {
            "routing_rules": {},
            "escalation_rules": {},
            "default_provider": "openai",
            "default_model": "gpt-4o-mini"
        }

        router = ModelRouter(routing_config=config)
        context = RoutingContext(role="unknown-role", complexity="simple")

        provider, model = router.select_model(context)

        assert provider == "openai"
        assert model == "gpt-4o-mini"

    def test_escalation_on_first_failure(self):
        """Test VF-063: escalation to stronger model after first failure."""
        config = {
            "routing_rules": {
                "worker": {
                    "simple": {"provider": "openai", "model": "gpt-4o-mini"}
                }
            },
            "escalation_rules": {
                "failure_thresholds": [
                    {"min_failures": 0, "max_failures": 0, "action": "use_configured_model"},
                    {"min_failures": 1, "max_failures": 2, "action": "escalate_to_gpt4o"}
                ]
            },
            "default_provider": "openai",
            "default_model": "gpt-4o-mini"
        }

        router = ModelRouter(routing_config=config)
        context = RoutingContext(role="worker", complexity="simple", failure_count=1)

        provider, model = router.select_model(context)

        assert provider == "openai"
        assert model == "gpt-4o"  # Escalated

    def test_escalation_on_multiple_failures(self):
        """Test escalation with multiple failures."""
        config = {
            "routing_rules": {
                "fixer": {
                    "medium": {"provider": "openai", "model": "gpt-4o-mini"}
                }
            },
            "escalation_rules": {
                "failure_thresholds": [
                    {"min_failures": 0, "max_failures": 0, "action": "use_configured_model"},
                    {"min_failures": 1, "max_failures": 999, "action": "escalate_to_gpt4o"}
                ]
            },
            "default_provider": "openai",
            "default_model": "gpt-4o-mini"
        }

        router = ModelRouter(routing_config=config)
        context = RoutingContext(role="fixer", complexity="medium", failure_count=3)

        provider, model = router.select_model(context)

        assert provider == "openai"
        assert model == "gpt-4o"

    def test_no_escalation_on_zero_failures(self):
        """Test that no escalation occurs when failure_count is 0."""
        config = {
            "routing_rules": {
                "worker": {
                    "simple": {"provider": "openai", "model": "gpt-4o-mini"}
                }
            },
            "escalation_rules": {
                "failure_thresholds": [
                    {"min_failures": 0, "max_failures": 0, "action": "use_configured_model"},
                    {"min_failures": 1, "max_failures": 999, "action": "escalate_to_gpt4o"}
                ]
            },
            "default_provider": "openai",
            "default_model": "gpt-4o-mini"
        }

        router = ModelRouter(routing_config=config)
        context = RoutingContext(role="worker", complexity="simple", failure_count=0)

        provider, model = router.select_model(context)

        assert provider == "openai"
        assert model == "gpt-4o-mini"  # Not escalated

    def test_get_escalation_temperature_default(self):
        """Test escalation temperature for zero failures."""
        router = ModelRouter()
        temp = router.get_escalation_temperature(failure_count=0)

        assert temp == 0.7  # Default

    def test_get_escalation_temperature_after_failures(self):
        """Test escalation temperature increases with failures."""
        router = ModelRouter()

        temp1 = router.get_escalation_temperature(failure_count=1)
        temp2 = router.get_escalation_temperature(failure_count=2)
        temp3 = router.get_escalation_temperature(failure_count=3)

        assert temp1 == 0.8
        assert temp2 == 0.8
        assert temp3 == 0.9

    def test_global_router_singleton(self):
        """Test that get_model_router returns singleton instance."""
        router1 = get_model_router()
        router2 = get_model_router()

        assert router1 is router2

    def test_routing_all_roles(self):
        """Test routing for all defined roles."""
        config_path = Path(__file__).parent.parent.parent.parent / "configs" / "models" / "routing.json"

        if config_path.exists():
            router = ModelRouter(config_path=config_path)
            roles = ["orchestrator", "worker", "foreman", "fixer", "reviewer"]

            for role in roles:
                context = RoutingContext(role=role, complexity="simple")
                provider, model = router.select_model(context)

                assert provider is not None
                assert model is not None


class TestForcedModelRouting:
    """Tests for VF-194: forced model override for workflow simulation mode."""

    def test_forced_model_with_provider(self):
        """Test forced_model with explicit provider:model format."""
        config = {
            "routing_rules": {
                "worker": {
                    "simple": {"provider": "openai", "model": "gpt-4o-mini"}
                }
            },
            "default_provider": "openai",
            "default_model": "gpt-4o-mini"
        }

        router = ModelRouter(routing_config=config)
        context = RoutingContext(
            role="worker",
            complexity="simple",
            forced_model="openai:gpt-4-turbo"
        )

        provider, model = router.select_model(context)

        assert provider == "openai"
        assert model == "gpt-4-turbo"  # Forced model used instead of routing rule

    def test_forced_model_without_provider(self):
        """Test forced_model with just model name (provider inferred)."""
        config = {
            "routing_rules": {
                "worker": {
                    "simple": {"provider": "openai", "model": "gpt-4o-mini"}
                }
            },
            "default_provider": "openai",
            "default_model": "gpt-4o-mini"
        }

        router = ModelRouter(routing_config=config)
        context = RoutingContext(
            role="worker",
            complexity="simple",
            forced_model="gpt-4o"  # No provider specified
        )

        provider, model = router.select_model(context)

        assert provider == "openai"  # Inferred from "gpt-" prefix
        assert model == "gpt-4o"

    def test_forced_model_claude(self):
        """Test forced_model with Claude model."""
        router = ModelRouter()
        context = RoutingContext(
            role="worker",
            forced_model="claude-3-opus"
        )

        provider, model = router.select_model(context)

        assert provider == "anthropic"
        assert model == "claude-3-opus"

    def test_forced_model_local(self):
        """Test forced_model with local model."""
        router = ModelRouter()
        context = RoutingContext(
            role="worker",
            forced_model="local:llama-3"
        )

        provider, model = router.select_model(context)

        assert provider == "local"
        assert model == "llama-3"

    def test_forced_model_invalid_falls_back(self):
        """Test invalid forced_model falls back to normal routing."""
        config = {
            "routing_rules": {
                "worker": {
                    "simple": {"provider": "openai", "model": "gpt-4o-mini"}
                }
            },
            "default_provider": "openai",
            "default_model": "gpt-4o-mini"
        }

        router = ModelRouter(routing_config=config)
        context = RoutingContext(
            role="worker",
            complexity="simple",
            forced_model="nonexistent-model-xyz"
        )

        provider, model = router.select_model(context)

        # Should fall back to routing rule since forced_model is invalid
        assert provider == "openai"
        assert model == "gpt-4o-mini"

    def test_forced_model_overrides_escalation(self):
        """Test forced_model takes precedence over escalation rules."""
        config = {
            "routing_rules": {
                "worker": {
                    "simple": {"provider": "openai", "model": "gpt-4o-mini"}
                }
            },
            "escalation_rules": {
                "failure_thresholds": [
                    {"min_failures": 1, "max_failures": 999, "action": "escalate_to_gpt4o"}
                ]
            },
            "default_provider": "openai",
            "default_model": "gpt-4o-mini"
        }

        router = ModelRouter(routing_config=config)
        context = RoutingContext(
            role="worker",
            complexity="simple",
            failure_count=2,  # Would normally trigger escalation
            forced_model="gpt-3.5-turbo"  # But forced_model overrides
        )

        provider, model = router.select_model(context)

        assert provider == "openai"
        assert model == "gpt-3.5-turbo"  # Forced model, not escalated

    def test_forced_model_empty_string_ignored(self):
        """Test empty forced_model string is ignored."""
        config = {
            "routing_rules": {
                "worker": {
                    "simple": {"provider": "openai", "model": "gpt-4o-mini"}
                }
            },
            "default_provider": "openai",
            "default_model": "gpt-4o-mini"
        }

        router = ModelRouter(routing_config=config)
        context = RoutingContext(
            role="worker",
            complexity="simple",
            forced_model=""  # Empty string
        )

        provider, model = router.select_model(context)

        # Should use normal routing
        assert provider == "openai"
        assert model == "gpt-4o-mini"

    def test_forced_model_with_whitespace(self):
        """Test forced_model handles whitespace correctly."""
        router = ModelRouter()
        context = RoutingContext(
            role="worker",
            forced_model="  openai:gpt-4o  "  # Whitespace around value
        )

        provider, model = router.select_model(context)

        assert provider == "openai"
        assert model == "gpt-4o"

    def test_infer_provider_gpt_models(self):
        """Test provider inference for GPT models."""
        router = ModelRouter()

        assert router._infer_provider("gpt-4") == "openai"
        assert router._infer_provider("gpt-4o-mini") == "openai"
        assert router._infer_provider("o1-preview") == "openai"

    def test_infer_provider_claude_models(self):
        """Test provider inference for Claude models."""
        router = ModelRouter()

        assert router._infer_provider("claude-3-opus") == "anthropic"
        assert router._infer_provider("claude-3-5-sonnet") == "anthropic"

    def test_infer_provider_local_models(self):
        """Test provider inference for local models."""
        router = ModelRouter()

        assert router._infer_provider("llama-3") == "local"
        assert router._infer_provider("mixtral-8x7b") == "local"
        assert router._infer_provider("local-llama") == "local"

    def test_is_valid_model_openai(self):
        """Test model validation for OpenAI models."""
        router = ModelRouter()

        assert router._is_valid_model("openai", "gpt-4") is True
        assert router._is_valid_model("openai", "gpt-4o") is True
        assert router._is_valid_model("openai", "invalid-model") is False

    def test_is_valid_model_anthropic(self):
        """Test model validation for Anthropic models."""
        router = ModelRouter()

        assert router._is_valid_model("anthropic", "claude-3-opus") is True
        assert router._is_valid_model("anthropic", "claude-3-sonnet") is True
        assert router._is_valid_model("anthropic", "invalid-model") is False

    def test_is_valid_model_local(self):
        """Test model validation for local models."""
        router = ModelRouter()

        assert router._is_valid_model("local", "llama-3") is True
        assert router._is_valid_model("local", "mixtral-8x7b") is True
        assert router._is_valid_model("local", "invalid-model") is False
