"""Tests for verifiers (BuildVerifier, TestVerifier, VerifierSuite)."""

from pathlib import Path
from unittest.mock import Mock, MagicMock

import pytest

from vibeforge_api.core.verifiers import (
    BuildVerifier,
    TestVerifier,
    VerifierSuite,
    VerificationResult,
)
from vibeforge_api.core.command_runner import CommandResult


class TestBuildVerifier:
    """Tests for BuildVerifier."""

    def test_build_verifier_success(self, tmp_path):
        """Test successful build verification."""
        # Mock command runner
        mock_runner = Mock()
        mock_runner.run_command.return_value = CommandResult(
            returncode=0,
            stdout="Build successful",
            stderr="",
            duration=5.2,
            timed_out=False,
            command="npm run build",
        )

        # Create build spec
        build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}

        # Create workspace
        workspace = tmp_path / "session1"
        repo = workspace / "repo"
        repo.mkdir(parents=True)

        # Run verifier
        verifier = BuildVerifier(command_runner=mock_runner)
        result = verifier.verify(workspace, build_spec)

        assert result.success is True
        assert "completed successfully" in result.message.lower()
        assert result.details["preset"] == "WEB_VITE_REACT_TS"
        assert result.details["command"] == "npm run build"

    def test_build_verifier_failure(self, tmp_path):
        """Test failed build verification."""
        # Mock command runner
        mock_runner = Mock()
        mock_runner.run_command.return_value = CommandResult(
            returncode=1,
            stdout="",
            stderr="Build error: syntax error",
            duration=2.1,
            timed_out=False,
            command="npm run build",
        )

        build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}
        workspace = tmp_path / "session1"
        (workspace / "repo").mkdir(parents=True)

        verifier = BuildVerifier(command_runner=mock_runner)
        result = verifier.verify(workspace, build_spec)

        assert result.success is False
        assert "failed" in result.message.lower()
        assert result.details["returncode"] == 1
        assert "Build error" in result.details["stderr"]

    def test_build_verifier_missing_preset(self, tmp_path):
        """Test build verification with missing preset."""
        mock_runner = Mock()

        build_spec = {}  # Missing stack.preset
        workspace = tmp_path / "session1"
        (workspace / "repo").mkdir(parents=True)

        verifier = BuildVerifier(command_runner=mock_runner)
        result = verifier.verify(workspace, build_spec)

        assert result.success is False
        assert "no stack preset" in result.message.lower()

    def test_build_verifier_unknown_preset(self, tmp_path):
        """Test build verification with unknown preset."""
        mock_runner = Mock()

        build_spec = {"stack": {"preset": "UNKNOWN_PRESET"}}
        workspace = tmp_path / "session1"
        (workspace / "repo").mkdir(parents=True)

        verifier = BuildVerifier(command_runner=mock_runner)
        result = verifier.verify(workspace, build_spec)

        assert result.success is False
        assert "no build command" in result.message.lower()

    def test_build_verifier_command_mapping(self):
        """Test that presets map to correct build commands."""
        verifier = BuildVerifier()

        assert verifier.BUILD_COMMANDS["WEB_VITE_REACT_TS"] == "npm run build"
        assert verifier.BUILD_COMMANDS["CLI_PYTHON"] == "python -m py_compile *.py"

    def test_build_verifier_python_preset(self, tmp_path):
        """Test build verification for Python preset."""
        mock_runner = Mock()
        mock_runner.run_command.return_value = CommandResult(
            returncode=0,
            stdout="",
            stderr="",
            duration=1.0,
            timed_out=False,
            command="python -m py_compile *.py",
        )

        build_spec = {"stack": {"preset": "CLI_PYTHON"}}
        workspace = tmp_path / "session1"
        (workspace / "repo").mkdir(parents=True)

        verifier = BuildVerifier(command_runner=mock_runner)
        result = verifier.verify(workspace, build_spec)

        assert result.success is True
        mock_runner.run_command.assert_called_once()
        call_args = mock_runner.run_command.call_args
        assert call_args[0][0] == "python -m py_compile *.py"


class TestTestVerifier:
    """Tests for TestVerifier."""

    def test_test_verifier_success(self, tmp_path):
        """Test successful test verification."""
        mock_runner = Mock()
        mock_runner.run_command.return_value = CommandResult(
            returncode=0,
            stdout="All tests passed\n5 passed",
            stderr="",
            duration=3.5,
            timed_out=False,
            command="npm test",
        )

        build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}
        workspace = tmp_path / "session1"
        (workspace / "repo").mkdir(parents=True)

        verifier = TestVerifier(command_runner=mock_runner)
        result = verifier.verify(workspace, build_spec)

        assert result.success is True
        assert "passed" in result.message.lower()
        assert result.details["command"] == "npm test"

    def test_test_verifier_failure(self, tmp_path):
        """Test failed test verification."""
        mock_runner = Mock()
        mock_runner.run_command.return_value = CommandResult(
            returncode=1,
            stdout="Test failed: expected 5 but got 3\n1 failed, 4 passed",
            stderr="",
            duration=2.8,
            timed_out=False,
            command="npm test",
        )

        build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}
        workspace = tmp_path / "session1"
        (workspace / "repo").mkdir(parents=True)

        verifier = TestVerifier(command_runner=mock_runner)
        result = verifier.verify(workspace, build_spec)

        assert result.success is False
        assert "failed" in result.message.lower()
        assert "expected 5 but got 3" in result.details["failure_summary"]

    def test_test_verifier_missing_preset(self, tmp_path):
        """Test test verification with missing preset."""
        mock_runner = Mock()

        build_spec = {}  # Missing stack.preset
        workspace = tmp_path / "session1"
        (workspace / "repo").mkdir(parents=True)

        verifier = TestVerifier(command_runner=mock_runner)
        result = verifier.verify(workspace, build_spec)

        assert result.success is False
        assert "no stack preset" in result.message.lower()

    def test_test_verifier_command_mapping(self):
        """Test that presets map to correct test commands."""
        verifier = TestVerifier()

        assert verifier.TEST_COMMANDS["WEB_VITE_REACT_TS"] == "npm test"
        assert verifier.TEST_COMMANDS["CLI_PYTHON"] == "pytest"

    def test_test_verifier_parse_failures(self):
        """Test parsing of test failures."""
        verifier = TestVerifier()

        stdout = """
        Test suite failed
        FAILED test_something.py::test_case - AssertionError: expected 5
        FAILED test_other.py::test_other - Expected True but got False
        2 failed, 3 passed
        """

        summary = verifier._parse_test_failures(stdout, "")

        assert "FAILED" in summary
        assert "AssertionError" in summary


class TestVerifierSuite:
    """Tests for VerifierSuite."""

    def test_verifier_suite_run_build_only(self, tmp_path):
        """Test running only build verification."""
        mock_runner = Mock()
        mock_runner.run_command.return_value = CommandResult(
            returncode=0,
            stdout="Build successful",
            stderr="",
            duration=5.0,
            timed_out=False,
            command="npm run build",
        )

        build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}
        workspace = tmp_path / "session1"
        (workspace / "repo").mkdir(parents=True)

        suite = VerifierSuite(command_runner=mock_runner)
        results = suite.run_task_verification(["build"], workspace, build_spec)

        assert len(results) == 1
        assert results[0].success is True

    def test_verifier_suite_run_build_and_test(self, tmp_path):
        """Test running build and test verification."""
        mock_runner = Mock()
        mock_runner.run_command.side_effect = [
            CommandResult(
                returncode=0,
                stdout="Build successful",
                stderr="",
                duration=5.0,
                timed_out=False,
                command="npm run build",
            ),
            CommandResult(
                returncode=0,
                stdout="All tests passed",
                stderr="",
                duration=3.0,
                timed_out=False,
                command="npm test",
            ),
        ]

        build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}
        workspace = tmp_path / "session1"
        (workspace / "repo").mkdir(parents=True)

        suite = VerifierSuite(command_runner=mock_runner)
        results = suite.run_task_verification(["build", "test"], workspace, build_spec)

        assert len(results) == 2
        assert results[0].success is True  # Build
        assert results[1].success is True  # Test

    def test_verifier_suite_stop_on_failure(self, tmp_path):
        """Test that suite stops on first failure when configured."""
        mock_runner = Mock()
        mock_runner.run_command.return_value = CommandResult(
            returncode=1,
            stdout="",
            stderr="Build failed",
            duration=2.0,
            timed_out=False,
            command="npm run build",
        )

        build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}
        workspace = tmp_path / "session1"
        (workspace / "repo").mkdir(parents=True)

        suite = VerifierSuite(command_runner=mock_runner, stop_on_first_failure=True)
        results = suite.run_task_verification(["build", "test"], workspace, build_spec)

        # Should stop after build failure, not run test
        assert len(results) == 1
        assert results[0].success is False

    def test_verifier_suite_continue_on_failure(self, tmp_path):
        """Test that suite continues after failure when configured."""
        mock_runner = Mock()
        mock_runner.run_command.side_effect = [
            CommandResult(
                returncode=1,
                stdout="",
                stderr="Build failed",
                duration=2.0,
                timed_out=False,
                command="npm run build",
            ),
            CommandResult(
                returncode=0,
                stdout="Tests passed",
                stderr="",
                duration=3.0,
                timed_out=False,
                command="npm test",
            ),
        ]

        build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}
        workspace = tmp_path / "session1"
        (workspace / "repo").mkdir(parents=True)

        suite = VerifierSuite(command_runner=mock_runner, stop_on_first_failure=False)
        results = suite.run_task_verification(["build", "test"], workspace, build_spec)

        # Should run both even though build failed
        assert len(results) == 2
        assert results[0].success is False  # Build failed
        assert results[1].success is True  # Test passed

    def test_verifier_suite_global_verification(self, tmp_path):
        """Test global verification (build + test)."""
        mock_runner = Mock()
        mock_runner.run_command.side_effect = [
            CommandResult(
                returncode=0,
                stdout="Build successful",
                stderr="",
                duration=5.0,
                timed_out=False,
                command="npm run build",
            ),
            CommandResult(
                returncode=0,
                stdout="All tests passed",
                stderr="",
                duration=3.0,
                timed_out=False,
                command="npm test",
            ),
        ]

        build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}
        workspace = tmp_path / "session1"
        (workspace / "repo").mkdir(parents=True)

        suite = VerifierSuite(command_runner=mock_runner)
        results = suite.run_global_verification(workspace, build_spec)

        assert len(results) == 2
        assert results[0].success is True  # Build
        assert results[1].success is True  # Test

    def test_verifier_suite_unknown_verifier(self, tmp_path):
        """Test handling of unknown verifier name."""
        mock_runner = Mock()

        build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}
        workspace = tmp_path / "session1"
        (workspace / "repo").mkdir(parents=True)

        suite = VerifierSuite(command_runner=mock_runner)
        results = suite.run_task_verification(["unknown"], workspace, build_spec)

        assert len(results) == 1
        assert results[0].success is False
        assert "unknown verifier" in results[0].message.lower()
