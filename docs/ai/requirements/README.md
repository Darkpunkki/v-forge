---
phase: requirements
title: VibeForge Requirements & Problem Understanding
description: Structured-only app generation via orchestrated multi-agent factory with strong safety gates and reproducible outputs
---

# VibeForge Requirements & Problem Understanding

## Problem Statement
People want to “vibe build” a small runnable app without writing code or crafting prompts, but current AI coding workflows are:
- **Prompt-driven** (free-text = unpredictable, hard to constrain)
- **Unsafe by default** (agents can propose risky file/system commands)
- **Hard to reproduce** (outputs vary, plans drift, debugging is painful)
- **Manual and fragile** (human glue between questionnaire → idea → plan → execution → verification)

**VibeForge** solves this by converting **strictly structured user input** into a **deterministic BuildSpec** and then executing a **gated multi-agent factory pipeline** that produces a **local runnable repo** with tests and a final run summary.

## Vision (What VibeForge is)
VibeForge is an “app factory” with three pillars:

1) **Structured-only user input**
   - No free text to describe the app.
   - Users choose from curated options (domain, platform, vibe sliders, constraints).
   - The system owns interpretation, scope control, and safety.

2) **Orchestrated creativity with controlled randomness**
   - The orchestrator uses a seed + “twist cards” to generate an idea that still fits the user’s constraints.
   - Users can influence “randomness” but cannot fully specify the exact result.

3) **A safe, test-driven build pipeline**
   - Multi-agent execution is mediated by policy gates, allowlists, and verification harnesses.
   - Artifacts are persisted at each stage for auditability and replay.

## Target Users and Roles
- **User (Builder):** Wants a fun/useful small app generated from structured questions, with minimal effort.
- **Operator (Developer/You):** Maintains the factory, policy rules, stack presets, and agent reliability.
- **Reviewer (Optional):** Approves/rejects plans, views diffs, sees verification results.

## Core Concepts (Glossary)
- **IntentProfile:** Structured answers from the questionnaire (no free-text).
- **BuildSpec:** Deterministic contract derived from IntentProfile (stack preset, seed, budgets, policies).
- **TaskGraph:** DAG execution plan of tasks with dependencies, constraints, and verification steps.
- **AgentResult:** Standard agent output contract (diff + commands-to-run + structured notes).
- **Workspace:** Isolated session directory where code is generated and validated.
- **Gates:** Safety/feasibility checks before diffs/commands touch disk.
- **Verification Harness:** Runs unit tests/build/smoke, captures logs, and produces pass/fail artifacts.

## Goals & Objectives
### G1 — Structured “vibe” input → deterministic spec
- Convert structured user input into a stable BuildSpec.
- Enforce budgets (time/features/screens/entities) and policy constraints (network, auth, allowed commands).
- Support controlled randomness through idea seeds + twist cards.

### G2 — Safe automated execution with auditability
- Ensure all code changes are applied via gated diffs inside a session workspace.
- Ensure all commands are executed via allowlists.
- Store artifacts at each stage (profile/spec/concept/plan/logs/results).

### G3 — Provider-agnostic agent layer
- Make it easy to switch between OpenAI API, Anthropic, and local models later.
- Keep agent output stable via schemas/validation (e.g., structured outputs / JSON schema). :contentReference[oaicite:1]{index=1}

### G4 — “It runs locally”
- Generated app must have a clear run path (README + commands).
- Minimal smoke verification should be supported in the pipeline.

## Non-Goals (MVP)
- Not a general-purpose “prompt IDE” for arbitrary prompts.
- Not a full cloud platform (remote deployment later).
- Not a marketplace / multi-tenant SaaS (until after the local MVP is stable).
- Not guaranteed production-grade apps; MVP targets “small but working” apps.

## Functional Requirements
### FR1 — Questionnaire & Intent capture (no free text)
- Present multiple-choice questions and slider-like choices.
- Persist answers as IntentProfile.
- Allow backtracking within rules (e.g., change domain selection, re-evaluate budgets).

### FR2 — Spec building (IntentProfile → BuildSpec)
- Produce deterministic BuildSpec including:
  - stack preset (allowlist)
  - seed/twists
  - scope budgets
  - policy guardrails (network/auth/commands)
  - acceptance criteria (must build, must test, must run)

### FR3 — Concept + Plan generation with review
- Orchestrator converts BuildSpec into:
  - Concept document (human-readable)
  - TaskGraph (machine-executable)
- User can approve/reject plan.
- Rejection supports revision loop (e.g., reduce scope, regenerate twist).

### FR4 — Distribution & agent execution
- TaskMaster schedules tasks from TaskGraph.
- Tasks are routed to “roles” (scaffold/ui/logic/tests/fixer/reviewer).
- Agents return AgentResult (diff + proposed commands + notes).

### FR5 — Gates and enforcement (safety & feasibility)
- Block unsafe diffs (path traversal, forbidden patterns, large diffs, disallowed file types).
- Block unsafe commands (only allowlisted families).
- Enforce “network during build” policy (deny/ask/allow).

### FR6 — Workspace management
- Create isolated workspace per session.
- Apply diffs only inside the workspace.
- Preserve an immutable artifact trail (inputs, outputs, logs).

### FR7 — Verification harness
- Run per-task verification steps and capture output logs.
- Run global verification at end (build/test/smoke).
- On failures, trigger fix loop policies (retry, escalate, hard-stop with report).

### FR8 — Progress + observability
- Emit progress events for UI:
  - phase transitions, task started/completed, gates passed/failed, verifications results
- Provide operator-friendly debug artifacts.

## System Qualities (Non-Functional Requirements)
### NFR1 — Safety-first defaults
- “Deny by default” posture for file writes, commands, and network access.
- All risky operations pass through gates and are logged.

### NFR2 — Determinism and reproducibility
- BuildSpec seed and policy configuration recorded in artifacts.
- Execution can be replayed to diagnose failures (within reason).

### NFR3 — Reliability under partial failures
- If an agent fails, system creates actionable failure artifacts.
- Fix loop is bounded (retry limits + escalation).

### NFR4 — Provider portability
- Minimal dependency on provider-specific features.
- Standardized AgentResult format keeps the pipeline stable across models.

## Success Criteria (MVP Definition of Done)
- A user can complete questionnaire → get a plan → approve → system generates a runnable repo in a workspace.
- Phase transitions are enforced (no illegal calls).
- At least one end-to-end “happy path” example passes:
  - gates pass
  - diffs apply
  - tests run
  - run instructions are produced
  - final summary is coherent
- Unsafe diffs/commands are blocked with clear error reports.
- Artifacts exist for each stage and allow debugging after the run.

## Constraints & Assumptions
- Local-first MVP with a simple UI (do not overbuild frontend).
- No database required initially; file-based persistence is acceptable.
- No free-text input for app intent; only curated options.
- Model keys may be missing; system must degrade gracefully (fail with clear guidance).
- Development workflow is WP-driven (Work Packages) using ai-devkit and Claude Code CLI custom commands. :contentReference[oaicite:2]{index=2}

## Questions & Open Items
- What is the initial allowlist of stack presets (e.g., FastAPI + React, Spring Boot + Vite)?
- What is the minimum “must run locally” standard per stack preset (commands + ports + smoke route)?
- How should “ask” mode work for network access during build (UI prompt + operator override)?
- What is the minimal set of twist cards that keeps outputs fun but predictable?
- How should verification output be summarized for the UI (short form) vs operator logs (full)?

## Out of Scope for Requirements (handled elsewhere)
- Detailed API schemas (see design + checklist)
- Detailed C4 diagrams and module boundaries (see design)
- Task breakdown and sequencing (see planning + WORK_PACKAGES + VF checklist)
