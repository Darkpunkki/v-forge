# idea.md — Sample App Idea (Generic)

## One-sentence idea

Build a small web application that helps users turn a problem statement into a structured plan and a set of actionable steps, with progress tracking and simple collaboration.

---

## Purpose and motivation

I want a proof-of-concept application that demonstrates:

- clear end-to-end product flow (input → processing → outputs)
- a backend API + a simple frontend UI
- basic persistence and auditability
- a maintainable, testable codebase

The application should be realistic enough to show engineering ability, but small enough to complete as an MVP.

---

## Target users

Primary:

- Individual developer (me) using the app to structure projects and learn.

Secondary:

- Small team (2–5 people) who want lightweight planning and tracking.

---

## User problem

When starting a project, it’s easy to lose clarity:

- requirements are vague
- scope creeps
- tasks are not well-defined
- progress is not visible

The user needs a lightweight flow to capture the “why/what/how” at a high level, then refine it into a clear plan with steps.

---

## Core user flow (conceptual)

1. User creates a new project (or “workspace”).
2. User writes a short description of what they want to build.
3. The system converts the description into a structured summary:
   - goals, constraints, assumptions, out-of-scope
4. The system generates a plan outline and a set of actionable items.
5. User can review, edit, and approve the plan.
6. Once approved, the user can track progress:
   - mark items done
   - view what remains
   - see basic history/audit log

---

## Inputs

- A project title
- A free-form description (text)
- Optional constraints (bullets) the user can add:
  - time/budget
  - platforms
  - must-have / must-not-have

---

## Outputs

- A structured “project summary” document
- A plan outline
- A list of actionable items (tasks/steps)
- Progress view (completed vs remaining)
- Basic audit/history log of key changes

---

## Key requirements (non-negotiables)

- Must support multiple projects/workspaces.
- Must persist data (so the user can return later).
- Must allow the user to edit the generated plan/items.
- Must support approval of the plan before tracking begins.
- Must have a simple UI that is usable without reading documentation.
- Must include basic tests for the core backend logic.

---

## Preferences (nice to have)

- Simple authentication (optional for MVP; may be added later).
- Export outputs as Markdown files.
- A “read-only share link” for a project (later).

---

## Out of scope (explicit)

- Payments/subscriptions
- Real-time multi-user editing
- Mobile app (web-only for now)
- Complex role-based access control (beyond basic auth, if any)

---

## Tech and implementation notes (optional / flexible)

- Web application with a backend API and a frontend UI.
- Backend could be Python (FastAPI) or Java (Spring Boot) — not decided yet.
- Frontend could be React/Vite or another lightweight UI — not decided yet.
- Database could be SQLite for MVP, later PostgreSQL.
- Deployment can be local-first; cloud deployment is a later step.

---

## Open questions

- What is the minimum set of fields for a “project summary”?
- Should the system generate items automatically, or only structure what the user wrote?
- Do we want authentication in MVP, or keep it single-user local?
- What export formats are required (Markdown only, or also JSON)?
