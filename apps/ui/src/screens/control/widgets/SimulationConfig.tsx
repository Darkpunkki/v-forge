import { useState } from 'react'
import {
  configureSimulation,
  type AgentConfig,
  type SimulationConfigRequest,
} from '../../../api/controlClient'

type SimulationConfigProps = {
  sessionId: string
  currentMode?: string
  currentDelayMs?: number | null
  currentTickBudget?: number | null
  agents?: AgentConfig[]
  initialPrompt?: string
  firstAgentId?: string
  onConfigured?: () => void
  onStartContextChange?: (context: {
    initialPrompt: string
    firstAgentId: string
  }) => void
}

export function SimulationConfig({
  sessionId,
  currentMode = 'manual',
  currentDelayMs = null,
  currentTickBudget = null,
  agents = [],
  initialPrompt = '',
  firstAgentId = '',
  onConfigured,
  onStartContextChange,
}: SimulationConfigProps) {
  const [mode, setMode] = useState<'manual' | 'auto'>(
    currentMode === 'auto' ? 'auto' : 'manual'
  )
  const [delayMs, setDelayMs] = useState<string>(
    currentDelayMs?.toString() ?? '1000'
  )
  const [tickBudget, setTickBudget] = useState<string>(
    currentTickBudget?.toString() ?? ''
  )
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const handleInitialPromptChange = (value: string) => {
    onStartContextChange?.({ initialPrompt: value, firstAgentId })
  }

  const handleFirstAgentChange = (value: string) => {
    onStartContextChange?.({ initialPrompt, firstAgentId: value })
  }

  const handleSubmit = async () => {
    setSubmitting(true)
    setError(null)
    setSuccessMessage(null)

    try {
      const config: SimulationConfigRequest = {
        simulation_mode: mode,
        auto_delay_ms: mode === 'auto' && delayMs ? parseInt(delayMs, 10) : null,
        tick_budget: tickBudget ? parseInt(tickBudget, 10) : null,
      }

      const result = await configureSimulation(sessionId, config)
      setSuccessMessage(result.message)
      onConfigured?.()
    } catch (err: any) {
      setError(err?.detail || err?.message || 'Failed to configure simulation')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      style={{
        background: '#f5f5f5',
        padding: '16px',
        borderRadius: '8px',
        marginBottom: '16px',
      }}
    >
      <h3 style={{ marginTop: 0, marginBottom: '12px' }}>Simulation Configuration</h3>
      <p style={{ fontSize: '14px', opacity: 0.7, marginBottom: '16px' }}>
        Configure simulation mode and timing parameters.
      </p>

      {/* Mode Toggle */}
      <div style={{ marginBottom: '16px' }}>
        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
          Simulation Mode
        </label>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            type="button"
            onClick={() => setMode('manual')}
            style={{
              flex: 1,
              padding: '10px 16px',
              border: mode === 'manual' ? '2px solid #1976d2' : '1px solid #ccc',
              borderRadius: '6px',
              background: mode === 'manual' ? '#e3f2fd' : '#fff',
              cursor: 'pointer',
              fontWeight: mode === 'manual' ? 600 : 400,
            }}
          >
            Manual
            <div style={{ fontSize: '11px', opacity: 0.7, marginTop: '4px' }}>
              Click to advance each tick
            </div>
          </button>
          <button
            type="button"
            onClick={() => setMode('auto')}
            style={{
              flex: 1,
              padding: '10px 16px',
              border: mode === 'auto' ? '2px solid #1976d2' : '1px solid #ccc',
              borderRadius: '6px',
              background: mode === 'auto' ? '#e3f2fd' : '#fff',
              cursor: 'pointer',
              fontWeight: mode === 'auto' ? 600 : 400,
            }}
          >
            Auto
            <div style={{ fontSize: '11px', opacity: 0.7, marginTop: '4px' }}>
              Auto-advance with delay
            </div>
          </button>
        </div>
      </div>

      {/* Auto-delay input (shown only in auto mode) */}
      {mode === 'auto' && (
        <div style={{ marginBottom: '16px' }}>
          <label
            htmlFor="sim-delay"
            style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}
          >
            Auto-Run Delay (ms)
          </label>
          <input
            id="sim-delay"
            type="number"
            min="0"
            step="100"
            value={delayMs}
            onChange={(e) => setDelayMs(e.target.value)}
            placeholder="1000"
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #ccc',
              borderRadius: '6px',
              fontSize: '14px',
              boxSizing: 'border-box',
            }}
          />
          <p style={{ fontSize: '12px', opacity: 0.6, marginTop: '4px' }}>
            Delay between automatic tick advances (0 = no delay)
          </p>
        </div>
      )}

      {/* Tick Budget input */}
      <div style={{ marginBottom: '16px' }}>
        <label
          htmlFor="sim-budget"
          style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}
        >
          Tick Budget (optional)
        </label>
        <input
          id="sim-budget"
          type="number"
          min="1"
          value={tickBudget}
          onChange={(e) => setTickBudget(e.target.value)}
          placeholder="Leave empty for unlimited"
          style={{
            width: '100%',
            padding: '8px 12px',
            border: '1px solid #ccc',
            borderRadius: '6px',
            fontSize: '14px',
            boxSizing: 'border-box',
          }}
        />
        <p style={{ fontSize: '12px', opacity: 0.6, marginTop: '4px' }}>
          Maximum events to process per tick (optional)
        </p>
      </div>

      {/* Start context inputs */}
      <div style={{ marginBottom: '16px' }}>
        <label
          htmlFor="sim-initial-prompt"
          style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}
        >
          Initial Prompt (required to start)
        </label>
        <textarea
          id="sim-initial-prompt"
          rows={3}
          value={initialPrompt}
          onChange={(e) => handleInitialPromptChange(e.target.value)}
          placeholder="Describe the opening instruction for the simulation"
          style={{
            width: '100%',
            padding: '8px 12px',
            border: '1px solid #ccc',
            borderRadius: '6px',
            fontSize: '14px',
            boxSizing: 'border-box',
            resize: 'vertical',
          }}
        />
        <p style={{ fontSize: '12px', opacity: 0.6, marginTop: '4px' }}>
          Sets the first instruction sent when the simulation starts.
        </p>
      </div>

      <div style={{ marginBottom: '16px' }}>
        <label
          htmlFor="sim-first-agent"
          style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}
        >
          First Agent (required to start)
        </label>
        <select
          id="sim-first-agent"
          value={firstAgentId}
          onChange={(e) => handleFirstAgentChange(e.target.value)}
          disabled={agents.length === 0}
          style={{
            width: '100%',
            padding: '8px 12px',
            border: '1px solid #ccc',
            borderRadius: '6px',
            fontSize: '14px',
            boxSizing: 'border-box',
            background: agents.length === 0 ? '#eee' : '#fff',
          }}
        >
          <option value="">Select an agent</option>
          {agents.map((agent) => (
            <option key={agent.agent_id} value={agent.agent_id}>
              {agent.display_name
                ? `${agent.display_name} (${agent.agent_id})`
                : agent.agent_id}
            </option>
          ))}
        </select>
        <p style={{ fontSize: '12px', opacity: 0.6, marginTop: '4px' }}>
          Choose which agent should receive the first prompt.
        </p>
      </div>

      {/* Error display */}
      {error && (
        <div
          style={{
            background: '#ffebee',
            color: '#c62828',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '16px',
            fontSize: '14px',
          }}
        >
          {error}
        </div>
      )}

      {/* Success display */}
      {successMessage && (
        <div
          style={{
            background: '#e8f5e9',
            color: '#2e7d32',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '16px',
            fontSize: '14px',
          }}
        >
          {successMessage}
        </div>
      )}

      {/* Submit button */}
      <button
        type="button"
        onClick={handleSubmit}
        disabled={submitting}
        style={{
          width: '100%',
          padding: '12px',
          background: submitting ? '#9e9e9e' : '#1976d2',
          color: '#fff',
          border: 'none',
          borderRadius: '6px',
          cursor: submitting ? 'not-allowed' : 'pointer',
          fontWeight: 600,
          fontSize: '14px',
        }}
      >
        {submitting ? 'Configuring...' : 'Configure Simulation'}
      </button>
    </div>
  )
}

export default SimulationConfig
