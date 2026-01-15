---
doc_type: sandboxing_levels
idea_id: "IDEA-0002-control-sim"
generated_by: "Codex"
generated_at: "2026-01-16T00:20:20.5948621+02:00"
source_inputs:
  - "docs/forge/ideas/IDEA-0002-control-sim/latest/tasks.md"
status: "Draft"
---

# Remaining FEATs by AI sandboxing level

Context: FEAT-001 through FEAT-003 are complete. Levels are cumulative.

## Level 0 - MVP (lowest tier, minimal real-agent interaction via API)

Priority order:
1. FEAT-004: Tick advancement with per-agent activity cap
2. FEAT-005: Graph-gated message validation
3. FEAT-008: Lifecycle state transitions and guardrails
4. FEAT-009: Status and tick state exposure

## Level 1 - Safe-mode sandbox (no external calls)

Priority order:
1. FEAT-006: Deterministic stubbed responses

## Level 2 - Observable sandbox (event clarity and durability)

Priority order:
1. FEAT-007: Message event emission with tick metadata
2. FEAT-010: Persisted simulation event log
3. FEAT-011: Event streaming for control panel

## Level 3 - Operator UX (monitoring and visual feedback)

Priority order:
1. FEAT-012: Agent graph visualization
2. FEAT-013: Message log view with filters
3. FEAT-014: Status and tick indicators
