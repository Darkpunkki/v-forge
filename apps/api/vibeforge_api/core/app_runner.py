"""App runner for dev server lifecycle and run instructions."""

from __future__ import annotations

import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from vibeforge_api.core.command_runner import is_command_allowed


@dataclass
class AppRunnerProcess:
    """Represents a running app process."""

    process: subprocess.Popen[str]
    command: str
    port: int


class AppRunner:
    """Handles run instructions and dev server lifecycle."""

    RUN_INSTRUCTIONS = {
        "WEB_VITE_REACT_TS": """# Run Instructions

1. Install dependencies:
   ```
   npm install
   ```

2. Start development server:
   ```
   npm run dev
   ```

3. Open http://localhost:5173 in your browser

4. Build for production:
   ```
   npm run build
   ```

5. Run tests:
   ```
   npm test
   ```
""",
        "CLI_PYTHON": """# Run Instructions

1. Install dependencies (if any):
   ```
   pip install -r requirements.txt
   ```

2. Run the CLI:
   ```
   python main.py --help
   ```

3. Run tests:
   ```
   python -m pytest
   ```
""",
    }

    DEV_SERVER_COMMANDS = {
        "WEB_VITE_REACT_TS": "npm run dev -- --host {host} --port {port}",
        "WEB_NEXTJS_TS": "npm run dev -- --hostname {host} --port {port}",
    }

    COMMAND_FAMILIES = {
        "WEB_VITE_REACT_TS": ["NODE_DEV"],
        "WEB_NEXTJS_TS": ["NODE_DEV"],
    }

    def __init__(self) -> None:
        self._process: Optional[AppRunnerProcess] = None
        self._log_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def get_run_instructions(self, build_spec: Optional[dict]) -> str:
        """Return run instructions for a BuildSpec."""
        if not build_spec:
            return "No build specification available."

        preset = build_spec.get("stack", {}).get("preset")
        if not preset:
            return "No stack preset defined in BuildSpec."

        return self.RUN_INSTRUCTIONS.get(preset, "See README.md for run instructions.")

    def start(
        self,
        workspace_path: Path,
        build_spec: dict,
        on_log: Optional[Callable[[str], None]] = None,
        host: str = "127.0.0.1",
        port: int = 5173,
    ) -> AppRunnerProcess:
        """Start a dev server and stream logs via callback."""
        if self._process:
            raise RuntimeError("AppRunner already has a running process.")

        preset = build_spec.get("stack", {}).get("preset")
        command_template = self.DEV_SERVER_COMMANDS.get(preset)
        if not command_template:
            raise ValueError(f"No dev server command defined for preset: {preset}")

        command = command_template.format(host=host, port=port)
        allowed_families = self.COMMAND_FAMILIES.get(preset, [])
        if allowed_families and not is_command_allowed(command, allowed_families):
            raise ValueError(f"Dev server command '{command}' not allowed.")

        repo_path = workspace_path / "repo"
        process = subprocess.Popen(
            command,
            cwd=str(repo_path),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        self._stop_event.clear()
        self._log_thread = threading.Thread(
            target=self._stream_logs, args=(process, on_log), daemon=True
        )
        self._log_thread.start()

        self._process = AppRunnerProcess(process=process, command=command, port=port)
        return self._process

    def stop(self, timeout: int = 5) -> None:
        """Stop the running dev server."""
        if not self._process:
            return

        self._stop_event.set()
        process = self._process.process

        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

        if self._log_thread and self._log_thread.is_alive():
            self._log_thread.join(timeout=timeout)

        self._process = None
        self._log_thread = None

    def _stream_logs(
        self, process: subprocess.Popen[str], on_log: Optional[Callable[[str], None]]
    ) -> None:
        if not process.stdout:
            return

        for line in process.stdout:
            if self._stop_event.is_set():
                break
            message = line.rstrip("\n")
            if on_log:
                on_log(message)


# Global app runner instance
app_runner = AppRunner()
