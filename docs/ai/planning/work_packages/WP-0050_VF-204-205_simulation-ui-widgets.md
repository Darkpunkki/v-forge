# WP-0050 — Simulation UI Widgets

## Goal
Add UI widgets for simulation control (mode toggle, tick buttons) and multi-agent messaging visualization (conversation-style view, event filtering).

## VF Tasks Included
- VF-204: Create Simulation UI widgets for control panel
- VF-205: Create multi-agent messaging visualization

## Dependencies
- WP-0048 ✓ (simulation lifecycle and tick control endpoints)
- WP-0049 ✓ (Tick Engine and graph-gated messaging)
- WP-0046 ✓ (workflow widgets)

## Execution Steps

### Step 1: Add simulation API client methods
- Add types for simulation request/response models to controlClient.ts
- Implement API methods:
  - `configureSimulation()` - configure mode, delay, budget
  - `startSimulation()` - validate and start
  - `resetSimulation()` - reset state
  - `advanceTick()` - single tick
  - `advanceTicks()` - N ticks
  - `pauseSimulation()` - pause auto-run
  - `getSimulationState()` - get current state

### Step 2: Create SimulationConfig widget (VF-204)
- Create `apps/ui/src/screens/control/widgets/SimulationConfig.tsx`
- Features:
  - Mode toggle: manual vs auto
  - Auto-delay input (ms) when in auto mode
  - Tick budget input (optional)
  - Configure button

### Step 3: Create TickControls widget (VF-204)
- Create `apps/ui/src/screens/control/widgets/TickControls.tsx`
- Features:
  - Current tick index display
  - Tick status indicator (idle/running/paused)
  - Run 1 tick button
  - Run N ticks input + button
  - Pause button (when auto mode running)
  - Reset button
  - Start simulation button (when not started)

### Step 4: Create MultiAgentMessages widget (VF-205)
- Create `apps/ui/src/screens/control/widgets/MultiAgentMessages.tsx`
- Features:
  - Conversation-style view grouped by agent
  - Show sender/recipient, timestamp/tick, role, model, message type
  - Filter by MESSAGE_SENT events
  - Visual distinction for different agents

### Step 5: Enhance EventStream with tick and agent filters (VF-205)
- Add tick index filter dropdown to EventStream
- Add event type filter presets for simulation events
- Support filtering by tick range

### Step 6: Integrate widgets into ControlPanel
- Add SimulationConfig widget to workflow configuration section
- Add TickControls widget below workflow config (when simulation configured)
- Add MultiAgentMessages to monitoring section

## Done Means
- [ ] Simulation API client methods in controlClient.ts
- [ ] SimulationConfig widget toggles mode, sets delay/budget
- [ ] TickControls widget advances ticks, shows state
- [ ] MultiAgentMessages shows agent-to-agent conversation view
- [ ] EventStream supports tick index filtering
- [ ] All widgets integrated into ControlPanel
- [ ] `cd apps/ui && npm run build` passes

## Verification Commands
```bash
cd apps/ui && npm run build
```
