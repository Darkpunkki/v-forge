# WP-0025 — Decision Transparency (Gates + Routing)

## VF Tasks Included
- [x] VF-175 — Gate decision log (block/warn/pass visualization)
  - **Files:**
    - `apps/ui/src/screens/control/widgets/GateLog.tsx` (real-time gate feed)
    - `apps/ui/src/screens/control/widgets/GateLog.css` (styling)
  - **Verify:** Log shows gate evaluations with status badges, filtering works
  - **Implementation Notes:**
    - Added GateLog widget that filters `gate_evaluated` events and renders status badges + details.
    - Emitted per-gate `gate_evaluated` events from SessionCoordinator.
  - **Verification:**
    - `cd apps/ui && npm run build`
    - `cd apps/api && pytest tests/test_gate_logging.py -v`

- [x] VF-176 — Model router decisions (model selection rationale)
  - **Files:**
    - `apps/ui/src/screens/control/widgets/ModelRouter.tsx` (routing decisions)
    - `apps/ui/src/screens/control/widgets/ModelRouter.css` (styling)
  - **Verify:** Shows escalation paths, model selection rationale, cost implications
  - **Implementation Notes:**
    - Added `model_routed` events with routing reasons + failure counts.
    - ModelRouter merges routing events with `llm_response_received` for model + cost estimates.
  - **Verification:**
    - `cd apps/ui && npm run build`

## Goal
Provide transparency into automated decision-making (gates and model routing) so developers can understand why tasks were blocked, which models were selected, and how escalation policies work in practice.

## Dependencies
- ✅ WP-0021 (EventLog + structured events) - provides GATE_EVALUATED and MODEL_SELECTED events
- ✅ WP-0022 (Control panel architecture) - provides widget container and SSE infrastructure

## Why Critical
Gates and model routing are black boxes without visualization. Developers need to see:
- Why a diff was blocked (security policy, command validation)
- When/how escalation occurred (worker failed → fixer invoked)
- Cost implications of model selection (gpt-4o vs gpt-4o-mini)

## Execution Steps

### 1. Gate Decision Log Widget

**Intent:** Real-time feed of gate evaluations with filtering by status (BLOCK/WARN/PASS).

**Implementation:**

Create `apps/ui/src/screens/control/widgets/GateLog.tsx`:
```tsx
import React, { useEffect, useState } from 'react';
import { controlClient, SessionEvent } from '../../../api/controlClient';
import './GateLog.css';

interface GateDecision {
  timestamp: Date;
  taskId: string;
  gateName: string;
  status: 'BLOCK' | 'WARN' | 'PASS';
  message: string;
  details?: Record<string, any>;
}

interface GateLogProps {
  sessionId: string;
}

const GateLog: React.FC<GateLogProps> = ({ sessionId }) => {
  const [decisions, setDecisions] = useState<GateDecision[]>([]);
  const [filter, setFilter] = useState<'ALL' | 'BLOCK' | 'WARN' | 'PASS'>('ALL');

  useEffect(() => {
    const eventSource = controlClient.streamSessionEvents(sessionId, handleEvent);
    return () => eventSource.close();
  }, [sessionId]);

  const handleEvent = (event: SessionEvent) => {
    if (event.event_type === 'GATE_EVALUATED') {
      const decision: GateDecision = {
        timestamp: new Date(event.timestamp),
        taskId: event.task_id || 'unknown',
        gateName: event.metadata?.gate_name || 'UnknownGate',
        status: event.metadata?.status || 'PASS',
        message: event.message,
        details: event.metadata?.details || {},
      };

      setDecisions((prev) => [decision, ...prev]); // Prepend (newest first)
    }
  };

  const filteredDecisions =
    filter === 'ALL'
      ? decisions
      : decisions.filter((d) => d.status === filter);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'BLOCK':
        return '🚫';
      case 'WARN':
        return '⚠️';
      case 'PASS':
        return '✅';
      default:
        return '❓';
    }
  };

  const getStatusClass = (status: string) => {
    return status.toLowerCase();
  };

  return (
    <div className="gate-log-widget">
      <div className="widget-header">
        <h3>Gate Decision Log</h3>
        <div className="filter-buttons">
          <button
            className={filter === 'ALL' ? 'active' : ''}
            onClick={() => setFilter('ALL')}
          >
            All ({decisions.length})
          </button>
          <button
            className={filter === 'BLOCK' ? 'active' : ''}
            onClick={() => setFilter('BLOCK')}
          >
            Blocked ({decisions.filter((d) => d.status === 'BLOCK').length})
          </button>
          <button
            className={filter === 'WARN' ? 'active' : ''}
            onClick={() => setFilter('WARN')}
          >
            Warnings ({decisions.filter((d) => d.status === 'WARN').length})
          </button>
          <button
            className={filter === 'PASS' ? 'active' : ''}
            onClick={() => setFilter('PASS')}
          >
            Passed ({decisions.filter((d) => d.status === 'PASS').length})
          </button>
        </div>
      </div>

      <div className="gate-log-content">
        {filteredDecisions.length === 0 ? (
          <div className="no-decisions">No gate evaluations yet</div>
        ) : (
          <ul className="decision-list">
            {filteredDecisions.map((decision, idx) => (
              <li key={idx} className={`decision-item ${getStatusClass(decision.status)}`}>
                <div className="decision-header">
                  <span className="status-icon">{getStatusIcon(decision.status)}</span>
                  <span className="gate-name">{decision.gateName}</span>
                  <span className="timestamp">
                    {decision.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                <div className="decision-body">
                  <div className="task-id">Task: {decision.taskId.substring(0, 8)}</div>
                  <div className="message">{decision.message}</div>
                  {Object.keys(decision.details).length > 0 && (
                    <details className="details-toggle">
                      <summary>Details</summary>
                      <pre className="details-json">
                        {JSON.stringify(decision.details, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default GateLog;
```

Create `apps/ui/src/screens/control/widgets/GateLog.css`:
```css
.gate-log-widget {
  background-color: #2d2d2d;
  padding: 1.5rem;
  border-radius: 8px;
  height: 600px;
  display: flex;
  flex-direction: column;
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.widget-header h3 {
  margin: 0;
  color: #e0e0e0;
  font-size: 1.1rem;
}

.filter-buttons {
  display: flex;
  gap: 0.5rem;
}

.filter-buttons button {
  padding: 0.5rem 1rem;
  background-color: #3a3a3a;
  color: #aaa;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.filter-buttons button:hover {
  background-color: #4a4a4a;
}

.filter-buttons button.active {
  background-color: #667eea;
  color: white;
}

.gate-log-content {
  flex: 1;
  background-color: #1e1e1e;
  border-radius: 4px;
  padding: 1rem;
  overflow-y: auto;
}

.no-decisions {
  text-align: center;
  padding: 2rem;
  color: #777;
}

.decision-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.decision-item {
  padding: 1rem;
  margin-bottom: 0.75rem;
  background-color: #2d2d2d;
  border-radius: 6px;
  border-left: 4px solid #6b7280;
  transition: transform 0.2s;
}

.decision-item:hover {
  transform: translateX(4px);
}

.decision-item.block {
  border-left-color: #ef4444;
}

.decision-item.warn {
  border-left-color: #f59e0b;
}

.decision-item.pass {
  border-left-color: #10b981;
}

.decision-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.status-icon {
  font-size: 1.2rem;
}

.gate-name {
  font-weight: 600;
  color: #e0e0e0;
  flex: 1;
}

.timestamp {
  font-size: 0.8rem;
  color: #777;
}

.decision-body {
  padding-left: 2rem;
}

.task-id {
  font-size: 0.85rem;
  color: #aaa;
  margin-bottom: 0.5rem;
}

.message {
  color: #e0e0e0;
  line-height: 1.5;
}

.details-toggle {
  margin-top: 0.5rem;
  cursor: pointer;
}

.details-toggle summary {
  font-size: 0.85rem;
  color: #667eea;
  user-select: none;
}

.details-json {
  background-color: #1e1e1e;
  padding: 0.75rem;
  border-radius: 4px;
  margin-top: 0.5rem;
  overflow-x: auto;
  font-size: 0.8rem;
  color: #10b981;
}
```

---

### 2. Model Router Widget

**Intent:** Visualize model selection decisions and escalation paths.

**Implementation:**

Create `apps/ui/src/screens/control/widgets/ModelRouter.tsx`:
```tsx
import React, { useEffect, useState } from 'react';
import { controlClient, SessionEvent } from '../../../api/controlClient';
import './ModelRouter.css';

interface RoutingDecision {
  timestamp: Date;
  taskId: string;
  agentRole: string;
  model: string;
  reason: string;
  failureCount: number;
  estimatedCost: number;
}

interface ModelRouterProps {
  sessionId: string;
}

const MODEL_PRICING: Record<string, { prompt: number; completion: number }> = {
  'gpt-4o': { prompt: 2.5, completion: 10.0 },
  'gpt-4o-mini': { prompt: 0.15, completion: 0.6 },
  'claude-sonnet-4': { prompt: 3.0, completion: 15.0 },
  'claude-opus-4': { prompt: 15.0, completion: 75.0 },
};

const ModelRouter: React.FC<ModelRouterProps> = ({ sessionId }) => {
  const [decisions, setDecisions] = useState<RoutingDecision[]>([]);

  useEffect(() => {
    const eventSource = controlClient.streamSessionEvents(sessionId, handleEvent);
    return () => eventSource.close();
  }, [sessionId]);

  const handleEvent = (event: SessionEvent) => {
    if (event.event_type === 'AGENT_INVOKED' && event.model) {
      const failureCount = event.metadata?.failure_count || 0;
      const reason = getRoutingReason(event.agent_role, failureCount);

      // Estimate cost (assuming 1000 prompt + 500 completion tokens)
      const pricing = MODEL_PRICING[event.model] || { prompt: 1.0, completion: 2.0 };
      const estimatedCost = ((1000 / 1_000_000) * pricing.prompt) + ((500 / 1_000_000) * pricing.completion);

      const decision: RoutingDecision = {
        timestamp: new Date(event.timestamp),
        taskId: event.task_id || 'unknown',
        agentRole: event.agent_role || 'unknown',
        model: event.model,
        reason,
        failureCount,
        estimatedCost,
      };

      setDecisions((prev) => [decision, ...prev]);
    }
  };

  const getRoutingReason = (role: string | undefined, failureCount: number): string => {
    if (role === 'orchestrator') {
      return 'Orchestrator always uses powerful model for planning';
    }
    if (role === 'worker' && failureCount === 0) {
      return 'Initial attempt: using balanced model';
    }
    if (role === 'worker' && failureCount === 1) {
      return 'Retry after failure: escalated to powerful model';
    }
    if (role === 'fixer') {
      return 'Escalated to fixer agent after worker failures';
    }
    return 'Default routing';
  };

  const getModelBadgeClass = (model: string): string => {
    if (model.includes('mini')) return 'balanced';
    if (model.includes('opus')) return 'powerful';
    return 'default';
  };

  return (
    <div className="model-router-widget">
      <h3>Model Routing Decisions</h3>

      <div className="routing-stats">
        <div className="stat-card">
          <div className="stat-label">Total Decisions</div>
          <div className="stat-value">{decisions.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Escalations</div>
          <div className="stat-value">
            {decisions.filter((d) => d.failureCount > 0).length}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Estimated Cost</div>
          <div className="stat-value">
            ${decisions.reduce((sum, d) => sum + d.estimatedCost, 0).toFixed(4)}
          </div>
        </div>
      </div>

      <div className="routing-log">
        {decisions.length === 0 ? (
          <div className="no-decisions">No routing decisions yet</div>
        ) : (
          <ul className="decision-list">
            {decisions.map((decision, idx) => (
              <li key={idx} className="routing-item">
                <div className="routing-header">
                  <span className={`model-badge ${getModelBadgeClass(decision.model)}`}>
                    {decision.model}
                  </span>
                  <span className="agent-role">{decision.agentRole}</span>
                  {decision.failureCount > 0 && (
                    <span className="escalation-badge">
                      ⚡ Escalation (attempt {decision.failureCount + 1})
                    </span>
                  )}
                  <span className="timestamp">
                    {decision.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                <div className="routing-body">
                  <div className="task-id">Task: {decision.taskId.substring(0, 8)}</div>
                  <div className="reason">{decision.reason}</div>
                  <div className="cost-estimate">
                    Est. cost: ${decision.estimatedCost.toFixed(4)}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default ModelRouter;
```

Create `apps/ui/src/screens/control/widgets/ModelRouter.css`:
```css
.model-router-widget {
  background-color: #2d2d2d;
  padding: 1.5rem;
  border-radius: 8px;
  height: 600px;
  display: flex;
  flex-direction: column;
}

.model-router-widget h3 {
  margin: 0 0 1rem 0;
  color: #e0e0e0;
  font-size: 1.1rem;
}

.routing-stats {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  flex: 1;
  background-color: #3a3a3a;
  padding: 1rem;
  border-radius: 6px;
  text-align: center;
}

.stat-label {
  font-size: 0.8rem;
  color: #aaa;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #667eea;
}

.routing-log {
  flex: 1;
  background-color: #1e1e1e;
  border-radius: 4px;
  padding: 1rem;
  overflow-y: auto;
}

.no-decisions {
  text-align: center;
  padding: 2rem;
  color: #777;
}

.decision-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.routing-item {
  padding: 1rem;
  margin-bottom: 0.75rem;
  background-color: #2d2d2d;
  border-radius: 6px;
  border-left: 4px solid #667eea;
}

.routing-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
}

.model-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
}

.model-badge.balanced {
  background-color: #10b981;
  color: white;
}

.model-badge.powerful {
  background-color: #f59e0b;
  color: white;
}

.model-badge.default {
  background-color: #6b7280;
  color: white;
}

.agent-role {
  font-weight: 600;
  color: #e0e0e0;
  text-transform: capitalize;
}

.escalation-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  background-color: #ef4444;
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
}

.timestamp {
  margin-left: auto;
  font-size: 0.8rem;
  color: #777;
}

.routing-body {
  padding-left: 1rem;
}

.task-id {
  font-size: 0.85rem;
  color: #aaa;
  margin-bottom: 0.5rem;
}

.reason {
  color: #e0e0e0;
  line-height: 1.5;
  margin-bottom: 0.5rem;
}

.cost-estimate {
  font-size: 0.85rem;
  color: #10b981;
  font-weight: 600;
}
```

---

### 3. Integrate Widgets into ControlPanel

**Intent:** Add gate log and model router widgets to control panel layout.

**Implementation:**

Update `apps/ui/src/screens/control/ControlPanel.tsx`:
```tsx
import GateLog from './widgets/GateLog';
import ModelRouter from './widgets/ModelRouter';

// Inside the widgets-grid:
<div className="widgets-grid">
  {/* WP-0023 widgets */}
  <AgentDashboard sessionId={selectedSession} />
  <TokenVisualization sessionId={selectedSession} />

  {/* WP-0024 widgets */}
  <AgentGraph sessionId={selectedSession} />
  <ExecutionTimeline sessionId={selectedSession} />

  {/* WP-0025 widgets (NEW) */}
  <GateLog sessionId={selectedSession} />
  <ModelRouter sessionId={selectedSession} />

  {/* WP-0026-0027 placeholders */}
  <div className="widget-slot">📈 Analytics (WP-0026)</div>
  <div className="widget-slot">📋 Event Stream (WP-0026)</div>
  <div className="widget-slot">🔍 Prompt Inspector (WP-0027)</div>
  <div className="widget-slot">💵 Cost Analytics (WP-0027)</div>
</div>
```

---

## Verification Commands
```bash
# Frontend build
cd apps/ui && npm run build

# Frontend dev server
cd apps/ui && npm run dev
# Visit: http://localhost:5173/control

# Test with active session:
# 1. Start a session that will trigger gate evaluations (e.g., unsafe commands)
# 2. Navigate to /control and select the session
# 3. Verify GateLog shows evaluations with BLOCK/WARN/PASS badges
# 4. Verify filtering buttons work
# 5. Verify ModelRouter shows model selections with escalation indicators
# 6. Verify cost estimates are displayed
```

## Done Means
- [x] GateLog component renders real-time gate evaluations
- [x] GateLog shows status badges (🚫 BLOCK, ⚠️ WARN, ✅ PASS)
- [x] GateLog filtering works (All/Block/Warn/Pass)
- [x] GateLog displays gate names, task IDs, messages, and details
- [x] ModelRouter component renders routing decisions
- [x] ModelRouter shows model badges (balanced/powerful)
- [x] ModelRouter highlights escalations with red badges
- [x] ModelRouter displays routing rationale
- [x] ModelRouter calculates and displays estimated costs
- [x] Both widgets integrate into ControlPanel layout
- [x] Widgets update in real-time via SSE events

## Architecture Notes

**Gate Log Design:**
- Newest decisions first (prepend, not append)
- Color-coded left border (red=block, orange=warn, green=pass)
- Collapsible details section for full metadata
- Filter counts update dynamically

**Routing Reason Logic:**
- Orchestrator → "always powerful" (planning requires reasoning)
- Worker attempt 1 → "balanced model" (cost-efficient first try)
- Worker attempt 2 → "escalated to powerful" (retry with more capability)
- Fixer → "escalated after worker failures" (last resort)

**Cost Estimation:**
- Assumes 1000 prompt tokens + 500 completion tokens per task
- Uses model-specific pricing (per 1M tokens)
- Provides rough order-of-magnitude estimates
- Can be refined later with actual token counts from LLM_RESPONSE_RECEIVED events

**Event Dependencies:**
- GATE_EVALUATED → gate log entries
  - Requires: gate_name, status, message in metadata
- AGENT_INVOKED → routing decisions
  - Requires: agent_role, model, failure_count in metadata

**Why These Widgets Matter:**
- **Gate Log** - Helps debug why diffs are blocked (security, validation)
- **Model Router** - Shows cost/performance tradeoffs and escalation behavior
- Together they provide full transparency into automated decision-making
