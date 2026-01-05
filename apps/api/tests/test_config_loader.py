"""Tests for configuration loader."""

import json
import pytest
from pathlib import Path

from vibeforge_api.config import (
    ConfigLoader,
    NetworkAccess,
    PolicyConfig,
    StackPreset,
    VibeForgeConfig,
    get_policy_config,
    get_stack_preset,
    list_available_stacks,
    load_config,
)


def test_load_config_from_project_root(tmp_path):
    """Test loading config from project root configs/ directory."""
    # Use the real config directory
    loader = ConfigLoader()
    config = loader.load()

    assert isinstance(config, VibeForgeConfig)
    assert isinstance(config.policies, PolicyConfig)
    assert isinstance(config.stacks, dict)


def test_load_stack_presets(tmp_path):
    """Test loading stack presets from JSON files."""
    # Create test config directory
    stacks_dir = tmp_path / "stacks"
    stacks_dir.mkdir()

    # Create test stack file
    stack_data = {
        "id": "test_stack",
        "platform": "web",
        "runtime": "node",
        "packageManager": "npm",
        "commands": {
            "install": ["npm", "install"],
            "build": ["npm", "run", "build"],
            "test": ["npm", "test"],
        },
    }

    with open(stacks_dir / "test_stack.json", "w") as f:
        json.dump(stack_data, f)

    # Load and validate
    loader = ConfigLoader(config_dir=tmp_path)
    config = loader.load()

    assert "test_stack" in config.stacks
    stack = config.stacks["test_stack"]
    assert stack.id == "test_stack"
    assert stack.platform == "web"
    assert stack.runtime == "node"
    assert stack.package_manager == "npm"
    assert stack.commands.install == ["npm", "install"]


def test_load_policies_config(tmp_path):
    """Test loading policy configuration."""
    # Create test config directory
    policies_dir = tmp_path / "policies"
    policies_dir.mkdir()

    # Create test policy file
    policy_data = {
        "networkAccess": "deny",
        "allowedCommandFamilies": ["npm", "git"],
        "forbiddenDiffRegex": [r"rm\s+-rf", r"eval\("],
        "forbiddenPaths": [r"^/", r"\.\./"],
    }

    with open(policies_dir / "default.json", "w") as f:
        json.dump(policy_data, f)

    # Load and validate
    loader = ConfigLoader(config_dir=tmp_path)
    config = loader.load()

    assert config.policies.network_access == NetworkAccess.DENY
    assert config.policies.allowed_command_families == ["npm", "git"]
    assert len(config.policies.forbidden_diff_regex) == 2
    assert len(config.policies.forbidden_paths) == 2


def test_policy_defaults_when_no_file(tmp_path):
    """Test that policy defaults are used when no config file exists."""
    loader = ConfigLoader(config_dir=tmp_path)
    config = loader.load()

    # Should use default values
    assert config.policies.network_access == NetworkAccess.ASK
    assert config.policies.allowed_command_families == []


def test_config_caching():
    """Test that config is cached and not reloaded unnecessarily."""
    loader = ConfigLoader()

    config1 = loader.load()
    config2 = loader.load()

    # Should return the same cached instance
    assert config1 is config2


def test_config_reload():
    """Test that reload() forces a fresh load."""
    loader = ConfigLoader()

    config1 = loader.load()
    config2 = loader.reload()

    # Should return new instance after reload
    assert config1 is not config2


def test_invalid_stack_json(tmp_path):
    """Test that invalid stack JSON raises error."""
    stacks_dir = tmp_path / "stacks"
    stacks_dir.mkdir()

    # Create invalid JSON file
    with open(stacks_dir / "invalid.json", "w") as f:
        f.write("{invalid json")

    loader = ConfigLoader(config_dir=tmp_path)

    with pytest.raises(ValueError, match="Failed to load stack preset"):
        loader.load()


def test_duplicate_stack_ids(tmp_path):
    """Test that duplicate stack IDs raise error."""
    stacks_dir = tmp_path / "stacks"
    stacks_dir.mkdir()

    # Create two stack files with same ID
    stack_data = {
        "id": "duplicate",
        "platform": "web",
        "runtime": "node",
        "commands": {},
    }

    with open(stacks_dir / "stack1.json", "w") as f:
        json.dump(stack_data, f)

    with open(stacks_dir / "stack2.json", "w") as f:
        json.dump(stack_data, f)

    loader = ConfigLoader(config_dir=tmp_path)

    with pytest.raises(ValueError, match="Duplicate stack ID"):
        loader.load()


def test_invalid_stack_id_format():
    """Test that invalid stack ID format is rejected."""
    with pytest.raises(ValueError, match="Invalid stack preset ID"):
        StackPreset(
            id="invalid id with spaces",
            platform="web",
            runtime="node",
            commands={},
        )


def test_get_stack_preset():
    """Test getting a specific stack preset."""
    stack = get_stack_preset("web_vite_react")

    if stack:
        assert stack.id == "web_vite_react"
        assert stack.platform == "web"
        assert stack.runtime == "node"


def test_get_nonexistent_stack():
    """Test getting a nonexistent stack returns None."""
    stack = get_stack_preset("nonexistent_stack_12345")
    assert stack is None


def test_list_available_stacks():
    """Test listing all available stack presets."""
    stacks = list_available_stacks()

    assert isinstance(stacks, list)
    # Should contain at least the web_vite_react stack
    assert "web_vite_react" in stacks


def test_get_policy_config():
    """Test getting policy configuration."""
    policies = get_policy_config()

    assert isinstance(policies, PolicyConfig)
    assert isinstance(policies.network_access, NetworkAccess)


def test_config_dir_not_found():
    """Test that missing config directory raises error."""
    loader = ConfigLoader(config_dir=Path("/nonexistent/path/12345"))

    with pytest.raises(FileNotFoundError, match="Config directory not found"):
        loader.load()


def test_stack_commands_optional_fields(tmp_path):
    """Test that stack commands can have optional fields."""
    stacks_dir = tmp_path / "stacks"
    stacks_dir.mkdir()

    # Create stack with only some commands
    stack_data = {
        "id": "minimal_stack",
        "platform": "cli",
        "runtime": "python",
        "commands": {
            "test": ["pytest"],
        },
    }

    with open(stacks_dir / "minimal.json", "w") as f:
        json.dump(stack_data, f)

    loader = ConfigLoader(config_dir=tmp_path)
    config = loader.load()

    stack = config.stacks["minimal_stack"]
    assert stack.commands.test == ["pytest"]
    assert stack.commands.install is None
    assert stack.commands.build is None


def test_network_access_enum_values():
    """Test NetworkAccess enum values."""
    assert NetworkAccess.ALLOW == "allow"
    assert NetworkAccess.DENY == "deny"
    assert NetworkAccess.ASK == "ask"


def test_policy_config_aliases():
    """Test that PolicyConfig accepts both snake_case and camelCase."""
    # Test with camelCase (from JSON)
    policy1 = PolicyConfig(
        networkAccess="allow",
        allowedCommandFamilies=["npm"],
        forbiddenDiffRegex=[r"rm\s+-rf"],
        forbiddenPaths=[r"^/"],
    )

    # Test with snake_case (Python style)
    policy2 = PolicyConfig(
        network_access="allow",
        allowed_command_families=["npm"],
        forbidden_diff_regex=[r"rm\s+-rf"],
        forbidden_paths=[r"^/"],
    )

    assert policy1.network_access == policy2.network_access
    assert policy1.allowed_command_families == policy2.allowed_command_families


def test_stack_preset_aliases():
    """Test that StackPreset accepts both snake_case and camelCase."""
    # Test with camelCase
    stack1 = StackPreset(
        id="test",
        platform="web",
        runtime="node",
        packageManager="npm",
        commands={},
    )

    # Test with snake_case
    stack2 = StackPreset(
        id="test",
        platform="web",
        runtime="node",
        package_manager="npm",
        commands={},
    )

    assert stack1.package_manager == stack2.package_manager


def test_vibe_forge_config_get_stack():
    """Test VibeForgeConfig.get_stack method."""
    config = load_config()

    # Test existing stack
    stack = config.get_stack("web_vite_react")
    if stack:
        assert stack.id == "web_vite_react"

    # Test nonexistent stack
    nonexistent = config.get_stack("does_not_exist")
    assert nonexistent is None


def test_vibe_forge_config_list_stack_ids():
    """Test VibeForgeConfig.list_stack_ids method."""
    config = load_config()

    ids = config.list_stack_ids()
    assert isinstance(ids, list)
    assert "web_vite_react" in ids
