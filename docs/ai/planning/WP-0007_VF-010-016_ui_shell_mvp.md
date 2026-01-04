# WP-0007 — UI Shell (MVP)

## VF Tasks Included
- VF-010: UI skeleton (simple web UI)
- VF-011: Questionnaire screen (single-question flow, no free text)
- VF-012: Plan review screen (approve/reject)
- VF-013: Progress screen (timeline + log stream)
- VF-014: Clarification screen (multiple-choice answers)
- VF-015: Summary screen (run instructions + open workspace link)
- VF-016: UI client for Local UI API (typed requests/responses)

## Goal
Enable users to interact with VibeForge through a structured web UI that covers questionnaire, plan review, progress tracking, clarifications, and final summary without any free-text inputs.

## Ordered Execution Steps

### 1. Establish UI skeleton and routing (VF-010)
- Set up base layout, navigation guard, and top-level state store (session id, phase, active task).
- Configure React Router (or simple view switcher) for the 6 screens.
- Ensure Vite dev server runs via `npm run dev` with TypeScript strict mode enabled.
- Files: `apps/ui/src/ui/App.tsx`, `apps/ui/src/main.tsx`

### 2. Build typed Local UI API client (VF-016)
- Define DTO types that mirror API contracts for sessions, questions, answers, plans, and results.
- Implement thin fetch wrapper with error handling and request/response validation.
- Centralize base URL/env config for API calls; support mock mode for offline dev.
- Files: `apps/ui/src/ui/api.ts`

### 3. Implement questionnaire screen (VF-011)
- Render one question at a time with structured controls only (radio/select/slider). No free-text fields.
- Show prior answers and allow resubmission per question.
- Wire submit to Local UI API client and advance on success.
- Files: `apps/ui/src/ui/screens/Questionnaire.tsx`

### 4. Implement plan review screen (VF-012)
- Display proposed plan/build spec summary with clear sections.
- Require explicit approve/reject buttons before proceeding; persist choice via API.
- Provide link/button to request clarifications if plan is rejected.
- Files: `apps/ui/src/ui/screens/PlanReview.tsx`

### 5. Implement progress screen (VF-013)
- Show current phase, active task, completed tasks, and live log stream (polling or SSE stub).
- Surface verifier results and gate decisions in timeline list.
- Allow navigation back to clarification/plan review when blocked.
- Files: `apps/ui/src/ui/screens/Progress.tsx`

### 6. Implement clarification screen (VF-014)
- Render multiple-choice clarification prompts returned by API (radio/buttons only).
- Display gate/verification context to explain why clarification is needed.
- Submit selected answer and route user back to appropriate screen.
- Files: `apps/ui/src/ui/screens/Clarification.tsx`

### 7. Implement summary screen (VF-015)
- Present final run instructions, key features built, and workspace path link.
- Offer buttons to download artifacts/logs and start a new session.
- Ensure the screen is reachable only after run completion.
- Files: `apps/ui/src/ui/screens/Summary.tsx`

## Done Means...

### Verification Commands
1. `cd apps/ui && npm install`
2. `cd apps/ui && npm run build`
3. `cd apps/ui && npm run dev -- --host` (manual smoke: load all screens, submit mock requests)
4. Manual: Confirm no free-text inputs appear on any screen and API calls succeed against Local UI API.

### Task Checklist
- [ ] VF-010: UI skeleton and routing
  - Layout and navigation between all screens in place
  - Shared session/phase state managed centrally
  - Verified by dev server smoke and routing tests (if added)
- [ ] VF-016: Typed Local UI API client
  - DTOs mirror Local UI API contracts
  - Fetch wrapper handles errors and mock mode
  - Verified by unit tests or integration stubs against API
- [ ] VF-011: Questionnaire screen
  - Structured controls only; per-question flow
  - Submits answers via typed client and advances phase
  - Verified by manual smoke and component tests
- [ ] VF-012: Plan review screen
  - Shows plan summary; approve/reject required
  - Routes to clarifications or progress appropriately
  - Verified by manual smoke and component tests
- [ ] VF-013: Progress screen
  - Timeline/log stream shows tasks and verifier status
  - Handles blocked states with navigation to clarifications
  - Verified by manual smoke and (optional) mock polling tests
- [ ] VF-014: Clarification screen
  - Renders multiple-choice prompts; no free text
  - Submits answer and returns to proper phase
  - Verified by manual smoke and component tests
- [ ] VF-015: Summary screen
  - Shows run instructions + workspace link
  - Offers restart/download actions
  - Verified by manual smoke after mocked completion

## Implementation Notes
- Use functional React components with hooks; keep state colocated but share via context/store for session data.
- Prefer reusable UI primitives (Button, Card, Timeline) to keep screens consistent.
- Mock API client responses when backend is unavailable to keep UI demoable.
- Enforce accessibility: label controls, manage focus on navigation, and ensure keyboard-only flows.
- Avoid introducing free-text inputs; prefer selects, radios, sliders, or buttons for all user choices.
