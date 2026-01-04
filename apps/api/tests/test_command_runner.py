"""Tests for CommandRunner."""

import sys
import time
from pathlib import Path

import pytest

from vibeforge_api.core.command_runner import CommandRunner, COMMAND_ALLOWLISTS


def test_command_runner_simple_command():
    """Test running a simple allowed command."""
    runner = CommandRunner()

    # Use echo command (universal)
    if sys.platform == "win32":
        result = runner.run_command("echo Hello", allowed_families=None)
    else:
        result = runner.run_command("echo 'Hello'", allowed_families=None)

    assert result.returncode == 0
    assert "Hello" in result.stdout
    assert result.timed_out is False
    assert result.duration >= 0


def test_command_runner_with_allowlist_allowed():
    """Test that allowed commands execute successfully."""
    runner = CommandRunner()

    # npm commands should be allowed with NODE_BUILD family
    result = runner.run_command(
        "npm --version", allowed_families=["NODE_BUILD"]
    )

    # Should execute (may fail if npm not installed, but shouldn't be blocked)
    assert result.command == "npm --version"
    # Don't assert returncode since npm might not be installed


def test_command_runner_with_allowlist_forbidden():
    """Test that forbidden commands are rejected."""
    runner = CommandRunner()

    # curl is not in NODE_BUILD allowlist
    with pytest.raises(ValueError, match="not allowed"):
        runner.run_command("curl https://example.com", allowed_families=["NODE_BUILD"])


def test_command_runner_timeout():
    """Test that commands timeout correctly."""
    runner = CommandRunner()

    # Use a sleep command that will timeout
    if sys.platform == "win32":
        # Windows: use timeout command (confusingly named)
        # Actually, let's use a Python one-liner for cross-platform compatibility
        cmd = 'python -c "import time; time.sleep(10)"'
    else:
        cmd = "sleep 10"

    result = runner.run_command(cmd, timeout=1, allowed_families=None)

    assert result.timed_out is True
    assert result.returncode == -1
    assert "timed out" in result.stderr.lower()


def test_command_runner_captures_stderr():
    """Test that stderr is captured."""
    runner = CommandRunner()

    # Python command that writes to stderr
    cmd = 'python -c "import sys; sys.stderr.write(\'Error message\\n\')"'

    result = runner.run_command(cmd, allowed_families=None)

    assert "Error message" in result.stderr


def test_command_runner_captures_stdout():
    """Test that stdout is captured."""
    runner = CommandRunner()

    # Python command that writes to stdout
    cmd = 'python -c "print(\'Output message\')"'

    result = runner.run_command(cmd, allowed_families=None)

    assert "Output message" in result.stdout


def test_command_runner_working_directory(tmp_path):
    """Test that working directory is respected."""
    runner = CommandRunner()

    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")

    # List directory contents
    if sys.platform == "win32":
        cmd = "dir /b"
    else:
        cmd = "ls"

    result = runner.run_command(cmd, cwd=tmp_path, allowed_families=None)

    assert result.returncode == 0
    assert "test.txt" in result.stdout


def test_command_runner_nonzero_exit():
    """Test command with non-zero exit code."""
    runner = CommandRunner()

    # Python command that exits with code 42
    cmd = 'python -c "import sys; sys.exit(42)"'

    result = runner.run_command(cmd, allowed_families=None)

    assert result.returncode == 42
    assert result.timed_out is False


def test_command_runner_duration_tracking():
    """Test that command duration is tracked."""
    runner = CommandRunner()

    start = time.time()
    if sys.platform == "win32":
        result = runner.run_command('python -c "import time; time.sleep(0.1)"', allowed_families=None)
    else:
        result = runner.run_command("sleep 0.1", allowed_families=None)
    elapsed = time.time() - start

    # Duration should be approximately the sleep time
    assert result.duration >= 0.1
    assert result.duration <= elapsed + 0.1  # Small margin for overhead


def test_command_allowlist_node_build():
    """Test NODE_BUILD allowlist."""
    runner = CommandRunner()

    allowed = [
        "npm run build",
        "npm install",
        "npm ci",
        "NPM RUN BUILD",  # case insensitive
    ]

    for cmd in allowed:
        # Should not raise ValueError
        assert runner._is_command_allowed(cmd, ["NODE_BUILD"]) is True

    forbidden = [
        "curl https://evil.com",
        "rm -rf /",
        "pip install malware",
    ]

    for cmd in forbidden:
        assert runner._is_command_allowed(cmd, ["NODE_BUILD"]) is False


def test_command_allowlist_python_test():
    """Test PYTHON_TEST allowlist."""
    runner = CommandRunner()

    allowed = [
        "pytest",
        "pytest -v",
        "python -m pytest",
        "PYTEST",  # case insensitive
    ]

    for cmd in allowed:
        assert runner._is_command_allowed(cmd, ["PYTHON_TEST"]) is True

    forbidden = [
        "npm test",
        "curl https://evil.com",
    ]

    for cmd in forbidden:
        assert runner._is_command_allowed(cmd, ["PYTHON_TEST"]) is False


def test_command_allowlist_multiple_families():
    """Test checking against multiple families."""
    runner = CommandRunner()

    # npm should be allowed with NODE_BUILD
    assert runner._is_command_allowed("npm run build", ["NODE_BUILD", "PYTHON_TEST"]) is True

    # pytest should be allowed with PYTHON_TEST
    assert runner._is_command_allowed("pytest", ["NODE_BUILD", "PYTHON_TEST"]) is True

    # curl should not be allowed
    assert runner._is_command_allowed("curl https://evil.com", ["NODE_BUILD", "PYTHON_TEST"]) is False


def test_command_allowlist_unknown_family():
    """Test that unknown families reject all commands."""
    runner = CommandRunner()

    # Unknown family should reject everything
    assert runner._is_command_allowed("npm run build", ["UNKNOWN_FAMILY"]) is False
    assert runner._is_command_allowed("pytest", ["UNKNOWN_FAMILY"]) is False


def test_command_runner_default_timeout():
    """Test that default timeout is used when not specified."""
    runner = CommandRunner(default_timeout=60)

    # Should use default timeout of 60
    assert runner.default_timeout == 60


def test_command_allowlists_defined():
    """Test that command allowlists are properly defined."""
    assert "NODE_BUILD" in COMMAND_ALLOWLISTS
    assert "NODE_TEST" in COMMAND_ALLOWLISTS
    assert "PYTHON_TEST" in COMMAND_ALLOWLISTS
    assert "GIT" in COMMAND_ALLOWLISTS

    # Each family should have at least one command prefix
    for family, prefixes in COMMAND_ALLOWLISTS.items():
        assert len(prefixes) > 0
        assert all(isinstance(p, str) for p in prefixes)
