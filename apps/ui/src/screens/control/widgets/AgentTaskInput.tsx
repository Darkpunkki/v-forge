import React, { useState } from 'react';
import * as controlClient from '../../../api/controlClient';

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
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) return;

    setSaving(true);
    setError(null);
    try {
      await controlClient.setMainTask(sessionId, description);
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
            rows={4}
          />
        </div>
        <button type="submit" disabled={saving || !description.trim()}>
          {saving ? 'Setting Task...' : 'Set Main Task'}
        </button>
        {error && <div className="error-message">{error}</div>}
        {currentTask && description !== currentTask && (
          <div className="current-task">
            <strong>Current:</strong> {currentTask}
          </div>
        )}
      </form>
    </div>
  );
};
