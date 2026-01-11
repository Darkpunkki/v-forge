---
doc_type: concept_summary
idea_id: "IDEA-0002-vforge"
run_id: "2026-01-11T14-45-12Z_run-c3b8"
generated_by: "Concept Summarizer"
generated_at: "2026-01-11T14:45:12Z"
source_inputs:
  - "docs/ai/forge/ideas/IDEA-0002-vforge/inputs/idea.md"
  - "docs/ai/forge/ideas/IDEA-0002-vforge/latest/idea_normalized.md"
configs: []
release_targets_supported: ["MVP", "V1", "Full", "Later"]
status: "Draft"
---

# Concept Summary

## System Intent

VibeForge is an AI-powered application factory that enables users to generate working applications by completing structured questionnaires—without writing code or providing free-text descriptions. The system orchestrates multiple specialized AI agents to transform user requirements into deployable application code.

The platform serves two distinct user groups through separate operational modes: end users interact via Session mode to generate applications, while administrators use Control Panel mode to customize agent pipelines, run simulations, and monitor costs. Both modes provide real-time visibility into agent activity.

## Core Capabilities

- The system can present structured questionnaires to capture application requirements
- The system can generate an application plan from questionnaire responses for user verification
- The system can orchestrate a multi-agent pipeline to produce application code
- The system can display real-time metrics during code generation (active agents, API requests, progress)
- The system can deliver generated application code with custom run instructions
- The system can run agent simulations with user-defined roles and tasks (Control Panel)
- The system can expose drill-down views into agent-to-agent communication
- The system can track and report API costs and token usage per agent
- The system can allow customization of agent provider/model settings

## Conceptual Workflow

### Session Mode (End User Flow)

1. User completes a structured questionnaire defining application requirements
2. System generates an application plan; user verifies/approves the plan
3. Orchestrator agent decomposes the plan into subtasks and delegates to specialized agents (Foreman → Worker → Reviewer → Fixer)
4. System displays real-time progress metrics during generation
5. User receives generated application code and custom run instructions

### Control Panel Mode (Admin Flow)

1. Admin configures a simulation: selects agents, assigns roles/tasks, sets provider/model
2. Simulation executes with real-time status and output per agent
3. Admin drills down into agent communication; reviews costs and token usage

## Invariants

- The system must only accept structured questionnaire input in Session mode (no free-text)
- The system must support multiple specialized agent roles: Orchestrator, Foreman, Worker, Reviewer, Fixer
- The system must provide real-time visibility into agent activity in both modes
- The system must produce working application code as output (not just partial snippets)
- The system must provide custom instructions for running the generated application
- The system must separate Session (end-user) and Control Panel (admin) interfaces

## Key Constraints

- Must use structured questionnaires only; free-text input is prohibited
- Must support configurable AI providers and models per agent
- Must track and expose API costs and token usage
- Must enable drill-down into agent-to-agent communication during simulations
- Cannot host or deploy generated applications; only code and run instructions are delivered

## In-Scope Responsibilities

- Structured questionnaire presentation and response collection
- Application plan generation and user verification
- Multi-agent orchestration for code generation
- Real-time progress/metrics display
- Agent simulation with role/task assignment (Control Panel)
- Agent configuration (provider, model, cost tracking)
- Drill-down visibility into agent communication
- Cost and token usage reporting

## Out-of-Scope / Explicit Exclusions

- Free-text or natural language input for application definition
- Hosting, deployment, or runtime execution of generated applications
- Authentication/authorization mechanisms (not specified; may be added later)
- Specific programming languages or frameworks for generated apps (not mandated)
- Persistence of past sessions or simulations (not specified)

## Primary Artifacts

- **Questionnaire:** Structured input mechanism for capturing application requirements
- **Application Plan:** Generated summary of the intended application for user verification
- **Generated Application Code:** The final code output produced by the agent pipeline
- **Run Instructions:** Custom instructions for running the generated application
- **Simulation Report:** Status, output, and cost data from a Control Panel simulation
- **Agent Communication Log:** Drill-down view of agent-to-agent messages and actions

## Key Entities and Boundaries

- **Session:** A single end-user flow from questionnaire to generated application
- **Simulation:** A configurable agent run in Control Panel mode for testing or custom tasks
- **Orchestrator:** Top-level agent that decomposes plans and coordinates other agents
- **Foreman:** Agent that defines code snippets and assigns tasks to Workers
- **Worker:** Agent that writes actual code
- **Reviewer:** Agent that reviews Worker output for quality and requirement compliance
- **Fixer:** Agent that handles special tasks, such as patching previously working code
- **Agent Configuration:** Per-agent settings including provider, model, and cost tracking

## Open Questions / Ambiguities

- What is the exact structure and content of the questionnaire?
- What application formats/types should be supported (SPA, backend+frontend, CLI, etc.)?
- Which AI providers and models should be supported out of the box?
- What is the mechanism for agent-to-agent communication (message passing, shared state, event bus)?
- Is authentication/authorization required for Session vs Control Panel access?
- Should sessions and simulations be persisted for later review?
- How granular is cost/token tracking (per-request, per-agent, per-session)?
- What happens if the agent pipeline fails mid-generation?
