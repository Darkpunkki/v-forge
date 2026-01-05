"""Configuration loader for VibeForge.

This module provides utilities to load and validate configuration from files.
Supports JSON format for MVP, with future YAML support planned.
"""

import json
import os
from pathlib import Path
from typing import Optional

from vibeforge_api.config.models import PolicyConfig, StackPreset, VibeForgeConfig


class ConfigLoader:
    """Configuration loader with validation and caching."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize config loader.

        Args:
            config_dir: Path to configuration directory. Defaults to project root/configs/
        """
        if config_dir is None:
            # Default to project root/configs/
            self.config_dir = Path(__file__).parent.parent.parent.parent.parent / "configs"
        else:
            self.config_dir = config_dir

        self._cached_config: Optional[VibeForgeConfig] = None

    def load(self, reload: bool = False) -> VibeForgeConfig:
        """Load and validate configuration from files.

        Args:
            reload: Force reload even if cached

        Returns:
            Validated VibeForgeConfig

        Raises:
            FileNotFoundError: If config directory doesn't exist
            ValueError: If configuration is invalid
        """
        if self._cached_config is not None and not reload:
            return self._cached_config

        if not self.config_dir.exists():
            raise FileNotFoundError(f"Config directory not found: {self.config_dir}")

        # Load stacks
        stacks = self._load_stacks()

        # Load policies
        policies = self._load_policies()

        # Build and cache config
        config = VibeForgeConfig(stacks=stacks, policies=policies)
        self._cached_config = config

        return config

    def _load_stacks(self) -> dict[str, StackPreset]:
        """Load all stack presets from configs/stacks/*.json.

        Returns:
            Dictionary of stack presets indexed by ID

        Raises:
            ValueError: If stack configuration is invalid
        """
        stacks = {}
        stacks_dir = self.config_dir / "stacks"

        if not stacks_dir.exists():
            return stacks

        for stack_file in stacks_dir.glob("*.json"):
            try:
                with open(stack_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                stack = StackPreset(**data)

                if stack.id in stacks:
                    raise ValueError(
                        f"Duplicate stack ID '{stack.id}' in {stack_file}"
                    )

                stacks[stack.id] = stack

            except (json.JSONDecodeError, ValueError) as e:
                raise ValueError(
                    f"Failed to load stack preset from {stack_file}: {e}"
                ) from e

        return stacks

    def _load_policies(self) -> PolicyConfig:
        """Load policy configuration from configs/policies/default.json.

        Returns:
            PolicyConfig with defaults if file doesn't exist

        Raises:
            ValueError: If policy configuration is invalid
        """
        policies_file = self.config_dir / "policies" / "default.json"

        if not policies_file.exists():
            # Return default policy if no file exists
            return PolicyConfig()

        try:
            with open(policies_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            return PolicyConfig(**data)

        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(
                f"Failed to load policy configuration from {policies_file}: {e}"
            ) from e

    def reload(self) -> VibeForgeConfig:
        """Force reload configuration from disk.

        Returns:
            Reloaded VibeForgeConfig
        """
        return self.load(reload=True)


# Global config loader instance
_loader: Optional[ConfigLoader] = None


def get_config_loader() -> ConfigLoader:
    """Get the global config loader instance.

    Returns:
        ConfigLoader singleton
    """
    global _loader
    if _loader is None:
        _loader = ConfigLoader()
    return _loader


def load_config(reload: bool = False) -> VibeForgeConfig:
    """Load configuration using the global loader.

    Args:
        reload: Force reload even if cached

    Returns:
        VibeForgeConfig
    """
    loader = get_config_loader()
    return loader.load(reload=reload)


def get_stack_preset(stack_id: str) -> Optional[StackPreset]:
    """Get a stack preset by ID.

    Args:
        stack_id: Stack preset identifier

    Returns:
        StackPreset if found, None otherwise
    """
    config = load_config()
    return config.get_stack(stack_id)


def get_policy_config() -> PolicyConfig:
    """Get the policy configuration.

    Returns:
        PolicyConfig
    """
    config = load_config()
    return config.policies


def list_available_stacks() -> list[str]:
    """List all available stack preset IDs.

    Returns:
        List of stack IDs
    """
    config = load_config()
    return config.list_stack_ids()
