---
doc_type: epic_validation_report
idea_id: "IDEA-0001-control-simulation"
run_id: "2026-01-14T18-33-13Z_run-e953"
generated_by: "Epic Validator"
generated_at: "2026-01-14T18:33:13Z"
source_inputs:
  - "docs/forge/ideas/IDEA-0001-control-simulation/latest/concept_summary.md"
  - "docs/forge/ideas/IDEA-0001-control-simulation/latest/epics.md"
  - "docs/forge/ideas/IDEA-0001-control-simulation/latest/idea_normalized.md"
  - "docs/forge/ideas/IDEA-0001-control-simulation/inputs/idea.md"
configs: []
status: "Draft"
---

# Epic Validation Report

## Summary

- Overall verdict: PASS_WITH_WARNINGS
- Critical issues: 0
- Warnings: 2
- Suggested patching: NO (validator_config.md not present or allow_patch not enabled)

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
- The system can log and display messages with agent metadata and execution order. -> EPIC-005, EPIC-006 (execution-order state in EPIC-003)
- The system can operate in deterministic stub mode and switch to OpenAI responses. -> EPIC-008

### Coverage by Workflow Step

- Configure agents and directed links, choose the first agent, and provide an initial prompt. -> EPIC-001, EPIC-002
- Start the simulation. -> EPIC-003
- Advance by manual ticks or slowed autorun while recording message flow and active agent order. -> EPIC-003, EPIC-004, EPIC-005
- Stop the simulation at any time. -> EPIC-003

## Overlap & Boundary Issues

- Type: OVERLAP
- Epic(s): EPIC-003, EPIC-005
- Evidence: EPIC-003 owns execution order tracking while EPIC-005 also claims preserving execution order cues in the message log, creating dual ownership of execution-order semantics.
- Recommended fix: Keep execution-order state ownership in EPIC-003 and clarify EPIC-005 to reference that state (e.g., add EPIC-005 out_of_scope: "Defining execution-order state (owned by EPIC-003)" or adjust EPIC-005 in_scope to say it consumes runtime order).

- Type: OVERLAP
- Epic(s): EPIC-006, EPIC-007
- Evidence: EPIC-006 is the broad /control surface while EPIC-007 also targets /control visualization, which can blur UI boundaries.
- Recommended fix: Add EPIC-006 out_of_scope bullet for topology/graph visualization to explicitly reserve that scope for EPIC-007.

## Invariant & Exclusion Violations (Critical)

- None found.

## Release Target & Priority Sanity

- MVP coherence: OK
- Notes on retargeting suggestions: Autorun is listed as a core capability but is deferred to V1; confirm this is acceptable for MVP given manual tick is the default.

## Metadata Defects

- None.

## Proposed Patch (if patching not allowed)

- EPIC-005 out_of_scope: add "Defining execution-order state (owned by EPIC-003)" or adjust EPIC-005 in_scope to clarify it consumes runtime execution-order state.
- EPIC-006 out_of_scope: add "Topology/graph visualization (owned by EPIC-007)."
