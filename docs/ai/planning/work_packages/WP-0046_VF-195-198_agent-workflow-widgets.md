# WP-0046 — Agent workflow UI widgets

## Overview

- **VF Tasks:** VF-195, VF-196, VF-197, VF-198
- **Goal:** Create 4 control panel widgets for agent initialization, role assignment, task input, and flow editing to enable visual workflow configuration.
- **Dependencies:** WP-0044 (API endpoints to call)

## Context

The control panel currently has 10 monitoring widgets (AgentDashboard, AgentGraph, ExecutionTimeline, etc.). We now need to add 4 configuration widgets to enable simulation mode:

1. **AgentInitializer** — Select agent count and initialize
2. **AgentAssignment** — Assign roles and models to each agent
3. **AgentTaskInput** — Set the main orchestration task
4. **AgentFlowEditor** — Configure agent-to-agent communication graph

## Implementation Steps

### Step 1: Create AgentInitializer widget (VF-195)

**File:** `apps/ui/src/screens/control/widgets/AgentInitializer.tsx`

```tsx
import React, { useState } from 'react';
import { controlClient } from '../../../api/controlClient';

interface AgentInitializerProps {
  sessionId: string;
  onInitialized: (agents: AgentInfo[]) => void;
}

export const AgentInitializer: React.FC<AgentInitializerProps> = ({
  sessionId,
  onInitialized
}) => {
  const [count, setCount] = useState(3);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleInitialize = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await controlClient.initializeAgents(sessionId, count);
      onInitialized(response.agents);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to initialize agents');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="agent-initializer widget">
      <h3>Initialize Agents</h3>
      <div className="init-controls">
        <label>
          Number of Agents:
          <input
            type="range"
            min={1}
            max={10}
            value={count}
            onChange={(e) => setCount(parseInt(e.target.value))}
          />
          <span className="count-display">{count}</span>
        </label>
        <button
          onClick={handleInitialize}
          disabled={loading}
          className="init-button"
        >
          {loading ? 'Initializing...' : `Initialize ${count} Agents`}
        </button>
      </div>
      {error && <div className="error-message">{error}</div>}
    </div>
  );
};
```

### Step 2: Create AgentAssignment widget (VF-196)

**File:** `apps/ui/src/screens/control/widgets/AgentAssignment.tsx`

```tsx
import React, { useState } from 'react';
import { controlClient } from '../../../api/controlClient';

interface Agent {
  agent_id: string;
  role?: string;
  model_id?: string;
  display_name?: string;
}

interface AgentAssignmentProps {
  sessionId: string;
  agents: Agent[];
  onAssigned: () => void;
}

const ROLES = ['orchestrator', 'foreman', 'worker', 'reviewer', 'fixer'];
const MODELS = ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo', 'claude-3-opus', 'claude-3-sonnet'];

export const AgentAssignment: React.FC<AgentAssignmentProps> = ({
  sessionId,
  agents,
  onAssigned
}) => {
  const [assignments, setAssignments] = useState<Record<string, { role: string; model: string }>>({});
  const [saving, setSaving] = useState<string | null>(null);

  const handleAssign = async (agentId: string) => {
    const assignment = assignments[agentId];
    if (!assignment?.role) return;

    setSaving(agentId);
    try {
      await controlClient.assignAgentRole(sessionId, agentId, assignment.role, assignment.model);
      onAssigned();
    } catch (err) {
      console.error('Failed to assign role:', err);
    } finally {
      setSaving(null);
    }
  };

  return (
    <div className="agent-assignment widget">
      <h3>Assign Roles & Models</h3>
      <div className="agent-cards">
        {agents.map((agent) => (
          <div key={agent.agent_id} className="agent-card">
            <div className="agent-header">
              <span className="agent-name">{agent.display_name || agent.agent_id}</span>
              {agent.role && <span className="current-role">{agent.role}</span>}
            </div>
            <div className="assignment-controls">
              <select
                value={assignments[agent.agent_id]?.role || agent.role || ''}
                onChange={(e) => setAssignments({
                  ...assignments,
                  [agent.agent_id]: {
                    ...assignments[agent.agent_id],
                    role: e.target.value
                  }
                })}
              >
                <option value="">Select Role</option>
                {ROLES.map(role => (
                  <option key={role} value={role}>{role}</option>
                ))}
              </select>
              <select
                value={assignments[agent.agent_id]?.model || agent.model_id || ''}
                onChange={(e) => setAssignments({
                  ...assignments,
                  [agent.agent_id]: {
                    ...assignments[agent.agent_id],
                    model: e.target.value
                  }
                })}
              >
                <option value="">Select Model</option>
                {MODELS.map(model => (
                  <option key={model} value={model}>{model}</option>
                ))}
              </select>
              <button
                onClick={() => handleAssign(agent.agent_id)}
                disabled={saving === agent.agent_id || !assignments[agent.agent_id]?.role}
              >
                {saving === agent.agent_id ? 'Saving...' : 'Assign'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

### Step 3: Create AgentTaskInput widget (VF-197)

**File:** `apps/ui/src/screens/control/widgets/AgentTaskInput.tsx`

```tsx
import React, { useState } from 'react';
import { controlClient } from '../../../api/controlClient';

interface AgentTaskInputProps {
  sessionId: string;
  currentTask?: string;
  onTaskSet: () => void;
}

export const AgentTaskInput: React.FC<AgentTaskInputProps> = ({
  sessionId,
  currentTask,
  onTaskSet
}) => {
  const [description, setDescription] = useState(currentTask || '');
  const [criteria, setCriteria] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) return;

    setSaving(true);
    setError(null);
    try {
      const acceptanceCriteria = criteria.split('\n').filter(c => c.trim());
      await controlClient.setMainTask(sessionId, description, acceptanceCriteria);
      onTaskSet();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to set task');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="agent-task-input widget">
      <h3>Main Task</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Task Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe what the agents should accomplish..."
            rows={3}
          />
        </div>
        <div className="form-group">
          <label>Acceptance Criteria (one per line)</label>
          <textarea
            value={criteria}
            onChange={(e) => setCriteria(e.target.value)}
            placeholder="- App starts without errors&#10;- All tests pass&#10;- Code is properly formatted"
            rows={4}
          />
        </div>
        <button type="submit" disabled={saving || !description.trim()}>
          {saving ? 'Setting Task...' : 'Set Main Task'}
        </button>
        {error && <div className="error-message">{error}</div>}
        {currentTask && (
          <div className="current-task">
            <strong>Current:</strong> {currentTask}
          </div>
        )}
      </form>
    </div>
  );
};
```

### Step 4: Create AgentFlowEditor widget (VF-198)

**File:** `apps/ui/src/screens/control/widgets/AgentFlowEditor.tsx`

```tsx
import React, { useState, useCallback } from 'react';
import { controlClient } from '../../../api/controlClient';

interface Agent {
  agent_id: string;
  display_name?: string;
  role?: string;
}

interface Edge {
  from_agent: string;
  to_agent: string;
  label?: string;
}

interface AgentFlowEditorProps {
  sessionId: string;
  agents: Agent[];
  existingEdges?: Edge[];
  onFlowConfigured: () => void;
}

export const AgentFlowEditor: React.FC<AgentFlowEditorProps> = ({
  sessionId,
  agents,
  existingEdges = [],
  onFlowConfigured
}) => {
  const [edges, setEdges] = useState<Edge[]>(existingEdges);
  const [newEdge, setNewEdge] = useState<{ from: string; to: string }>({ from: '', to: '' });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  const addEdge = () => {
    if (!newEdge.from || !newEdge.to) return;
    if (newEdge.from === newEdge.to) {
      setError('Cannot connect agent to itself');
      return;
    }

    // Check for duplicate
    const exists = edges.some(e => e.from_agent === newEdge.from && e.to_agent === newEdge.to);
    if (exists) {
      setError('This connection already exists');
      return;
    }

    setEdges([...edges, { from_agent: newEdge.from, to_agent: newEdge.to }]);
    setNewEdge({ from: '', to: '' });
    setError(null);
  };

  const removeEdge = (index: number) => {
    setEdges(edges.filter((_, i) => i !== index));
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setValidationError(null);
    try {
      const response = await controlClient.configureAgentFlow(sessionId, edges);
      if (!response.is_valid) {
        setValidationError(response.validation_error || 'Invalid flow configuration');
        return;
      }
      onFlowConfigured();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save flow');
    } finally {
      setSaving(false);
    }
  };

  const getAgentName = (id: string) => {
    const agent = agents.find(a => a.agent_id === id);
    return agent?.display_name || agent?.role || id;
  };

  return (
    <div className="agent-flow-editor widget">
      <h3>Agent Communication Flow</h3>

      {/* Visual graph representation */}
      <div className="flow-graph">
        <svg width="100%" height="200" viewBox="0 0 400 200">
          {/* Render agents as nodes */}
          {agents.map((agent, i) => {
            const x = 50 + (i * 100) % 300;
            const y = 50 + Math.floor(i / 3) * 80;
            return (
              <g key={agent.agent_id}>
                <circle cx={x} cy={y} r="25" fill="#4a5568" stroke="#718096" strokeWidth="2" />
                <text x={x} y={y + 5} textAnchor="middle" fill="white" fontSize="10">
                  {agent.display_name || `A${i + 1}`}
                </text>
              </g>
            );
          })}
          {/* Render edges as arrows */}
          {edges.map((edge, i) => {
            const fromIdx = agents.findIndex(a => a.agent_id === edge.from_agent);
            const toIdx = agents.findIndex(a => a.agent_id === edge.to_agent);
            if (fromIdx === -1 || toIdx === -1) return null;

            const x1 = 50 + (fromIdx * 100) % 300;
            const y1 = 50 + Math.floor(fromIdx / 3) * 80;
            const x2 = 50 + (toIdx * 100) % 300;
            const y2 = 50 + Math.floor(toIdx / 3) * 80;

            return (
              <line key={i} x1={x1} y1={y1} x2={x2} y2={y2}
                stroke="#48bb78" strokeWidth="2" markerEnd="url(#arrow)" />
            );
          })}
          <defs>
            <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
              <path d="M0,0 L0,6 L9,3 z" fill="#48bb78" />
            </marker>
          </defs>
        </svg>
      </div>

      {/* Add new edge */}
      <div className="add-edge-controls">
        <select value={newEdge.from} onChange={(e) => setNewEdge({ ...newEdge, from: e.target.value })}>
          <option value="">From Agent</option>
          {agents.map(a => (
            <option key={a.agent_id} value={a.agent_id}>{getAgentName(a.agent_id)}</option>
          ))}
        </select>
        <span className="arrow">→</span>
        <select value={newEdge.to} onChange={(e) => setNewEdge({ ...newEdge, to: e.target.value })}>
          <option value="">To Agent</option>
          {agents.map(a => (
            <option key={a.agent_id} value={a.agent_id}>{getAgentName(a.agent_id)}</option>
          ))}
        </select>
        <button onClick={addEdge} disabled={!newEdge.from || !newEdge.to}>Add</button>
      </div>

      {/* Edge list */}
      <div className="edge-list">
        {edges.map((edge, i) => (
          <div key={i} className="edge-item">
            <span>{getAgentName(edge.from_agent)} → {getAgentName(edge.to_agent)}</span>
            <button onClick={() => removeEdge(i)} className="remove-btn">×</button>
          </div>
        ))}
        {edges.length === 0 && (
          <div className="empty-state">No connections defined. Add edges to define communication flow.</div>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}
      {validationError && <div className="validation-error">{validationError}</div>}

      <button onClick={handleSave} disabled={saving} className="save-button">
        {saving ? 'Saving...' : 'Save Flow Configuration'}
      </button>
    </div>
  );
};
```

### Step 5: Integrate widgets into ControlPanel

**File:** `apps/ui/src/screens/ControlPanel.tsx` (update)

```tsx
import { AgentInitializer } from './control/widgets/AgentInitializer';
import { AgentAssignment } from './control/widgets/AgentAssignment';
import { AgentTaskInput } from './control/widgets/AgentTaskInput';
import { AgentFlowEditor } from './control/widgets/AgentFlowEditor';

// In the render section, add a "Workflow Configuration" tab or section:
<div className="workflow-configuration">
  <h2>Workflow Configuration</h2>

  {!workflowConfig?.agents?.length ? (
    <AgentInitializer
      sessionId={selectedSessionId}
      onInitialized={handleAgentsInitialized}
    />
  ) : (
    <>
      <AgentAssignment
        sessionId={selectedSessionId}
        agents={workflowConfig.agents}
        onAssigned={refreshWorkflowConfig}
      />
      <AgentTaskInput
        sessionId={selectedSessionId}
        currentTask={workflowConfig.main_task}
        onTaskSet={refreshWorkflowConfig}
      />
      <AgentFlowEditor
        sessionId={selectedSessionId}
        agents={workflowConfig.agents}
        existingEdges={workflowConfig.flow_edges}
        onFlowConfigured={refreshWorkflowConfig}
      />
    </>
  )}
</div>
```

## Verification

```bash
cd apps/ui && npm run build
# Visual verification: All 4 widgets render in control panel
```

## Files to Touch

- `apps/ui/src/screens/control/widgets/AgentInitializer.tsx` (new)
- `apps/ui/src/screens/control/widgets/AgentAssignment.tsx` (new)
- `apps/ui/src/screens/control/widgets/AgentTaskInput.tsx` (new)
- `apps/ui/src/screens/control/widgets/AgentFlowEditor.tsx` (new)
- `apps/ui/src/screens/ControlPanel.tsx` (integrate widgets)

## Done When

- [ ] AgentInitializer widget with count slider and init button
- [ ] AgentAssignment widget with role/model dropdowns per agent
- [ ] AgentTaskInput widget with description and criteria fields
- [ ] AgentFlowEditor widget with visual graph and edge controls
- [ ] All widgets integrated into ControlPanel
- [ ] Build passes with no TypeScript errors
