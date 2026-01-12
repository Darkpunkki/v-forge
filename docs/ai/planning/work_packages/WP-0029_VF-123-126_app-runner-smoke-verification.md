# WP-0029 — App runner + smoke verification

## Status
- Done
- Verified: `PYTHONPATH=/workspace/v-forge pytest`
- Completed: 2026-01-07 12:13 (local)

## Context
- Chapter(s): 12 Verification + Command Runner + AppRunner
- Why now:
  - App execution and run instructions are required for complete end-to-end sessions.
  - Smoke checks provide a minimal runnable validation beyond build/test.
  - Run lifecycle control is needed for UI-driven “Run” actions and log streaming.

## Goal
- Enable app run instructions, dev server lifecycle management, and a smoke check to confirm apps start successfully.

## VF Tasks (canonical)
- [x] **VF-123 — Implement SmokeVerifier (server starts and/or route responds)**
  - Run a lightweight end-to-end check (start server or hit a route) to confirm the app can run locally.
  - Files: `apps/api/vibeforge_api/core/verifiers.py`, `apps/api/tests/test_verifiers.py`
  - Verify: `PYTHONPATH=/workspace/v-forge pytest`
- [x] **VF-125 — Implement AppRunner.getRunInstructions() per stack preset**
  - Generate clear run instructions (install/build/dev server) and expose them in the final summary.
  - Files: `apps/api/vibeforge_api/core/app_runner.py`, `apps/api/vibeforge_api/routers/sessions.py`
  - Verify: `PYTHONPATH=/workspace/v-forge pytest`
- [x] **VF-126 — Implement AppRunner.start()/stop() dev server + stream logs**
  - Provide a ‘Run’ button that starts the app locally and streams logs back to the UI.
  - Files: `apps/api/vibeforge_api/core/app_runner.py`, `apps/api/tests/test_app_runner.py`
  - Verify: `PYTHONPATH=/workspace/v-forge pytest`

## Plan
### Approach
- Extend the verification system with a SmokeVerifier that can run a minimal startup/health check per stack preset.
- Introduce an AppRunner component responsible for run instructions and dev server lifecycle.
- Wire AppRunner outputs into final summaries and log streaming for UI consumption.
- Add focused tests for smoke verification and runner lifecycle/log handling.

### Actionable Task Array
BEGIN_ACTIONABLE_TASK_ARRAY
steps:
  - vf: VF-123
    intent: "Add a SmokeVerifier that validates app startup or route response per stack preset."
    touches:
      - "apps/api/vibeforge_api/core/verifiers.py"
      - "apps/api/tests/test_verifiers.py"
    done_when:
      - "SmokeVerifier runs a lightweight server/route check and reports pass/fail."
    verify:
      - "pytest"
  - vf: VF-125
    intent: "Implement AppRunner.getRunInstructions() to emit install/build/run steps per stack preset."
    touches:
      - "apps/api/vibeforge_api/core/app_runner.py"
      - "apps/api/vibeforge_api/core/spec_builder.py"
    done_when:
      - "Run instructions are generated deterministically from stack presets and included in summaries."
    verify:
      - "pytest"
  - vf: VF-126
    intent: "Implement AppRunner.start()/stop() to manage dev server lifecycle and stream logs."
    touches:
      - "apps/api/vibeforge_api/core/app_runner.py"
      - "apps/api/vibeforge_api/core/command_runner.py"
      - "apps/api/tests/test_app_runner.py"
    done_when:
      - "Dev server start/stop works with log streaming suitable for UI display."
    verify:
      - "pytest"
END_ACTIONABLE_TASK_ARRAY

## Acceptance Criteria
- VF-123: SmokeVerifier executes a minimal startup/route check and reports failures clearly.
- VF-125: Run instructions are generated per stack preset and surfaced in final summaries.
- VF-126: Dev server lifecycle management supports start/stop and log streaming for UI.
- All new tests or updates pass under the WP verification command.

## Verify
- `pytest`

## Dependencies
- WP-0003 ✓ (CommandRunner/Verifiers), WP-0010 ✓ (stack presets)

## Risks / Recovery
- Risk: Smoke checks may be flaky across stacks -> Mitigation: keep checks minimal, configurable per preset.
- Risk: Dev server processes may hang -> Mitigation: enforce timeouts and ensure stop() cleans up processes.
- Recovery: If verification fails, isolate failing test, reduce scope to core smoke check, and rerun `pytest`.
