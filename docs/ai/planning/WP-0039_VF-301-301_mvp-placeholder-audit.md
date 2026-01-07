# WP-0039 — MVP placeholder audit inventory

## Status
- Done

## Context
- Chapter(s): 30 MVP/Placeholder Cleanup
- Why now:
  - Multiple MVP shortcuts remain and need a consolidated cleanup plan.
  - Teams need a single inventory to prioritize post-MVP remediation work.
  - The audit unblocks follow-on WPs that replace placeholder flows.

## Goal
- Publish a consolidated inventory of MVP/placeholder shortcuts with remediation guidance.

## VF Tasks (canonical)
- [x] **VF-301 — Audit MVP/placeholder shortcuts and publish cleanup inventory**
  - Catalog every MVP/placeholder/stub implementation still in use (e.g., mock demo flow in `apps/api/vibeforge_api/routers/sessions.py`, mock project generator in `apps/api/vibeforge_api/core/mock_generator.py`, stub adapters in `models/agent_framework_stubs.py`, local provider stub in `models/local/provider.py`). Produce a consolidated inventory doc with file paths, line refs, and suggested remediation path for each item.
  - **Status:** Done
  - **Done when:** `docs/ai/planning/mvp_placeholder_audit.md` (or similar) lists each placeholder with owner, impact, and whether to replace, guard, or defer.
  - **Verify:** Manual review of the audit doc against the cited files; CI/docs build if applicable.
  - **Files:** `docs/ai/planning/mvp_placeholder_audit.md`, `docs/ai/planning/WORK_PACKAGES.md`
  - **Verified:** `PYTHONPATH=/workspace/v-forge pytest` (note: plain `pytest` fails without PYTHONPATH)

## Plan
### Approach
- Scan the codebase for known MVP/placeholder paths and confirm current usage.
- Compile a single inventory doc with file paths, line references, and remediation options.
- Include owner/impact notes and classify each placeholder (replace/guard/defer).
- Cross-link the inventory from future WPs or checklist items as needed.

### Progress Notes
- 2026-01-07: Drafted MVP placeholder inventory at `docs/ai/planning/mvp_placeholder_audit.md`.

### Actionable Task Array
BEGIN_ACTIONABLE_TASK_ARRAY
steps:
  - vf: VF-301
    intent: "Create a consolidated MVP placeholder audit document with remediation guidance."
    touches:
      - "docs/ai/planning/mvp_placeholder_audit.md"
      - "apps/api/vibeforge_api/routers/sessions.py"
      - "apps/api/vibeforge_api/core/mock_generator.py"
      - "models/agent_framework_stubs.py"
      - "models/local/provider.py"
    done_when:
      - "Audit doc lists each placeholder with file path, line references, owner, impact, and remediation recommendation."
      - "Checklist references remain unchanged; audit doc is discoverable from planning docs."
    verify:
      - "Manual review"
END_ACTIONABLE_TASK_ARRAY

## Acceptance Criteria
- VF-301: Inventory doc lists each placeholder with path and line references.
- VF-301: Each entry includes owner, impact, and replace/guard/defer recommendation.
- VF-301: Audit doc location is documented and easy to find.

## Verify
- `pytest`

## Dependencies
- None

## Risks / Recovery
- Risk: Placeholder inventory misses less obvious stubs.
  - Mitigation: Cross-check against checklist and known stub modules; invite follow-up additions.
- Risk: Audit doc becomes outdated as placeholders are removed.
  - Mitigation: Add a “last reviewed” date and update when related WPs land.
- Recovery: If verification fails, scope the inventory to the listed files and expand iteratively.
