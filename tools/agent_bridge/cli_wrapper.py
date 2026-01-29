"""Claude Code CLI wrapper for agent bridge."""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ClaudeResult:
    """Structured Claude CLI result."""

    content: str
    usage: dict[str, Any]
    exit_code: int


class ClaudeInvocationError(RuntimeError):
    """Raised when Claude CLI invocation fails."""

    def __init__(
        self,
        message: str,
        *,
        exit_code: Optional[int] = None,
        stderr: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.stderr = stderr


def invoke_claude(
    task_content: str,
    workdir: Optional[str] = None,
    timeout_seconds: int = 600,
) -> ClaudeResult:
    """Invoke the Claude Code CLI and return structured output.

    Runs: claude --print --output-format json
    """
    cmd = ["claude", "--print", "--output-format", "json"]

    try:
        result = subprocess.run(
            cmd,
            input=task_content,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            cwd=workdir or None,
        )
    except subprocess.TimeoutExpired as exc:
        raise ClaudeInvocationError("Claude CLI timed out", stderr=str(exc)) from exc
    except FileNotFoundError as exc:
        raise ClaudeInvocationError("Claude CLI not found in PATH") from exc

    if result.returncode != 0:
        raise ClaudeInvocationError(
            "Claude CLI returned non-zero exit code",
            exit_code=result.returncode,
            stderr=result.stderr,
        )

    raw = (result.stdout or "").strip()
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError as exc:
        raise ClaudeInvocationError(
            "Claude CLI output was not valid JSON",
            exit_code=result.returncode,
            stderr=result.stderr,
        ) from exc

    content = payload.get("content")
    if content is None:
        content = payload.get("result") or payload.get("completion") or payload.get("response") or ""
    if not isinstance(content, str):
        content = str(content)

    usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}

    return ClaudeResult(content=content, usage=usage, exit_code=result.returncode)
