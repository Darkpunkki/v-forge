# Storage & Persistence

This directory contains persistence logic for VibeForge sessions, artifacts, and events.

## Purpose
Handles all data persistence:
- Session state (IntentProfile, BuildSpec, TaskGraph, phase)
- Artifacts (generated files, patches, verification results)
- Event logs (audit trail of session actions)

## Structure
```
storage/
├── sessions/       # Session store
├── artifacts/      # Artifact storage
└── events/         # Event log storage
```

## Responsibilities
- Persist and retrieve session data
- Store artifacts (diffs, files, metadata)
- Record events for debugging and audit
- Provide query interfaces for coordinators

## Storage Strategy
- MVP: File-based storage (JSON files per session)
- Future: Database backend (SQLite, PostgreSQL)
- Session directories: `workspaces/{session_id}/`
- Artifacts: `workspaces/{session_id}/artifacts/`

## Principles
- Simple MVP: Start with file system
- Atomic writes: Use temp files + rename
- Immutable artifacts: Never overwrite
- Queryable events: Support filtering by session/phase/task

## Dependencies
- Minimal external dependencies (use stdlib where possible)
- Used by: orchestration/, apps/api
