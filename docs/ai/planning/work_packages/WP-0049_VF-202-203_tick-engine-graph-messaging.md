# WP-0049 — Tick Engine and graph-gated messaging

## Overview

- **VF Tasks:** VF-202, VF-203
- **Goal:** Implement the Tick Engine for discrete simulation progression and enforce graph-gated messaging (messages only allowed along configured agent_graph edges).
- **Dependencies:** WP-0043 (AgentFlowGraph model), WP-0048 (simulation endpoints)

## Context

The simulation endpoints (WP-0048) provide API control for starting/ticking/pausing simulations. Now we need the actual tick engine that performs work during each tick, and the messaging gating logic that ensures messages only flow along configured agent graph edges.

### What is "one tick"?

In the VibeForge simulation mode, one tick represents one atomic unit of progress:
- **Option 1:** One scheduling decision (selecting what to do next)
- **Option 2:** One agent message exchange batch (send + receive)
- **Option 3:** One state-machine transition batch

For this implementation, we'll start with a simple model:
- One tick = one agent execution cycle (process pending messages → execute → emit responses)

## Implementation Steps

### Step 1: Create TickEngine class (VF-202)

**File:** `orchestration/coordinator/tick_engine.py`

```python
class TickEngine:
    """Engine for discrete tick-based simulation progression.

    Manages the tick lifecycle:
    - advance_tick(): Perform one atomic unit of work
    - get_tick_events(): Get events produced during the tick
    - get_tick_state(): Get current tick status
    """

    def __init__(self, session: Session, graph: AgentFlowGraph):
        self.session = session
        self.graph = graph
        self.message_queue = []
        self.tick_events = []

    def advance_tick(self) -> TickResult:
        """Advance simulation by one tick.

        Returns:
            TickResult with events_in_tick, messages_in_tick
        """
        # 1. Process pending messages
        # 2. Execute ready agents
        # 3. Emit new messages to queue
        # 4. Return events produced
```

### Step 2: Implement graph-gated messaging (VF-203)

**File:** `orchestration/coordinator/tick_engine.py` (add to TickEngine)

```python
def validate_message(self, from_agent: str, to_agent: str) -> MessageValidation:
    """Validate if message is allowed based on agent_graph.

    A message A→B is allowed if:
    - Edge A→B exists in agent_graph, OR
    - from_agent is orchestrator (broadcast), OR
    - Message is a system/internal message

    Returns:
        MessageValidation with is_allowed, reason, event_type
    """

def send_message(self, from_agent: str, to_agent: str, content: dict) -> SendResult:
    """Send a message with graph validation.

    If blocked, emits MESSAGE_BLOCKED_BY_GRAPH event.
    """
```

### Step 3: Integrate tick engine with simulation endpoints

**File:** `apps/api/vibeforge_api/routers/control.py`

Update the `/simulation/tick` endpoint to call TickEngine.advance_tick() instead of just incrementing the counter.

### Step 4: Add MESSAGE_BLOCKED_BY_GRAPH event type

**File:** `apps/api/vibeforge_api/core/event_log.py`

Add the new event type so the UI can display why a message was blocked.

## Verification

```bash
cd apps/api && pytest tests/test_tick_engine.py tests/test_graph_gated_messaging.py -v
```

## Files to Touch

- `orchestration/coordinator/tick_engine.py` (new - main tick engine implementation)
- `apps/api/vibeforge_api/core/event_log.py` (add MESSAGE_BLOCKED_BY_GRAPH event type)
- `apps/api/tests/test_tick_engine.py` (new test file)
- `apps/api/tests/test_graph_gated_messaging.py` (new test file)

## Done When

- [x] VF-202: TickEngine class implemented with advance_tick() method
- [x] VF-202: Tick events are emitted and returned (TICK_ADVANCED, MESSAGE_SENT)
- [x] VF-203: Graph-gated messaging validation implemented (validate_message, send_message)
- [x] VF-203: Blocked messages emit MESSAGE_BLOCKED_BY_GRAPH event
- [x] VF-203: Allowed messages pass through (edge exists, orchestrator broadcast, self-message)
- [x] Tests cover single-tick and multi-tick scenarios (13 tick engine tests)
- [x] Tests verify graph-gated message blocking and allowing (16 messaging tests)
