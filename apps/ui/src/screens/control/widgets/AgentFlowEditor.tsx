import React, { useState } from 'react';
import * as controlClient from '../../../api/controlClient';
import type { AgentConfig, AgentFlowEdge } from '../../../api/controlClient';

interface AgentFlowEditorProps {
  sessionId: string;
  agents: AgentConfig[];
  existingEdges?: AgentFlowEdge[];
  onFlowConfigured: () => void;
}

export const AgentFlowEditor: React.FC<AgentFlowEditorProps> = ({
  sessionId,
  agents,
  existingEdges = [],
  onFlowConfigured
}) => {
  const [edges, setEdges] = useState<AgentFlowEdge[]>(existingEdges);
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
      if (response.is_valid === false) {
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
        <svg width="100%" height="200" viewBox="0 0 600 200">
          {/* Render agents as nodes */}
          {agents.map((agent, i) => {
            const x = 80 + (i * 120) % 480;
            const y = 60 + Math.floor(i / 4) * 80;
            return (
              <g key={agent.agent_id}>
                <circle cx={x} cy={y} r="30" fill="#4a5568" stroke="#718096" strokeWidth="2" />
                <text x={x} y={y + 5} textAnchor="middle" fill="white" fontSize="12">
                  {agent.role?.substring(0, 4) || `A${i + 1}`}
                </text>
              </g>
            );
          })}
          {/* Render edges as arrows */}
          {edges.map((edge, i) => {
            const fromIdx = agents.findIndex(a => a.agent_id === edge.from_agent);
            const toIdx = agents.findIndex(a => a.agent_id === edge.to_agent);
            if (fromIdx === -1 || toIdx === -1) return null;

            const x1 = 80 + (fromIdx * 120) % 480;
            const y1 = 60 + Math.floor(fromIdx / 4) * 80;
            const x2 = 80 + (toIdx * 120) % 480;
            const y2 = 60 + Math.floor(toIdx / 4) * 80;

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
