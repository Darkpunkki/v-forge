# WP-0051 — Simulation Event Logging and API Client

## Goal
Extend event logging with simulation event types and add API client methods for simulation control with filtering support.

## VF Tasks Included
- VF-206: Extend event logging for simulation events
- VF-207: Add API client methods for simulation endpoints

## Dependencies
- WP-0048 ✓ (simulation lifecycle and tick control endpoints)
- WP-0049 ✓ (tick engine emits events)
- WP-0050 ✓ (simulation UI widgets added most API client methods)

## Execution Steps

### Step 1: Add missing simulation event types (VF-206)
- Add to EventType enum in `event_log.py`:
  - `SIMULATION_CONFIGURED` — when simulation mode is set
  - `SIMULATION_STARTED` — when simulation starts
  - `SIMULATION_RESET` — when simulation is reset
  - `SIMULATION_PAUSED` — when simulation is paused
  - `TICK_STARTED` — when a tick begins
  - `TICK_COMPLETED` — when a tick completes
- Note: TICK_ADVANCED, MESSAGE_SENT, MESSAGE_BLOCKED_BY_GRAPH already exist from WP-0049

### Step 2: Enhance EventLog filtering (VF-206)
- Extend `get_events()` method to support additional filters:
  - `tick_index` — filter by tick (from metadata)
  - `agent_id` — filter by agent (from metadata)
- Add `get_events_filtered()` method for multi-criteria filtering

### Step 3: Add events endpoint with filtering (VF-206)
- Add `GET /control/sessions/{session_id}/events/filter` endpoint
- Support query params: `event_type`, `tick_index`, `tick_min`, `tick_max`, `agent_id`

### Step 4: Add getEvents client method with filtering (VF-207)
- Add `EventsFilter` interface to controlClient.ts
- Add `getEvents(sessionId, filters)` method
- Note: Other simulation methods already added in WP-0050

### Step 5: Add integration tests (VF-207)
- Test full simulation lifecycle: config → start → tick → observe events → reset

## Done Means
- [ ] All simulation event types defined in EventType enum
- [ ] Events include tick_index and agent_id in metadata when applicable
- [ ] GET /events/filter supports query param filtering
- [ ] getEvents() client method with filtering works
- [ ] Integration tests pass
- [ ] `cd apps/api && pytest tests/test_event_log.py tests/test_simulation_api.py -v` passes
- [ ] `cd apps/ui && npm run build` passes

## Verification Commands
```bash
cd apps/api && pytest tests/test_event_log.py tests/test_simulation_api.py -v
cd apps/ui && npm run build
```
