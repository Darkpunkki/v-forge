# Execution Runtime

This directory contains the execution runtime for VibeForge, handling workspace management and command execution.

## Purpose
Provides a safe, isolated execution environment:
- Workspace creation and management
- Command execution with allowlists
- Sandbox isolation (future)
- File system operations within workspace bounds

## Structure
```
runtime/
├── workspace/      # Workspace manager
├── commands/       # Command runner with safety checks
└── sandbox/        # Sandboxing capabilities (future)
```

## Responsibilities
- Create per-session workspace directories
- Apply patches (unified diffs) to workspace files
- Execute allowlisted commands within workspace
- Enforce path constraints (no traversal attacks)
- Capture command outputs for verification

## Safety Principles
- Workspace isolation: Each session has its own workspace
- Path validation: Block `..` and absolute paths
- Command allowlisting: Only approved commands can run
- Timeouts: Commands have execution time limits
- Dry-run mode: Preview changes before applying

## Dependencies
- Should have minimal external dependencies
- Used by: orchestration/ (for task execution)
