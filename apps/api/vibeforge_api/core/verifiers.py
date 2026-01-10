"""Verification runners for build, test, and smoke checks."""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
import socket
import time
from typing import Any, Optional
from urllib import request, error

from vibeforge_api.core.app_runner import AppRunner
from vibeforge_api.core.command_runner import CommandRunner, CommandResult


@dataclass
class VerificationResult:
    """Result from running a verification step."""

    success: bool
    message: str
    details: Optional[dict[str, Any]] = None
    command_results: Optional[list[CommandResult]] = None


class Verifier(ABC):
    """Base interface for all verifiers."""

    def __init__(self, command_runner: Optional[CommandRunner] = None):
        """Initialize verifier.

        Args:
            command_runner: CommandRunner instance (creates default if not provided)
        """
        from vibeforge_api.core.command_runner import command_runner as default_runner

        self.command_runner = command_runner or default_runner

    @abstractmethod
    def verify(
        self, workspace_path: Path, build_spec: dict[str, Any]
    ) -> VerificationResult:
        """Run verification.

        Args:
            workspace_path: Path to session workspace
            build_spec: BuildSpec dictionary

        Returns:
            VerificationResult with pass/fail and details
        """
        pass


class BuildVerifier(Verifier):
    """Verifies that the project builds successfully."""

    # Map stack presets to build commands
    BUILD_COMMANDS = {
        "WEB_VITE_REACT_TS": "npm run build",
        "WEB_NEXTJS_TS": "npm run build",
        "CLI_PYTHON": "python -m py_compile *.py",  # Simple Python syntax check
        "API_SPRINGBOOT_JAVA": "mvn package",
    }

    # Map stack presets to allowed command families
    COMMAND_FAMILIES = {
        "WEB_VITE_REACT_TS": ["NODE_BUILD"],
        "WEB_NEXTJS_TS": ["NODE_BUILD"],
        "CLI_PYTHON": ["PYTHON_TEST"],  # Use PYTHON_TEST for py_compile
        "API_SPRINGBOOT_JAVA": ["JAVA_BUILD"],
    }

    def verify(
        self, workspace_path: Path, build_spec: dict[str, Any]
    ) -> VerificationResult:
        """Verify that the project builds.

        Args:
            workspace_path: Path to session workspace
            build_spec: BuildSpec dictionary

        Returns:
            VerificationResult indicating build success/failure
        """
        # Extract stack preset
        preset = build_spec.get("stack", {}).get("preset")

        if not preset:
            return VerificationResult(
                success=False,
                message="No stack preset defined in BuildSpec",
                details={"error": "Missing stack.preset in BuildSpec"},
            )

        # Get build command for preset
        build_command = self.BUILD_COMMANDS.get(preset)

        if not build_command:
            return VerificationResult(
                success=False,
                message=f"No build command defined for preset: {preset}",
                details={"preset": preset, "error": "Unknown preset"},
            )

        # Get allowed families
        allowed_families = self.COMMAND_FAMILIES.get(preset, [])

        # Execute build command in repo directory
        repo_path = workspace_path / "repo"

        try:
            result = self.command_runner.run_command(
                build_command,
                timeout=300,  # 5 minutes for build
                cwd=repo_path,
                allowed_families=allowed_families,
            )

            if result.returncode == 0:
                return VerificationResult(
                    success=True,
                    message="Build completed successfully",
                    details={
                        "preset": preset,
                        "command": build_command,
                        "duration": result.duration,
                    },
                    command_results=[result],
                )
            else:
                return VerificationResult(
                    success=False,
                    message=f"Build failed with exit code {result.returncode}",
                    details={
                        "preset": preset,
                        "command": build_command,
                        "returncode": result.returncode,
                        "stderr": result.stderr[:500],  # Truncate for brevity
                    },
                    command_results=[result],
                )

        except Exception as e:
            return VerificationResult(
                success=False,
                message=f"Build verification failed: {str(e)}",
                details={
                    "preset": preset,
                    "command": build_command,
                    "error": str(e),
                },
            )


class TestVerifier(Verifier):
    """Verifies that tests pass."""

    # Map stack presets to test commands
    TEST_COMMANDS = {
        "WEB_VITE_REACT_TS": "npm test",
        "WEB_NEXTJS_TS": "npm test",
        "CLI_PYTHON": "pytest",
        "API_SPRINGBOOT_JAVA": "mvn test",
    }

    # Map stack presets to allowed command families
    COMMAND_FAMILIES = {
        "WEB_VITE_REACT_TS": ["NODE_TEST"],
        "WEB_NEXTJS_TS": ["NODE_TEST"],
        "CLI_PYTHON": ["PYTHON_TEST"],
        "API_SPRINGBOOT_JAVA": ["JAVA_TEST"],
    }

    def verify(
        self, workspace_path: Path, build_spec: dict[str, Any]
    ) -> VerificationResult:
        """Verify that tests pass.

        Args:
            workspace_path: Path to session workspace
            build_spec: BuildSpec dictionary

        Returns:
            VerificationResult indicating test success/failure
        """
        # Extract stack preset
        preset = build_spec.get("stack", {}).get("preset")

        if not preset:
            return VerificationResult(
                success=False,
                message="No stack preset defined in BuildSpec",
                details={"error": "Missing stack.preset in BuildSpec"},
            )

        # Get test command for preset
        test_command = self.TEST_COMMANDS.get(preset)

        if not test_command:
            return VerificationResult(
                success=False,
                message=f"No test command defined for preset: {preset}",
                details={"preset": preset, "error": "Unknown preset"},
            )

        # Get allowed families
        allowed_families = self.COMMAND_FAMILIES.get(preset, [])

        # Execute test command in repo directory
        repo_path = workspace_path / "repo"

        try:
            result = self.command_runner.run_command(
                test_command,
                timeout=180,  # 3 minutes for tests
                cwd=repo_path,
                allowed_families=allowed_families,
            )

            if result.returncode == 0:
                return VerificationResult(
                    success=True,
                    message="All tests passed",
                    details={
                        "preset": preset,
                        "command": test_command,
                        "duration": result.duration,
                    },
                    command_results=[result],
                )
            else:
                # Parse test failures (basic parsing for MVP)
                failure_summary = self._parse_test_failures(result.stdout, result.stderr)

                return VerificationResult(
                    success=False,
                    message=f"Tests failed with exit code {result.returncode}",
                    details={
                        "preset": preset,
                        "command": test_command,
                        "returncode": result.returncode,
                        "failure_summary": failure_summary,
                        "stderr": result.stderr[:500],  # Truncate for brevity
                    },
                    command_results=[result],
                )

        except Exception as e:
            return VerificationResult(
                success=False,
                message=f"Test verification failed: {str(e)}",
                details={
                    "preset": preset,
                    "command": test_command,
                    "error": str(e),
                },
            )

    def _parse_test_failures(self, stdout: str, stderr: str) -> str:
        """Parse test output for failure information (basic MVP implementation).

        Args:
            stdout: Standard output from test command
            stderr: Standard error from test command

        Returns:
            Brief summary of test failures
        """
        # MVP: Just return a truncated version of the output
        # Future: Parse pytest/jest output for specific test failures
        output = stdout + "\n" + stderr
        lines = output.split("\n")

        # Look for common test failure indicators
        failure_lines = [
            line
            for line in lines
            if any(
                keyword in line.lower()
                for keyword in ["failed", "error", "assertion", "expected"]
            )
        ]

        if failure_lines:
            return "\n".join(failure_lines[:10])  # Return first 10 failure lines
        else:
            return "Tests failed (no specific failure details parsed)"


class SmokeVerifier(Verifier):
    """Verifies that the app can run locally (smoke check)."""

    COMMAND_FAMILIES = {
        "CLI_PYTHON": ["PYTHON_RUN"],
    }

    def __init__(
        self,
        command_runner: Optional[CommandRunner] = None,
        app_runner: Optional[AppRunner] = None,
    ):
        super().__init__(command_runner=command_runner)
        self.app_runner = app_runner or AppRunner()

    def verify(
        self, workspace_path: Path, build_spec: dict[str, Any]
    ) -> VerificationResult:
        """Verify that the app can run locally."""
        preset = build_spec.get("stack", {}).get("preset")
        if not preset:
            return VerificationResult(
                success=False,
                message="No stack preset defined in BuildSpec",
                details={"error": "Missing stack.preset in BuildSpec"},
            )

        if preset == "CLI_PYTHON":
            return self._verify_cli(workspace_path, build_spec)

        if preset in {"WEB_VITE_REACT_TS", "WEB_NEXTJS_TS"}:
            return self._verify_web(workspace_path, build_spec)

        return VerificationResult(
            success=False,
            message=f"No smoke check defined for preset: {preset}",
            details={"preset": preset, "error": "Unknown preset"},
        )

    def _verify_cli(
        self, workspace_path: Path, build_spec: dict[str, Any]
    ) -> VerificationResult:
        preset = build_spec["stack"]["preset"]
        smoke_routes = build_spec.get("acceptance", {}).get("smokeRoutes", ["--help"])
        smoke_arg = smoke_routes[0] if smoke_routes else "--help"

        command = f"python main.py {smoke_arg}".strip()
        repo_path = workspace_path / "repo"

        try:
            result = self.command_runner.run_command(
                command,
                timeout=30,
                cwd=repo_path,
                allowed_families=self.COMMAND_FAMILIES.get(preset, []),
            )
            if result.returncode == 0:
                return VerificationResult(
                    success=True,
                    message="Smoke check succeeded",
                    details={"preset": preset, "command": command},
                    command_results=[result],
                )
            return VerificationResult(
                success=False,
                message=f"Smoke check failed with exit code {result.returncode}",
                details={
                    "preset": preset,
                    "command": command,
                    "returncode": result.returncode,
                    "stderr": result.stderr[:500],
                },
                command_results=[result],
            )
        except Exception as e:
            return VerificationResult(
                success=False,
                message=f"Smoke verification failed: {str(e)}",
                details={"preset": preset, "command": command, "error": str(e)},
            )

    def _verify_web(
        self, workspace_path: Path, build_spec: dict[str, Any]
    ) -> VerificationResult:
        preset = build_spec["stack"]["preset"]
        smoke_routes = build_spec.get("acceptance", {}).get("smokeRoutes", ["/"])
        port = _find_open_port()

        try:
            run_process = self.app_runner.start(
                workspace_path, build_spec, port=port
            )
            success, route = self._wait_for_routes(
                smoke_routes, port=port, timeout=20
            )
            if success:
                return VerificationResult(
                    success=True,
                    message="Smoke check succeeded",
                    details={
                        "preset": preset,
                        "command": run_process.command,
                        "route": route,
                        "port": port,
                    },
                )
            return VerificationResult(
                success=False,
                message="Smoke check failed to reach app",
                details={
                    "preset": preset,
                    "command": run_process.command,
                    "routes": smoke_routes,
                    "port": port,
                },
            )
        except Exception as e:
            return VerificationResult(
                success=False,
                message=f"Smoke verification failed: {str(e)}",
                details={"preset": preset, "error": str(e)},
            )
        finally:
            self.app_runner.stop()

    def _wait_for_routes(
        self, routes: list[str], port: int, timeout: int = 20
    ) -> tuple[bool, Optional[str]]:
        base_url = f"http://127.0.0.1:{port}"
        start_time = time.time()

        while time.time() - start_time < timeout:
            for route in routes:
                url = base_url + route
                try:
                    with request.urlopen(url, timeout=2) as response:
                        if 200 <= response.status < 500:
                            return True, route
                except error.URLError:
                    continue
            time.sleep(0.5)

        return False, None


def _find_open_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class VerifierSuite:
    """Orchestrates multiple verification steps."""

    def __init__(
        self,
        command_runner: Optional[CommandRunner] = None,
        stop_on_first_failure: bool = True,
    ):
        """Initialize verifier suite.

        Args:
            command_runner: CommandRunner instance
            stop_on_first_failure: Stop running verifiers after first failure
        """
        self.command_runner = command_runner
        self.stop_on_first_failure = stop_on_first_failure

    def run_task_verification(
        self,
        task_verifiers: list[str],
        workspace_path: Path,
        build_spec: dict[str, Any],
    ) -> list[VerificationResult]:
        """Run verification steps defined for a specific task.

        Args:
            task_verifiers: List of verifier names (e.g., ["build", "test"])
            workspace_path: Path to session workspace
            build_spec: BuildSpec dictionary

        Returns:
            List of VerificationResults
        """
        if _should_skip_verification():
            return [
                VerificationResult(
                    success=True,
                    message="Verification skipped in stub mode",
                    details={"mode": "stub"},
                )
            ]
        return self._run_verifiers(task_verifiers, workspace_path, build_spec)

    def run_global_verification(
        self, workspace_path: Path, build_spec: dict[str, Any]
    ) -> list[VerificationResult]:
        """Run global verification suite (build + test).

        Args:
            workspace_path: Path to session workspace
            build_spec: BuildSpec dictionary

        Returns:
            List of VerificationResults
        """
        if _should_skip_verification():
            return [
                VerificationResult(
                    success=True,
                    message="Verification skipped in stub mode",
                    details={"mode": "stub"},
                )
            ]
        # Global verification: build + test
        return self._run_verifiers(["build", "test"], workspace_path, build_spec)

    def _run_verifiers(
        self,
        verifier_names: list[str],
        workspace_path: Path,
        build_spec: dict[str, Any],
    ) -> list[VerificationResult]:
        """Run specified verifiers.

        Args:
            verifier_names: List of verifier names
            workspace_path: Path to session workspace
            build_spec: BuildSpec dictionary

        Returns:
            List of VerificationResults
        """
        results = []

        # Map verifier names to classes
        verifier_map = {
            "build": BuildVerifier,
            "test": TestVerifier,
            "smoke": SmokeVerifier,
        }

        for name in verifier_names:
            verifier_class = verifier_map.get(name)

            if not verifier_class:
                # Unknown verifier - skip with warning
                results.append(
                    VerificationResult(
                        success=False,
                        message=f"Unknown verifier: {name}",
                        details={"verifier": name},
                    )
                )
                continue

            # Instantiate and run verifier
            verifier = verifier_class(command_runner=self.command_runner)
            result = verifier.verify(workspace_path, build_spec)
            results.append(result)

            # Stop on first failure if configured
            if self.stop_on_first_failure and not result.success:
                break

        return results


# Global verifier instances
build_verifier = BuildVerifier()
test_verifier = TestVerifier()
verifier_suite = VerifierSuite()


def _should_skip_verification() -> bool:
    llm_mode = (os.getenv("VIBEFORGE_LLM_MODE") or "").strip().lower()
    no_spend = (os.getenv("VIBEFORGE_NO_SPEND") or "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    return llm_mode in {"stub", "dry_run", "dry-run"} or no_spend
