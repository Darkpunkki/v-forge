import { useCallback, useEffect, useRef, useState } from 'react'
import {
  startSimulation,
  advanceTick,
  advanceTicks,
  pauseSimulation,
  resetSimulation,
  getSimulationState,
  type SimulationStateResponse,
} from '../../../api/controlClient'

type TickControlsProps = {
  sessionId: string
  initialPrompt?: string
  firstAgentId?: string
  onStateChange?: () => void
}

type TickStatus = 'idle' | 'running' | 'paused' | 'waiting' | 'complete'

function getStatusColor(status: TickStatus): string {
  switch (status) {
    case 'running':
      return '#4caf50'
    case 'paused':
      return '#ff9800'
    case 'complete':
      return '#2196f3'
    case 'waiting':
      return '#9e9e9e'
    case 'idle':
    default:
      return '#757575'
  }
}

function getStatusLabel(status: string): TickStatus {
  const normalized = status.toLowerCase()
  if (normalized === 'running' || normalized === 'auto_running') return 'running'
  if (normalized === 'paused') return 'paused'
  if (normalized === 'complete' || normalized === 'completed') return 'complete'
  if (normalized === 'waiting' || normalized === 'pending') return 'waiting'
  return 'idle'
}

export function TickControls({
  sessionId,
  initialPrompt,
  firstAgentId,
  onStateChange,
}: TickControlsProps) {
  const [state, setState] = useState<SimulationStateResponse | null>(null)
  const [ticksInput, setTicksInput] = useState('5')
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const autoTickInFlight = useRef(false)
  const initialPromptValue = initialPrompt?.trim() ?? ''
  const firstAgentIdValue = firstAgentId?.trim() ?? ''
  const canStart = initialPromptValue.length > 0 && firstAgentIdValue.length > 0

  // Load simulation state
  useEffect(() => {
    let mounted = true

    async function loadState() {
      try {
        const result = await getSimulationState(sessionId)
        if (mounted) {
          setState(result)
          setLoading(false)
        }
      } catch (err: any) {
        if (mounted) {
          setError(err?.detail || 'Failed to load simulation state')
          setLoading(false)
        }
      }
    }

    loadState()
    return () => {
      mounted = false
    }
  }, [sessionId])

  const refreshState = useCallback(async () => {
    try {
      const result = await getSimulationState(sessionId)
      setState(result)
      onStateChange?.()
    } catch (err) {
      console.error('Failed to refresh state:', err)
    }
  }, [sessionId, onStateChange])

  const tickStatus = state ? getStatusLabel(state.tick_status) : 'idle'
  const isRunning = tickStatus === 'running'
  const isAutoMode = state?.simulation_mode === 'auto'
  const isConfigured = state?.simulation_mode !== undefined
  const canTick = isRunning && !isAutoMode
  const currentCost = state?.simulation_cost_usd ?? 0
  const maxCost = state?.max_cost_usd ?? 0
  const costRatio = maxCost > 0 ? currentCost / maxCost : 0
  const costColor = costRatio > 0.8 ? '#d32f2f' : '#424242'

  useEffect(() => {
    if (!isRunning) {
      return
    }

    let mounted = true
    const interval = setInterval(async () => {
      try {
        const result = await getSimulationState(sessionId)
        if (mounted) {
          setState(result)
        }
      } catch (err) {
        console.error('Failed to poll simulation state:', err)
      }
    }, 1500)

    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [sessionId, isRunning])

  useEffect(() => {
    if (!isAutoMode || !isRunning) {
      return
    }

    let cancelled = false
    const delayMs = Math.max(0, state?.auto_delay_ms ?? 1000)
    let timeoutId: number | null = null

    const runTick = async () => {
      if (cancelled || autoTickInFlight.current) {
        return
      }
      autoTickInFlight.current = true
      try {
        await advanceTick(sessionId)
        await refreshState()
      } catch (err: any) {
        if (!cancelled) {
          setError(err?.detail || err?.message || 'Failed to auto-advance tick')
        }
        if (err?.status === 429) {
          autoTickInFlight.current = false
          return
        }
      } finally {
        autoTickInFlight.current = false
        if (!cancelled) {
          timeoutId = window.setTimeout(runTick, delayMs)
        }
      }
    }

    timeoutId = window.setTimeout(runTick, delayMs)

    return () => {
      cancelled = true
      if (timeoutId !== null) {
        window.clearTimeout(timeoutId)
      }
    }
  }, [sessionId, isAutoMode, isRunning, state?.auto_delay_ms, refreshState])

  const handleAction = async (
    actionName: string,
    action: () => Promise<{ message: string }>
  ) => {
    setActionLoading(actionName)
    setError(null)
    setSuccessMessage(null)

    try {
      const result = await action()
      setSuccessMessage(result.message)
      await refreshState()
    } catch (err: any) {
      setError(err?.detail || err?.message || `Failed to ${actionName}`)
    } finally {
      setActionLoading(null)
    }
  }

  const handleStart = () => {
    if (!canStart) {
      setError('Set an initial prompt and first agent before starting.')
      return
    }
    return handleAction('start', () =>
      startSimulation(sessionId, {
        initial_prompt: initialPromptValue,
        first_agent_id: firstAgentIdValue,
      })
    )
  }

  const handleTick = () => {
    if (!canTick) {
      setError('Simulation must be running in manual mode to advance ticks.')
      return
    }
    return handleAction('tick', () => advanceTick(sessionId))
  }

  const handleTicks = () => {
    if (!canTick) {
      setError('Simulation must be running in manual mode to advance ticks.')
      return
    }
    const count = parseInt(ticksInput, 10)
    if (isNaN(count) || count < 1) {
      setError('Please enter a valid number of ticks (1-100)')
      return
    }
    handleAction(`run ${count} ticks`, () => advanceTicks(sessionId, count))
  }

  const handlePause = () =>
    handleAction('pause', () => pauseSimulation(sessionId))

  const handleReset = () =>
    handleAction('reset', () => resetSimulation(sessionId, true))

  if (loading) {
    return (
      <div
        style={{
          background: '#f5f5f5',
          padding: '16px',
          borderRadius: '8px',
          marginBottom: '16px',
        }}
      >
        <h3 style={{ marginTop: 0, marginBottom: '12px' }}>Tick Controls</h3>
        <p style={{ opacity: 0.6 }}>Loading simulation state...</p>
      </div>
    )
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
      <h3 style={{ marginTop: 0, marginBottom: '12px' }}>Tick Controls</h3>

      {/* Status display */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          marginBottom: '16px',
          padding: '12px',
          background: '#fff',
          borderRadius: '6px',
          border: '1px solid #e0e0e0',
        }}
      >
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '12px', opacity: 0.7, textTransform: 'uppercase' }}>
            Tick Index
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700 }}>
            {state?.tick_index ?? 0}
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '12px', opacity: 0.7, textTransform: 'uppercase' }}>
            Status
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                background: getStatusColor(tickStatus),
                animation: isRunning ? 'pulse 1s infinite' : 'none',
              }}
            />
            <span style={{ fontSize: '16px', fontWeight: 600, textTransform: 'capitalize' }}>
              {tickStatus}
            </span>
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '12px', opacity: 0.7, textTransform: 'uppercase' }}>
            Mode
          </div>
          <div style={{ fontSize: '16px', fontWeight: 600, textTransform: 'capitalize' }}>
            {state?.simulation_mode ?? 'Not configured'}
          </div>
        </div>
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '10px 12px',
          background: '#fff',
          borderRadius: '6px',
          border: '1px solid #e0e0e0',
          marginBottom: '16px',
        }}
      >
        <div style={{ fontSize: '12px', opacity: 0.7, textTransform: 'uppercase' }}>
          Cost
        </div>
        <div style={{ fontSize: '16px', fontWeight: 600, color: costColor }}>
          ${currentCost.toFixed(2)} / ${maxCost.toFixed(2)}
        </div>
      </div>

      {/* Pending work summary */}
      {state?.pending_work_summary && (
        <div
          style={{
            background: '#fff3cd',
            border: '1px solid #ffc107',
            padding: '10px 12px',
            borderRadius: '6px',
            marginBottom: '16px',
            fontSize: '13px',
          }}
        >
          <strong>Pending:</strong> {state.pending_work_summary}
        </div>
      )}

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

      {/* Control buttons */}
      {!isConfigured ? (
        <p style={{ fontSize: '14px', opacity: 0.6, textAlign: 'center', margin: 0 }}>
          Configure simulation settings above to enable controls.
        </p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {/* Start button (when not yet started) */}
          {tickStatus === 'idle' && (
            <button
              type="button"
              onClick={handleStart}
              disabled={actionLoading !== null || !canStart}
              style={{
                padding: '12px',
                background: actionLoading || !canStart ? '#9e9e9e' : '#4caf50',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                cursor: actionLoading || !canStart ? 'not-allowed' : 'pointer',
                fontWeight: 600,
                fontSize: '14px',
              }}
            >
              {actionLoading === 'start' ? 'Starting...' : 'Start Simulation'}
            </button>
          )}

          {/* Tick controls row */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              type="button"
              onClick={handleTick}
              disabled={actionLoading !== null || !canTick}
              style={{
                flex: 1,
                padding: '10px',
                background: actionLoading || !canTick ? '#9e9e9e' : '#1976d2',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                cursor: actionLoading || !canTick ? 'not-allowed' : 'pointer',
                fontWeight: 600,
                fontSize: '13px',
              }}
            >
              {actionLoading === 'tick' ? 'Ticking...' : 'Run 1 Tick'}
            </button>

            <div style={{ display: 'flex', flex: 1, gap: '4px' }}>
              <input
                type="number"
                min="1"
                max="100"
                value={ticksInput}
                onChange={(e) => setTicksInput(e.target.value)}
                disabled={actionLoading !== null || !canTick}
                style={{
                  width: '60px',
                  padding: '8px',
                  border: '1px solid #ccc',
                  borderRadius: '6px 0 0 6px',
                  fontSize: '13px',
                  textAlign: 'center',
                }}
              />
              <button
                type="button"
                onClick={handleTicks}
                disabled={actionLoading !== null || !canTick}
                style={{
                  flex: 1,
                  padding: '10px',
                  background: actionLoading || !canTick ? '#9e9e9e' : '#1976d2',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '0 6px 6px 0',
                  cursor: actionLoading || !canTick ? 'not-allowed' : 'pointer',
                  fontWeight: 600,
                  fontSize: '13px',
                }}
              >
                {actionLoading?.startsWith('run ') ? 'Running...' : 'Run N Ticks'}
              </button>
            </div>
          </div>

          {/* Pause/Reset row */}
          <div style={{ display: 'flex', gap: '8px' }}>
            {isAutoMode && (
              <button
                type="button"
                onClick={handlePause}
                disabled={actionLoading !== null || !isRunning}
                style={{
                  flex: 1,
                  padding: '10px',
                  background: actionLoading || !isRunning ? '#9e9e9e' : '#ff9800',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: actionLoading || !isRunning ? 'not-allowed' : 'pointer',
                  fontWeight: 600,
                  fontSize: '13px',
                }}
              >
                {actionLoading === 'pause' ? 'Pausing...' : 'Pause'}
              </button>
            )}
            <button
              type="button"
              onClick={handleReset}
              disabled={actionLoading !== null}
              style={{
                flex: 1,
                padding: '10px',
                background: actionLoading ? '#9e9e9e' : '#f44336',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                cursor: actionLoading ? 'not-allowed' : 'pointer',
                fontWeight: 600,
                fontSize: '13px',
              }}
            >
              {actionLoading === 'reset' ? 'Resetting...' : 'Reset'}
            </button>
          </div>
        </div>
      )}

      {/* Inline pulse animation style */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  )
}

export default TickControls
