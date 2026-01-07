# MVP Placeholder Audit Inventory

_Last reviewed: 2026-01-07_

## Scope
This inventory tracks MVP placeholders and stubs that remain in the runtime path and require post-MVP remediation. Each entry includes file + line references, ownership, impact, and a recommended disposition.

## Inventory
| ID | Location (file:lines) | Placeholder / Shortcut | Owner | Impact | Recommendation | Follow-up |
| --- | --- | --- | --- | --- | --- | --- |
| MP-001 | `apps/api/vibeforge_api/routers/sessions.py:122-130` | Questionnaire completion triggers `mock_generator.generate()` and skips directly to `COMPLETE` (MVP demo shortcut). | API (Sessions) | Skips concept/plan/execution phases; prevents real pipeline from running. | **Replace** with real BuildSpec → concept → plan flow or gate behind feature flag. | VF-302 |
| MP-002 | `apps/api/vibeforge_api/core/mock_generator.py:1-233` | Mock generator writes demo projects instead of real artifacts. | API (Workspace/Artifacts) | Demo-only output; no real app scaffolding or execution pipeline. | **Replace** with real scaffold pipeline or keep behind explicit demo flag. | VF-302 |
| MP-003 | `apps/api/vibeforge_api/routers/sessions.py:158-166` | `get_plan_summary` returns hardcoded plan summary. | API (Plan Review) | Plan review displays fake plan details; no TaskGraph linkage. | **Replace** with TaskGraph-backed summary and real constraints. | VF-303 |
| MP-004 | `apps/api/vibeforge_api/routers/sessions.py:213-238` | `get_progress` uses simplified task lists/logs instead of TaskGraph + event data. | API (Progress) | Progress UI lacks real task status, sequencing, or event context. | **Replace** with TaskGraph/event-backed progress report. | VF-303 |
| MP-005 | `models/agent_framework_stubs.py:1-105` | LangGraph/CrewAI/AutoGen adapters raise `NotImplementedError`. | Model layer (Agent frameworks) | Non-OpenAI frameworks unavailable; runtime fails if selected. | **Replace** with real adapters or guard with feature flags. | VF-304 |
| MP-006 | `models/local/provider.py:1-118` | LocalProvider stub raises `NotImplementedError` for local model usage. | Model layer (LLM providers) | Local model selection fails; only OpenAI path works. | **Replace** with local provider integrations or guard. | VF-304 |
| MP-007 | `models/agent_framework.py:106-223` | DirectLlmAdapter uses hardcoded prompts and treats any response as success. | Model layer (Agent runtime) | Limited role configuration and validation; errors slip through. | **Replace** with AgentRegistry prompts + strict validation. | VF-102 follow-through |

## Ownership Notes
- **API (Sessions/Plan/Progress):** Backend team maintaining `apps/api/vibeforge_api/routers/sessions.py`.
- **Model layer:** Agent and provider integrations under `models/`.

## Follow-up Guidance
- Prefer creating feature flags for demo-only shortcuts if replacement is not immediate.
- Update this inventory whenever stubs are removed or replaced.
