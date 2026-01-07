"""Tests for AppRunner."""

from __future__ import annotations

import io
import subprocess

from vibeforge_api.core.app_runner import AppRunner


class DummyProcess:
    """Minimal subprocess-like object for testing."""

    def __init__(self, stdout: io.StringIO):
        self.stdout = stdout
        self._poll = None

    def poll(self):
        return self._poll

    def terminate(self):
        self._poll = 0

    def wait(self, timeout=None):
        self._poll = 0
        return 0

    def kill(self):
        self._poll = 0


def test_app_runner_run_instructions_web():
    runner = AppRunner()
    instructions = runner.get_run_instructions({"stack": {"preset": "WEB_VITE_REACT_TS"}})

    assert "npm install" in instructions
    assert "npm run dev" in instructions


def test_app_runner_start_stop_streams_logs(tmp_path, monkeypatch):
    workspace = tmp_path / "session1"
    repo = workspace / "repo"
    repo.mkdir(parents=True)

    dummy_process = DummyProcess(stdout=io.StringIO("line1\nline2\n"))

    def fake_popen(*args, **kwargs):
        return dummy_process

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    runner = AppRunner()
    logs: list[str] = []

    runner.start(
        workspace,
        {"stack": {"preset": "WEB_VITE_REACT_TS"}},
        on_log=logs.append,
        port=5173,
    )
    runner.stop()

    assert any("line1" in line for line in logs)
