---
doc_type: epic_validation_report
idea_id: "IDEA-0002-control-sim"
run_id: "2026-01-15T03-01-40Z_run-1e7d"
generated_by: "Epic Validator"
generated_at: "2026-01-15T03:01:40.379643+00:00"
source_inputs:
  - "docs/forge/ideas/IDEA-0002-control-sim/latest/concept_summary.md"
  - "docs/forge/ideas/IDEA-0002-control-sim/latest/epics_backlog.md"
  - "docs/forge/ideas/IDEA-0002-control-sim/latest/idea_normalized.md"
  - "docs/forge/ideas/IDEA-0002-control-sim/inputs/idea.md"
configs: []
status: "Draft"
---

# Epic Validation Report

## Summary

- Overall verdict: PASS_WITH_WARNINGS
- Critical issues: 0
- Warnings: 3
- Suggested patching: NO (validator_config.md not present)

## Required-Field Checks

- YAML parse: OK
- Epic count: WARN (5 epics; guideline is 6–12)
- Required fields present: OK
- ID sequence: OK

## Coverage Check

### Coverage by Concept Capability

- Capability: Configure agents (id/name/role/model) -> EPIC-001
- Capability: Configure directed/bidirectional links -> EPIC-001
- Capability: Start simulation with initial prompt + first agent -> EPIC-001, EPIC-003
- Capability: Advance ticks and record messages -> EPIC-002
- Capability: Render message log, graph view, status/tick -> EPIC-005 (status/tick state in EPIC-003)
- Capability: Controls for start/tick/pause/stop/reset -> EPIC-003
- Capability: Deterministic stubbed responses -> EPIC-002

### Coverage by Workflow Step

- Step: Define agents and links -> EPIC-001
- Step: Select first agent, provide prompt, start simulation -> EPIC-001, EPIC-003
- Step: Per-tick activity with message recording -> EPIC-002
- Step: Update status/tick and display graph/log -> EPIC-003, EPIC-005
- Step: Pause/stop/reset (rewind if in scope) -> EPIC-003

## Overlap & Boundary Issues

- Type: OVERLAP
- Epic(s): EPIC-002, EPIC-004
- Evidence: EPIC-002 in_scope includes “Message log entries...” while EPIC-004 claims “Event records for ticks, messages...”; ownership of log artifacts/persistence is unclear.
- Recommended fix: Change EPIC-002 to “emit message events with tick metadata” and add out_of_scope “Event persistence/streaming”; keep EPIC-004 as the owner of persisted/streamed event logs.

- Type: MIS-SCOPED
- Epic(s): EPIC-001
- Evidence: EPIC-001 promises bidirectional links, but codebase_context notes the current AgentFlowGraph validation enforces a DAG, which blocks true bidirectional links.
- Recommended fix: Add an explicit dependency or note in EPIC-001 that bidirectional links require relaxing DAG validation in the existing graph model (no new subsystem).

## Invariant & Exclusion Violations (Critical)

- None found.

## Release Target & Priority Sanity

- MVP coherence: OK
- Notes: All epics are MVP-aligned with the core control simulation flow; rewind remains explicitly out-of-scope unless confirmed.

## Metadata Defects

- None beyond the epic-count warning.

## Proposed Patch (if patching not allowed)

- EPIC-002 in_scope: replace “Message log entries with sender, receiver, timestamp, and tick index.” with “Emits message events with sender/receiver/tick metadata.”
- EPIC-002 out_of_scope: add “Event persistence/streaming (owned by EPIC-004).”
- EPIC-001 description or in_scope: add “Bidirectional links require relaxing existing DAG validation in AgentFlowGraph (see codebase_context).”
- Optional: If you want to meet the 6–12 epic guideline, split EPIC-005 into two epics (“Agent Graph View” and “Message Log & Status View”) and adjust dependencies accordingly.
