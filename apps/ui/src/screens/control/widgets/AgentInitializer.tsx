import React, { useState } from 'react';
import * as controlClient from '../../../api/controlClient';

interface AgentInitializerProps {
  sessionId: string;
  onInitialized: (agentIds: string[]) => void;
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
      onInitialized(response.agent_ids);
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
