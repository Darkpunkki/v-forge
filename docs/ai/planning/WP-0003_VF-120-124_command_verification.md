# WP-0003 — Command runner + verification harness

**Status:** In Progress
**Started:** 2026-01-04
**VF Tasks:** VF-120, VF-121, VF-122, VF-124

---

## Goal

Implement safe command execution infrastructure and verification harness to enable:
- Running allowlisted shell commands with timeout enforcement
- Capturing stdout/stderr for logging and UI display
- Building verification runners for different verification types (build, test)
- Orchestrating verification steps per-task and globally

This enables the system to safely execute build/test commands and verify task outcomes.

---

## VF Tasks Included

- **VF-120**: Implement CommandRunner (allowlist enforcement, timeouts, output capture)
- **VF-121**: Implement BuildVerifier (stack preset build command)
- **VF-122**: Implement TestVerifier (stack preset test command)
- **VF-124**: Implement VerifierSuite (per-task + global verification)

---

## Execution Plan (Ordered Steps)

### 1. VF-120 — CommandRunner (foundation)
**File:** `apps/api/vibeforge_api/core/command_runner.py` (new)

**Implementation:**
- Create `CommandResult` dataclass (returncode, stdout, stderr, duration, timed_out)
- Create `CommandRunner` class with:
  - `run_command(command, timeout, cwd, allowed_families)` method
  - Allowlist enforcement based on command families (NODE_BUILD, NODE_TEST, PYTHON_TEST, etc.)
  - Timeout enforcement using subprocess.run with timeout parameter
  - Capture stdout/stderr separately
  - Return structured CommandResult
- Define command family allowlists (maps family → command prefixes)

**Test:** `apps/api/tests/test_command_runner.py`
- Test allowed commands execute successfully
- Test forbidden commands are rejected
- Test timeout enforcement
- Test output capture
- Test working directory handling

**Done means:**
- Commands can be executed with allowlist enforcement
- Timeouts work correctly
- Output is captured and returned
- Tests pass: `pytest tests/test_command_runner.py -v`

---

### 2. VF-121 — BuildVerifier
**File:** `apps/api/vibeforge_api/core/verifiers.py` (new)

**Implementation:**
- Create `VerificationResult` dataclass (success, message, details, command_results)
- Create base `Verifier` interface/ABC
- Implement `BuildVerifier` class:
  - Takes BuildSpec (to determine stack preset)
  - Maps preset → build command (e.g., WEB_VITE_REACT_TS → "npm run build")
  - Uses CommandRunner to execute build command
  - Returns VerificationResult with pass/fail and captured output

**Test:** Add to `apps/api/tests/test_verifiers.py`
- Test build verification with mock BuildSpec
- Test command mapping for different stack presets
- Test failure handling

**Done means:**
- BuildVerifier can determine and run the correct build command
- Returns structured verification result
- Tests pass

---

### 3. VF-122 — TestVerifier
**File:** `apps/api/vibeforge_api/core/verifiers.py` (extend)

**Implementation:**
- Implement `TestVerifier` class (similar to BuildVerifier):
  - Maps preset → test command (e.g., WEB_VITE_REACT_TS → "npm test")
  - Uses CommandRunner to execute test command
  - Returns VerificationResult with pass/fail and captured output
  - Parse test output for failure details (basic parsing for MVP)

**Test:** Add to `apps/api/tests/test_verifiers.py`
- Test test verification with mock BuildSpec
- Test command mapping for different stack presets
- Test failure output parsing

**Done means:**
- TestVerifier can determine and run the correct test command
- Returns structured verification result with failure details
- Tests pass

---

### 4. VF-124 — VerifierSuite
**File:** `apps/api/vibeforge_api/core/verifiers.py` (extend)

**Implementation:**
- Implement `VerifierSuite` class:
  - Orchestrates multiple verifiers
  - `run_task_verification(task, workspace_path, build_spec)` method
    - Runs verifiers specified in task definition
    - Collects all results
  - `run_global_verification(workspace_path, build_spec)` method
    - Runs final verification suite (build + test)
    - Returns aggregated results
  - Short-circuit on first failure (configurable)

**Test:** Add to `apps/api/tests/test_verifiers.py`
- Test running multiple verifiers in sequence
- Test early termination on failure
- Test aggregated results

**Done means:**
- VerifierSuite can orchestrate multiple verification steps
- Per-task and global verification modes work
- Tests pass

---

## Integration Test

**File:** `apps/api/tests/test_verification_integration.py` (new)

Create a tiny fixture project (simple Node.js or Python project) and:
- Use CommandRunner to run real commands
- Use BuildVerifier to build the fixture project
- Use TestVerifier to test the fixture project
- Use VerifierSuite to run both in sequence

**Done means:**
- Real commands execute against fixture project
- Build and test verification work end-to-end
- Integration test passes

---

## WP-Level Verification

Run all verification tests:
```bash
cd apps/api
pytest tests/test_command_runner.py tests/test_verifiers.py tests/test_verification_integration.py -v
pytest -v  # All tests should pass
```

---

## Task Checklist

- [x] VF-120: CommandRunner with allowlist, timeouts, output capture
  - Files: command_runner.py, test_command_runner.py
  - Verify: `pytest tests/test_command_runner.py -v` ✓ (15 tests passed)
  - Key features: Allowlist enforcement, timeout handling, stdout/stderr capture, working directory support

- [x] VF-121: BuildVerifier for stack preset build commands
  - Files: verifiers.py (BuildVerifier class)
  - Verify: `pytest tests/test_verifiers.py::TestBuildVerifier -v` ✓ (6 tests passed)
  - Maps presets to build commands, enforces timeouts, captures output

- [x] VF-122: TestVerifier for stack preset test commands
  - Files: verifiers.py (TestVerifier class)
  - Verify: `pytest tests/test_verifiers.py::TestTestVerifier -v` ✓ (5 tests passed)
  - Maps presets to test commands, parses test failures

- [x] VF-124: VerifierSuite for orchestrating verification steps
  - Files: verifiers.py (VerifierSuite class)
  - Verify: `pytest tests/test_verifiers.py::TestVerifierSuite -v` ✓ (6 tests passed)
  - Runs multiple verifiers, supports stop-on-failure, provides global verification

- [x] Integration test with fixture project
  - Files: test_verification_integration.py, fixture project (tests/fixtures/node-project)
  - Verify: `pytest tests/test_verification_integration.py -v` ✓ (9 tests passed)
  - Real command execution, timeout testing, fixture-based verification

---

## Notes / Decisions

- **MVP Scope**: Keep verifiers simple; advanced output parsing can come later
- **Allowlist Design**: Use command families (e.g., NODE_BUILD) mapped to prefixes (e.g., ["npm run build", "npm run"])
- **Timeout Defaults**: 120s for build, 60s for test (configurable)
- **Fixture Project**: Use minimal Node.js project with package.json, simple test, to verify real execution
