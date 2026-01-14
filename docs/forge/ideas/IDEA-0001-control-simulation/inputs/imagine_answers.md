### 2026-01-14T15:44:24Z - Answers for 2026-01-14T15-33-34Z_imagine-d6cf

1. Internal devs (me).
2. Start with deterministic stubs and provide a path to real LLM responses. Provider: OpenAI; MVP model should be a cheap option.
3. User-selected first agent.
4. Manual, per-link selection (e.g., agent A can only send to agent B). Keep it simple.
5. One tick = a full round where all agents advance one step if needed. If tickless auto-run is added, add guardrails to avoid runaway API cost.
6. Provide basic default models; no hard limits on agent count. All configuration must be set before starting the sim.
7. Display all agent metadata with messages (role, name, model, etc.).
8. In-memory only; no export needs.
9. No UI preferences; clarity and simplicity.
10. Success criteria: setup agents/roles/models/links, start and stop simulation, view messages individually, and convey execution order (active agent).
