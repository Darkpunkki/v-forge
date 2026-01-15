# Minimal Tasks for LLM Sandbox Environment

**Analysis:** The existing codebase already has most infrastructure in place:
- Agent init/assign endpoints
- Flow configuration with graph storage
- Simulation config, start, pause, reset, tick endpoints
- TickEngine with graph-gated messaging
- EventLog with MESSAGE_SENT, MESSAGE_BLOCKED_BY_GRAPH, TICK_ADVANCED
- UI widgets: SimulationConfig, TickControls, MultiAgentMessages, AgentGraph

**Critical gap:** TickEngine is NOT wired to the API tick endpoints—they just increment a counter.

---

## Level 0: "It Works" (1 task)

The absolute minimum to demo the sandbox workflow via API.

| Task | Description | Estimate |
|------|-------------|----------|
| **TASK-011** | Wire TickEngine to control API tick endpoints | L |

**What you get:**
- Configure agents via existing UI/API
- Configure links via existing UI/API
- Start simulation (existing endpoint)
- Click "Tick" → TickEngine processes messages, emits events
- Messages appear in MultiAgentMessages widget
- Status/tick updates in TickControls widget

**What you don't get:**
- Initial prompt / first agent selection (start context)
- Cycles in graph (DAG enforced)
- FIFO single-event-per-tick (processes all pending)
- Stub responses (no auto-reply)

**Total: ~1-2 days**

---

## Level 1: Usable Sandbox (4 tasks)

Add the initial prompt flow and allow bidirectional/cyclic graphs.

| Task | Description | Estimate |
|------|-------------|----------|
| TASK-011 | Wire TickEngine to control API tick endpoints | L |
| **TASK-004** | Update graph validation to allow cycles/bidirectional | M |
| **TASK-007** | Add initial_prompt and first_agent_id to Session model | S |
| **TASK-008** | Extend start endpoint to require prompt + first agent | M |

**What you get (on top of Level 0):**
- Bidirectional and cyclic communication graphs
- User provides initial prompt before starting
- User selects which agent receives the first message
- Clear start context stored in session

**What you still skip:**
- UI for prompt/first agent (use API directly or extend later)
- FIFO processing (all queued events fire per tick)
- Stub responses
- Per-agent activity cap

**Total: ~3-4 days**

---

## Level 2: Proper Sandbox (8 tasks)

Add FIFO tick processing, per-agent activity cap, and deterministic stubs.

| Task | Description | Estimate |
|------|-------------|----------|
| TASK-011 | Wire TickEngine to control API tick endpoints | L |
| TASK-004 | Update graph validation to allow cycles/bidirectional | M |
| TASK-007 | Add initial_prompt and first_agent_id to Session model | S |
| TASK-008 | Extend start endpoint to require prompt + first agent | M |
| **TASK-010** | Add initial prompt + first agent UI inputs | M |
| **TASK-012** | Implement FIFO single-event-per-tick processing | M |
| **TASK-013** | Implement per-agent activity cap tracking | M |
| **TASK-019** | Implement deterministic stub response generator | M |

**What you get (on top of Level 1):**
- Full UI flow: configure → prompt → start → tick
- One event processed per tick (controlled stepping)
- Each agent acts at most once per tick (no runaway loops)
- Stub responses clearly labeled `[STUB]`

**What you still skip:**
- Stub response auto-queueing (TASK-020)
- Extensive validation / error messages
- Test coverage
- UI polish (empty states, filters already exist)

**Total: ~6-8 days**

---

## Level 3: Complete Sandbox (14 tasks)

A polished, tested sandbox with full validation and stub auto-reply.

| Task | Description | Estimate |
|------|-------------|----------|
| TASK-011 | Wire TickEngine to control API tick endpoints | L |
| TASK-004 | Update graph validation to allow cycles/bidirectional | M |
| TASK-007 | Add initial_prompt and first_agent_id to Session model | S |
| TASK-008 | Extend start endpoint to require prompt + first agent | M |
| TASK-010 | Add initial prompt + first agent UI inputs | M |
| TASK-012 | Implement FIFO single-event-per-tick processing | M |
| TASK-013 | Implement per-agent activity cap tracking | M |
| TASK-019 | Implement deterministic stub response generator | M |
| **TASK-020** | Integrate stub response into tick processing (auto-queue) | M |
| **TASK-027** | Implement reset with configuration preservation | M |
| **TASK-017** | Emit blocked message events with clear format | S |
| **TASK-015** | Add tick engine unit tests (FIFO, activity cap) | M |
| **TASK-021** | Add stub response tests for determinism | S |
| **TASK-037** | Update AgentGraph to render simulation links | M |

**What you get (on top of Level 2):**
- Full stub conversation flow (message → stub reply → queued)
- Reset preserves config, clears messages
- Blocked sends show "A → B not allowed"
- Graph visualization shows simulation links (not task edges)
- Test coverage for core tick engine behavior

**Total: ~10-12 days**

---

## Tasks NOT needed (already work or polish)

These 33 tasks from the full list are either:
1. **Verification only** — existing code likely already handles it
2. **Polish** — empty states, error messages, filters already implemented
3. **Redundant** — covered by other tasks

| Category | Tasks | Reason |
|----------|-------|--------|
| Verification | 001, 016, 022, 023, 030, 032, 033, 035, 040, 042, 043, 044, 045 | Existing code already does this |
| Validation polish | 002, 006, 025, 026, 028 | Nice guardrails but not blocking |
| API response polish | 003, 005, 009, 014, 024, 031 | Existing responses work |
| UI polish | 038, 039, 041, 046, 047 | Already exists or cosmetic |
| Test coverage | 015*, 018, 021*, 029, 034, 036 | Defer to Level 3+ |

*Included in Level 3

---

## Recommendation

**For a quick internal demo:** Level 1 (4 tasks, ~3-4 days)
- Wire the engine, allow cycles, add start context via API

**For a usable dev sandbox:** Level 2 (8 tasks, ~6-8 days)  
- Full UI flow, controlled tick stepping, stub labels

**For production/sharing:** Level 3 (14 tasks, ~10-12 days)
- Tests, polish, auto-reply stubs, proper graph viz
