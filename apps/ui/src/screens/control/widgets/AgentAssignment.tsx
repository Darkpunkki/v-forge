import React, { useState } from 'react';
import * as controlClient from '../../../api/controlClient';
import type { AgentConfig } from '../../../api/controlClient';

interface AgentAssignmentProps {
  sessionId: string;
  agents: AgentConfig[];
  onAssigned: () => void;
}

const ROLES = ['orchestrator', 'foreman', 'worker', 'reviewer', 'fixer'];
const MODELS = ['gpt-4', 'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo', 'claude-3-opus', 'claude-3-sonnet'];

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
