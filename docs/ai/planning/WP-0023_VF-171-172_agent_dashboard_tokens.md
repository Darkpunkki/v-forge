# WP-0023 — Agent Activity Dashboard and Token Visualization

## VF Tasks Included
- [ ] VF-171 — Agent activity dashboard (live status grid)
  - **Files:** `apps/ui/src/screens/control/widgets/AgentDashboard.tsx`
  - **Tests:** Visual verification with active sessions
- [ ] VF-172 — Token usage visualization (per-agent, per-session, cumulative)
  - **Files:** `apps/ui/src/screens/control/widgets/TokenVisualization.tsx`
  - **Tests:** `apps/api/tests/test_token_tracking.py`
  - **Verify:** Charts display token usage correctly

## Goal
Display live agent status and real-time token consumption to enable execution monitoring and cost control.

## Dependencies
- ✅ WP-0022 (Control panel architecture)
- ✅ WP-0021 (EventLog with token metadata)

## Execution Steps

### 1. VF-171: Agent Activity Dashboard

**Intent:** Show grid of agent cards with live status indicators (idle/thinking/executing).

**Implementation:**

Create `apps/ui/src/screens/control/widgets/AgentDashboard.tsx`:
```tsx
import React, { useState, useEffect } from 'react';
import { controlClient, SessionEvent } from '../../../api/controlClient';
import './AgentDashboard.css';

interface AgentStatus {
  role: string;
  status: 'idle' | 'thinking' | 'executing';
  currentTask?: string;
  model?: string;
  elapsedSeconds: number;
  lastActivity: Date;
}

interface AgentDashboardProps {
  sessionId: string;
}

const AgentDashboard: React.FC<AgentDashboardProps> = ({ sessionId }) => {
  const [agents, setAgents] = useState<Map<string, AgentStatus>>(new Map());

  useEffect(() => {
    // Stream events to update agent status
    const eventSource = controlClient.streamSessionEvents(sessionId, handleEvent);

    return () => {
      eventSource.close();
    };
  }, [sessionId]);

  const handleEvent = (event: SessionEvent) => {
    setAgents((prev) => {
      const updated = new Map(prev);

      // Initialize agent roles if not present
      const allRoles = ['orchestrator', 'worker', 'foreman', 'fixer', 'reviewer'];
      allRoles.forEach((role) => {
        if (!updated.has(role)) {
          updated.set(role, {
            role,
            status: 'idle',
            elapsedSeconds: 0,
            lastActivity: new Date(),
          });
        }
      });

      // Update based on event type
      if (event.event_type === 'AGENT_INVOKED' && event.agent_role) {
        updated.set(event.agent_role, {
          role: event.agent_role,
          status: 'thinking',
          currentTask: event.task_id,
          model: event.model,
          elapsedSeconds: 0,
          lastActivity: new Date(event.timestamp),
        });
      } else if (event.event_type === 'AGENT_RESPONSE' && event.agent_role) {
        updated.set(event.agent_role, {
          role: event.agent_role,
          status: 'executing',
          currentTask: event.task_id,
          model: event.model,
          elapsedSeconds: 0,
          lastActivity: new Date(event.timestamp),
        });
      } else if (event.event_type === 'TASK_COMPLETED' && event.metadata?.agent_role) {
        updated.set(event.metadata.agent_role, {
          role: event.metadata.agent_role,
          status: 'idle',
          elapsedSeconds: 0,
          lastActivity: new Date(event.timestamp),
        });
      }

      return updated;
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'idle':
        return '🟢';
      case 'thinking':
        return '🟡';
      case 'executing':
        return '🔴';
      default:
        return '⚪';
    }
  };

  return (
    <div className="agent-dashboard">
      <h3>🤖 Agent Activity</h3>
      <div className="agent-grid">
        {Array.from(agents.values()).map((agent) => (
          <div key={agent.role} className={`agent-card ${agent.status}`}>
            <div className="agent-header">
              <span className="agent-icon">{getStatusIcon(agent.status)}</span>
              <span className="agent-role">{agent.role}</span>
            </div>
            <div className="agent-details">
              <div className="agent-status">{agent.status}</div>
              {agent.currentTask && (
                <div className="agent-task">Task: {agent.currentTask.substring(0, 12)}</div>
              )}
              {agent.model && <div className="agent-model">Model: {agent.model}</div>}
              <div className="agent-activity">
                Last: {agent.lastActivity.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AgentDashboard;
```

Create `apps/ui/src/screens/control/widgets/AgentDashboard.css`:
```css
.agent-dashboard {
  background-color: #2d2d2d;
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.agent-dashboard h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: #e0e0e0;
}

.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.agent-card {
  background-color: #3a3a3a;
  padding: 1rem;
  border-radius: 6px;
  border-left: 4px solid #555;
  transition: all 0.3s;
}

.agent-card.thinking {
  border-left-color: #f59e0b;
  box-shadow: 0 0 10px rgba(245, 158, 11, 0.3);
}

.agent-card.executing {
  border-left-color: #ef4444;
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.3);
  animation: pulse 2s infinite;
}

.agent-card.idle {
  border-left-color: #10b981;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 10px rgba(239, 68, 68, 0.3);
  }
  50% {
    box-shadow: 0 0 20px rgba(239, 68, 68, 0.6);
  }
}

.agent-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.agent-icon {
  font-size: 1.2rem;
}

.agent-role {
  font-weight: bold;
  text-transform: capitalize;
  color: #e0e0e0;
}

.agent-details {
  font-size: 0.85rem;
  color: #aaa;
}

.agent-status {
  text-transform: uppercase;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.agent-task,
.agent-model,
.agent-activity {
  margin-bottom: 0.25rem;
}
```

---

### 2. VF-172: Token Usage Visualization

**Intent:** Display token consumption charts with cost estimates and budget alerts.

**Implementation:**

Create `apps/ui/src/screens/control/widgets/TokenVisualization.tsx`:
```tsx
import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { controlClient, SessionEvent } from '../../../api/controlClient';
import './TokenVisualization.css';

interface TokenData {
  role: string;
  tokens: number;
  cost: number;
}

interface TimelinePoint {
  timestamp: string;
  cumulativeTokens: number;
  costUSD: number;
}

interface TokenVisualizationProps {
  sessionId: string;
}

// Pricing per 1M tokens (example rates)
const PRICING = {
  'gpt-4o': { prompt: 2.50, completion: 10.00 },
  'gpt-4o-mini': { prompt: 0.15, completion: 0.60 },
  'claude-3-5-sonnet': { prompt: 3.00, completion: 15.00 },
};

const COLORS = ['#667eea', '#764ba2', '#f59e0b', '#10b981', '#ef4444'];

const TokenVisualization: React.FC<TokenVisualizationProps> = ({ sessionId }) => {
  const [tokensByRole, setTokensByRole] = useState<TokenData[]>([]);
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [totalTokens, setTotalTokens] = useState(0);
  const [totalCost, setTotalCost] = useState(0);

  useEffect(() => {
    const eventSource = controlClient.streamSessionEvents(sessionId, handleEvent);
    return () => eventSource.close();
  }, [sessionId]);

  const handleEvent = (event: SessionEvent) => {
    if (event.event_type === 'LLM_RESPONSE_RECEIVED' && event.metadata) {
      const { total_tokens, prompt_tokens, completion_tokens } = event.metadata;
      const model = event.model || 'gpt-4o-mini';
      const role = event.agent_role || 'orchestrator';

      // Calculate cost
      const pricing = PRICING[model as keyof typeof PRICING] || PRICING['gpt-4o-mini'];
      const cost =
        (prompt_tokens / 1_000_000) * pricing.prompt +
        (completion_tokens / 1_000_000) * pricing.completion;

      // Update by role
      setTokensByRole((prev) => {
        const updated = [...prev];
        const existing = updated.find((d) => d.role === role);
        if (existing) {
          existing.tokens += total_tokens;
          existing.cost += cost;
        } else {
          updated.push({ role, tokens: total_tokens, cost });
        }
        return updated;
      });

      // Update timeline
      setTimeline((prev) => {
        const newTotal = prev.length > 0 ? prev[prev.length - 1].cumulativeTokens + total_tokens : total_tokens;
        const newCost = prev.length > 0 ? prev[prev.length - 1].costUSD + cost : cost;
        return [
          ...prev,
          {
            timestamp: new Date(event.timestamp).toLocaleTimeString(),
            cumulativeTokens: newTotal,
            costUSD: parseFloat(newCost.toFixed(4)),
          },
        ];
      });

      // Update totals
      setTotalTokens((prev) => prev + total_tokens);
      setTotalCost((prev) => prev + cost);
    }
  };

  return (
    <div className="token-visualization">
      <h3>💰 Token Usage</h3>

      {/* Summary Stats */}
      <div className="token-stats">
        <div className="stat-card">
          <div className="stat-label">Total Tokens</div>
          <div className="stat-value">{totalTokens.toLocaleString()}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Est. Cost</div>
          <div className="stat-value">${totalCost.toFixed(4)}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Budget Alert</div>
          <div className={`stat-value ${totalCost > 0.50 ? 'warning' : 'ok'}`}>
            {totalCost > 0.50 ? '⚠️ High' : '✅ OK'}
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="charts-container">
        {/* Pie Chart: Distribution by Role */}
        <div className="chart-box">
          <h4>Distribution by Role</h4>
          {tokensByRole.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={tokensByRole}
                  dataKey="tokens"
                  nameKey="role"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={(entry) => `${entry.role}: ${entry.tokens}`}
                >
                  {tokensByRole.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="no-data">No token data yet</div>
          )}
        </div>

        {/* Line Chart: Cumulative over Time */}
        <div className="chart-box">
          <h4>Cumulative Tokens</h4>
          {timeline.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={timeline}>
                <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                <XAxis dataKey="timestamp" stroke="#aaa" />
                <YAxis stroke="#aaa" />
                <Tooltip contentStyle={{ backgroundColor: '#2d2d2d', border: '1px solid #555' }} />
                <Legend />
                <Line type="monotone" dataKey="cumulativeTokens" stroke="#667eea" name="Tokens" />
                <Line type="monotone" dataKey="costUSD" stroke="#f59e0b" name="Cost ($)" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="no-data">No timeline data yet</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TokenVisualization;
```

Create `apps/ui/src/screens/control/widgets/TokenVisualization.css`:
```css
.token-visualization {
  background-color: #2d2d2d;
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.token-visualization h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: #e0e0e0;
}

.token-stats {
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
  font-size: 0.85rem;
  color: #aaa;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #e0e0e0;
}

.stat-value.warning {
  color: #f59e0b;
}

.stat-value.ok {
  color: #10b981;
}

.charts-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.chart-box {
  background-color: #3a3a3a;
  padding: 1rem;
  border-radius: 6px;
}

.chart-box h4 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: #e0e0e0;
  font-size: 1rem;
}

.no-data {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 250px;
  color: #777;
  font-style: italic;
}
```

---

### 3. Backend: Token Tracking in Events

**Intent:** Ensure LLM events include token metadata.

**Implementation:**

Update SessionCoordinator and Orchestrator to emit token events (already planned in WP-0021):

```python
# In Orchestrator or DirectLlmAdapter, after LLM call:
event = Event(
    event_type=EventType.LLM_RESPONSE_RECEIVED,
    timestamp=datetime.utcnow(),
    session_id=session_id,
    message=f"LLM response from {response.model}",
    agent_role=role,
    model=response.model,
    metadata={
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
        "finish_reason": response.finish_reason,
    },
)
event_log.append(event)
```

**Tests:**

Create `apps/api/tests/test_token_tracking.py`:
```python
def test_llm_response_event_includes_token_metadata():
    """Test that LLM events include usage metadata."""
    event = Event(
        event_type=EventType.LLM_RESPONSE_RECEIVED,
        timestamp=datetime.utcnow(),
        session_id="test",
        message="LLM response",
        model="gpt-4o-mini",
        metadata={
            "prompt_tokens": 150,
            "completion_tokens": 300,
            "total_tokens": 450,
        },
    )

    assert event.metadata["total_tokens"] == 450
    event_dict = event.to_dict()
    assert event_dict["metadata"]["prompt_tokens"] == 150
```

---

### 4. Integration into Control Panel

**Intent:** Add widgets to ControlPanel.tsx.

**Implementation:**

Update `apps/ui/src/screens/control/ControlPanel.tsx`:
```tsx
import AgentDashboard from './widgets/AgentDashboard';
import TokenVisualization from './widgets/TokenVisualization';

// Inside session-details div:
<div className="session-details">
  <h2>Session: {selectedSession.substring(0, 8)}</h2>

  {/* Add widgets */}
  <AgentDashboard sessionId={selectedSession} />
  <TokenVisualization sessionId={selectedSession} />

  {/* Remaining placeholder widgets */}
  <div className="widgets-placeholder">
    <div className="widget-slot">🕸️ Agent Graph (WP-0024)</div>
    <div className="widget-slot">📅 Timeline (WP-0024)</div>
    {/* ... etc */}
  </div>
</div>
```

---

## Verification Commands
```bash
# Token tracking tests
cd apps/api && pytest tests/test_token_tracking.py -v

# Full test suite
cd apps/api && pytest -v

# Frontend build
cd apps/ui && npm run build

# Frontend dev
cd apps/ui && npm run dev
# Visit http://localhost:5173/control and select a session
```

## Done Means
- [ ] AgentDashboard widget displays agent cards with status indicators
- [ ] Agent status updates in real-time via SSE
- [ ] TokenVisualization widget shows pie chart (by role) and line chart (cumulative)
- [ ] Token metadata included in LLM_RESPONSE_RECEIVED events
- [ ] Cost calculations use model-specific pricing
- [ ] Budget alert changes color when cost exceeds threshold
- [ ] Widgets integrated into ControlPanel
- [ ] Charts use Recharts library for interactive visualization
- [ ] All token tracking tests pass

## Dependencies

Add to `apps/ui/package.json`:
```json
{
  "dependencies": {
    "recharts": "^2.10.0"
  }
}
```

Run: `cd apps/ui && npm install`
