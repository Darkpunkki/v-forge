# Orchestration Layer

This directory contains the coordination and orchestration logic for VibeForge sessions.

## Purpose
Manages the lifecycle of a VibeForge session:
- Coordinates between phases (QUESTIONNAIRE → SPEC_BUILD → IDEA → PLAN_REVIEW → EXECUTION → COMPLETE)
- Routes tasks to appropriate agents
- Enforces phase transitions and guards
- Manages session state

## Structure
```
orchestration/
├── coordinator/    # Main session coordinator
├── phases/         # Phase-specific handlers
└── routing/        # Agent routing logic
```

## Responsibilities
- Session state machine
- Phase transition logic
- Task routing to agents (worker, foreman, fixer, reviewer)
- Coordination between core/, runtime/, and storage/

## Dependencies
- Depends on: core/ (for gates, verifiers), storage/ (for persistence)
- Used by: apps/api (to drive sessions)
