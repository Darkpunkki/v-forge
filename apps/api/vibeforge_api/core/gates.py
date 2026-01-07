"""Gate pipeline for safety and feasibility checks."""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from vibeforge_api.models.types import GateResult, GateResultStatus


@dataclass
class GateContext:
    """Context for gate evaluation."""

    build_spec: dict[str, Any]
    proposed_commands: Optional[list[str]] = None
    proposed_diff: Optional[str] = None
    task_data: Optional[dict[str, Any]] = None
    workspace_path: Optional[Path] = None


class Gate(ABC):
    """Base class for all gates."""

    @abstractmethod
    def evaluate(self, context: GateContext) -> GateResult:
        """Evaluate the gate against the context.

        Args:
            context: GateContext with proposed changes

        Returns:
            GateResult with OK/WARN/BLOCK status
        """
        pass


class GatePipeline:
    """Orchestrates multiple gates in sequence."""

    def __init__(self, gates: list[Gate], stop_on_block: bool = True):
        """Initialize gate pipeline.

        Args:
            gates: List of gates to run
            stop_on_block: Stop evaluation on first BLOCK (default: True)
        """
        self.gates = gates
        self.stop_on_block = stop_on_block

    def evaluate(self, context: GateContext) -> GateResult:
        """Run all gates and aggregate results.

        Args:
            context: GateContext with proposed changes

        Returns:
            Aggregated GateResult
        """
        aggregate_result, _ = self.evaluate_with_results(context)
        return aggregate_result

    def evaluate_with_results(
        self, context: GateContext
    ) -> tuple[GateResult, list[tuple[Gate, GateResult]]]:
        """Run all gates and return aggregate + per-gate results.

        Args:
            context: GateContext with proposed changes

        Returns:
            Tuple of (aggregated GateResult, list of (gate, result))
        """
        results: list[tuple[Gate, GateResult]] = []

        for gate in self.gates:
            result = gate.evaluate(context)
            results.append((gate, result))

            # Stop on first BLOCK if configured
            if self.stop_on_block and result.status == GateResultStatus.BLOCK:
                break

        aggregate_result = self._aggregate_results([result for _, result in results])
        return aggregate_result, results

    def _aggregate_results(self, results: list[GateResult]) -> GateResult:
        """Aggregate multiple gate results.

        Logic:
        - If any BLOCK, return BLOCK with first blocker message
        - If any WARN, return WARN with all warnings
        - Otherwise return OK

        Args:
            results: List of GateResults

        Returns:
            Aggregated GateResult
        """
        if not results:
            return GateResult(
                status=GateResultStatus.OK,
                message="No gates evaluated",
            )

        # Check for any BLOCK
        blockers = [r for r in results if r.status == GateResultStatus.BLOCK]
        if blockers:
            # Return first blocker
            return blockers[0]

        # Check for any WARN
        warnings = [r for r in results if r.status == GateResultStatus.WARN]
        if warnings:
            # Combine all warning messages
            messages = [w.message for w in warnings]
            return GateResult(
                status=GateResultStatus.WARN,
                message=f"{len(warnings)} warnings: " + "; ".join(messages),
                details={"warnings": messages},
            )

        # All OK
        return GateResult(
            status=GateResultStatus.OK,
            message="All gates passed",
        )


class PolicyGate(Gate):
    """Enforces forbidden patterns and path constraints."""

    # Default forbidden patterns (dangerous commands/code)
    DEFAULT_FORBIDDEN_PATTERNS = [
        r"rm\s+-rf\s+/",  # rm -rf /
        r"curl.*\|.*sh",  # curl | sh
        r"wget.*\|.*sh",  # wget | sh
        r"eval\s*\(",  # eval()
        r"__import__\s*\([\"']os[\"']\)",  # __import__('os')
        r"subprocess\.(call|run|Popen)\(",  # Direct subprocess use
        r";\s*rm\s+",  # Command chaining with rm
        r"&&\s*rm\s+",  # Command chaining with rm
    ]

    # Forbidden file paths/patterns
    FORBIDDEN_PATHS = [
        r"^\.\./",  # Path traversal
        r"/\.\./",  # Path traversal
        r"^/etc/",  # System files
        r"^/sys/",  # System files
        r"^/proc/",  # System files
        r"^\.git/",  # Git internal files
    ]

    def evaluate(self, context: GateContext) -> GateResult:
        """Evaluate policy constraints.

        Args:
            context: GateContext with proposed changes

        Returns:
            GateResult (BLOCK if policy violated)
        """
        # Get forbidden patterns from BuildSpec or use defaults
        forbidden_patterns = context.build_spec.get("policies", {}).get(
            "forbiddenPatterns", self.DEFAULT_FORBIDDEN_PATTERNS
        )

        # Check commands
        if context.proposed_commands:
            for cmd in context.proposed_commands:
                # Check forbidden patterns
                for pattern in forbidden_patterns:
                    if re.search(pattern, cmd, re.IGNORECASE):
                        return GateResult(
                            status=GateResultStatus.BLOCK,
                            message=f"Forbidden pattern detected in command: {pattern}",
                            details={"command": cmd, "pattern": pattern},
                        )

        # Check diff for forbidden patterns
        if context.proposed_diff:
            for pattern in forbidden_patterns:
                if re.search(pattern, context.proposed_diff, re.IGNORECASE):
                    return GateResult(
                        status=GateResultStatus.BLOCK,
                        message=f"Forbidden pattern detected in diff: {pattern}",
                        details={"pattern": pattern},
                    )

            # Check for path traversal in diff
            for forbidden_path in self.FORBIDDEN_PATHS:
                if re.search(forbidden_path, context.proposed_diff):
                    return GateResult(
                        status=GateResultStatus.BLOCK,
                        message=f"Forbidden path detected in diff: {forbidden_path}",
                        details={"pattern": forbidden_path},
                    )

        return GateResult(
            status=GateResultStatus.OK,
            message="Policy check passed",
        )


class RiskGate(Gate):
    """Enforces command family allowlists and network rules."""

    def evaluate(self, context: GateContext) -> GateResult:
        """Evaluate risk constraints.

        Args:
            context: GateContext with proposed changes

        Returns:
            GateResult (BLOCK if command not allowed, WARN if network ASK)
        """
        if not context.proposed_commands:
            return GateResult(
                status=GateResultStatus.OK,
                message="No commands to check",
            )

        # Get allowed command families from BuildSpec
        allowed_families = context.build_spec.get("policies", {}).get(
            "allowedCommandFamilies", []
        )

        if not allowed_families:
            return GateResult(
                status=GateResultStatus.WARN,
                message="No allowed command families defined in BuildSpec",
            )

        # Check each command against allowed families
        # Import COMMAND_ALLOWLISTS from command_runner
        from vibeforge_api.core.command_runner import COMMAND_ALLOWLISTS

        for cmd in context.proposed_commands:
            allowed = False
            for family in allowed_families:
                if family in COMMAND_ALLOWLISTS:
                    prefixes = COMMAND_ALLOWLISTS[family]
                    for prefix in prefixes:
                        if cmd.lower().strip().startswith(prefix.lower()):
                            allowed = True
                            break
                if allowed:
                    break

            if not allowed:
                return GateResult(
                    status=GateResultStatus.BLOCK,
                    message=f"Command not in allowed families: {cmd}",
                    details={
                        "command": cmd,
                        "allowed_families": allowed_families,
                    },
                )

        # Check network access rules
        network_access = context.build_spec.get("policies", {}).get("networkAccess", "ALLOW")

        # Network-related command patterns
        network_commands = ["curl", "wget", "fetch", "http", "git clone", "npm install", "pip install"]

        has_network_command = any(
            any(net_cmd in cmd.lower() for net_cmd in network_commands)
            for cmd in context.proposed_commands
        )

        if has_network_command:
            if network_access == "DENY":
                return GateResult(
                    status=GateResultStatus.BLOCK,
                    message="Network access denied by BuildSpec policy",
                    details={"network_access": network_access},
                )
            elif network_access == "ASK":
                return GateResult(
                    status=GateResultStatus.WARN,
                    message="Commands require network access - user confirmation needed",
                    details={"network_access": network_access},
                )

        return GateResult(
            status=GateResultStatus.OK,
            message="Risk check passed",
        )


class FeasibilityGate(Gate):
    """Enforces scope budgets and limits."""

    WARN_THRESHOLD = 0.8  # Warn at 80% of limit

    def evaluate(self, context: GateContext) -> GateResult:
        """Evaluate feasibility constraints.

        Args:
            context: GateContext with proposed changes

        Returns:
            GateResult (WARN at 80% limit, BLOCK if exceeded)
        """
        scope_budget = context.build_spec.get("scopeBudget", {})

        # Check commands per task (only if scope budget exists)
        if scope_budget and context.proposed_commands:
            max_commands = scope_budget.get("maxCommandsPerTask", 10)
            num_commands = len(context.proposed_commands)

            if num_commands > max_commands:
                return GateResult(
                    status=GateResultStatus.BLOCK,
                    message=f"Too many commands: {num_commands} > {max_commands}",
                    details={"count": num_commands, "limit": max_commands},
                )
            elif num_commands > max_commands * self.WARN_THRESHOLD:
                return GateResult(
                    status=GateResultStatus.WARN,
                    message=f"Approaching command limit: {num_commands}/{max_commands}",
                    details={"count": num_commands, "limit": max_commands},
                )

        # Check diff size (lines changed)
        if context.proposed_diff:
            lines = context.proposed_diff.split("\n")
            # Count lines starting with + or - (but not +++ or ---)
            changed_lines = sum(
                1 for line in lines
                if (line.startswith("+") and not line.startswith("+++"))
                or (line.startswith("-") and not line.startswith("---"))
            )

            # Reasonable limit: 500 lines per task
            max_lines = 500

            if changed_lines > max_lines:
                return GateResult(
                    status=GateResultStatus.BLOCK,
                    message=f"Diff too large: {changed_lines} lines > {max_lines}",
                    details={"lines": changed_lines, "limit": max_lines},
                )
            elif changed_lines > max_lines * self.WARN_THRESHOLD:
                return GateResult(
                    status=GateResultStatus.WARN,
                    message=f"Large diff: {changed_lines}/{max_lines} lines",
                    details={"lines": changed_lines, "limit": max_lines},
                )

        return GateResult(
            status=GateResultStatus.OK,
            message="Feasibility check passed",
        )


class DiffAndCommandGate(Gate):
    """Validates diffs and commands for safety."""

    # Secret/credential patterns to detect
    SECRET_PATTERNS = [
        r"password\s*=\s*[\"'][^\"']+[\"']",
        r"api[_-]?key\s*=\s*[\"'][^\"']+[\"']",
        r"secret\s*=\s*[\"'][^\"']+[\"']",
        r"token\s*=\s*[\"'][^\"']+[\"']",
        r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",
        r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
    ]

    MAX_FILES_PER_TASK = 20
    MAX_LINES_PER_TASK = 500

    def evaluate(self, context: GateContext) -> GateResult:
        """Evaluate diff and command safety.

        Args:
            context: GateContext with proposed changes

        Returns:
            GateResult (BLOCK if unsafe diff/commands)
        """
        if not context.proposed_diff:
            return GateResult(
                status=GateResultStatus.OK,
                message="No diff to check",
            )

        # Check for secrets in diff
        for pattern in self.SECRET_PATTERNS:
            if re.search(pattern, context.proposed_diff, re.IGNORECASE):
                return GateResult(
                    status=GateResultStatus.BLOCK,
                    message=f"Potential secret detected in diff",
                    details={"pattern": pattern},
                )

        # Count files modified
        # Simple heuristic: count "diff --git" or "+++ " lines
        file_markers = re.findall(r"^\+\+\+ ", context.proposed_diff, re.MULTILINE)
        num_files = len(file_markers)

        if num_files > self.MAX_FILES_PER_TASK:
            return GateResult(
                status=GateResultStatus.BLOCK,
                message=f"Too many files modified: {num_files} > {self.MAX_FILES_PER_TASK}",
                details={"files": num_files, "limit": self.MAX_FILES_PER_TASK},
            )

        # Count lines changed
        lines = context.proposed_diff.split("\n")
        changed_lines = sum(1 for line in lines if line.startswith(("+", "-")))

        if changed_lines > self.MAX_LINES_PER_TASK:
            return GateResult(
                status=GateResultStatus.BLOCK,
                message=f"Diff too large: {changed_lines} lines > {self.MAX_LINES_PER_TASK}",
                details={"lines": changed_lines, "limit": self.MAX_LINES_PER_TASK},
            )

        return GateResult(
            status=GateResultStatus.OK,
            message="Diff and command check passed",
        )


class GateAdapter:
    """Adapts gate results for UI consumption."""

    @staticmethod
    def format_blocker_message(gate_result: GateResult) -> str:
        """Format a blocker message for user display.

        Args:
            gate_result: GateResult with BLOCK status

        Returns:
            User-friendly error message
        """
        if gate_result.status != GateResultStatus.BLOCK:
            return ""

        message = f"⛔ Blocked: {gate_result.message}"

        if gate_result.details:
            details_str = ", ".join(f"{k}={v}" for k, v in gate_result.details.items())
            message += f"\n   Details: {details_str}"

        return message

    @staticmethod
    def generate_clarification_question(gate_result: GateResult) -> Optional[dict[str, Any]]:
        """Generate a multiple-choice clarification question for WARN results.

        Args:
            gate_result: GateResult with WARN status

        Returns:
            Clarification question dict or None
        """
        if gate_result.status != GateResultStatus.WARN:
            return None

        return {
            "question": f"Warning: {gate_result.message}. How would you like to proceed?",
            "options": [
                {"value": "proceed", "label": "Proceed anyway"},
                {"value": "modify", "label": "Modify the request"},
                {"value": "cancel", "label": "Cancel this operation"},
            ],
        }

    @staticmethod
    def format_warning_message(gate_result: GateResult) -> str:
        """Format a warning message for user display.

        Args:
            gate_result: GateResult with WARN status

        Returns:
            User-friendly warning message
        """
        if gate_result.status != GateResultStatus.WARN:
            return ""

        message = f"⚠️  Warning: {gate_result.message}"

        if gate_result.details:
            details_str = ", ".join(f"{k}={v}" for k, v in gate_result.details.items())
            message += f"\n   Details: {details_str}"

        return message


# Global gate instances
policy_gate = PolicyGate()
risk_gate = RiskGate()
feasibility_gate = FeasibilityGate()
diff_and_command_gate = DiffAndCommandGate()

# Default gate pipeline (order: cheapest checks first)
default_gate_pipeline = GatePipeline([
    policy_gate,
    risk_gate,
    feasibility_gate,
    diff_and_command_gate,
])
