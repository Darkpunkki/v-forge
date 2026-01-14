---
doc_type: feature_validation_report
idea_id: "IDEA-0001-control-simulation"
run_id: "2026-01-14T22-39-39.893Z_run-1b5f"
generated_by: "Feature Validator"
generated_at: "2026-01-15T00:40:49.9899577+02:00"
source_inputs:
  - "docs/forge/ideas/IDEA-0001-control-simulation/latest/concept_summary.md"
  - "docs/forge/ideas/IDEA-0001-control-simulation/latest/epics_backlog.md"
  - "docs/forge/ideas/IDEA-0001-control-simulation/latest/epics.md (fallback if backlog missing)"
  - "docs/forge/ideas/IDEA-0001-control-simulation/latest/features_backlog.md"
  - "docs/forge/ideas/IDEA-0001-control-simulation/latest/features.md (fallback if backlog missing)"
  - "docs/forge/ideas/IDEA-0001-control-simulation/latest/idea_normalized.md (if present)"
  - "docs/forge/ideas/IDEA-0001-control-simulation/inputs/idea.md"
configs:
  - "docs/forge/ideas/IDEA-0001-control-simulation/inputs/validator_config.md"
status: "Draft"
---

# Feature Validation Report

## Summary

- Overall verdict: FAIL
- Critical issues: 1
- Warnings: 0
- Suggested patching: YES — allow_patch enabled; fixed malformed YAML list separators in the features backlog.

## Required-Field Checks

- YAML parse: FAIL (missing line breaks between multiple list items; `tags` lines run into the next `- id`).
- Feature count: WARN (YAML parse failed; inferred 23 features from the Markdown section).
- Required fields present: WARN (not machine-validated due to YAML parse failure).
- ID sequence: WARN (appears sequential FEAT-001..FEAT-023 in the Markdown section).
- epic_id references valid: WARN (epic_ids appear to map to EPIC-001..EPIC-008).

## Coverage Check (by Epic)

Note: Coverage mapping inferred from the Markdown section because the YAML list was malformed.

- EPIC-001: OK
  - Missing areas: None.
  - Notes: None.
- EPIC-002: OK
  - Missing areas: None.
  - Notes: None.
- EPIC-003: OK
  - Missing areas: None.
  - Notes: None.
- EPIC-004: OK
  - Missing areas: None.
  - Notes: None.
- EPIC-005: OK
  - Missing areas: None.
  - Notes: None.
- EPIC-006: OK
  - Missing areas: None.
  - Notes: None.
- EPIC-007: OK
  - Missing areas: None.
  - Notes: None.
- EPIC-008: OK
  - Missing areas: None.
  - Notes: None.

## Boundary Issues (Cross-Epic Leakage)

- None identified.

## Duplicate & Overlap Issues

- None identified.

## Acceptance Criteria Quality

- Features with weak criteria: None.
- Required fixes: None.

## Invariant & Exclusion Violations (Critical)

- None identified.

## Release Target & Priority Sanity

- MVP coherence: OK.
- Notes on retargeting suggestions: None.

## Metadata Defects

- Malformed YAML list separators in the features backlog (`tags` lines run into the next `- id`), preventing parsing; fixed by inserting line breaks between list items.

## Proposed Patch (if patching not allowed)

- Insert a newline between each `tags: [...]` line and the next `- id:` entry to restore valid YAML list structure.

```yaml
features:
  - id: "FEAT-002"
    ...
    tags: ["config", "ui"]
  - id: "FEAT-003"
    ...
```
