# New Features Added to tasks.md

**Date:** 2026-01-16
**Idea:** IDEA-0002-control-sim
**Target:** LLM Sandbox UI with Real Agent Conversations

---

## Summary

Added **12 new tasks** (TASK-048 through TASK-059) organized into **2 features**:

1. **FEAT-015: UI Testing Verification** (4 tasks) - MVP release target
2. **FEAT-016: Real LLM Agent Responses with Guardrails** (8 tasks) - V1 release target

**New Epic:**
- **EPIC-006: Real LLM Agent Responses**

---

## FEAT-015: UI Testing Verification (MVP)

**Purpose:** Verify the simulation UI works correctly with stub responses before adding real LLM integration.

### Tasks:

#### TASK-048: Manual UI workflow verification with stub responses
- **Priority:** P0 | **Estimate:** S
- **Description:** Complete end-to-end manual test of simulation workflow via browser UI
- **Validates:** Agent init, role assignment, graph config, simulation start/tick/pause/reset
- **Deliverable:** Documentation of any bugs or UX issues found

#### TASK-049: Add polling fallback for simulation state updates
- **Priority:** P1 | **Estimate:** S
- **Description:** 2-second polling for "live enough" updates until SSE implemented
- **Why:** FEAT-011 (SSE) not yet done, polling provides interim solution
- **Cleanup:** Remove when FEAT-011 completed

#### TASK-050: Update AgentGraph to render simulation communication links
- **Priority:** P1 | **Estimate:** M
- **Description:** Fix graph to show actual agent links instead of task edges
- **Why:** Current graph shows wrong data (task dependencies, not agent comm topology)
- **Visual:** Arrows for directed links, bidirectional support

#### TASK-051: Format blocked and stub messages in message log
- **Priority:** P1 | **Estimate:** S
- **Description:** Add visual badges for [STUB] and (BLOCKED) messages
- **Why:** Improves readability and simulation state clarity
- **Includes:** Tick numbers on each message row

---

## FEAT-016: Real LLM Agent Responses with Guardrails (V1)

**Purpose:** Replace deterministic stubs with real LLM API calls (gpt-4o-mini) while enforcing safety guardrails.

**Critical Safety Features:**
1. Default to stub mode (use_real_llm=False)
2. Cost budget ($1.00 default, configurable)
3. Rate limiting (1 tick/second max)
4. Fallback to stub on LLM failure
5. UI warnings before enabling real LLM

### Tasks:

#### TASK-052: Add session-level LLM configuration fields
- **Priority:** P0 | **Estimate:** S
- **Description:** Extend Session model with LLM config fields
- **New Fields:** use_real_llm, llm_provider, default_model, default_temperature, simulation_cost_usd
- **Default:** gpt-4o-mini, temp=0.7, stub mode=True (safe defaults)
- **API Impact:** Update simulation state response + TypeScript types

#### TASK-053: Add LLM cost and rate limiting guardrails
- **Priority:** P0 | **Estimate:** M
- **Description:** Prevent runaway API costs and enforce tick rate limits
- **Guardrail 1:** Cost budget (default $1.00) - returns HTTP 429 when exceeded
- **Guardrail 2:** Rate limit (default 1000ms) - prevents more than 1 tick/second
- **Why Critical:** Prevents bugs from causing $100+ API bills
- **Validation:** Unit tests for both guardrails

#### TASK-054: Create LlmResponseGenerator service with role-based prompts
- **Priority:** P0 | **Estimate:** M
- **Description:** Service layer for all LLM interactions
- **New File:** orchestration/coordinator/llm_response_generator.py
- **System Prompts:** Defined for all 5 roles (orchestrator, worker, reviewer, fixer, foreman)
- **Async:** generate_response() method returns LlmResponse
- **Error Handling:** Raise exception on failure (caller handles fallback)

#### TASK-055: Add agent conversation history tracking
- **Priority:** P0 | **Estimate:** M
- **Description:** Maintain per-agent conversation context across ticks
- **Storage:** agent_conversations: dict[str, list[dict]] in TickEngine
- **Persistence:** Saved to/from session.simulation_agent_conversations
- **Memory Management:** Limit to last 20 messages per agent (configurable)
- **Format:** {"role": "user"/"assistant", "content": {...}}

#### TASK-056: Wire real LLM calls into TickEngine with cost tracking
- **Priority:** P0 | **Estimate:** L
- **Description:** Core integration - conditionally call LLM instead of stub
- **Logic:**
  ```python
  if session.use_real_llm:
      response = await llm_generator.generate_response(...)
  else:
      response = self.generate_stub_response(...)
  ```
- **Cost Tracking:** Calculate from token usage, emit COST_TRACKING events
- **Async Conversion:** advance_tick() becomes async, API handlers use await
- **Fallback:** On LLM failure, log error and use stub
- **Model Pricing:** gpt-4o-mini: $0.15 input / $0.60 output per 1M tokens

#### TASK-057: Add UI controls for LLM mode and cost display
- **Priority:** P0 | **Estimate:** M
- **Description:** SimulationConfig toggle + cost tracking display
- **UI Elements:**
  - Toggle: "Use Real LLM" (default off)
  - Model dropdown: gpt-4o-mini, gpt-4o, gpt-4-turbo
  - Temperature slider: 0.0 - 1.0
  - Cost budget input: USD (default $1.00)
  - Rate limit input: ms (default 1000ms)
  - Warning: "Real LLM calls will incur API costs"
- **Cost Display:** TickControls shows "${current} / ${max}" (red when >80%)
- **Safety:** Inputs disabled once simulation started

#### TASK-058: Add unit tests for LLM integration and guardrails
- **Priority:** P1 | **Estimate:** M
- **Description:** Comprehensive test coverage for all LLM features
- **Test File:** apps/api/tests/test_llm_integration.py
- **Coverage:**
  - Role-based system prompts
  - Conversation history tracking
  - History depth limiting
  - Cost calculation accuracy
  - Cost budget enforcement (429 response)
  - Rate limit enforcement (429 response)
  - LLM failure fallback to stub
  - Stub mode never calls LLM

#### TASK-059: Add integration test for end-to-end LLM simulation
- **Priority:** P1 | **Estimate:** M
- **Description:** Full simulation test with real LLM calls (mocked)
- **Test File:** apps/api/tests/test_llm_simulation_integration.py
- **Scenario:**
  - 2 agents with communication link
  - 5 ticks with use_real_llm=True
  - Verify LLM responses (not stubs)
  - Verify conversation history grows
  - Verify cost tracking works
- **Mocking:** Uses mock LLM client (not production API)

---

## Implementation Path

### Phase 1: UI Verification (FEAT-015)
**Estimated Effort:** ~5-6 hours (1 day)
**Execute:** TASK-048 → TASK-049 → TASK-050 → TASK-051
**Outcome:** Working UI demo with stub responses, ready for user testing

### Phase 2: Real LLM Integration (FEAT-016)
**Estimated Effort:** ~13-16 hours (2-3 days)
**Execute:** TASK-052 → TASK-053 → TASK-054 → TASK-055 → TASK-056 → TASK-057 → TASK-058 → TASK-059
**Outcome:** Production-ready LLM sandbox with guardrails

### Total Effort: 18-22 hours (3-4 days)

---

## Guardrails Summary

The following safety mechanisms prevent runaway API costs:

1. **Default to Stub Mode**
   - Session.use_real_llm defaults to False
   - Explicit opt-in required for API calls

2. **Cost Budget**
   - Default: $1.00 per simulation
   - Configurable per session
   - HTTP 429 when exceeded
   - UI shows warning at 80% budget

3. **Rate Limiting**
   - Default: 1 tick per second max
   - Prevents tight loops from hammering API
   - HTTP 429 if limit violated
   - Configurable per session

4. **Fallback to Stub**
   - Any LLM failure → automatic stub response
   - Simulation continues even if API down
   - Errors logged to EventLog

5. **UI Warnings**
   - "Real LLM calls will incur API costs"
   - Model selector shows cost implications
   - Toggle disabled once simulation started

6. **Model Defaults**
   - gpt-4o-mini: cheapest reasonable model
   - ~$0.01 for 100-message simulation
   - Easy upgrade to gpt-4o or Claude later

---

## Usage After Implementation

### Using the execute-feat skill

The new tasks follow the same format as existing tasks, so they can be executed using:

```bash
# Execute FEAT-015 (UI verification)
/execute-feat FEAT-015

# Execute FEAT-016 (LLM integration)
/execute-feat FEAT-016
```

The execute-feat skill will:
1. Read task definitions from tasks.md
2. Create checklist in planning/FEC-FEAT-XXX-workspace-checklist.md
3. Execute tasks in order
4. Run verification commands
5. Update feature_execution_progress.md

### Manual Execution

Alternatively, you can execute individual tasks:
1. Read task definition from tasks.md
2. Implement according to acceptance criteria
3. Run verification commands
4. Mark task complete in checklist

---

## Cost Estimation

Using gpt-4o-mini with default guardrails:

| Scenario | Agents | Messages | Tokens | Cost |
|----------|--------|----------|--------|------|
| Small test | 2 | 10 | 2k | $0.002 |
| Medium demo | 3 | 50 | 10k | $0.01 |
| Large demo | 5 | 100 | 20k | $0.02 |
| Full session (budget limit) | 5 | ~500 | ~100k | $1.00 |

**Note:** $1.00 default budget prevents accidental overspend. Typical testing costs < $0.10.

---

## Next Steps

1. **Review** this summary and tasks.md entries
2. **Execute FEAT-015** for immediate UI testing (1 day)
3. **Execute FEAT-016** for real LLM integration (2-3 days)
4. **Test** end-to-end with real OpenAI API calls
5. **Iterate** based on findings

The tasks are now ready for structured execution using the existing VibeForge workflow!
