import { useCallback, useEffect, useRef, useState } from 'react'
import { createSession } from '../api/client'
import {
  getSimulationState,
  getWorkflowConfig,
  streamSessionEvents,
  type SessionEvent,
  type SimulationStateResponse,
  type WorkflowConfigResponse,
} from '../api/controlClient'
import { AgentAssignment } from './control/widgets/AgentAssignment'
import { AgentFlowEditor } from './control/widgets/AgentFlowEditor'
import { AgentInitializer } from './control/widgets/AgentInitializer'
import { AgentTaskInput } from './control/widgets/AgentTaskInput'
import AgentGraph from './control/widgets/AgentGraph'
import MultiAgentMessages from './control/widgets/MultiAgentMessages'
import { SimulationConfig } from './control/widgets/SimulationConfig'
import { TickControls } from './control/widgets/TickControls'

export function SimulationScreen() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [creatingSession, setCreatingSession] = useState(true)
  const [loadingSession, setLoadingSession] = useState(false)
  const [sessionError, setSessionError] = useState<string | null>(null)
  const [workflowConfig, setWorkflowConfig] = useState<WorkflowConfigResponse | null>(null)
  const [simulationState, setSimulationState] = useState<SimulationStateResponse | null>(null)
  const [sessionEvents, setSessionEvents] = useState<SessionEvent[]>([])
  const [initialPrompt, setInitialPrompt] = useState('')
  const [firstAgentId, setFirstAgentId] = useState('')
  const [sseError, setSseError] = useState<string | null>(null)
  const createRequestId = useRef(0)

  const createNewSession = useCallback(async () => {
    const requestId = ++createRequestId.current
    setCreatingSession(true)
    setSessionError(null)
    setSessionId(null)
    setWorkflowConfig(null)
    setSimulationState(null)
    setSessionEvents([])
    setInitialPrompt('')
    setFirstAgentId('')
    setSseError(null)

    try {
      const session = await createSession()
      if (createRequestId.current !== requestId) {
        return
      }
      setSessionId(session.session_id)
    } catch (err: any) {
      if (createRequestId.current !== requestId) {
        return
      }
      setSessionError(err?.detail || err?.message || String(err))
    } finally {
      if (createRequestId.current === requestId) {
        setCreatingSession(false)
      }
    }
  }, [])

  useEffect(() => {
    createNewSession()
  }, [createNewSession])

  const refreshWorkflowConfig = useCallback(async () => {
    if (!sessionId) return
    try {
      const config = await getWorkflowConfig(sessionId)
      setWorkflowConfig(config)
    } catch (err) {
      console.error('Failed to refresh workflow config:', err)
    }
  }, [sessionId])

  const refreshSimulationState = useCallback(async () => {
    if (!sessionId) return
    try {
      const state = await getSimulationState(sessionId)
      setSimulationState(state)
    } catch (err) {
      console.error('Failed to refresh simulation state:', err)
    }
  }, [sessionId])

  const refreshAll = useCallback(async () => {
    if (!sessionId) return
    await Promise.all([refreshWorkflowConfig(), refreshSimulationState()])
  }, [sessionId, refreshWorkflowConfig, refreshSimulationState])

  useEffect(() => {
    if (!sessionId) return
    const activeSessionId = sessionId
    let cancelled = false
    setLoadingSession(true)
    setSessionError(null)

    async function loadSessionDetails() {
      try {
        const [workflow, state] = await Promise.all([
          getWorkflowConfig(activeSessionId),
          getSimulationState(activeSessionId),
        ])
        if (!cancelled) {
          setWorkflowConfig(workflow)
          setSimulationState(state)
        }
      } catch (err: any) {
        if (!cancelled) {
          setSessionError(err?.detail || err?.message || String(err))
        }
      } finally {
        if (!cancelled) {
          setLoadingSession(false)
        }
      }
    }

    loadSessionDetails()

    return () => {
      cancelled = true
    }
  }, [sessionId])

  useEffect(() => {
    if (
      simulationState?.initial_prompt !== null &&
      simulationState?.initial_prompt !== undefined
    ) {
      setInitialPrompt(simulationState.initial_prompt)
    }
    if (
      simulationState?.first_agent_id !== null &&
      simulationState?.first_agent_id !== undefined
    ) {
      setFirstAgentId(simulationState.first_agent_id)
    }
  }, [simulationState?.initial_prompt, simulationState?.first_agent_id])

  useEffect(() => {
    if (!sessionId) return
    setSessionEvents([])
    setSseError(null)

    let eventSource: EventSource | null = null
    let reconnectAttempts = 0
    const maxReconnectAttempts = 5
    const reconnectDelay = 2000

    const connect = () => {
      eventSource = streamSessionEvents(sessionId)

      const handleEvent = (event: MessageEvent) => {
        try {
          const parsed: SessionEvent = JSON.parse(event.data)
          setSessionEvents((prev) => {
            const next = [...prev, parsed]
            return next.length > 500 ? next.slice(next.length - 500) : next
          })
          // Reset reconnect attempts on successful event
          reconnectAttempts = 0
          setSseError(null)
        } catch (parseErr) {
          console.error('Failed to parse SSE event:', parseErr, event.data)
        }
      }

      eventSource.addEventListener('session_event', handleEvent)

      eventSource.onerror = () => {
        eventSource?.close()
        reconnectAttempts++
        if (reconnectAttempts <= maxReconnectAttempts) {
          console.log(`SSE reconnecting... (attempt ${reconnectAttempts}/${maxReconnectAttempts})`)
          setTimeout(connect, reconnectDelay)
        } else {
          console.error('SSE max reconnect attempts reached')
          setSseError('Real-time updates disconnected')
        }
      }
    }

    connect()

    return () => {
      reconnectAttempts = maxReconnectAttempts + 1 // Prevent reconnection after cleanup
      eventSource?.close()
    }
  }, [sessionId])

  useEffect(() => {
    if (!sessionId) return
    if ((simulationState?.tick_status || '').toLowerCase() !== 'running') return

    const intervalId = window.setInterval(() => {
      refreshSimulationState()
    }, 2000)

    return () => {
      window.clearInterval(intervalId)
    }
  }, [sessionId, simulationState?.tick_status, refreshSimulationState])

  const agents =
    simulationState?.agents && simulationState.agents.length > 0
      ? simulationState.agents
      : workflowConfig?.agents || []
  const hasAgents = agents.length > 0
  const graphEdges = simulationState?.agent_graph?.edges || []
  const pendingDelegation = simulationState?.simulation_expected_responses || []
  const delegationLabel =
    pendingDelegation.length > 0
      ? `Waiting on: ${pendingDelegation.join(', ')}`
      : 'Delegation complete'
  const delegationColor = pendingDelegation.length > 0 ? '#ff9800' : '#2e7d32'

  return (
    <div style={{ padding: '24px' }}>
      <header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px',
          marginBottom: '24px',
          flexWrap: 'wrap',
        }}
      >
        <div>
          <h1 style={{ marginTop: 0, marginBottom: '8px' }}>Simulation Sandbox</h1>
          <p style={{ margin: 0, opacity: 0.7 }}>
            Configure agents, run ticks, and review message flow.
          </p>
        </div>
        <button
          type="button"
          onClick={createNewSession}
          disabled={creatingSession}
          style={{
            padding: '10px 16px',
            borderRadius: '6px',
            border: '1px solid #ccc',
            background: creatingSession ? '#eee' : '#fff',
            cursor: creatingSession ? 'not-allowed' : 'pointer',
            fontWeight: 600,
          }}
        >
          {creatingSession ? 'Creating...' : 'New'}
        </button>
      </header>

      {sessionError && (
        <div
          style={{
            background: '#ffebee',
            color: '#c62828',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '16px',
          }}
        >
          {sessionError}
        </div>
      )}

      {creatingSession && (
        <p style={{ marginBottom: '16px', opacity: 0.7 }}>
          Creating a new simulation session...
        </p>
      )}

      {loadingSession && sessionId && (
        <p style={{ marginBottom: '16px', opacity: 0.7 }}>
          Loading session data...
        </p>
      )}

      {sseError && (
        <div
          style={{
            background: '#fff3cd',
            border: '1px solid #ffc107',
            color: '#856404',
            padding: '12px 16px',
            borderRadius: '6px',
            marginBottom: '16px',
          }}
        >
          {sseError}
        </div>
      )}

      {sessionId && !creatingSession && (
        <>
          <section style={{ marginBottom: '24px' }}>
            <h2>Workflow Setup</h2>
            {!hasAgents ? (
              <AgentInitializer
                sessionId={sessionId}
                onInitialized={() => refreshAll()}
              />
            ) : (
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                  gap: '16px',
                }}
              >
                <AgentAssignment
                  sessionId={sessionId}
                  agents={agents}
                  availableRoles={simulationState?.available_roles}
                  onAssigned={refreshAll}
                />
                <AgentTaskInput
                  sessionId={sessionId}
                  currentTask={workflowConfig?.main_task || undefined}
                  onTaskSet={refreshAll}
                />
                <AgentFlowEditor
                  sessionId={sessionId}
                  agents={agents}
                  existingEdges={workflowConfig?.agent_graph?.edges || []}
                  onFlowConfigured={refreshAll}
                />
              </div>
            )}
          </section>

          <section style={{ marginBottom: '24px' }}>
            <h2>Simulation Controls</h2>
            {!hasAgents ? (
              <p style={{ opacity: 0.7 }}>
                Initialize agents to configure simulation settings.
              </p>
            ) : (
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                  gap: '16px',
                }}
              >
                <SimulationConfig
                  sessionId={sessionId}
                  currentMode={simulationState?.simulation_mode}
                  currentDelayMs={simulationState?.auto_delay_ms}
                  currentTickBudget={simulationState?.tick_budget}
                  currentUseRealLlm={simulationState?.use_real_llm}
                  currentDefaultModel={simulationState?.default_model}
                  currentDefaultTemperature={simulationState?.default_temperature}
                  currentMaxCostUsd={simulationState?.max_cost_usd}
                  currentTickRateLimitMs={simulationState?.tick_rate_limit_ms}
                  tickStatus={simulationState?.tick_status}
                  agents={agents}
                  initialPrompt={initialPrompt}
                  firstAgentId={firstAgentId}
                  onStartContextChange={(context) => {
                    setInitialPrompt(context.initialPrompt)
                    setFirstAgentId(context.firstAgentId)
                  }}
                  onConfigured={refreshSimulationState}
                />
                <TickControls
                  sessionId={sessionId}
                  initialPrompt={initialPrompt}
                  firstAgentId={firstAgentId}
                  onStateChange={refreshSimulationState}
                />
              </div>
            )}
          </section>

          <section style={{ marginBottom: '24px' }}>
            <h2>Final Answer</h2>
            <div style={{ marginBottom: '12px' }}>
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 10px',
                  borderRadius: '999px',
                  background: '#fff',
                  border: `1px solid ${delegationColor}`,
                  color: delegationColor,
                  fontSize: '12px',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.4px',
                }}
              >
                {delegationLabel}
              </span>
            </div>
            <div
              style={{
                background: '#f5f5f5',
                padding: '16px',
                borderRadius: '8px',
                border: '1px solid #e0e0e0',
              }}
            >
              {simulationState?.simulation_final_answer ? (
                <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                  {simulationState.simulation_final_answer}
                </p>
              ) : (
                <p style={{ margin: 0, opacity: 0.6 }}>
                  No final answer yet. Start the simulation and let agents conclude.
                </p>
              )}
            </div>
          </section>

          <section>
            <h2>Live Output</h2>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
                gap: '16px',
              }}
            >
              <MultiAgentMessages events={sessionEvents} />
              <AgentGraph agents={agents} edges={graphEdges} />
            </div>
          </section>
        </>
      )}
    </div>
  )
}
