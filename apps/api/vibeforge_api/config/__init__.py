"""Configuration module for VibeForge.

Provides typed configuration loading and validation for:
- Stack presets (commands, platform, runtime)
- Command policies (allowlists, network rules)
- Forbidden patterns and path constraints
"""

from vibeforge_api.config.loader import (
    ConfigLoader,
    get_config_loader,
    get_policy_config,
    get_stack_preset,
    list_available_stacks,
    load_config,
)
from vibeforge_api.config.models import (
    CommandSpec,
    NetworkAccess,
    PolicyConfig,
    StackPreset,
    VibeForgeConfig,
)

__all__ = [
    # Loader functions
    "load_config",
    "get_config_loader",
    "get_stack_preset",
    "get_policy_config",
    "list_available_stacks",
    # Loader class
    "ConfigLoader",
    # Models
    "VibeForgeConfig",
    "StackPreset",
    "PolicyConfig",
    "CommandSpec",
    "NetworkAccess",
]
