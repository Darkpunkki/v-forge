# WP-0048 — Simulation lifecycle and tick control endpoints

## Overview

- **VF Tasks:** VF-200, VF-201
- **Goal:** Add simulation lifecycle endpoints (config, start, reset) and tick control endpoints (tick, ticks, pause, state) to enable UI-driven manual simulation progression.
- **Dependencies:** WP-0043 (session model with simulation fields), WP-0044 (workflow endpoints)

## Context

With the workflow configuration endpoints (WP-0044) in place, we now need simulation control endpoints to:

1. Configure simulation mode (manual/auto) and parameters
2. Start simulations (with validation that workflow is complete)
3. Control tick progression (advance one/N ticks, pause, get state)
4. Reset simulations

The session model already has simulation fields (simulation_mode, tick_index, tick_status, auto_delay_ms, tick_budget) from VF-190.

## Implementation Steps

### Step 1: Add request/response models for simulation endpoints

**File:** `apps/api/vibeforge_api/models/requests.py`

```python
class SimulationConfigRequest(BaseModel):
    """Request to configure simulation mode."""
    simulation_mode: str = "manual"  # "manual" | "auto"
    auto_delay_ms: int | None = None  # Delay between auto ticks

class SimulationStartRequest(BaseModel):
    """Request to start simulation (validates workflow is complete)."""
    pass  # No body needed - validates session state

class SimulationResetRequest(BaseModel):
    """Request to reset simulation state."""
    preserve_workflow: bool = True  # Keep agent config, clear tick state

class SimulationTickRequest(BaseModel):
    """Request to advance simulation by one tick."""
    pass  # No body needed

class SimulationTicksRequest(BaseModel):
    """Request to advance simulation by N ticks."""
    count: int = Field(ge=1, le=100, default=1)  # Safety limit
```

**File:** `apps/api/vibeforge_api/models/responses.py`

```python
class SimulationConfigResponse(BaseModel):
    """Response after configuring simulation."""
    session_id: str
    simulation_mode: str
    auto_delay_ms: int | None
    message: str

class SimulationStartResponse(BaseModel):
    """Response after starting simulation."""
    session_id: str
    started: bool
    tick_index: int
    tick_status: str
    message: str

class SimulationResetResponse(BaseModel):
    """Response after resetting simulation."""
    session_id: str
    tick_index: int
    tick_status: str
    workflow_preserved: bool
    message: str

class SimulationTickResponse(BaseModel):
    """Response after advancing one tick."""
    session_id: str
    tick_index: int
    tick_status: str
    events_produced: int
    message: str

class SimulationStateResponse(BaseModel):
    """Current simulation state."""
    session_id: str
    simulation_mode: str
    tick_index: int
    tick_status: str
    auto_delay_ms: int | None
    tick_budget: int | None
    is_started: bool
    is_paused: bool
    queued_work_summary: dict
```

### Step 2: Implement VF-200 simulation lifecycle endpoints

**File:** `apps/api/vibeforge_api/routers/control.py` (add after workflow endpoints)

```python
# VF-200: Simulation lifecycle endpoints

@router.post("/sessions/{session_id}/simulation/config")
async def configure_simulation(session_id: str, request: SimulationConfigRequest):
    """Configure simulation mode and parameters (VF-200)."""
    # Validate session exists and not terminal
    # Cannot configure if simulation is already running
    # Set simulation_mode and auto_delay_ms

@router.post("/sessions/{session_id}/simulation/start")
async def start_simulation(session_id: str):
    """Start simulation - validates workflow is complete (VF-200)."""
    # Validate: agents initialized, roles assigned, graph configured, main_task set
    # Set tick_status to "running"
    # Lock configuration (prevent changes during simulation)

@router.post("/sessions/{session_id}/simulation/reset")
async def reset_simulation(session_id: str, request: SimulationResetRequest):
    """Reset simulation state (VF-200)."""
    # Reset tick_index to 0
    # Set tick_status to "idle"
    # Optionally clear workflow config based on preserve_workflow
```

### Step 3: Implement VF-201 tick control endpoints

```python
# VF-201: Tick control endpoints

@router.post("/sessions/{session_id}/simulation/tick")
async def advance_tick(session_id: str):
    """Advance simulation by exactly one tick (VF-201)."""
    # Validate simulation is started (tick_status != "idle")
    # Increment tick_index
    # Return events produced (placeholder for now)

@router.post("/sessions/{session_id}/simulation/ticks")
async def advance_ticks(session_id: str, request: SimulationTicksRequest):
    """Advance simulation by N ticks (VF-201)."""
    # Validate simulation is started
    # Advance tick_index by N (with safety limit)
    # Return aggregated events produced

@router.post("/sessions/{session_id}/simulation/pause")
async def pause_simulation(session_id: str):
    """Pause auto-run simulation (VF-201)."""
    # Only valid if simulation_mode == "auto" and tick_status == "running"
    # Set tick_status to "paused"

@router.get("/sessions/{session_id}/simulation/state")
async def get_simulation_state(session_id: str):
    """Get current simulation state (VF-201)."""
    # Return tick_index, simulation_mode, tick_status, queued work summary
```

### Step 4: Add comprehensive tests

**File:** `apps/api/tests/test_simulation_api.py` (new)

Cover:
- Lifecycle: config → start (valid) → reset
- Start validation (reject if workflow incomplete)
- Tick control (advance 1, advance N, pause)
- State retrieval
- Error cases (start without config, tick without start, etc.)

## Verification

```bash
cd apps/api && pytest tests/test_simulation_api.py -v
```

## Files to Touch

- `apps/api/vibeforge_api/models/requests.py` — add 5 request models
- `apps/api/vibeforge_api/models/responses.py` — add 5 response models
- `apps/api/vibeforge_api/models/__init__.py` — export new models
- `apps/api/vibeforge_api/routers/control.py` — add 7 endpoints
- `apps/api/tests/test_simulation_api.py` — new test file

## Done When

- [x] VF-200: Simulation lifecycle endpoints (config, start, reset) implemented
- [x] VF-201: Tick control endpoints (tick, ticks, pause, state) implemented
- [x] Request/response models added and exported
- [x] Tests cover all endpoints with success and error cases (27 tests)
- [x] CI passes with all tests (27 passed)
