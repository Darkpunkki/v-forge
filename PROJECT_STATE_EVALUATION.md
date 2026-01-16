# Project State Evaluation: LLM Sandbox UI
**Date:** 2026-01-16
**Goal:** Browser-based UI with configurable "LLM sandbox"
**Idea:** IDEA-0002-control-sim

---

## Executive Summary

**Current State:** 🟢 **READY FOR UI TESTING**

The project has completed **10 out of 14 MVP features** (71% complete). The core simulation engine is **fully functional** and the UI is **already built**. You can test the sandbox workflow via the browser **right now**.

**What works:**
- ✅ Configure agents with roles/models
- ✅ Configure communication graph (including cycles)
- ✅ Set initial prompt and first agent
- ✅ Start simulation
- ✅ Advance simulation tick-by-tick
- ✅ View messages with tick metadata
- ✅ Pause, reset simulation
- ✅ Deterministic stub responses
- ✅ Graph-gated messaging
- ✅ FIFO event processing
- ✅ Per-agent activity cap

**What's missing for full MVP:**
- ⚠️ Event streaming (FEAT-011) - messages don't auto-update in UI yet
- ⚠️ Agent graph visualization (FEAT-012) - graph widget shows task edges, not simulation links
- ⚠️ Message log polish (FEAT-013) - filters and formatting
- ⚠️ Status indicators (FEAT-014) - tick/status display polish

---

## Completed Work (FEAT-001 through FEAT-010)

### FEAT-001: Agent Roster Configuration ✅
**Tasks:** TASK-001, TASK-002, TASK-003
**What it does:**
- API endpoints for agent initialization (`POST /control/sessions/{id}/agents/init`)
- Agent assignment with roles/models (`POST /control/sessions/{id}/agents/assign`)
- Validation for duplicate/empty agent IDs
- Default role list exposed to UI

**UI Component:** `AgentInitializer`, `AgentAssignment`

---

### FEAT-002: Communication Graph Configuration ✅
**Tasks:** TASK-004, TASK-005, TASK-006
**What it does:**
- Allow cycles and bidirectional links (removed DAG restriction)
- Store link directionality in agent graph
- Validate link endpoints against roster
- Clear error messages for invalid links

**UI Component:** `AgentFlowEditor`

---

### FEAT-003: Initial Prompt and First Agent Selection ✅
**Tasks:** TASK-007, TASK-008, TASK-009, TASK-010
**What it does:**
- Session model includes `initial_prompt` and `first_agent_id`
- Start endpoint requires both fields
- Validation that first agent exists in roster
- UI inputs for prompt and first agent selection

**UI Component:** `SimulationConfig` (text input + dropdown)

---

### FEAT-004: Tick Advancement with Per-Agent Activity Cap ✅
**Tasks:** TASK-011, TASK-012, TASK-013, TASK-014, TASK-015
**What it does:**
- **TickEngine wired to API** (CRITICAL: this was the main gap identified in minimal_tasks.md)
- FIFO single-event-per-tick processing
- Per-agent activity tracking (max 1 activity per tick)
- Tick summary responses
- Comprehensive unit tests

**UI Component:** `TickControls` (Start, Pause, Tick, Reset buttons)

---

### FEAT-005: Graph-Gated Message Validation ✅
**Tasks:** TASK-016, TASK-017, TASK-018
**What it does:**
- Messages blocked if no graph edge exists
- Blocked sends logged as system events
- Clear validation results with reasons

**Backend:** TickEngine.validate_message()

---

### FEAT-006: Deterministic Stubbed Responses ✅
**Tasks:** TASK-019, TASK-020, TASK-021
**What it does:**
- Deterministic stub generator (hash-based)
- Stub responses clearly labeled `[STUB]`
- Auto-queueing of stub replies during tick
- Tests for determinism

**Backend:** StubResponseGenerator

---

### FEAT-007: Message Event Emission with Tick Metadata ✅
**Tasks:** TASK-022, TASK-023, TASK-024
**What it does:**
- Events include tick index, timestamps
- MESSAGE_SENT, MESSAGE_BLOCKED_BY_GRAPH, TICK_ADVANCED event types
- EventLog integration

**Backend:** EventLog, Event types

---

### FEAT-008: Lifecycle State Transitions and Guardrails ✅
**Tasks:** TASK-025, TASK-026, TASK-027, TASK-028, TASK-029
**What it does:**
- State machine: configured → running → paused → completed
- Guards prevent invalid transitions (e.g., can't tick if not running)
- Reset preserves configuration, clears messages
- Clear error messages for invalid state transitions

**Backend:** Session.simulation_status

---

### FEAT-009: Status and Tick State Exposure ✅
**Tasks:** TASK-030, TASK-031
**What it does:**
- Simulation state endpoint returns status, current tick, config
- TypeScript types in `controlClient.ts`

**UI Component:** Status displays throughout `ControlPanel.tsx`

---

### FEAT-010: Persisted Simulation Event Log ✅
**Tasks:** TASK-032, TASK-033, TASK-034
**What it does:**
- Events persisted with timestamps
- Message events include sender/receiver
- Graceful error handling (log failures don't block simulation)

**Backend:** EventLog with in-memory storage (v1)

---

## Remaining MVP Work (FEAT-011 through FEAT-014)

### FEAT-011: Event Streaming for Control Panel ⚠️
**Tasks:** TASK-035, TASK-036
**Status:** Queued
**Why it matters:** Currently, the UI doesn't auto-update when tick events occur. Users must manually refresh to see new messages.

**What's needed:**
- SSE endpoint streams events to UI (`GET /control/sessions/{id}/events`)
- UI reconnection handling
- Estimated effort: ~0.5-1 day

---

### FEAT-012: Agent Graph Visualization ⚠️
**Tasks:** TASK-037, TASK-038, TASK-039
**Status:** Queued
**Why it matters:** The `AgentGraph` widget currently shows task-based edges, not the configured simulation communication links.

**What's needed:**
- Update `AgentGraph.tsx` to render `agent_graph` from simulation state
- Show directionality (arrows)
- Empty state when no agents configured
- Estimated effort: ~0.5-1 day

---

### FEAT-013: Message Log View with Filters ⚠️
**Tasks:** TASK-040, TASK-041, TASK-042, TASK-043
**Status:** Queued
**Why it matters:** Message log polish (formatting, filters, empty states)

**What's needed:**
- Verify `MultiAgentMessages` shows all required fields
- Format blocked messages as system entries
- Add filters (by agent, by tick)
- Empty state message
- Estimated effort: ~0.5-1 day

---

### FEAT-014: Status and Tick Indicators ⚠️
**Tasks:** Similar to FEAT-013
**Status:** Queued
**Why it matters:** Polish for status/tick displays

**Estimated effort:** ~0.5 day

---

## Gap Analysis: Minimal Tasks vs. Current State

According to `minimal_tasks.md`:

| Level | Description | Tasks | Status |
|-------|-------------|-------|--------|
| **Level 0** | "It Works" | TASK-011 | ✅ DONE |
| **Level 1** | Usable Sandbox | TASK-011, 004, 007, 008 | ✅ DONE |
| **Level 2** | Proper Sandbox | +TASK-010, 012, 013, 019 | ✅ DONE |
| **Level 3** | Complete Sandbox | +TASK-020, 027, 037, tests | 🟡 PARTIAL |

**You are currently at Level 2+** (proper sandbox with auto-reply stubs and reset).

---

## Can You Test Via UI Right Now?

### YES! Here's how:

1. **Start the API** (already running at http://localhost:8000)
2. **Start the UI** (already running at http://localhost:5173)
3. **Open browser:** http://localhost:5173/control
4. **Select or create a session** from the sidebar
5. **Configure agents:**
   - Click "Initialize Agents" → set agent count, prefix
   - Assign roles/models to each agent
6. **Configure graph:**
   - Use "Agent Flow Editor" to add communication links
   - Click edges to toggle directionality
7. **Set initial context:**
   - Enter initial prompt in "Simulation Config"
   - Select first agent from dropdown
8. **Start simulation:**
   - Click "Start" button
9. **Advance ticks:**
   - Click "Tick" button to process one event at a time
   - Watch messages appear in "Multi-Agent Messages" widget

**Known limitations for manual testing:**
- Messages won't auto-update (must click tick repeatedly)
- Graph won't show simulation links (shows old task edges)
- No filters on message log

---

## Proposed Fast-Path Feature: "UI Testing MVP"

To get you testing **immediately** without waiting for FEAT-011-014, I propose a new **FEAT-015: Quick UI Testing Patch**.

### FEAT-015: Quick UI Testing Patch

**Goal:** Make the existing UI fully functional for manual testing with minimal effort.

**Tasks:**

1. **TASK-QUICK-01: Verify end-to-end UI workflow** (S - 1 hour)
   - Manually test: init agents → assign → configure graph → set prompt → start → tick → view messages
   - Document any broken flows
   - Verify stub responses appear

2. **TASK-QUICK-02: Add polling fallback for message updates** (S - 1 hour)
   - Since SSE isn't wired yet, add a simple 2-second polling interval to `ControlPanel.tsx`
   - Fetch simulation state every 2s when status is "running"
   - This gives "live enough" updates for testing

3. **TASK-QUICK-03: Quick-fix AgentGraph to show simulation links** (M - 2 hours)
   - Update `AgentGraph.tsx` to read `simulationState?.agent_graph?.edges` instead of task edges
   - Show arrows based on link direction
   - If no links, show "Configure communication graph"

4. **TASK-QUICK-04: Add basic message log formatting** (S - 1 hour)
   - Ensure blocked messages show "(BLOCKED)" badge
   - Ensure stub messages show "[STUB]" label
   - Add tick number to each message row

**Total effort:** ~5-6 hours (can be done in 1 day)

**Outcome:** Fully testable UI with decent UX, bypassing the need for proper SSE and full polish.

---

## Recommendation

### Option A: Fast-Path (Recommended for immediate testing)
**Execute FEAT-015** → get a working demo in 1 day → iterate based on testing feedback

### Option B: Complete MVP (Recommended for polish)
**Execute FEAT-011, 012, 013, 014** → get full MVP in ~2-3 days → professional-grade UI

### Option C: Hybrid
**Execute TASK-QUICK-02 and TASK-QUICK-03 now** (3 hours) → test immediately → then complete FEAT-011+ for polish

---

## Uncommitted Changes

```
M apps/api/tests/test_tick_engine.py
M docs/forge/ideas/IDEA-0002-control-sim/latest/feature_execution_progress.md
M orchestration/coordinator/tick_engine.py
```

These are work-in-progress from FEAT-010 and should be reviewed before proceeding.

---

## Next Steps

1. **Decision:** Choose Option A, B, or C above
2. **Commit current changes** (if safe)
3. **Execute chosen path**
4. **Test via browser UI**
5. **Iterate based on findings**

---

## Real LLM Integration Status

### Current State: 🟡 PARTIAL INFRASTRUCTURE

**What exists:**
- ✅ `LlmClient` abstract base class in `models/base/llm_client.py`
- ✅ `OpenAiProvider` implementation (functional, tested)
- ✅ `LocalProvider` for local models
- ✅ Request/Response types (`LlmRequest`, `LlmResponse`, `LlmMessage`, `LlmUsage`)
- ✅ `DeterministicStubClient` for no-spend mode
- ✅ `get_llm_client()` factory with env-based selection
- ✅ Environment-based configuration (`VIBEFORGE_LLM_MODE`, `VIBEFORGE_NO_SPEND`, `OPENAI_API_KEY`)

**What's missing for simulation:**
- ❌ Integration point in `TickEngine` (currently hardcoded stub responses)
- ❌ Per-session LLM mode configuration (currently global env var only)
- ❌ Agent-level model/provider configuration
- ❌ Anthropic/Claude provider (infrastructure exists, not implemented)
- ❌ Conversation history tracking for agents
- ❌ System prompt configuration per agent role
- ❌ UI controls for toggling stub/real LLM mode
- ❌ Cost tracking for simulation runs

### How Stub Responses Currently Work

**Location:** `orchestration/coordinator/tick_engine.py:197-222`

When a message expects a response, the TickEngine calls:
```python
stub_content = self.generate_stub_response(
    responding_agent=message.to_agent,
    source_agent=message.from_agent,
    message_content=message.content,
    tick_index=new_tick,
)
```

This generates a deterministic hash-based stub like:
```
[STUB] agent-2 -> agent-1 @ tick 3 (a1b2c3d4e5)
```

**What needs to change:**
Instead of always calling `generate_stub_response()`, the engine should:
1. Check session-level LLM mode (`use_real_llm` flag)
2. If stub mode → use existing logic
3. If real mode → call `LlmClient.complete()` with agent's conversation history

### Required Architecture Changes

#### 1. Session-level LLM Configuration
```python
# In apps/api/vibeforge_api/core/session.py
class Session:
    # Add these fields:
    use_real_llm: bool = False  # Toggle stub vs real
    llm_provider: str = "openai"  # "openai", "anthropic", "local"
    default_model: str = "gpt-4o-mini"  # Model for agents without specific model
    default_temperature: float = 0.7
    simulation_cost_usd: float = 0.0  # Track accumulated cost
```

#### 2. Agent-level Conversation History
```python
# In TickEngine or Session
agent_conversations: dict[str, list[LlmMessage]] = {}
# Key: agent_id, Value: conversation history for that agent
```

#### 3. LLM Response Generator Service
```python
# New file: orchestration/coordinator/llm_response_generator.py
class LlmResponseGenerator:
    def __init__(self, llm_client: LlmClient):
        self.llm_client = llm_client

    async def generate_response(
        self,
        agent_id: str,
        agent_role: str,
        agent_model: str,
        message_history: list[LlmMessage],
        incoming_message: dict,
    ) -> LlmResponse:
        # Build system prompt based on role
        # Append incoming message to history
        # Call llm_client.complete()
        # Return response
```

#### 4. TickEngine Integration
```python
# In TickEngine.advance_tick() around line 444
if self._message_expects_response(message):
    if self.session.use_real_llm:
        # NEW: Real LLM path
        response_content = await self._generate_llm_response(
            agent_id=message.to_agent,
            incoming_message=message.content,
        )
    else:
        # EXISTING: Stub path
        response_content = self.generate_stub_response(...)
```

### Environment Variables Reference

**Current:**
- `VIBEFORGE_LLM_MODE` - "stub" | "dry_run" | "real" (default: real if API key exists)
- `VIBEFORGE_NO_SPEND` - "1" | "true" | "yes" (forces stub mode)
- `OPENAI_API_KEY` - OpenAI API key
- `OPENAI_BASE_URL` - Custom OpenAI endpoint (optional)

**Needed:**
- `ANTHROPIC_API_KEY` - Claude API key (for Anthropic provider)

---

## Updated FEAT-015: Quick UI Testing + Real LLM Integration

### Part A: Quick UI Testing Patch (Original - ~5-6 hours)

1. **TASK-QUICK-01: Verify end-to-end UI workflow** (S - 1 hour)
   - Manually test: init agents → assign → configure graph → set prompt → start → tick → view messages
   - Document any broken flows
   - Verify stub responses appear

2. **TASK-QUICK-02: Add polling fallback for message updates** (S - 1 hour)
   - Since SSE isn't wired yet, add a simple 2-second polling interval to `ControlPanel.tsx`
   - Fetch simulation state every 2s when status is "running"
   - This gives "live enough" updates for testing

3. **TASK-QUICK-03: Quick-fix AgentGraph to show simulation links** (M - 2 hours)
   - Update `AgentGraph.tsx` to read `simulationState?.agent_graph?.edges` instead of task edges
   - Show arrows based on link direction
   - If no links, show "Configure communication graph"

4. **TASK-QUICK-04: Add basic message log formatting** (S - 1 hour)
   - Ensure blocked messages show "(BLOCKED)" badge
   - Ensure stub messages show "[STUB]" label
   - Add tick number to each message row

### Part B: Real LLM Integration (~8-10 hours)

5. **TASK-LLM-01: Add session-level LLM configuration fields** (S - 1 hour)
   - Add `use_real_llm`, `llm_provider`, `default_model`, `default_temperature`, `simulation_cost_usd` to Session model
   - Update `to_dict()` and `from_dict()` serialization
   - Add fields to simulation state API response
   - Update TypeScript types in `controlClient.ts`

6. **TASK-LLM-02: Create LlmResponseGenerator service** (M - 2 hours)
   - Create `orchestration/coordinator/llm_response_generator.py`
   - Implement `LlmResponseGenerator` class with role-based system prompts
   - Support conversation history building
   - Handle async LLM calls with error handling
   - Return formatted response content matching stub format (but real)

7. **TASK-LLM-03: Add agent conversation history tracking to TickEngine** (M - 2 hours)
   - Add `agent_conversations: dict[str, list[LlmMessage]]` to TickEngine
   - Persist to/from session state
   - Append incoming messages to recipient's history
   - Append responses to sender's history
   - Limit history depth (e.g., last 20 messages per agent)

8. **TASK-LLM-04: Wire real LLM calls into TickEngine.advance_tick()** (L - 3 hours)
   - Modify `advance_tick()` to check `session.use_real_llm`
   - If true, call `LlmResponseGenerator.generate_response()`
   - If false, use existing `generate_stub_response()`
   - Handle async/await (convert advance_tick to async if needed)
   - Track token usage and update `session.simulation_cost_usd`
   - Emit cost tracking events to EventLog
   - Add error handling for API failures (fallback to stub or retry)

9. **TASK-LLM-05: Add UI toggle for stub vs real LLM mode** (M - 2 hours)
   - Add toggle switch in `SimulationConfig.tsx`
   - Show current mode ("Stub Responses" vs "Real LLM")
   - If real mode enabled, show model selector dropdown
   - Show warning: "Real LLM calls will incur costs"
   - Disable toggle once simulation is started
   - Display accumulated cost in TickControls widget

10. **TASK-LLM-06: Add basic role-based system prompts** (S - 1 hour)
    - Define system prompts for each role (orchestrator, worker, reviewer, fixer, foreman)
    - Store in `orchestration/prompts.py` or similar
    - Use in `LlmResponseGenerator`
    - Example: "You are a worker agent in a multi-agent system. Respond concisely to requests..."

11. **TASK-LLM-07: Add Anthropic/Claude provider (optional)** (M - 2-3 hours)
    - Create `models/anthropic/provider.py`
    - Implement `AnthropicProvider(LlmClient)`
    - Use `anthropic` Python SDK
    - Update `get_llm_client()` to check `ANTHROPIC_API_KEY`
    - Add to model selector dropdown in UI

**Part B Total:** ~8-13 hours (1-2 days)

---

## Updated Recommendations

### Option A: Fast UI Testing Only (Original FEAT-015 Part A)
**Effort:** ~5-6 hours (1 day)
**Outcome:** Working UI demo with stub responses
**Use case:** Quick validation of simulation workflow

### Option B: Full LLM Integration (FEAT-015 Parts A + B)
**Effort:** ~13-19 hours (2-3 days)
**Outcome:** Production-ready sandbox with real LLM conversations
**Use case:** Real multi-agent simulations with OpenAI/Claude

### Option C: Hybrid - UI First, Then LLM
**Effort:** Day 1 (Part A) → Day 2-3 (Part B)
**Outcome:** Test with stubs immediately, add real LLMs after validation
**Use case:** Iterative development with early feedback

### Option D: LLM-Only (Skip UI polish, add real LLMs)
**Effort:** ~8-13 hours (1-2 days)
**Outcome:** Real LLM responses, but UI still rough (no SSE, graph issues)
**Use case:** You prioritize real conversations over UI polish

---

## Technical Notes

### Making TickEngine Async

If `advance_tick()` becomes async, you'll need to update:
1. API endpoint handlers in `control.py` to use `await`
2. All callers of `advance_tick()` to await the result
3. FastAPI endpoints already support async, so minimal changes needed

### Cost Estimation

Using `gpt-4o-mini` (cheapest decent model):
- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens

Example simulation:
- 5 agents, 20 messages each = 100 messages
- ~100 tokens per message = 10k tokens
- Cost: ~$0.01 (negligible)

Using `gpt-4o`:
- Input: $2.50 per 1M tokens
- Output: $10.00 per 1M tokens
- Same simulation: ~$0.10

Using `claude-3-5-sonnet`:
- Input: $3.00 per 1M tokens
- Output: $15.00 per 1M tokens
- Same simulation: ~$0.15

### Security Considerations

- Never store API keys in session data (use env vars only)
- Validate all agent inputs before sending to LLM (prevent injection)
- Set max_tokens limits to prevent runaway costs
- Consider rate limiting on tick advancement

---

Would you like me to proceed with Option A, B, C, or D?
