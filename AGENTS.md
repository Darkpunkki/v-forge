# AGENTS.md — VibeForge (Codex)

This file tells Codex how to work effectively in this repository.

## Objective

Make small, verifiable changes that keep the app runnable. Prefer fixes that improve correctness, determinism, and observability.

## How the app is expected to behave

- The UI is phase-aware and should route users based on the session phase.
- The backend exposes session endpoints and enforces phase rules (e.g., `/result` only when phase is `COMPLETE`).
- The UI polls `/progress` while work is running.

## Where to look first

- Backend routes: `apps/api/vibeforge_api/routers/sessions.py`
- Models/types: `apps/api/vibeforge_api/models/`
- Orchestration: `session_coordinator.py` (primary workflow engine)
- LLM provider/adapter: `llm_provider.py` and provider classes
- Session storage + workspace/artifacts management: session store + workspace manager modules

## Change discipline

- Prefer targeted edits over refactors.
- Add logging where it reduces ambiguity (phase transitions, task start/finish, LLM call boundaries).
- Keep interfaces stable; introduce seams (interfaces/types) before swapping implementations.

## Safety and determinism

Implement or maintain an LLM “safe mode” so the pipeline can be tested without spending tokens:

- `stub`: no network calls; deterministic outputs sufficient to move phases forward
- optional: `record/replay` cache so real outputs can be captured once and replayed

## Verification expectations

After changes:

- Run the relevant backend tests (and add tests when behavior changes).
- Ensure the app can start locally (backend + UI).
- Confirm key flows do not regress:
  - questionnaire completion routes to plan review
  - plan approval advances to execution/progress
  - result is only fetched when phase is COMPLETE (or FAILED routes to result/error view)

## Output expectations for PRs/changes

- Describe what changed, why, and how to verify.
- If behavior changed, include a minimal test or a reproducible verification step.
