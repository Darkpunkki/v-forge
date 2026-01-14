# Imagine Questions — IDEA-0001-control-simulation

1. Who is the primary user for the /control simulation view (internal devs, demo stakeholders, end users)?
2. Should simulation messages be real LLM responses, deterministic stubs, or both? If real, which provider/model?
3. How should the "first agent" be chosen at start (user-selected, fixed order, graph rule)?
4. Do you want directed links only, undirected links only, or a per-link toggle? Any graph constraints?
5. What exactly happens in one "tick" (single message, one agent step, or a full round)?
6. Are there limits or defaults for agent count, roles, or model labels in the MVP?
7. What message metadata must be recorded and displayed (timestamp, tick index, from/to ids, role, model label, etc.)?
8. Should sessions persist across refreshes or be in-memory only? Any reset/export needs?
9. Any UI preferences for the message viewer (group by tick, filter by agent, show graph alongside log)?
10. What is the minimal success criteria for this iteration (demo scenario or acceptance checklist)?
