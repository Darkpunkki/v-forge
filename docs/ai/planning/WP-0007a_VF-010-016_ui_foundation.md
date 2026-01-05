# WP-0007a — UI Foundation (skeleton + API client)

**Status:** In Progress
**Started:** 2026-01-05

## VF Tasks Included
- VF-010: UI skeleton (simple web UI)
- VF-016: UI client for Local UI API (typed requests/responses)

## Goal
Set up Vite+React project with routing, layout structure, and typed API client for communicating with the Local UI API.

## Ordered Execution Steps

### 1. Initialize Vite+React+TypeScript project
- Create Vite project in `apps/ui/` with React and TypeScript
- Set up development server configuration
- Configure base routing with React Router
- Create basic layout structure (header, main content area)
- Add minimal styling (MVP: simple CSS, no complex framework needed)

### 2. Implement typed API client
- Create API client module with typed request/response interfaces
- Match API endpoints from Local UI API:
  - POST /sessions - Create session
  - GET /sessions/{id}/question - Get next question
  - POST /sessions/{id}/answers - Submit answer
  - GET /sessions/{id}/progress - Get progress
  - GET /sessions/{id}/result - Get final result
- Use fetch API with proper error handling
- Export typed functions for each endpoint

### 3. Create placeholder screens with routing
- Home/start screen
- Questionnaire screen (placeholder)
- Plan review screen (placeholder)
- Progress screen (placeholder)
- Clarification screen (placeholder)
- Summary/result screen (placeholder)
- Set up React Router for navigation between screens

## Done Means...

### Verification Commands
1. `cd apps/ui && npm install` - Dependencies install successfully
2. `cd apps/ui && npm run dev` - Dev server starts on http://localhost:5173
3. `cd apps/ui && npm run build` - Production build succeeds
4. `cd apps/ui && npm run type-check` (if configured) - TypeScript compilation succeeds
5. Manual: Navigate to http://localhost:5173 and verify routing works
6. Manual: Test API client can create session (check browser console/network tab)

### Task Checklist
- [x] VF-010: UI skeleton created
  - Vite+React+TypeScript project initialized in apps/ui/ (already existed, enhanced)
  - React Router configured with basic routes
  - Layout component with header and main content area
  - Placeholder screens for all major views (Home, Questionnaire, PlanReview, Progress, Clarification, Result)
  - Dev server runs on http://localhost:5173
  - **Files created:**
    - `src/components/Layout.tsx` - Main layout with navigation
    - `src/screens/Home.tsx` - Home/start screen
    - `src/screens/Questionnaire.tsx` - Question answering screen
    - `src/screens/PlanReview.tsx` - Plan approval screen
    - `src/screens/Progress.tsx` - Progress monitoring screen (with polling)
    - `src/screens/Clarification.tsx` - Placeholder for clarifications
    - `src/screens/Result.tsx` - Final result display
  - **Verify:** `npm run dev` starts server, routing works in browser

- [x] VF-016: API client implemented
  - Typed interfaces for all API request/response models matching backend Pydantic models
  - API client functions for: createSession, getQuestion, submitAnswer, getProgress, getResult, getPlan, decidePlan
  - Proper error handling with typed error responses and custom ApiError class
  - Base URL configuration (defaults to http://localhost:8000, configurable via VITE_API_BASE)
  - Exported from centralized module (src/api/client.ts)
  - **Files created:**
    - `src/types/api.ts` - TypeScript type definitions matching backend models
    - `src/api/client.ts` - Typed API client with all endpoints
  - **Verify:** API client can create session and get questions (test in browser console or component)

## Implementation Notes
- Keep dependencies minimal for MVP:
  - Vite (build tool)
  - React + React DOM
  - React Router (routing)
  - TypeScript (type safety)
  - No state management library needed yet (use React state/context)
  - No UI component library needed yet (use plain HTML elements styled with CSS)
- API client should be simple fetch wrapper, no need for complex libraries like React Query yet
- Focus on getting the foundation solid - individual screens will be implemented in follow-up WPs
- Ensure CORS is handled correctly (API must allow requests from http://localhost:5173)
