"""Configuration models for VibeForge.

This module defines typed configuration models for:
- Stack presets (commands, platform, runtime)
- Command policies (allowlists, network rules)
- Forbidden patterns and path constraints
"""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NetworkAccess(str, Enum):
    """Network access policy."""

    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


class PolicyConfig(BaseModel):
    """Command execution and safety policies."""

    network_access: NetworkAccess = Field(
        default=NetworkAccess.ASK,
        alias="networkAccess",
        description="Network access policy for commands",
    )
    allowed_command_families: list[str] = Field(
        default_factory=list,
        alias="allowedCommandFamilies",
        description="Allowed command family names (e.g., 'npm', 'node', 'git')",
    )
    forbidden_diff_regex: list[str] = Field(
        default_factory=list,
        alias="forbiddenDiffRegex",
        description="Regex patterns forbidden in diffs",
    )
    forbidden_paths: list[str] = Field(
        default_factory=list,
        alias="forbiddenPaths",
        description="Regex patterns for forbidden file paths",
    )

    model_config = ConfigDict(populate_by_name=True)  # Allow both alias and field name


class CommandSpec(BaseModel):
    """Command specification for a stack preset."""

    install: Optional[list[str]] = Field(
        default=None,
        description="Command to install dependencies",
    )
    dev: Optional[list[str]] = Field(
        default=None,
        description="Command to start development server",
    )
    build: Optional[list[str]] = Field(
        default=None,
        description="Command to build the project",
    )
    test: Optional[list[str]] = Field(
        default=None,
        description="Command to run tests",
    )


class StackPreset(BaseModel):
    """Stack preset configuration."""

    id: str = Field(
        ...,
        description="Unique identifier for this stack preset",
    )
    platform: str = Field(
        ...,
        description="Platform type (e.g., 'web', 'cli', 'mobile')",
    )
    runtime: str = Field(
        ...,
        description="Runtime environment (e.g., 'node', 'python', 'go')",
    )
    package_manager: Optional[str] = Field(
        default=None,
        alias="packageManager",
        description="Package manager (e.g., 'npm', 'pip', 'cargo')",
    )
    commands: CommandSpec = Field(
        ...,
        description="Commands for common operations",
    )
    scaffold: Optional[dict[str, Any]] = Field(
        default=None,
        description="Scaffolding configuration or notes",
    )

    model_config = ConfigDict(populate_by_name=True)  # Allow both alias and field name

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate stack preset ID format."""
        if not v or not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(f"Invalid stack preset ID: {v}")
        return v


class VibeForgeConfig(BaseModel):
    """Root configuration model."""

    stacks: dict[str, StackPreset] = Field(
        default_factory=dict,
        description="Stack presets indexed by ID",
    )
    policies: PolicyConfig = Field(
        default_factory=PolicyConfig,
        description="Command policies and safety rules",
    )

    def get_stack(self, stack_id: str) -> Optional[StackPreset]:
        """Get a stack preset by ID.

        Args:
            stack_id: Stack preset identifier

        Returns:
            StackPreset if found, None otherwise
        """
        return self.stacks.get(stack_id)

    def list_stack_ids(self) -> list[str]:
        """List all available stack preset IDs.

        Returns:
            List of stack IDs
        """
        return list(self.stacks.keys())
