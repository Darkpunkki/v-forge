"""Integration tests for verification system with real commands."""

import shutil
from pathlib import Path

import pytest

from vibeforge_api.core.command_runner import command_runner
from vibeforge_api.core.verifiers import (
    BuildVerifier,
    TestVerifier,
    VerifierSuite,
)


@pytest.fixture
def fixture_project(tmp_path):
    """Create a temporary copy of the fixture Node.js project."""
    fixture_src = Path(__file__).parent / "fixtures" / "node-project"
    fixture_dst = tmp_path / "session-test" / "repo"

    # Copy fixture project to tmp workspace
    shutil.copytree(fixture_src, fixture_dst)

    return tmp_path / "session-test"


def test_command_runner_real_npm_command(fixture_project):
    """Test CommandRunner with real npm command."""
    repo_path = fixture_project / "repo"

    # Run npm --version (should work if npm is installed)
    result = command_runner.run_command(
        "npm --version",
        cwd=repo_path,
        allowed_families=["NODE_BUILD"],
    )

    # Should complete without timing out
    assert result.timed_out is False
    assert result.command == "npm --version"


def test_build_verifier_real_build(fixture_project):
    """Test BuildVerifier with real build command."""
    build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}

    verifier = BuildVerifier()
    result = verifier.verify(fixture_project, build_spec)

    # Build should succeed (it's just an echo command in fixture)
    assert result.success is True
    assert "Build complete" in result.command_results[0].stdout


def test_test_verifier_real_test(fixture_project):
    """Test TestVerifier with real test command."""
    build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}

    verifier = TestVerifier()
    result = verifier.verify(fixture_project, build_spec)

    # Tests should pass (it's just an echo command in fixture)
    assert result.success is True
    assert "All tests passed" in result.command_results[0].stdout


def test_verifier_suite_real_execution(fixture_project):
    """Test VerifierSuite orchestrating real build and test commands."""
    build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}

    suite = VerifierSuite()
    results = suite.run_global_verification(fixture_project, build_spec)

    # Should run build and test
    assert len(results) == 2
    assert results[0].success is True  # Build
    assert results[1].success is True  # Test

    # Check command outputs
    assert "Build complete" in results[0].command_results[0].stdout
    assert "All tests passed" in results[1].command_results[0].stdout


def test_command_runner_timeout_real(tmp_path):
    """Test that real commands timeout correctly."""
    # Use a Python sleep command that will timeout
    result = command_runner.run_command(
        'python -c "import time; time.sleep(10)"',
        timeout=1,
        cwd=tmp_path,
        allowed_families=None,
    )

    assert result.timed_out is True
    assert "timed out" in result.stderr.lower()


def test_build_verifier_failure_real(tmp_path):
    """Test BuildVerifier with a command that fails."""
    # Create workspace with no package.json (will fail)
    workspace = tmp_path / "session-fail"
    (workspace / "repo").mkdir(parents=True)

    build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}

    verifier = BuildVerifier()
    result = verifier.verify(workspace, build_spec)

    # Should fail since there's no package.json
    assert result.success is False
    assert result.command_results[0].returncode != 0


@pytest.mark.skipif(
    not shutil.which("npm"),
    reason="npm not installed"
)
def test_real_npm_install_in_fixture(fixture_project):
    """Test running real npm install (if npm is available)."""
    repo_path = fixture_project / "repo"

    result = command_runner.run_command(
        "npm --version",  # Just check version, don't install
        cwd=repo_path,
        allowed_families=["NODE_BUILD"],
        timeout=30,
    )

    assert result.returncode == 0
    assert result.timed_out is False


def test_verification_captures_output_detail(fixture_project):
    """Test that verification results include detailed command output."""
    build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}

    verifier = BuildVerifier()
    result = verifier.verify(fixture_project, build_spec)

    # Should have command results attached
    assert result.command_results is not None
    assert len(result.command_results) == 1

    cmd_result = result.command_results[0]
    assert cmd_result.command == "npm run build"
    assert cmd_result.duration >= 0
    assert cmd_result.stdout is not None


def test_verifier_suite_stop_on_first_failure_real(tmp_path):
    """Test that VerifierSuite stops on first failure with real commands."""
    # Create workspace that will fail build
    workspace = tmp_path / "session-fail"
    (workspace / "repo").mkdir(parents=True)

    build_spec = {"stack": {"preset": "WEB_VITE_REACT_TS"}}

    suite = VerifierSuite(stop_on_first_failure=True)
    results = suite.run_task_verification(["build", "test"], workspace, build_spec)

    # Should stop after build failure, not run test
    assert len(results) == 1
    assert results[0].success is False
