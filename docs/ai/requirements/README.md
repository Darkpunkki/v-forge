---
phase: requirements
title: Requirements & Problem Understanding
description: Clarify the problem space, gather requirements, and define success criteria
---

# Requirements & Problem Understanding

## Problem Statement
**What problem are we solving?**

- Builders need a safe way to generate runnable app skeletons from structured questionnaires without allowing arbitrary prompts.
- Today, handoff between questionnaire, plan, and execution is manual and error-prone; VibeForge aims to automate it end-to-end.
- Current workaround is running bespoke scripts for each project; this is slow, inconsistent, and risky for host machines.

## Goals & Objectives
**What do we want to achieve?**

- Generate isolated workspaces per session that contain code and artifacts derived from approved plans.
- Maintain a deterministic, multiple-choice questionnaire that feeds plan generation and execution steps.
- Provide a local API (FastAPI) for UI clients with clear DTOs and phase-guarded transitions.
- Enforce safety rails on file operations (path whitelisting, patch validation) before any write.
- Keep provider-agnostic model hooks to swap between OpenAI and future local models.

## User Stories & Use Cases
**How will users interact with the solution?**

- As a **builder**, I start a session, answer structured questions, and receive a generated plan for review.
- As a **reviewer**, I approve or reject the plan; approvals trigger code generation and patch application inside my workspace.
- As an **operator**, I can view session progress, artifacts, and logs to validate that safety rules are enforced.

## Success Criteria
**How will we know when we're done?**

- All `/sessions` endpoints enforce valid phase transitions and return typed responses.
- Workspace creation and patch application never escape `workspaces/{session_id}` and fail safely on invalid diffs.
- Questionnaire flow completes with deterministic prompts; plan summaries are generated and can be approved or rejected.
- Unit tests in `apps/api/tests` remain passing and cover new flows; new functionality includes corresponding tests.

## Constraints & Assumptions
**What limitations do we need to work within?**

- MVP runs locally; remote deployment will come later with token-based auth.
- File system is the primary persistence layer; no database is required yet.
- No free-text inputs are permitted from the UI; all inputs are structured choices.
- Model providers may be offline; code should allow graceful degradation or skips when keys are missing.

## Questions & Open Items
**What do we still need to clarify?**

- How should verification harness results be surfaced to the UI once command runner work begins (WP-0003)?
- What minimum telemetry is required before enabling remote deployments?
- Which additional plan review gates are needed to catch unsafe commands beyond patch validation?
