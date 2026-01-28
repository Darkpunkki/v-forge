# WP-0056 - Agent Bridge Standalone Service

## Goal
Build the standalone agent bridge service (tools/agent_bridge/) that runs on remote machines, connects to VibeForge via WebSocket, invokes Claude Code CLI, and streams results back.

## Idea-ID
IDEA-0003-vibeforge-is-pivoting

## Tasks
- TASK-014 - Build bridge WebSocket client with registration handshake
- TASK-015 - Add heartbeat sending and reconnection with backoff
- TASK-016 - Implement Claude Code CLI wrapper for task execution
- TASK-017 - Wire dispatch handling to CLI execution with progress streaming
- TASK-018 - Add CLI interface and signal handling to bridge

## Ordered execution plan
1) TASK-014 - Baseline WebSocket client + register/registered handshake
2) TASK-016 - Claude CLI wrapper module
3) TASK-017 - Dispatch handling + progress/response streaming
4) TASK-015 - Heartbeat + reconnection/backoff
5) TASK-018 - Argparse CLI, signal handling, requirements.txt

## Done means
- `python tools/agent_bridge/bridge.py --url ws://localhost:8000/ws/agent-bridge --agent-id test --token secret --workdir .` registers successfully
- Heartbeat messages are sent and reconnect with capped backoff works
- Dispatch triggers Claude Code CLI execution and streams progress + response
- SIGINT/SIGTERM triggers graceful shutdown

## Task checklist
- [x] TASK-014 - Build bridge WebSocket client with registration handshake
  - Files: tools/agent_bridge/bridge.py, tools/agent_bridge/__init__.py
  - Verify: `python -c "import ast, pathlib; ast.parse(pathlib.Path('tools/agent_bridge/bridge.py').read_text()); ast.parse(pathlib.Path('tools/agent_bridge/cli_wrapper.py').read_text()); print('syntax-ok')"`
- [x] TASK-016 - Implement Claude Code CLI wrapper for task execution
  - Files: tools/agent_bridge/cli_wrapper.py
  - Verify: `python -c "import ast, pathlib; ast.parse(pathlib.Path('tools/agent_bridge/bridge.py').read_text()); ast.parse(pathlib.Path('tools/agent_bridge/cli_wrapper.py').read_text()); print('syntax-ok')"`
- [x] TASK-017 - Wire dispatch handling to CLI execution with progress streaming
  - Files: tools/agent_bridge/bridge.py
  - Verify: `python -c "import ast, pathlib; ast.parse(pathlib.Path('tools/agent_bridge/bridge.py').read_text()); ast.parse(pathlib.Path('tools/agent_bridge/cli_wrapper.py').read_text()); print('syntax-ok')"`
- [x] TASK-015 - Add heartbeat sending and reconnection with backoff
  - Files: tools/agent_bridge/bridge.py
  - Verify: `python -c "import ast, pathlib; ast.parse(pathlib.Path('tools/agent_bridge/bridge.py').read_text()); ast.parse(pathlib.Path('tools/agent_bridge/cli_wrapper.py').read_text()); print('syntax-ok')"`
- [x] TASK-018 - Add CLI interface and signal handling to bridge
  - Files: tools/agent_bridge/bridge.py, tools/agent_bridge/requirements.txt
  - Verify: `python -c "import ast, pathlib; ast.parse(pathlib.Path('tools/agent_bridge/bridge.py').read_text()); ast.parse(pathlib.Path('tools/agent_bridge/cli_wrapper.py').read_text()); print('syntax-ok')"`

## Notes / Decisions
- Record blockers, command outputs, and any deviations from task order here.
