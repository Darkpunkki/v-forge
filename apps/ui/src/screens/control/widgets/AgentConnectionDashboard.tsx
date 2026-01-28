import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  getTaskStatus,
  listAgents,
  type RemoteAgent,
  type TaskStatusResponse,
} from '../../../api/controlClient'

type AgentConnectionDashboardProps = {
  onSelectAgent: (agent: RemoteAgent) => void
  refreshIntervalMs?: number
  selectedAgentId?: string | null
}

type DisplayStatus = 'connected' | 'busy' | 'idle' | 'disconnected' | 'error'

const STATUS_COLORS: Record<DisplayStatus, { bg: string; fg: string }> = {
  connected: { bg: '#e8f5e9', fg: '#2e7d32' },
  busy: { bg: '#e3f2fd', fg: '#0d47a1' },
  idle: { bg: '#f5f5f5', fg: '#424242' },
  disconnected: { bg: '#ffebee', fg: '#c62828' },
  error: { bg: '#ffebee', fg: '#b71c1c' },
}

function deriveDisplayStatus(
  agent: RemoteAgent,
  taskStatus?: TaskStatusResponse
): DisplayStatus {
  if (agent.status === 'disconnected') return 'disconnected'
  if (!taskStatus) return 'connected'
  const status = taskStatus.status.toLowerCase()
  if (status === 'error') return 'error'
  if (status === 'running' || status === 'dispatched') return 'busy'
  if (status === 'idle' || status === 'completed') return 'idle'
  return 'connected'
}

export function AgentConnectionDashboard({
  onSelectAgent,
  refreshIntervalMs = 5000,
  selectedAgentId,
}: AgentConnectionDashboardProps) {
  const [agents, setAgents] = useState<RemoteAgent[]>([])
  const [taskStatuses, setTaskStatuses] = useState<Record<string, TaskStatusResponse>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refreshAgents = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await listAgents()
      setAgents(response.agents)

      const connectedAgents = response.agents.filter((agent) => agent.status === 'connected')
      const statusEntries = await Promise.all(
        connectedAgents.map(async (agent) => {
          try {
            const status = await getTaskStatus(agent.agent_id)
            return [agent.agent_id, status] as const
          } catch {
            return null
          }
        })
      )

      const nextStatuses: Record<string, TaskStatusResponse> = {}
      statusEntries.forEach((entry) => {
        if (!entry) return
        nextStatuses[entry[0]] = entry[1]
      })
      setTaskStatuses(nextStatuses)
    } catch (err: any) {
      setError(err?.detail || err?.message || 'Failed to load agents')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshAgents()
    if (refreshIntervalMs <= 0) return
    const intervalId = window.setInterval(refreshAgents, refreshIntervalMs)
    return () => window.clearInterval(intervalId)
  }, [refreshAgents, refreshIntervalMs])

  const displayAgents = useMemo(() => {
    return agents.map((agent) => {
      const taskStatus = taskStatuses[agent.agent_id]
      return {
        agent,
        taskStatus,
        displayStatus: deriveDisplayStatus(agent, taskStatus),
      }
    })
  }, [agents, taskStatuses])

  return (
    <section
      style={{
        background: '#f5f5f5',
        border: '1px solid #e0e0e0',
        borderRadius: '10px',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
      }}
    >
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ margin: 0 }}>Agent Connections</h3>
          <p style={{ margin: 0, fontSize: '12px', opacity: 0.7 }}>
            Registered agents and their current status.
          </p>
        </div>
        <button
          type="button"
          onClick={refreshAgents}
          disabled={loading}
          style={{
            fontSize: '12px',
            padding: '6px 10px',
            borderRadius: '6px',
            border: '1px solid #ccc',
            background: loading ? '#eee' : '#fff',
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </header>

      {error && (
        <div
          style={{
            background: '#ffebee',
            border: '1px solid #ef9a9a',
            color: '#b71c1c',
            borderRadius: '6px',
            padding: '8px 10px',
            fontSize: '12px',
          }}
        >
          {error}
        </div>
      )}

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '12px',
        }}
      >
        {displayAgents.length === 0 ? (
          <div style={{ opacity: 0.7, fontSize: '13px' }}>
            No agents registered yet.
          </div>
        ) : (
          displayAgents.map(({ agent, taskStatus, displayStatus }) => {
            const color = STATUS_COLORS[displayStatus]
            const isSelected = selectedAgentId && selectedAgentId === agent.agent_id
            return (
              <button
                key={agent.agent_id}
                type="button"
                onClick={() => onSelectAgent(agent)}
                style={{
                  textAlign: 'left',
                  border: isSelected ? '2px solid #111' : '1px solid #e0e0e0',
                  borderRadius: '10px',
                  padding: '12px',
                  background: '#fff',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px' }}>
                  <div>
                    <div style={{ fontWeight: 700 }}>{agent.name}</div>
                    <div style={{ fontSize: '12px', opacity: 0.7 }}>{agent.agent_id}</div>
                  </div>
                  <span
                    style={{
                      alignSelf: 'flex-start',
                      padding: '4px 8px',
                      borderRadius: '999px',
                      fontSize: '11px',
                      fontWeight: 600,
                      background: color.bg,
                      color: color.fg,
                      textTransform: 'uppercase',
                    }}
                  >
                    {displayStatus}
                  </span>
                </div>

                <div style={{ fontSize: '12px', opacity: 0.7 }}>
                  Endpoint: {agent.endpoint_url || 'Not provided'}
                </div>

                {taskStatus && (
                  <div style={{ fontSize: '12px', opacity: 0.7 }}>
                    Task status: {taskStatus.status}
                  </div>
                )}
              </button>
            )
          })
        )}
      </div>
    </section>
  )
}

export default AgentConnectionDashboard
