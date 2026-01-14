---
doc_type: epic_validation_report
idea_id: "IDEA-0001-control-simulation"
run_id: "2026-01-14T21-47-46Z_run-f5a3"
generated_by: "Epic Validator"
generated_at: "2026-01-14T21:47:47.3265627Z"
source_inputs:
  - "docs/forge/ideas/IDEA-0001-control-simulation/latest/concept_summary.md"
  - "docs/forge/ideas/IDEA-0001-control-simulation/latest/epics.md (fallback; epics_backlog missing)"
  - "docs/forge/ideas/IDEA-0001-control-simulation/latest/idea_normalized.md"
  - "docs/forge/ideas/IDEA-0001-control-simulation/inputs/idea.md"
configs:
  - "docs/forge/ideas/IDEA-0001-control-simulation/inputs/validator_config.md"
status: "Draft"
---

# Epic Validation Report

## Summary

- Overall verdict: PASS_WITH_WARNINGS
- Critical issues: 0
- Warnings: 2
- Suggested patching: YES (allow_patch: true; epics_backlog created)

## Required-Field Checks

- YAML parse: OK
- Epic count: OK (8)
- Required fields present: OK
- ID sequence: OK

## Coverage Check

### Coverage by Concept Capability

- The system can configure agents (count, name/id, role, model label) before a run starts. -> EPIC-001
- The system can define directed links that restrict which agents can message each other. -> EPIC-002
- The system can start, stop, and advance a simulation via tick or autorun. -> EPIC-003, EPIC-004
- The system can log and display messages with agent metadata and execution order. -> EPIC-005, EPIC-006 (execution order state in EPIC-003)
- The system can operate in deterministic stub mode and switch to OpenAI responses. -> EPIC-008

### Coverage by Workflow Step

- Configure agents and directed links, choose the first agent, and provide an initial prompt. -> EPIC-001, EPIC-002
- Start the simulation. -> EPIC-003
- Advance by manual ticks or slowed autorun while recording message flow and active agent order. -> EPIC-003, EPIC-004, EPIC-005 (order state in EPIC-003)
- Stop the simulation at any time. -> EPIC-003

## Overlap & Boundary Issues

- Type: OVERLAP
- Epic(s): EPIC-003, EPIC-005
- Evidence: EPIC-003 owns execution-order state while EPIC-005 also claims preserving execution order cues in the message log, creating dual ownership.
- Recommended fix: Clarify EPIC-005 to consume execution-order cues from EPIC-003 and add an out_of_scope note that execution-order state is owned by EPIC-003.

- Type: OVERLAP
- Epic(s): EPIC-006, EPIC-007
- Evidence: EPIC-006 is the broad /control interaction surface while EPIC-007 covers topology visualization; both mention active agent cues, which can blur UI ownership.
- Recommended fix: Add EPIC-006 out_of_scope bullet reserving topology/graph visualization for EPIC-007.

## Invariant & Exclusion Violations (Critical)

- None found.

## Release Target & Priority Sanity

- MVP coherence: OK
- Notes on retargeting suggestions: Autorun is deferred to V1; confirm MVP does not require it beyond manual tick default.

## Metadata Defects

- None.
