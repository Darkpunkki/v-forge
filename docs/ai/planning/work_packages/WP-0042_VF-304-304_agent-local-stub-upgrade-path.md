# WP-0042 — Agent/local stub upgrade path plan

## Status
- Done (2026-01-12)

## Context
- Chapter(s): 30 MVP/Placeholder Cleanup
- Why now:
  - Stub adapters and local provider placeholders need an explicit upgrade path before scheduling real integrations.
  - The MVP placeholder audit calls for clear next steps and acceptance tests.
  - A documented plan prevents ambiguous scope creep in future WPs.

## Goal
- Define a clear, testable upgrade path for agent framework stubs and LocalProvider integrations.

## VF Tasks (canonical)
- [ ] **VF-304 — Define upgrade path for agent/local stubs (LangGraph/CrewAI/AutoGen + LocalProvider)**
  - Turn the stub adapters in `models/agent_framework_stubs.py` and the `LocalProvider` stub in `models/local/provider.py` into explicit upgrade tasks: document intended feature flags, minimum viable integrations, and acceptance tests so they can be scheduled without ambiguity.
  - **Status:** Planned
  - **Done when:** A follow-on design/plan doc exists outlining scope, rollout guards, and test hooks for each stubbed provider/adapter; stubs are referenced from the audit with clear next-step VF IDs or WP links.
  - **Verify:** Manual review of the plan doc and cross-check that stubs are annotated with links to the planned work.

## Plan
### Approach
- Review current stub adapters and LocalProvider placeholders to catalog expected behaviors.
- Define feature flags or configuration toggles to gate future integrations.
- Outline acceptance tests and verification hooks for each provider/adapter path.
- Document the upgrade path in a plan/design doc and link it from the audit/stub locations.

### Actionable Task Array
BEGIN_ACTIONABLE_TASK_ARRAY
steps:
  - vf: VF-304
    intent: "Produce a documented upgrade path for stubbed agent frameworks and the LocalProvider with explicit acceptance tests."
    touches:
      - "models/agent_framework_stubs.py"
      - "models/local/provider.py"
      - "docs/ai/planning/WP-0042_VF-304-304_agent-local-stub-upgrade-path.md"
    done_when:
      - "Plan/design documentation specifies scope, guards, and acceptance tests for each stubbed provider/adapter."
      - "Audit/stub references point to the planned work items or VF IDs."
    verify:
      - "pytest"
END_ACTIONABLE_TASK_ARRAY

## Acceptance Criteria
- VF-304: Upgrade plan documents scope, rollout guards, and acceptance tests for each stubbed provider/adapter.
- VF-304: Stubs are cross-referenced with the planned work items or VF IDs.
- VF-304: Documentation includes verification hooks for future implementation.

## Verify
- Add tests
- `pytest`

## Dependencies
- WP-0039 ✓

## Risks / Recovery
- Risk: Plan doc becomes too broad, making later WPs ambiguous.
  - Mitigation: Keep scope minimal and enumerate concrete acceptance tests per provider.
- Risk: Stub references are missed, leaving gaps in the upgrade path.
  - Mitigation: Search for stub files and annotate them with links to the plan.
- Recovery: If verification fails, narrow the plan to the minimum viable integration steps and revalidate references.
