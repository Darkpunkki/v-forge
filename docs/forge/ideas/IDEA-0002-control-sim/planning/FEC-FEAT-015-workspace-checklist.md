# FEAT-015 - UI Testing Verification

- Idea ID: IDEA-0002-control-sim
- Run ID: 2026-01-16T02-52-45.460Z_run-697f

## Tasks
- [x] TASK-048: Manual UI workflow verification with stub responses
  - Files: `apps/api/vibeforge_api/routers/control.py` (bug fix)
  - Verify: `python -m pytest apps/api/tests/test_simulation_api.py -v -k "tick"`
  - Files changed: `apps/api/vibeforge_api/routers/control.py`
  - Commands: API tests via curl + pytest
  - **Bug fixed**: Initial prompt now queued as first message
- [ ] TASK-049: Add polling fallback for simulation state updates
  - Files: `apps/ui/src/screens/ControlPanel.tsx`
  - Verify: `cd apps/ui && npx tsc --noEmit`
- [ ] TASK-050: Update AgentGraph to render simulation communication links
  - Files: `apps/ui/src/screens/control/widgets/AgentGraph.tsx`
  - Verify: `cd apps/ui && npx tsc --noEmit`
- [ ] TASK-051: Format blocked and stub messages in message log
  - Files: `apps/ui/src/screens/control/widgets/MultiAgentMessages.tsx`
  - Verify: `cd apps/ui && npx tsc --noEmit`

## Notes / Decisions

### TASK-048 Bug Fix

**Critical Bug Found & Fixed:**
The `initial_prompt` was stored in session but never queued as a message. 

**Fix Applied** (control.py, lines 867-883 and 947-963):
- Before `advance_tick()`, check if tick_index == 0 and initial_prompt exists
- If so, queue a message from "user" to first_agent_id with the prompt
- Use `bypass_validation=True` since "user" isn't in the agent roster

**Verification:**
- ✅ All tick tests pass (9 passed)
- ✅ API flow tested: message_sent events now appear
- ✅ Stub response generated: `[STUB] agent-2 -> user @ tick 1 (hash)`
- ✅ No real LLM calls (confirmed safe)

### LLM Safety Confirmed
- ✅ TickEngine always uses `generate_stub_response()`
- ✅ `use_real_llm` flag doesn't exist yet (to be added in FEAT-016)
- ✅ Simulation is 100% stub-based
