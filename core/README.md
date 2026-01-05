# Core Domain Logic

This directory contains the core domain logic for VibeForge, independent of specific frameworks or delivery mechanisms.

## Purpose
Core business logic that implements the VibeForge workflow:
- Gates (policy, risk, feasibility checks)
- Verification engines (build, test, smoke)
- Spec builders (BuildSpec, IntentProfile)
- Domain models and interfaces

## Structure
```
core/
├── gates/          # Policy, risk, and feasibility gates
├── verifiers/      # Build, test, and smoke verification engines
└── spec/           # BuildSpec and IntentProfile builders
```

## Principles
- Framework-agnostic: No direct dependencies on FastAPI, Flask, etc.
- Pure domain logic: Business rules and policies
- Testable: Easy to unit test without external dependencies
- Reusable: Can be imported by apps/api or other services

## Dependencies
- Should depend only on standard library and minimal external packages
- Should NOT depend on apps/, orchestration/, or runtime/
