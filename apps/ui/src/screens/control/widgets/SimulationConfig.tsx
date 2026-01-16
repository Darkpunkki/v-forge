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
  currentUseRealLlm?: boolean
  currentDefaultModel?: string
  currentDefaultTemperature?: number | null
  currentMaxCostUsd?: number | null
  currentTickRateLimitMs?: number | null
  tickStatus?: string
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
  currentUseRealLlm = false,
  currentDefaultModel = 'gpt-4o-mini',
  currentDefaultTemperature = 0.7,
  currentMaxCostUsd = null,
  currentTickRateLimitMs = null,
  tickStatus = 'idle',
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
  const [useRealLlm, setUseRealLlm] = useState(currentUseRealLlm)
  const [model, setModel] = useState(currentDefaultModel)
  const [temperature, setTemperature] = useState<string>(
    currentDefaultTemperature?.toString() ?? '0.7'
  )
  const [maxCostUsd, setMaxCostUsd] = useState<string>(
    currentMaxCostUsd?.toString() ?? '1.00'
  )
  const [tickRateLimitMs, setTickRateLimitMs] = useState<string>(
    currentTickRateLimitMs?.toString() ?? '1000'
  )
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const isLocked = ['running', 'paused'].includes(tickStatus.toLowerCase())

  const parseNumber = (value: string): number | null => {
    if (!value.trim()) {
      return null
    }
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }

  const parseInteger = (value: string): number | null => {
    const parsed = parseNumber(value)
    return parsed === null ? null : Math.round(parsed)
  }

  const temperatureDisplay = (parseNumber(temperature) ?? 0.7).toFixed(2)

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
        use_real_llm: useRealLlm,
        default_model: model,
        default_temperature: parseNumber(temperature),
        max_cost_usd: parseNumber(maxCostUsd),
        tick_rate_limit_ms: parseInteger(tickRateLimitMs),
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
            disabled={isLocked}
            style={{
              flex: 1,
              padding: '10px 16px',
              border: mode === 'manual' ? '2px solid #1976d2' : '1px solid #ccc',
              borderRadius: '6px',
              background: mode === 'manual' ? '#e3f2fd' : '#fff',
              cursor: isLocked ? 'not-allowed' : 'pointer',
              fontWeight: mode === 'manual' ? 600 : 400,
              opacity: isLocked ? 0.6 : 1,
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
            disabled={isLocked}
            style={{
              flex: 1,
              padding: '10px 16px',
              border: mode === 'auto' ? '2px solid #1976d2' : '1px solid #ccc',
              borderRadius: '6px',
              background: mode === 'auto' ? '#e3f2fd' : '#fff',
              cursor: isLocked ? 'not-allowed' : 'pointer',
              fontWeight: mode === 'auto' ? 600 : 400,
              opacity: isLocked ? 0.6 : 1,
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
            disabled={isLocked}
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #ccc',
              borderRadius: '6px',
              fontSize: '14px',
              boxSizing: 'border-box',
              background: isLocked ? '#eee' : '#fff',
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
          disabled={isLocked}
          style={{
            width: '100%',
            padding: '8px 12px',
            border: '1px solid #ccc',
            borderRadius: '6px',
            fontSize: '14px',
            boxSizing: 'border-box',
            background: isLocked ? '#eee' : '#fff',
          }}
        />
        <p style={{ fontSize: '12px', opacity: 0.6, marginTop: '4px' }}>
          Maximum events to process per tick (optional)
        </p>
      </div>

      {/* LLM mode */}
      <div style={{ marginBottom: '16px' }}>
        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
          LLM Mode
        </label>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            type="button"
            onClick={() => setUseRealLlm(false)}
            disabled={isLocked}
            style={{
              flex: 1,
              padding: '10px 16px',
              border: !useRealLlm ? '2px solid #1976d2' : '1px solid #ccc',
              borderRadius: '6px',
              background: !useRealLlm ? '#e3f2fd' : '#fff',
              cursor: isLocked ? 'not-allowed' : 'pointer',
              fontWeight: !useRealLlm ? 600 : 400,
              opacity: isLocked ? 0.6 : 1,
            }}
          >
            Stubbed
            <div style={{ fontSize: '11px', opacity: 0.7, marginTop: '4px' }}>
              Deterministic, no cost
            </div>
          </button>
          <button
            type="button"
            onClick={() => setUseRealLlm(true)}
            disabled={isLocked}
            style={{
              flex: 1,
              padding: '10px 16px',
              border: useRealLlm ? '2px solid #1976d2' : '1px solid #ccc',
              borderRadius: '6px',
              background: useRealLlm ? '#e3f2fd' : '#fff',
              cursor: isLocked ? 'not-allowed' : 'pointer',
              fontWeight: useRealLlm ? 600 : 400,
              opacity: isLocked ? 0.6 : 1,
            }}
          >
            Real LLM
            <div style={{ fontSize: '11px', opacity: 0.7, marginTop: '4px' }}>
              Live provider calls
            </div>
          </button>
        </div>
        {useRealLlm ? (
          <div
            style={{
              marginTop: '8px',
              background: '#fff3cd',
              border: '1px solid #ffe082',
              padding: '8px 10px',
              borderRadius: '6px',
              fontSize: '12px',
            }}
          >
            Real LLM calls will incur API costs.
          </div>
        ) : (
          <p style={{ fontSize: '12px', opacity: 0.6, marginTop: '6px' }}>
            Using deterministic stub responses (no cost).
          </p>
        )}
      </div>

      {useRealLlm && (
        <div
          style={{
            marginBottom: '16px',
            padding: '12px',
            background: '#fff',
            border: '1px solid #e0e0e0',
            borderRadius: '6px',
          }}
        >
          <div style={{ marginBottom: '12px' }}>
            <label
              htmlFor="sim-model"
              style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}
            >
              Model
            </label>
            <select
              id="sim-model"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              disabled={isLocked}
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #ccc',
                borderRadius: '6px',
                fontSize: '14px',
                boxSizing: 'border-box',
                background: isLocked ? '#eee' : '#fff',
              }}
            >
              <option value="gpt-4o-mini">gpt-4o-mini</option>
              <option value="gpt-4o">gpt-4o</option>
              <option value="gpt-4-turbo">gpt-4-turbo</option>
            </select>
            <p style={{ fontSize: '12px', opacity: 0.6, marginTop: '4px' }}>
              Select the default model used for agent replies.
            </p>
          </div>

          <div style={{ marginBottom: '12px' }}>
            <label
              htmlFor="sim-temperature"
              style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}
            >
              Temperature
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <input
                id="sim-temperature"
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={temperature}
                onChange={(e) => setTemperature(e.target.value)}
                disabled={isLocked}
                style={{ flex: 1 }}
              />
              <span style={{ minWidth: '48px', textAlign: 'right' }}>
                {temperatureDisplay}
              </span>
            </div>
            <p style={{ fontSize: '12px', opacity: 0.6, marginTop: '4px' }}>
              Lower is more deterministic. Higher is more creative.
            </p>
          </div>

          <div style={{ marginBottom: '12px' }}>
            <label
              htmlFor="sim-max-cost"
              style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}
            >
              Max Cost Budget (USD)
            </label>
            <input
              id="sim-max-cost"
              type="number"
              min="0"
              step="0.01"
              value={maxCostUsd}
              onChange={(e) => setMaxCostUsd(e.target.value)}
              disabled={isLocked}
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #ccc',
                borderRadius: '6px',
                fontSize: '14px',
                boxSizing: 'border-box',
                background: isLocked ? '#eee' : '#fff',
              }}
            />
            <p style={{ fontSize: '12px', opacity: 0.6, marginTop: '4px' }}>
              Maximum allowed spend before ticks are blocked.
            </p>
          </div>

          <div>
            <label
              htmlFor="sim-rate-limit"
              style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}
            >
              Tick Rate Limit (ms)
            </label>
            <input
              id="sim-rate-limit"
              type="number"
              min="0"
              step="100"
              value={tickRateLimitMs}
              onChange={(e) => setTickRateLimitMs(e.target.value)}
              disabled={isLocked}
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #ccc',
                borderRadius: '6px',
                fontSize: '14px',
                boxSizing: 'border-box',
                background: isLocked ? '#eee' : '#fff',
              }}
            />
            <p style={{ fontSize: '12px', opacity: 0.6, marginTop: '4px' }}>
              Minimum delay between ticks when real LLM is enabled.
            </p>
          </div>
        </div>
      )}

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
          disabled={isLocked}
          style={{
            width: '100%',
            padding: '8px 12px',
            border: '1px solid #ccc',
            borderRadius: '6px',
            fontSize: '14px',
            boxSizing: 'border-box',
            resize: 'vertical',
            background: isLocked ? '#eee' : '#fff',
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
          disabled={agents.length === 0 || isLocked}
          style={{
            width: '100%',
            padding: '8px 12px',
            border: '1px solid #ccc',
            borderRadius: '6px',
            fontSize: '14px',
            boxSizing: 'border-box',
            background: agents.length === 0 || isLocked ? '#eee' : '#fff',
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
        disabled={submitting || isLocked}
        style={{
          width: '100%',
          padding: '12px',
          background: submitting || isLocked ? '#9e9e9e' : '#1976d2',
          color: '#fff',
          border: 'none',
          borderRadius: '6px',
          cursor: submitting || isLocked ? 'not-allowed' : 'pointer',
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
