---
phase: testing
title: Testing Strategy
description: Define testing approach, test cases, and quality assurance
---

# Testing Strategy

## Test Coverage Goals
**What level of testing do we aim for?**

- Aim for near-100% coverage on new/changed code in `apps/api/vibeforge_api/core` and routers.
- Integration coverage for critical flows: session lifecycle, workspace creation, patch application.
- End-to-end smoke paths for questionnaire → plan summary → decision once orchestration matures.
- Align scenarios with VF backlog acceptance criteria and Work Packages.

## Unit Tests
**What individual components need testing?**

### Session & Questionnaire
- [ ] Valid session creation initializes workspace + artifacts store.
- [ ] Phase enforcement rejects out-of-order calls (e.g., plan fetch before questionnaire complete).
- [ ] Questionnaire answers persist and drive plan prompts deterministically.

### Workspace & Patch
- [ ] Workspace manager prevents traversal and creates required directories/files.
- [ ] Patch applier validates diff paths and rejects unsafe/invalid diffs without mutating files.
- [ ] Artifact logging writes metadata per applied patch.

## Integration Tests
**How do we test component interactions?**

- [ ] End-to-end session API flow (create → get question → submit answers → plan summary).
- [ ] Patch apply + artifact recording within a session workspace.
- [ ] Error surfaces: invalid phase transitions, invalid patch, missing session.

## End-to-End Tests
**What user flows need validation?**

- [ ] UI client (when ready): questionnaire completion and plan approval using real API.
- [ ] Regression: previously passing session flows remain intact after model or router changes.

## Test Data
**What data do we use for testing?**

- Deterministic questionnaire fixtures defined in `core/questionnaire.py`.
- Workspace fixtures isolated per test (temporary directories) to avoid cross-test contamination.
- Mocked model provider responses to avoid external calls during CI.

## Test Reporting & Coverage
**How do we verify and communicate test results?**

- Run `pytest -v` from `apps/api`; add `--cov=vibeforge_api --cov-report=term-missing` for coverage.
- Document gaps (files/functions below target) directly in this file with rationale and remediation plan.
- Surface coverage deltas in PR descriptions when significant modules change.

## Manual Testing
**What requires human validation?**

- Smoke the questionnaire flow via `curl`/`httpie` against local API after major changes.
- Verify workspace directory contents and patch outcomes when modifying file ops.
- UI accessibility and browser/device checks once UI is implemented.

## Performance Testing
**How do we validate performance?**

- Load-test `/sessions` endpoints with representative traffic once remote deployment is available.
- Measure patch apply duration on large diffs; establish thresholds and alerts.
- Track model request latency distributions to catch regressions.

## Bug Tracking
**How do we manage issues?**

- Track open issues via VF IDs in `vibeforge_master_checklist.md` and Work Packages.
- Reproduce with minimal steps; add regression tests before closing.
- Annotate this document with known flaky areas or temporary skips.
