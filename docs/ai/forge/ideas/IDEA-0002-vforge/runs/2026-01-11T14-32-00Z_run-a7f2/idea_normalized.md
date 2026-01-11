---
doc_type: idea_normalized
idea_id: "IDEA-0002-vforge"
run_id: "2026-01-11T14-32-00Z_run-a7f2"
generated_by: "Idea Normalizer"
generated_at: "2026-01-11T14:32:00Z"
source_inputs:
  - "docs/ai/forge/ideas/IDEA-0002-vforge/inputs/idea.md"
configs: []
status: "Draft"
---

# Idea (Normalized)

## Summary

VibeForge is an AI-powered application factory that generates working applications from structured questionnaires (no free-text input). The system operates in two modes: a user-facing Session mode for app generation, and an admin-facing Control Panel for pipeline customization and agent simulation.

## Goals

- Enable non-technical users to generate working applications through guided questionnaire completion
- Provide real-time visibility into the multi-agent app generation process
- Allow admin users to fully customize and simulate the agent pipeline
- Deliver working application code with deployment instructions

## Target Users

- **End users (Session mode):** Users who want to create applications without coding, guided by structured questionnaires
- **Admin users (Control Panel mode):** Technical users who configure, customize, and simulate agent pipelines

## Primary Use Cases

- **UC-01:** End user fills a questionnaire to define an application, receives generated code and run instructions
- **UC-02:** Admin user creates custom agent simulations with configurable roles and tasks
- **UC-03:** Admin user monitors and drills down into agent-to-agent communication during simulations
- **UC-04:** Admin user customizes agent settings (provider, model, cost reporting)

## Inputs

- **Session mode:** User responses to a structured questionnaire (no free-text)
- **Control Panel mode:** Agent configuration (roles, tasks, provider/model selection)

## Outputs

- **Session mode:**
  - Generated application code
  - Custom instructions on how to run the application
  - Real-time metrics (agent count, API requests, etc.)
- **Control Panel mode:**
  - Simulation status and agent output
  - Drill-down views into agent communication and actions
  - Cost and token usage reports

## Conceptual Workflow

### Session Mode (End User)

1. User fills a structured questionnaire
2. System generates a plan/idea for the application
3. User verifies/approves the plan
4. Plan is forwarded to the Orchestrator agent
5. Orchestrator divides the plan into subtasks
6. Subtasks are distributed to role-based agents:
   - Foreman: defines code snippets, assigns tasks to Workers
   - Worker: writes actual code
   - Reviewer: reviews Worker output for quality and requirements
   - Fixer: handles special tasks (e.g., fixing previously working code)
7. Real-time progress/metrics displayed to user
8. Final application code and run instructions presented to user

### Control Panel Mode (Admin)

1. Admin selects number of agents for simulation
2. Admin assigns role and task to each agent
3. Admin configures agent settings (provider, model, cost tracking)
4. Simulation runs with real-time status and output per agent
5. Admin can drill down into agent-to-agent communication
6. Results and costs are displayed

## Core Capabilities

- The system can generate structured questionnaires for app definition
- The system can convert questionnaire responses into an application plan
- The system can orchestrate multiple specialized agents to produce code
- The system can display real-time progress metrics during generation
- The system can provide agent simulation with customizable roles and tasks
- The system can track and report API costs and token usage per agent

## Constraints

- Session mode questionnaires must be structured (no free-text input allowed)
- Agent pipeline must support multiple specialized roles (Orchestrator, Foreman, Worker, Reviewer, Fixer)
- Real-time visibility into agent activity is required during both modes

## Preferences

- Clear separation between Session (end-user) and Control Panel (admin) interfaces
- Agents should be customizable per provider/model from the Control Panel
- UI should allow drilling down into agent-to-agent communication

## Out-of-Scope / Exclusions

- Free-text input for application definition (questionnaire must be structured)
- (Implicit) Hosting or deployment of generated applications—only code and instructions are provided

## Terminology

- **Session mode:** The end-user-facing workflow for generating an application
- **Control Panel mode:** The admin-facing interface for pipeline customization and simulation (`/control` route)
- **Orchestrator:** Top-level agent that divides plans into subtasks and coordinates other agents
- **Foreman:** Agent that defines necessary code snippets and forwards tasks to Workers
- **Worker:** Agent that writes actual code
- **Reviewer:** Agent that reviews Worker output for quality and requirements
- **Fixer:** Agent that handles special tasks, such as fixing code that was previously deemed working
- **Simulation:** A configurable run of agents with assigned roles and tasks, used for testing or custom purposes

## Open Questions / Ambiguities

- What is the exact structure and content of the questionnaire? (not specified)
- What is the format of the generated application? (single-page app, backend+frontend, etc.)
- What AI providers/models should be supported out of the box?
- What is the mechanism for agent-to-agent communication? (message passing, shared state, etc.)
- Is there authentication/authorization for accessing Session vs Control Panel modes?
- What languages/frameworks should the generated applications support?
- Should there be persistence of past sessions or simulations?
- How are costs calculated and displayed? (per-request, per-session, etc.)
