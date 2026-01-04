---
phase: implementation
title: Implementation Guide
description: Technical implementation notes, patterns, and code guidelines
---

# Implementation Guide

## Development Setup
**How do we get started?**

- Python 3.11+ with virtualenv: `cd apps/api && python -m venv .venv && source .venv/bin/activate`.
- Install dependencies: `pip install -r requirements.txt` (API) and `npm install` inside `apps/ui` when UI work resumes.
- Create `.env` under `apps/api` with `OPENAI_API_KEY=...`; keep secrets out of git.
- Run API locally: `uvicorn vibeforge_api.main:app --reload --port 8000`.

## Code Structure
**How is the code organized?**

- `apps/api/vibeforge_api/main.py`: FastAPI app and router wiring.
- `apps/api/vibeforge_api/routers/`: HTTP surface area for sessions, plan decision, and progress.
- `apps/api/vibeforge_api/core/`: session state machine, questionnaire logic, workspace manager, patch applier, and artifact store.
- `apps/api/vibeforge_api/models/`: Pydantic request/response DTOs and shared enums for phases and result envelopes.
- `apps/api/tests/`: pytest suites covering sessions, workspace, patch, and artifact behaviors.
- `configs/` and `schemas/`: stack presets, policies, and JSON schema contracts for build specs and task graphs.

## Implementation Notes
**Key technical details to remember:**

### Core Features
- **Session lifecycle**: enforce allowed transitions defined in `core/session.py`; reject operations that don't match the current phase.
- **Questionnaire engine**: deterministic questions/answers in `core/questionnaire.py`—no free text allowed.
- **Workspace management**: `core/workspace.py` must validate paths and create per-session directories.
- **Patch application**: `core/patch.py` validates unified diffs and blocks traversal outside workspace root.

### Patterns & Best Practices
- Keep DTOs the single source of truth for API contracts; update both models and routers together.
- Favor pure functions in core modules to simplify testing; inject I/O dependencies where needed.
- Use structured exceptions for predictable HTTP error handling.

## Integration Points
**How do pieces connect?**

- Routers call into `core` services; session store orchestrates workspace + questionnaire state.
- Model provider wrappers (OpenAI today) are invoked by session/plan generation helpers; design for adapter swapping.
- Patch applier integrates with workspace manager to ensure validated write operations.

## Error Handling
**How do we handle failures?**

- Centralize validation errors via Pydantic and FastAPI exception handlers.
- Reject invalid phase transitions with explicit error responses; keep logs for rejected attempts.
- Patch failures should be surfaced with clear messages and leave workspace unchanged; prefer atomic writes.

## Performance Considerations
**How do we keep it fast?**

- Avoid redundant model calls; cache questionnaire definitions in memory.
- Keep file I/O scoped to session directories; reuse open file handles only when necessary.
- Use async FastAPI handlers where I/O bound; model calls remain synchronous until provider supports async.

## Security Notes
**What security measures are in place?**

- Enforce path whitelists and traversal checks before any file write.
- Maintain structured, non-free-text inputs throughout the flow to limit prompt injection.
- Guard secrets via environment variables and avoid logging sensitive content.
- Plan for auth/token middleware when deploying beyond local environments.
