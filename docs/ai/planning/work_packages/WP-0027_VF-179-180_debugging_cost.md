# WP-0027 — Deep Debugging (Prompts + Cost Analytics)

## VF Tasks Included
- [x] VF-179 — Agent prompt inspector (view actual prompts sent to LLMs)
  - **Files:**
    - `apps/ui/src/screens/control/widgets/PromptInspector.tsx` (prompt viewer)
    - `apps/ui/src/screens/control/widgets/PromptInspector.css` (styling)
    - `apps/api/vibeforge_api/routers/control.py` (prompt retrieval endpoint)
    - `orchestration/coordinator/session_coordinator.py` (emit LLM request events)
  - **Tests:**
    - `apps/api/tests/test_control_api.py::TestControlPrompts` (prompt endpoint)
  - **Verify:** Inspector shows full prompts with template variables expanded, syntax highlighting
  - **Completed:** Added prompt event emission + prompt inspector UI with copy controls and metadata.

- [x] VF-180 — Cost analytics (token cost breakdown by provider/model)
  - **Files:**
    - `apps/ui/src/screens/control/widgets/CostAnalytics.tsx` (cost breakdown)
    - `apps/ui/src/screens/control/widgets/CostAnalytics.css` (styling)
  - **Tests:**
    - `apps/api/tests/test_cost_tracking.py` (token metadata persistence)
  - **Verify:** Shows cost breakdown by model, burn rate chart, budget alerts
  - **Completed:** Cost analytics widget uses LLM response events to compute spend, burn rate, and budgets.

## Goal
Enable deep debugging of LLM interactions by inspecting actual prompts sent to models, and provide granular cost analytics to help optimize budget allocation and detect cost anomalies.

## Dependencies
- ✅ WP-0021 (EventLog + structured events) - provides LLM_REQUEST_SENT/RESPONSE events
- ✅ WP-0022 (Control panel architecture) - provides widget container and SSE infrastructure
- ✅ WP-0023 (Token visualization) - provides baseline token tracking

## Why Critical
Prompts are the most critical debugging tool for LLM behavior:
- "Why did the agent generate this code?"
- "What context was included in the prompt?"
- "Are template variables expanding correctly?"

Cost analytics prevent budget overruns:
- "Which model is consuming the most tokens?"
- "Is our burn rate sustainable?"
- "Should we use cheaper models for certain tasks?"

## Execution Steps

### 1. Backend: Prompt Storage and Retrieval

**Intent:** Store prompts in event log and expose retrieval endpoint.

**Implementation:**

Update `apps/api/vibeforge_api/core/event_log.py` to ensure LLM_REQUEST_SENT events include full prompts:
```python
# When logging LLM requests, include full prompt in metadata
event_log.append(Event(
    event_type=EventType.LLM_REQUEST_SENT,
    timestamp=datetime.now(timezone.utc),
    session_id=session_id,
    message=f"LLM request sent to {model}",
    task_id=task_id,
    agent_role=agent_role,
    model=model,
    metadata={
        "prompt": full_prompt_text,  # Full prompt with template expansion
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system_message": system_message,  # Optional: separate system prompt
    }
))
```

Update `apps/api/vibeforge_api/routers/control.py` to add prompt retrieval endpoint:
```python
@router.get("/sessions/{session_id}/prompts")
async def get_session_prompts(session_id: str):
    """Get all prompts sent during a session."""
    from vibeforge_api.core.event_log import EventLog
    from vibeforge_api.core.workspace import WorkspaceManager

    workspace_manager = WorkspaceManager()
    workspace_path = workspace_manager.workspace_root / session_id
    event_log_path = workspace_path / "events.jsonl"

    if not event_log_path.exists():
        raise HTTPException(status_code=404, detail="Event log not found")

    event_log = EventLog(str(event_log_path))
    events = event_log.get_events(event_type=EventType.LLM_REQUEST_SENT)

    prompts = []
    for event in events:
        prompts.append({
            "timestamp": event.timestamp.isoformat(),
            "task_id": event.task_id,
            "agent_role": event.agent_role,
            "model": event.model,
            "prompt": event.metadata.get("prompt", ""),
            "system_message": event.metadata.get("system_message", ""),
            "max_tokens": event.metadata.get("max_tokens"),
            "temperature": event.metadata.get("temperature"),
        })

    return {"prompts": prompts, "total": len(prompts)}
```

**Tests in `apps/api/tests/test_control_api.py`:**
```python
@pytest.mark.asyncio
async def test_get_session_prompts(tmp_path):
    """Test prompt retrieval endpoint."""
    session_id = "test_session"
    workspace_path = tmp_path / session_id
    workspace_path.mkdir(parents=True)
    event_log_path = workspace_path / "events.jsonl"

    # Create event log with LLM_REQUEST_SENT events
    event_log = EventLog(str(event_log_path))
    event_log.append(Event(
        event_type=EventType.LLM_REQUEST_SENT,
        timestamp=datetime.now(timezone.utc),
        session_id=session_id,
        message="LLM request",
        task_id="task_1",
        agent_role="worker",
        model="gpt-4o-mini",
        metadata={
            "prompt": "Write a Python function to add two numbers",
            "system_message": "You are a helpful coding assistant",
            "max_tokens": 1000,
            "temperature": 0.7,
        }
    ))

    # Mock WorkspaceManager
    with patch('vibeforge_api.routers.control.WorkspaceManager') as mock_wm:
        mock_wm.return_value.workspace_root = tmp_path

        response = await get_session_prompts(session_id)

        assert response["total"] == 1
        assert response["prompts"][0]["model"] == "gpt-4o-mini"
        assert "add two numbers" in response["prompts"][0]["prompt"]
```

---

### 2. Frontend: Prompt Inspector Widget

**Intent:** Display prompts with syntax highlighting and filtering.

**Implementation:**

Install syntax highlighting library:
```bash
cd apps/ui && npm install react-syntax-highlighter @types/react-syntax-highlighter
```

Create `apps/ui/src/screens/control/widgets/PromptInspector.tsx`:
```tsx
import React, { useEffect, useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { controlClient } from '../../../api/controlClient';
import './PromptInspector.css';

interface Prompt {
  timestamp: string;
  taskId: string;
  agentRole: string;
  model: string;
  prompt: string;
  systemMessage: string;
  maxTokens: number;
  temperature: number;
}

interface PromptInspectorProps {
  sessionId: string;
}

const PromptInspector: React.FC<PromptInspectorProps> = ({ sessionId }) => {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [selectedPrompt, setSelectedPrompt] = useState<Prompt | null>(null);
  const [filterAgent, setFilterAgent] = useState<string>('ALL');

  useEffect(() => {
    loadPrompts();
  }, [sessionId]);

  const loadPrompts = async () => {
    try {
      const response = await fetch(`http://localhost:8000/control/sessions/${sessionId}/prompts`);
      const data = await response.json();

      const promptsData: Prompt[] = data.prompts.map((p: any) => ({
        timestamp: p.timestamp,
        taskId: p.task_id,
        agentRole: p.agent_role,
        model: p.model,
        prompt: p.prompt,
        systemMessage: p.system_message,
        maxTokens: p.max_tokens,
        temperature: p.temperature,
      }));

      setPrompts(promptsData);
      if (promptsData.length > 0) {
        setSelectedPrompt(promptsData[0]);
      }
    } catch (error) {
      console.error('Failed to load prompts:', error);
    }
  };

  const agentRoles = ['ALL', ...new Set(prompts.map((p) => p.agentRole))];

  const filteredPrompts =
    filterAgent === 'ALL'
      ? prompts
      : prompts.filter((p) => p.agentRole === filterAgent);

  return (
    <div className="prompt-inspector-widget">
      <div className="inspector-header">
        <h3>Prompt Inspector</h3>
        <select
          className="agent-filter"
          value={filterAgent}
          onChange={(e) => setFilterAgent(e.target.value)}
        >
          {agentRoles.map((role) => (
            <option key={role} value={role}>
              {role === 'ALL' ? 'All Agents' : role}
            </option>
          ))}
        </select>
      </div>

      <div className="inspector-layout">
        {/* Left sidebar: Prompt list */}
        <aside className="prompt-list">
          {filteredPrompts.length === 0 ? (
            <div className="no-prompts">No prompts found</div>
          ) : (
            <ul>
              {filteredPrompts.map((prompt, idx) => (
                <li
                  key={idx}
                  className={`prompt-item ${selectedPrompt === prompt ? 'selected' : ''}`}
                  onClick={() => setSelectedPrompt(prompt)}
                >
                  <div className="prompt-agent">{prompt.agentRole}</div>
                  <div className="prompt-model">{prompt.model}</div>
                  <div className="prompt-task">
                    Task: {prompt.taskId.substring(0, 8)}
                  </div>
                  <div className="prompt-time">
                    {new Date(prompt.timestamp).toLocaleTimeString()}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </aside>

        {/* Main content: Prompt viewer */}
        <main className="prompt-viewer">
          {selectedPrompt ? (
            <div className="prompt-details">
              <div className="prompt-meta">
                <div className="meta-item">
                  <span className="meta-label">Agent:</span>
                  <span className="meta-value">{selectedPrompt.agentRole}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Model:</span>
                  <span className="meta-value">{selectedPrompt.model}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Task:</span>
                  <span className="meta-value">{selectedPrompt.taskId}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Max Tokens:</span>
                  <span className="meta-value">{selectedPrompt.maxTokens}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Temperature:</span>
                  <span className="meta-value">{selectedPrompt.temperature}</span>
                </div>
              </div>

              {selectedPrompt.systemMessage && (
                <div className="system-message-section">
                  <h4>System Message</h4>
                  <SyntaxHighlighter
                    language="markdown"
                    style={vscDarkPlus}
                    customStyle={{ fontSize: '0.85rem', borderRadius: '4px' }}
                  >
                    {selectedPrompt.systemMessage}
                  </SyntaxHighlighter>
                </div>
              )}

              <div className="user-prompt-section">
                <h4>User Prompt</h4>
                <SyntaxHighlighter
                  language="markdown"
                  style={vscDarkPlus}
                  customStyle={{ fontSize: '0.85rem', borderRadius: '4px' }}
                >
                  {selectedPrompt.prompt}
                </SyntaxHighlighter>
              </div>
            </div>
          ) : (
            <div className="no-selection">Select a prompt from the list</div>
          )}
        </main>
      </div>
    </div>
  );
};

export default PromptInspector;
```

Create `apps/ui/src/screens/control/widgets/PromptInspector.css`:
```css
.prompt-inspector-widget {
  background-color: #2d2d2d;
  padding: 1.5rem;
  border-radius: 8px;
  height: 800px;
  display: flex;
  flex-direction: column;
}

.inspector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.inspector-header h3 {
  margin: 0;
  color: #e0e0e0;
  font-size: 1.1rem;
}

.agent-filter {
  padding: 0.5rem 1rem;
  background-color: #3a3a3a;
  color: #e0e0e0;
  border: 1px solid #555;
  border-radius: 4px;
  font-size: 0.85rem;
}

.inspector-layout {
  flex: 1;
  display: flex;
  gap: 1rem;
  overflow: hidden;
}

.prompt-list {
  width: 250px;
  background-color: #1e1e1e;
  border-radius: 4px;
  padding: 1rem;
  overflow-y: auto;
}

.no-prompts {
  text-align: center;
  padding: 2rem;
  color: #777;
}

.prompt-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.prompt-item {
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  background-color: #2d2d2d;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  border-left: 3px solid transparent;
}

.prompt-item:hover {
  background-color: #3a3a3a;
}

.prompt-item.selected {
  background-color: #667eea;
  color: white;
  border-left-color: #fff;
}

.prompt-agent {
  font-weight: 600;
  margin-bottom: 0.25rem;
  text-transform: capitalize;
}

.prompt-model {
  font-size: 0.8rem;
  opacity: 0.8;
  margin-bottom: 0.25rem;
}

.prompt-task,
.prompt-time {
  font-size: 0.75rem;
  opacity: 0.7;
}

.prompt-viewer {
  flex: 1;
  background-color: #1e1e1e;
  border-radius: 4px;
  padding: 1.5rem;
  overflow-y: auto;
}

.no-selection {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #777;
  font-size: 1.1rem;
}

.prompt-details {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.prompt-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  padding: 1rem;
  background-color: #2d2d2d;
  border-radius: 4px;
}

.meta-item {
  display: flex;
  gap: 0.5rem;
}

.meta-label {
  font-weight: 600;
  color: #aaa;
}

.meta-value {
  color: #e0e0e0;
}

.system-message-section,
.user-prompt-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.system-message-section h4,
.user-prompt-section h4 {
  margin: 0;
  color: #667eea;
  font-size: 1rem;
}
```

---

### 3. Frontend: Cost Analytics Widget

**Intent:** Granular cost breakdown with burn rate analysis and budget alerts.

**Implementation:**

Create `apps/ui/src/screens/control/widgets/CostAnalytics.tsx`:
```tsx
import React, { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { controlClient, SessionEvent } from '../../../api/controlClient';
import './CostAnalytics.css';

interface ModelCost {
  model: string;
  totalTokens: number;
  promptTokens: number;
  completionTokens: number;
  cost: number;
}

interface BurnRatePoint {
  timestamp: string;
  cumulativeCost: number;
}

interface CostAnalyticsProps {
  sessionId: string;
  budgetUSD?: number;
}

const MODEL_PRICING: Record<string, { prompt: number; completion: number }> = {
  'gpt-4o': { prompt: 2.5, completion: 10.0 },
  'gpt-4o-mini': { prompt: 0.15, completion: 0.6 },
  'claude-sonnet-4': { prompt: 3.0, completion: 15.0 },
  'claude-opus-4': { prompt: 15.0, completion: 75.0 },
};

const COLORS = ['#667eea', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

const CostAnalytics: React.FC<CostAnalyticsProps> = ({ sessionId, budgetUSD = 1.0 }) => {
  const [costsByModel, setCostsByModel] = useState<ModelCost[]>([]);
  const [burnRate, setBurnRate] = useState<BurnRatePoint[]>([]);
  const [totalCost, setTotalCost] = useState(0);

  useEffect(() => {
    const eventSource = controlClient.streamSessionEvents(sessionId, handleEvent);
    return () => eventSource.close();
  }, [sessionId]);

  const handleEvent = (event: SessionEvent) => {
    if (event.event_type === 'LLM_RESPONSE_RECEIVED' && event.model) {
      const { total_tokens, prompt_tokens, completion_tokens } = event.metadata || {};
      const model = event.model;

      if (!total_tokens) return;

      // Calculate cost
      const pricing = MODEL_PRICING[model] || { prompt: 1.0, completion: 2.0 };
      const cost = ((prompt_tokens || 0) / 1_000_000) * pricing.prompt +
                    ((completion_tokens || 0) / 1_000_000) * pricing.completion;

      // Update costs by model
      setCostsByModel((prev) => {
        const existing = prev.find((c) => c.model === model);
        if (existing) {
          return prev.map((c) =>
            c.model === model
              ? {
                  ...c,
                  totalTokens: c.totalTokens + total_tokens,
                  promptTokens: c.promptTokens + (prompt_tokens || 0),
                  completionTokens: c.completionTokens + (completion_tokens || 0),
                  cost: c.cost + cost,
                }
              : c
          );
        } else {
          return [
            ...prev,
            {
              model,
              totalTokens: total_tokens,
              promptTokens: prompt_tokens || 0,
              completionTokens: completion_tokens || 0,
              cost,
            },
          ];
        }
      });

      // Update burn rate
      setBurnRate((prev) => {
        const newCumulativeCost = prev.length > 0 ? prev[prev.length - 1].cumulativeCost + cost : cost;
        return [
          ...prev,
          {
            timestamp: new Date(event.timestamp).toLocaleTimeString(),
            cumulativeCost: newCumulativeCost,
          },
        ];
      });

      setTotalCost((prev) => prev + cost);
    }
  };

  const budgetRemaining = budgetUSD - totalCost;
  const budgetUsedPercent = (totalCost / budgetUSD) * 100;

  const pieData = costsByModel.map((c) => ({
    name: c.model,
    value: c.cost,
  }));

  return (
    <div className="cost-analytics-widget">
      <h3>Cost Analytics</h3>

      {/* Budget Alert */}
      <div className={`budget-alert ${budgetUsedPercent > 80 ? 'warning' : ''} ${budgetUsedPercent >= 100 ? 'critical' : ''}`}>
        <div className="budget-header">
          <span className="budget-label">Budget</span>
          <span className="budget-value">
            ${totalCost.toFixed(4)} / ${budgetUSD.toFixed(2)}
          </span>
        </div>
        <div className="budget-bar">
          <div
            className="budget-fill"
            style={{ width: `${Math.min(budgetUsedPercent, 100)}%` }}
          ></div>
        </div>
        <div className="budget-footer">
          {budgetRemaining > 0 ? (
            <span className="budget-remaining">
              ${budgetRemaining.toFixed(4)} remaining ({(100 - budgetUsedPercent).toFixed(1)}%)
            </span>
          ) : (
            <span className="budget-exceeded">
              ⚠️ Budget exceeded by ${Math.abs(budgetRemaining).toFixed(4)}
            </span>
          )}
        </div>
      </div>

      {/* Cost Breakdown */}
      <div className="analytics-charts">
        {/* Pie Chart: Cost by Model */}
        <div className="chart-section">
          <h4>Cost Distribution by Model</h4>
          {costsByModel.length === 0 ? (
            <div className="no-data">No cost data yet</div>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={(entry) => `${entry.name}: $${entry.value.toFixed(4)}`}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => `$${value.toFixed(4)}`} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Bar Chart: Token Breakdown */}
        <div className="chart-section">
          <h4>Token Breakdown by Model</h4>
          {costsByModel.length === 0 ? (
            <div className="no-data">No token data yet</div>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={costsByModel}>
                <XAxis dataKey="model" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="promptTokens" fill="#667eea" name="Prompt" />
                <Bar dataKey="completionTokens" fill="#10b981" name="Completion" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Cost Table */}
      <div className="cost-table-section">
        <h4>Detailed Cost Breakdown</h4>
        <table className="cost-table">
          <thead>
            <tr>
              <th>Model</th>
              <th>Prompt Tokens</th>
              <th>Completion Tokens</th>
              <th>Total Tokens</th>
              <th>Cost (USD)</th>
            </tr>
          </thead>
          <tbody>
            {costsByModel.map((c) => (
              <tr key={c.model}>
                <td className="model-name">{c.model}</td>
                <td className="numeric">{c.promptTokens.toLocaleString()}</td>
                <td className="numeric">{c.completionTokens.toLocaleString()}</td>
                <td className="numeric">{c.totalTokens.toLocaleString()}</td>
                <td className="numeric cost">${c.cost.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td><strong>Total</strong></td>
              <td className="numeric">
                <strong>{costsByModel.reduce((sum, c) => sum + c.promptTokens, 0).toLocaleString()}</strong>
              </td>
              <td className="numeric">
                <strong>{costsByModel.reduce((sum, c) => sum + c.completionTokens, 0).toLocaleString()}</strong>
              </td>
              <td className="numeric">
                <strong>{costsByModel.reduce((sum, c) => sum + c.totalTokens, 0).toLocaleString()}</strong>
              </td>
              <td className="numeric cost">
                <strong>${totalCost.toFixed(4)}</strong>
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
};

export default CostAnalytics;
```

Create `apps/ui/src/screens/control/widgets/CostAnalytics.css`:
```css
.cost-analytics-widget {
  background-color: #2d2d2d;
  padding: 1.5rem;
  border-radius: 8px;
  height: 900px;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  overflow-y: auto;
}

.cost-analytics-widget h3 {
  margin: 0;
  color: #e0e0e0;
  font-size: 1.1rem;
}

.budget-alert {
  background-color: #3a3a3a;
  padding: 1rem;
  border-radius: 6px;
  border-left: 4px solid #10b981;
  transition: border-color 0.3s;
}

.budget-alert.warning {
  border-left-color: #f59e0b;
}

.budget-alert.critical {
  border-left-color: #ef4444;
  background-color: rgba(239, 68, 68, 0.1);
}

.budget-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.budget-label {
  font-weight: 600;
  color: #aaa;
}

.budget-value {
  font-weight: 700;
  color: #e0e0e0;
  font-size: 1.1rem;
}

.budget-bar {
  height: 12px;
  background-color: #1e1e1e;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.budget-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #667eea);
  transition: width 0.3s, background 0.3s;
}

.budget-alert.warning .budget-fill {
  background: linear-gradient(90deg, #f59e0b, #fb923c);
}

.budget-alert.critical .budget-fill {
  background: linear-gradient(90deg, #ef4444, #f87171);
}

.budget-footer {
  text-align: center;
  font-size: 0.85rem;
}

.budget-remaining {
  color: #10b981;
}

.budget-exceeded {
  color: #ef4444;
  font-weight: 600;
}

.analytics-charts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.chart-section {
  background-color: #1e1e1e;
  padding: 1rem;
  border-radius: 6px;
}

.chart-section h4 {
  margin: 0 0 1rem 0;
  color: #667eea;
  font-size: 0.95rem;
}

.no-data {
  text-align: center;
  padding: 2rem;
  color: #777;
}

.cost-table-section {
  background-color: #1e1e1e;
  padding: 1rem;
  border-radius: 6px;
}

.cost-table-section h4 {
  margin: 0 0 1rem 0;
  color: #667eea;
  font-size: 0.95rem;
}

.cost-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.cost-table th,
.cost-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #3a3a3a;
}

.cost-table th {
  color: #aaa;
  font-weight: 600;
  background-color: #2d2d2d;
}

.cost-table td {
  color: #e0e0e0;
}

.model-name {
  font-weight: 600;
}

.numeric {
  text-align: right;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
}

.cost {
  color: #10b981;
  font-weight: 600;
}

.cost-table tfoot td {
  background-color: #2d2d2d;
  border-top: 2px solid #667eea;
}
```

---

### 4. Integrate Widgets into ControlPanel

**Intent:** Replace final placeholders with PromptInspector and CostAnalytics.

**Implementation:**

Update `apps/ui/src/screens/control/ControlPanel.tsx`:
```tsx
import PromptInspector from './widgets/PromptInspector';
import CostAnalytics from './widgets/CostAnalytics';

// Inside the widgets-grid:
<div className="widgets-grid">
  {/* WP-0023 widgets */}
  <AgentDashboard sessionId={selectedSession} />
  <TokenVisualization sessionId={selectedSession} />

  {/* WP-0024 widgets */}
  <AgentGraph sessionId={selectedSession} />
  <ExecutionTimeline sessionId={selectedSession} />

  {/* WP-0025 widgets */}
  <GateLog sessionId={selectedSession} />
  <ModelRouter sessionId={selectedSession} />

  {/* WP-0026 widgets */}
  <SessionComparison sessionIds={[selectedSession]} />
  <EventStream sessionId={selectedSession} />

  {/* WP-0027 widgets (NEW) */}
  <PromptInspector sessionId={selectedSession} />
  <CostAnalytics sessionId={selectedSession} budgetUSD={1.0} />
</div>
```

Update `apps/ui/src/api/controlClient.ts` to add prompt retrieval method:
```typescript
export interface Prompt {
  timestamp: string;
  task_id: string;
  agent_role: string;
  model: string;
  prompt: string;
  system_message: string;
  max_tokens: number;
  temperature: number;
}

export const controlClient = {
  // ... existing methods ...

  async getSessionPrompts(sessionId: string): Promise<{ prompts: Prompt[]; total: number }> {
    const response = await fetch(`${API_BASE}/control/sessions/${sessionId}/prompts`);
    if (!response.ok) throw new Error('Failed to get session prompts');
    return response.json();
  },
};
```

---

## Verification Commands
```bash
# Install syntax highlighting library
cd apps/ui && npm install react-syntax-highlighter @types/react-syntax-highlighter

# Backend tests
cd apps/api && pytest tests/test_control_api.py::test_get_session_prompts -v

# Frontend build
cd apps/ui && npm run build

# Frontend dev server
cd apps/ui && npm run dev
# Visit: http://localhost:5173/control

# Test prompt inspector:
# 1. Start a session with LLM invocations
# 2. Navigate to /control and select the session
# 3. Verify PromptInspector shows prompts with syntax highlighting
# 4. Verify filtering by agent role works
# 5. Verify system message and user prompt are displayed separately

# Test cost analytics:
# 1. Verify budget bar shows current spend vs budget
# 2. Verify pie chart shows cost distribution by model
# 3. Verify bar chart shows token breakdown (prompt vs completion)
# 4. Verify cost table shows detailed breakdown
# 5. Test budget alerts (warning at 80%, critical at 100%)
```

## Progress Notes
- 2026-01-07: Emitted LLM request events with prompt metadata, added PromptInspector + CostAnalytics widgets, and wired prompts endpoint + control panel integration.
  - Verification: `cd apps/api && pytest tests/test_cost_tracking.py -v`, `cd apps/ui && npm run build`
  - Visual check: Control panel with demo session shows prompt inspector and cost analytics widgets.

## Done Means
- [x] Backend endpoint `/control/sessions/{id}/prompts` returns all prompts
- [x] LLM_REQUEST_SENT events include full prompt in metadata
- [x] PromptInspector component renders prompt list and viewer
- [x] PromptInspector displays syntax-highlighted prompts
- [x] PromptInspector filters by agent role
- [x] PromptInspector shows system message and user prompt separately
- [x] CostAnalytics component calculates cost from token events
- [x] CostAnalytics displays budget bar with warning/critical states
- [x] CostAnalytics shows pie chart (cost by model)
- [x] CostAnalytics shows bar chart (token breakdown)
- [x] CostAnalytics shows detailed cost table
- [x] Both widgets integrate into ControlPanel layout
- [x] All control UI features (WP-0022 through WP-0027) complete

## Architecture Notes

**Prompt Storage:**
- Prompts stored in EventLog as LLM_REQUEST_SENT events
- Full prompt text included in metadata (template expansion complete)
- Separate system_message field for multi-part prompts
- Prompt retrieval endpoint filters events by type

**Syntax Highlighting:**
- Uses react-syntax-highlighter (Prism engine)
- vscDarkPlus theme matches dark control panel aesthetic
- Markdown language for prompt syntax highlighting
- Auto-scrolling code blocks for long prompts

**Cost Calculation:**
- Real-time updates from LLM_RESPONSE_RECEIVED events
- Model-specific pricing (per 1M tokens)
- Separate tracking for prompt vs completion tokens
- Cumulative cost calculation for burn rate

**Budget Alerts:**
- Green: 0-80% budget used
- Orange: 80-100% budget used (warning)
- Red: 100%+ budget used (critical)
- Visual progress bar with color transitions

**Chart Types:**
- Pie chart: cost distribution by model (helps identify expensive models)
- Bar chart: token breakdown (helps understand prompt vs completion ratio)
- Table: detailed per-model breakdown (for precise analysis)

**Why These Widgets Matter:**
- **PromptInspector** - Debug LLM behavior by inspecting actual prompts
- **CostAnalytics** - Prevent budget overruns and optimize model selection
- Together they complete the control UI with deep debugging and cost control

**Control UI Completion:**
This WP completes the full control UI roadmap (VF-170 through VF-180):
- ✅ WP-0022: Control panel architecture
- ✅ WP-0023: Agent dashboard + token visualization
- ✅ WP-0024: Agent graph + execution timeline
- ✅ WP-0025: Gate log + model router
- ✅ WP-0026: Session comparison + event stream
- ✅ WP-0027: Prompt inspector + cost analytics

All 10 control UI widgets are now fully specified and ready for implementation.
