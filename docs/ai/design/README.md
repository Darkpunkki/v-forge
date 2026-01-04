---
phase: design
title: System Design & Architecture
description: Define the technical architecture, components, and data models
---

# System Design & Architecture

VibeForge is an AI-powered application factory that turns structured questionnaire answers into runnable app workspaces. The current focus is a FastAPI-driven Local UI API plus safety rails around workspace isolation and patch application.

## Architecture Overview
**What is the high-level system structure?**

```mermaid
graph TD
  UI[Constrained Questionnaire UI] -->|Typed requests| API[Local UI API (FastAPI)]
  API -->|Session lifecycle| Session[Session Coordinator]
  Session -->|Questionnaire/plan state| Store[Workspace + Artifacts]
  Session -->|Patch specs| Patch[Patch Applier]
  Session -->|Model prompts| Model[Model Layer]
  Model -->|Concept/plan responses| Session
  Patch -->|Validated file writes| Store
```

- **UI (React+Vite skeleton)**: renders multiple-choice questions only and calls the Local UI API.
- **Local UI API (FastAPI)**: routers under `apps/api/vibeforge_api/routers/` handle sessions, questionnaire flow, and plan approvals.
- **Session Coordinator**: orchestrates questionnaire → plan → execution phases; enforces allowed transitions.
- **Workspace Manager**: creates isolated `workspaces/{session_id}` directories and prevents path traversal.
- **Patch Applier**: applies unified diffs with validation to keep writes inside the workspace root.
- **Model Layer**: provider-agnostic abstraction (OpenAI today, future local LLMs) that produces plan/concept text.

## Data Models
**What data do we need to manage?**

- **Sessions**: `session_id`, `phase`, questionnaire progress, plan decision state.
- **Artifacts**: metadata about generated files and operations per session stored alongside workspaces.
- **Patches**: unified diffs plus validation context (allowed paths, file existence checks).
- **Build Specs / Plans**: serialized concept/plan outputs generated from questionnaire answers.
- **Questionnaire State**: ordered questions, allowed options, and recorded answers.

## API Design
**How do components communicate?**

- **External API**: FastAPI endpoints under `/sessions` for creating sessions, fetching questions, submitting answers, viewing plan summaries, and recording approve/reject decisions.
- **Internal interfaces**: Session coordinator methods in `vibeforge_api/core/` expose operations used by routers; workspace and patch helpers provide validated file operations.
- **Contracts**: Pydantic models in `vibeforge_api/models/` define request/response envelopes; session phases gate transitions.
- **Auth**: MVP is local-only and unauthenticated; plan to introduce token-based auth when remote deployment begins.

## Component Breakdown
**What are the major building blocks?**

- **Frontend**: `apps/ui` (skeleton) for constrained questionnaire and plan review screens.
- **Backend services**: FastAPI app in `apps/api/vibeforge_api/main.py` wiring routers and dependencies.
- **Core modules**: session management (`core/session.py`), questionnaire engine (`core/questionnaire.py`), workspace manager (`core/workspace.py`), patch applier (`core/patch.py`), artifacts store (`core/artifacts.py`).
- **Storage**: filesystem-only persistence under `workspaces/` with metadata JSON files; no database yet.
- **Integrations**: OpenAI client (via env `OPENAI_API_KEY`), future provider adapters will plug into model layer.

## Design Decisions
**Why did we choose this approach?**

- **No free text inputs** to minimize prompt injection and keep plan generation deterministic.
- **Phase-safe transitions** ensure questionnaire completion before plan approval/execution.
- **Workspace isolation** per session protects host filesystem and simplifies artifact cleanup.
- **Patch validation** blocks path traversal and enforces write boundaries before applying diffs.
- **Provider-agnostic model layer** preserves flexibility for local or hosted LLMs.

## Non-Functional Requirements
**How should the system perform?**

- **Performance**: API latency should stay low for questionnaire calls; model requests dominate response time.
- **Scalability**: horizontal scaling via multiple FastAPI workers; shared storage can be introduced when moving beyond single-host dev.
- **Security**: enforce path whitelists for file writes, validate session phases, avoid free-form user input, and keep secrets in environment variables.
- **Reliability**: unit tests for core modules; workspace operations must be idempotent and rollback-safe on failure.
