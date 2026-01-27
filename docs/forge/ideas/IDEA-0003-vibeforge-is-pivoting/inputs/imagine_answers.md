### 2026-01-27T18:08:48.4418060+02:00 — Answers for 2026-01-27T15-40-24.315Z_run-1f99

1) Primary target user for /control and /simulation

Primary user: an individual who wants to control multiple agents from one UI.
Priority: get it working for me first (single-user, local-first).
Secondary later: other developers/teams who want the same control-room + simulator experience.

2) MVP scope for /control (must-have for first release)

MVP goal: from my PC, I can initiate/control a live coding agent running on my laptop (e.g., clawdbot/Claude Code style agent) and use it to perform tasks.
Must-have capabilities:

- Add/connect to an agent instance on another machine.
- Send a task/command to that agent.
- See streamed output (chat + tool calls at minimum).
- Send follow-up messages (basic back-and-forth).
- Observe agent status (connected/busy/idle + last activity).

3) How should agents be registered/connected?

Best-practice MVP answer: start simple and explicit; do not do discovery yet.

Manual registration in the UI: user enters a name + endpoint/connection target for the agent (e.g., http://laptop:PORT or ws://...).

Optional: allow importing/exporting a small config file later (JSON/YAML), but not required for MVP.

Discovery can be a later enhancement once the protocol is stable.

4) What control channel/protocol is expected?

MVP expectation: local-network friendly, easy to debug, and supports streaming.

Use a simple HTTP API for commands + WebSocket (or SSE) for streaming logs/events.

The agent host (laptop) runs a small "agent bridge" service that exposes:

- connect/handshake
- run task
- stream events/output
- optional file ops later

This keeps the browser app clean and avoids trying to directly "remote control" via fragile hacks.

5) What streaming detail is required in /control?

MVP: show enough to feel like a real agent session.

Stream chat messages + tool call events + tool results.

Include stdout/stderr style logs if available, but not required on day 1.

Final artifacts can be links/paths + a summary for now (no fancy artifact viewer needed yet).

6) For /simulation, what level of fidelity is needed?

Simple message passing only.

Simulation is a sandbox to practice orchestration/delegation and see message chains.

No tool execution emulation needed right now.

No record/replay needed for MVP.

7) What inputs should define a simulation scenario?

UI-driven inputs (MVP).

The user configures agents in the UI (names/roles), sets the hierarchy, and provides an initial prompt/task.

The scenario is defined by:

- agent list + roles
- hierarchy/edges (who can message whom)
- initial task and optional per-agent system prompts

Optional later: save/load scenario templates (JSON/YAML export) for reproducibility, but not required for MVP.

8) Explicit non-goals for the initial pivot

- No multi-user collaboration or shared workspaces yet.
- No complex auth/roles (single-user local only).
- No automatic agent discovery (manual registration only).
- No full remote filesystem browser/editor in the UI.
- No tool execution simulation beyond message passing.
- No big-bang rewrite; refactor incrementally.

9) How aggressive should deprecation of /session be?

Very aggressive.

/session functionality should be removed (UI/routes) unless a piece is genuinely reusable for /control or /simulation.
If something is needed, migrate it into the new architecture; do not keep session as a supported flow.

Outcome: session is gone as a product concept; only salvaged components remain.

10) What does success look like in 1-3 months?

Simulation success demo:

User selects devices and assigns agents in a hierarchy.

Running the simulation shows a complete message chain:

orchestrator -> laptop agent -> pico agent -> laptop agent -> orchestrator -> user

The UI clearly visualizes the chain of messages and the intermediate hops.

Control success demo:

From my PC in /control, I can select a laptop agent and give it a real task like:

"Read instructions from file X, implement changes in file Y, run verification, commit to GitHub."

I can observe progress via streamed messages/tool calls and follow up interactively.

