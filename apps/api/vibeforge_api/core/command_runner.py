"""Safe command execution with allowlist enforcement and output capture."""

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class CommandResult:
    """Result from command execution."""

    returncode: int
    stdout: str
    stderr: str
    duration: float  # seconds
    timed_out: bool
    command: str


# Command family allowlists - maps family name to allowed command prefixes
COMMAND_ALLOWLISTS = {
    "NODE_BUILD": ["npm run build", "npm run", "npm ci", "npm install", "npm"],
    "NODE_TEST": ["npm test", "npm run test", "vitest", "jest"],
    "PYTHON_TEST": ["pytest", "python -m pytest", "python -m unittest"],
    "JAVA_BUILD": ["mvn clean", "mvn compile", "mvn package", "gradle build"],
    "JAVA_TEST": ["mvn test", "gradle test"],
    "GIT": ["git status", "git diff", "git log", "git add", "git commit"],
    "FORMAT": ["prettier", "black", "eslint --fix", "autopep8"],
}


class CommandRunner:
    """Executes shell commands with safety guardrails."""

    def __init__(self, default_timeout: int = 120):
        """Initialize command runner.

        Args:
            default_timeout: Default timeout in seconds (default: 120)
        """
        self.default_timeout = default_timeout

    def run_command(
        self,
        command: str,
        timeout: Optional[int] = None,
        cwd: Optional[Path] = None,
        allowed_families: Optional[list[str]] = None,
    ) -> CommandResult:
        """Run a shell command with safety checks.

        Args:
            command: Shell command to execute
            timeout: Timeout in seconds (uses default if not specified)
            cwd: Working directory for command execution
            allowed_families: List of allowed command families (e.g., ["NODE_BUILD", "NODE_TEST"])

        Returns:
            CommandResult with execution details

        Raises:
            ValueError: If command is not in allowlist
        """
        # Enforce allowlist if families specified
        if allowed_families is not None:
            if not self._is_command_allowed(command, allowed_families):
                raise ValueError(
                    f"Command '{command}' not allowed. Must match one of: {allowed_families}"
                )

        # Use default timeout if not specified
        if timeout is None:
            timeout = self.default_timeout

        # Prepare execution
        start_time = time.time()
        timed_out = False

        try:
            # Run command with timeout
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(cwd) if cwd else None,
            )

            duration = time.time() - start_time

            return CommandResult(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                duration=duration,
                timed_out=False,
                command=command,
            )

        except subprocess.TimeoutExpired as e:
            duration = time.time() - start_time
            timed_out = True

            # Get partial output if available
            stdout = e.stdout.decode() if e.stdout else ""
            stderr = e.stderr.decode() if e.stderr else ""

            return CommandResult(
                returncode=-1,  # Indicate failure
                stdout=stdout,
                stderr=f"Command timed out after {timeout}s\n{stderr}",
                duration=duration,
                timed_out=True,
                command=command,
            )

        except Exception as e:
            duration = time.time() - start_time

            return CommandResult(
                returncode=-1,
                stdout="",
                stderr=f"Command execution failed: {str(e)}",
                duration=duration,
                timed_out=False,
                command=command,
            )

    def _is_command_allowed(self, command: str, allowed_families: list[str]) -> bool:
        """Check if command matches any allowed family prefix.

        Args:
            command: Command to check
            allowed_families: List of allowed command families

        Returns:
            True if command is allowed, False otherwise
        """
        command_lower = command.lower().strip()

        for family in allowed_families:
            if family not in COMMAND_ALLOWLISTS:
                # Unknown family - reject for safety
                continue

            allowed_prefixes = COMMAND_ALLOWLISTS[family]
            for prefix in allowed_prefixes:
                if command_lower.startswith(prefix.lower()):
                    return True

        return False


# Global command runner instance
command_runner = CommandRunner()
