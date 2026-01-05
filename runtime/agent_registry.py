"""
AgentRegistry: Central registry for agent role configurations.

VF-102: Maps roles to prompts, tool permissions, and output schemas
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class RoleConfig:
    """Configuration for an agent role."""

    role: str
    system_prompt: str
    prompt_template: str
    output_schema: dict[str, Any]
    allowed_tools: list[str]


class AgentRegistry:
    """
    VF-102: Central registry for agent role configurations.

    Maps roles to prompts, tool permissions, and output schemas.
    Ensures consistent agent behavior across the system.
    """

    def __init__(self):
        """Initialize with default role configurations."""
        self.roles: dict[str, RoleConfig] = {
            "worker": RoleConfig(
                role="worker",
                system_prompt="You are a software development agent. Implement the requested task precisely following best practices.",
                prompt_template=(
                    "Task ID: {task_id}\n"
                    "Description: {description}\n"
                    "Expected outputs: {expected_outputs}\n\n"
                    "Context: {context}\n\n"
                    "Implement this task and return the result as JSON with 'files' (array of file paths) and 'summary' (string)."
                ),
                output_schema={
                    "type": "object",
                    "properties": {
                        "files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Files created or modified",
                        },
                        "summary": {
                            "type": "string",
                            "minLength": 10,
                            "description": "Summary of work completed",
                        },
                    },
                    "required": ["files", "summary"],
                    "additionalProperties": False,
                },
                allowed_tools=["read", "write", "bash", "glob", "grep"],
            ),
            "foreman": RoleConfig(
                role="foreman",
                system_prompt="You are a planning and coordination agent. Break down complex tasks into manageable steps.",
                prompt_template=(
                    "Task ID: {task_id}\n"
                    "Description: {description}\n\n"
                    "Context: {context}\n\n"
                    "Plan the implementation approach. Return JSON with 'plan' (array of step descriptions) and 'dependencies' (array of dependency descriptions)."
                ),
                output_schema={
                    "type": "object",
                    "properties": {
                        "plan": {
                            "type": "array",
                            "items": {"type": "string", "minLength": 10},
                            "minItems": 1,
                            "description": "Implementation plan steps",
                        },
                        "dependencies": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "External dependencies or requirements",
                        },
                    },
                    "required": ["plan"],
                    "additionalProperties": False,
                },
                allowed_tools=["read", "glob", "grep"],
            ),
            "reviewer": RoleConfig(
                role="reviewer",
                system_prompt="You are a code review agent. Verify quality, correctness, and adherence to best practices.",
                prompt_template=(
                    "Task ID: {task_id}\n"
                    "Description: {description}\n\n"
                    "Context: {context}\n\n"
                    "Review the implementation. Return JSON with 'approved' (boolean), 'issues' (array of critical issues), and 'suggestions' (array of improvements)."
                ),
                output_schema={
                    "type": "object",
                    "properties": {
                        "approved": {
                            "type": "boolean",
                            "description": "Whether the implementation is approved",
                        },
                        "issues": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Critical issues found",
                        },
                        "suggestions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Improvement suggestions",
                        },
                    },
                    "required": ["approved"],
                    "additionalProperties": False,
                },
                allowed_tools=["read", "grep", "bash", "glob"],
            ),
            "fixer": RoleConfig(
                role="fixer",
                system_prompt="You are a debugging and fixing agent. Diagnose issues systematically and implement targeted fixes.",
                prompt_template=(
                    "Task ID: {task_id}\n"
                    "Description: {description}\n"
                    "Previous error: {context}\n\n"
                    "Diagnose the root cause and implement a fix. Return JSON with 'diagnosis' (string), 'fix_applied' (boolean), and 'files_modified' (array of file paths)."
                ),
                output_schema={
                    "type": "object",
                    "properties": {
                        "diagnosis": {
                            "type": "string",
                            "minLength": 20,
                            "description": "Root cause analysis",
                        },
                        "fix_applied": {
                            "type": "boolean",
                            "description": "Whether a fix was successfully applied",
                        },
                        "files_modified": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Files modified during fix",
                        },
                    },
                    "required": ["diagnosis", "fix_applied"],
                    "additionalProperties": False,
                },
                allowed_tools=["read", "write", "bash", "grep", "glob"],
            ),
        }

    def get_role_config(self, role: str) -> RoleConfig:
        """
        Get configuration for a role.

        Args:
            role: Agent role name

        Returns:
            RoleConfig for the role

        Raises:
            ValueError: If role is unknown
        """
        if role not in self.roles:
            raise ValueError(
                f"Unknown role: {role}. Available roles: {list(self.roles.keys())}"
            )
        return self.roles[role]

    def list_roles(self) -> list[str]:
        """
        Return list of registered roles.

        Returns:
            List of role names
        """
        return list(self.roles.keys())

    def register_role(self, role_config: RoleConfig) -> None:
        """
        Register a new role or update existing role configuration.

        Args:
            role_config: Role configuration to register
        """
        self.roles[role_config.role] = role_config

    def has_role(self, role: str) -> bool:
        """
        Check if a role is registered.

        Args:
            role: Role name to check

        Returns:
            True if role is registered
        """
        return role in self.roles


# Global registry instance
_agent_registry = None


def get_agent_registry() -> AgentRegistry:
    """
    Get global agent registry instance.

    Returns:
        Singleton AgentRegistry instance
    """
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry
