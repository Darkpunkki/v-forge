"""Model routing logic for selecting appropriate models based on context.

VF-063: Route model calls based on role, complexity, and failure history.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class RoutingContext:
    """Context information for routing decisions.

    Attributes:
        role: Agent role (orchestrator, worker, foreman, fixer, reviewer)
        complexity: Task complexity (simple, medium, complex)
        failure_count: Number of previous failures (for escalation)
        forced_model: Optional model override for workflow simulation mode (VF-194)
        metadata: Optional additional context
    """
    role: str
    complexity: str = "medium"
    failure_count: int = 0
    forced_model: Optional[str] = None
    metadata: Optional[dict] = None


class ModelRouter:
    """Routes model requests based on role, complexity, and failure history.

    VF-063: Implements routing policy that selects models based on:
    - Agent role (different roles need different capabilities)
    - Task complexity (simple tasks can use smaller models)
    - Failure count (escalate to stronger models on retries)
    """

    def __init__(
        self, routing_config: Optional[dict] = None, config_path: Optional[Path] = None
    ):
        """Initialize router with configuration.

        Args:
            routing_config: Routing configuration dict (if provided, overrides file)
            config_path: Path to routing.json config file (default: configs/models/routing.json)
        """
        env_config_path = os.getenv("VIBEFORGE_MODEL_ROUTING_CONFIG")
        if routing_config:
            self.config = routing_config
        elif env_config_path:
            config_file = Path(env_config_path)
            if config_file.exists():
                with open(config_file, "r") as f:
                    self.config = json.load(f)
            else:
                raise FileNotFoundError(
                    f"Model routing config not found: {config_file}"
                )
        elif config_path:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        else:
            # Default config path
            default_path = Path(__file__).parent.parent / "configs" / "models" / "routing.json"
            if default_path.exists():
                with open(default_path, 'r') as f:
                    self.config = json.load(f)
            else:
                # Minimal fallback config
                self.config = {
                    "routing_rules": {},
                    "escalation_rules": {"failure_thresholds": []},
                    "default_provider": "openai",
                    "default_model": "gpt-4o-mini"
                }

        self.routing_rules = self.config.get("routing_rules", {})
        self.escalation_rules = self.config.get("escalation_rules", {})
        self.default_provider = self.config.get("default_provider", "openai")
        self.default_model = self.config.get("default_model", "gpt-4o-mini")

        provider_override = os.getenv("VIBEFORGE_MODEL_PROVIDER")
        model_override = os.getenv("VIBEFORGE_MODEL")
        if provider_override or model_override:
            self._apply_overrides(
                provider_override=provider_override, model_override=model_override
            )

    def _apply_overrides(
        self,
        provider_override: Optional[str] = None,
        model_override: Optional[str] = None,
    ) -> None:
        if provider_override:
            self.default_provider = provider_override
        if model_override:
            self.default_model = model_override

        for _, role_rules in self.routing_rules.items():
            for _, rule in role_rules.items():
                if provider_override:
                    rule["provider"] = provider_override
                if model_override:
                    rule["model"] = model_override

    def select_model(self, context: RoutingContext) -> tuple[str, str]:
        """Select appropriate model based on routing context.

        Args:
            context: Routing context with role, complexity, failure count

        Returns:
            Tuple of (provider_name, model_name)
        """
        # VF-194: Check for forced model override (workflow simulation mode)
        if context.forced_model:
            validated = self._validate_forced_model(context.forced_model)
            if validated:
                return validated
            # If validation fails, fall through to normal routing

        # Check for escalation due to failures
        if context.failure_count > 0:
            escalated = self._apply_escalation(context)
            if escalated:
                return escalated

        # Normal routing based on role and complexity
        role_rules = self.routing_rules.get(context.role, {})
        complexity_rule = role_rules.get(context.complexity, {})

        if complexity_rule:
            provider = complexity_rule.get("provider", self.default_provider)
            model = complexity_rule.get("model", self.default_model)
            return (provider, model)

        # Fallback to default
        return (self.default_provider, self.default_model)

    def _validate_forced_model(self, forced_model: str) -> Optional[tuple[str, str]]:
        """Validate and parse forced model string (VF-194).

        Args:
            forced_model: Model string (format: "provider:model" or "model")

        Returns:
            Tuple of (provider, model) if valid, None if invalid
        """
        if not forced_model or not forced_model.strip():
            return None

        # Parse provider:model format
        if ":" in forced_model:
            parts = forced_model.split(":", 1)
            provider = parts[0].strip()
            model = parts[1].strip()
        else:
            # No provider specified, infer from model name
            model = forced_model.strip()
            provider = self._infer_provider(model)

        # Validate the model name exists in known models
        if self._is_valid_model(provider, model):
            return (provider, model)

        # Invalid model - return None to fall through to normal routing
        return None

    def _infer_provider(self, model: str) -> str:
        """Infer provider from model name (VF-194).

        Args:
            model: Model name (e.g., "gpt-4", "claude-3-opus")

        Returns:
            Provider name
        """
        model_lower = model.lower()
        if model_lower.startswith("gpt-") or model_lower.startswith("o1-"):
            return "openai"
        elif model_lower.startswith("claude-"):
            return "anthropic"
        elif "llama" in model_lower or "mixtral" in model_lower or "local" in model_lower:
            return "local"
        else:
            # Default fallback
            return self.default_provider

    def _is_valid_model(self, provider: str, model: str) -> bool:
        """Check if provider:model combination is valid (VF-194).

        Args:
            provider: Provider name
            model: Model name

        Returns:
            True if valid, False otherwise
        """
        # Common known models
        known_models = {
            "openai": ["gpt-4", "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "o1-preview", "o1-mini"],
            "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "claude-3-5-sonnet"],
            "local": ["local-llama", "local-mixtral", "llama-3", "llama-2", "mixtral-8x7b"],
        }

        provider_models = known_models.get(provider, [])
        return model in provider_models

    def _apply_escalation(self, context: RoutingContext) -> Optional[tuple[str, str]]:
        """Apply escalation rules based on failure count.

        Args:
            context: Routing context with failure count

        Returns:
            Tuple of (provider, model) if escalation applies, None otherwise
        """
        thresholds = self.escalation_rules.get("failure_thresholds", [])

        for threshold in thresholds:
            min_failures = threshold.get("min_failures", 0)
            max_failures = threshold.get("max_failures", 999)

            if min_failures <= context.failure_count <= max_failures:
                action = threshold.get("action", "use_configured_model")

                if action == "escalate_to_gpt4o":
                    return ("openai", "gpt-4o")
                elif action == "escalate_to_gpt4o_high_temp":
                    # Caller should handle temperature adjustment
                    return ("openai", "gpt-4o")
                elif action == "use_configured_model":
                    # Continue to normal routing
                    return None

        return None

    def get_escalation_temperature(self, failure_count: int) -> float:
        """Get recommended temperature based on failure count.

        Higher temperatures on retries can help avoid repeating the same mistake.

        Args:
            failure_count: Number of previous failures

        Returns:
            Recommended temperature (0.0 to 1.0)
        """
        if failure_count == 0:
            return 0.7  # Default temperature
        elif failure_count <= 2:
            return 0.8  # Slightly higher
        else:
            return 0.9  # High temperature for desperate retries


# Global router instance (lazy-loaded)
_router_instance: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    """Get global ModelRouter instance (singleton pattern).

    Returns:
        Global ModelRouter instance
    """
    global _router_instance
    if _router_instance is None:
        _router_instance = ModelRouter()
    return _router_instance
