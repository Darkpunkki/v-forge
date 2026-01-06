import { useMemo } from 'react'

import type { SessionEvent } from '../../../api/controlClient'

type AgentStatus = {
  role: string
  status: 'idle' | 'thinking' | 'executing' | 'error'
  currentTask?: string
  model?: string
  lastUpdated?: string
}

const DEFAULT_ROLES = ['orchestrator', 'worker', 'foreman', 'reviewer', 'fixer']
const STATUS_COLOR: Record<AgentStatus['status'], string> = {
  idle: '#2e7d32',
  thinking: '#f9a825',
  executing: '#d32f2f',
  error: '#c62828',
}

function formatTimestamp(timestamp?: string) {
  if (!timestamp) return '—'
  const date = new Date(timestamp)
  return date.toLocaleTimeString()
}

export default function AgentDashboard({ events }: { events: SessionEvent[] }) {
  const agentStatuses = useMemo(() => {
    const map = new Map<string, AgentStatus>()
    DEFAULT_ROLES.forEach((role) => map.set(role, { role, status: 'idle' }))

    events.forEach((event) => {
      const role = event.metadata?.agent_role
      if (!role) return

      const existing = map.get(role) || { role, status: 'idle' as const }
      const status: AgentStatus = {
        ...existing,
        lastUpdated: event.timestamp,
      }

      if (event.metadata?.model) {
        status.model = event.metadata.model as string
      }

      switch (event.event_type) {
        case 'agent_invoked':
          status.status = 'thinking'
          status.currentTask = event.task_id
          break
        case 'task_started':
          status.status = 'executing'
          status.currentTask = event.task_id
          break
        case 'task_completed':
          status.status = 'idle'
          status.currentTask = undefined
          break
        case 'task_failed':
          status.status = 'error'
          break
        case 'agent_completed':
          status.status = event.metadata?.success === False ? 'error' : 'idle'
          status.currentTask = undefined
          break
        default:
          break
      }

      map.set(role, status)
    })

    events
      .filter((event) => event.metadata?.agent_role && !map.has(event.metadata.agent_role))
      .forEach((event) => {
        const role = event.metadata?.agent_role as string
        map.set(role, { role, status: 'idle' })
      })

    return Array.from(map.values())
  }, [events])

  return (
    <section>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '12px',
        }}
      >
        <h2 style={{ margin: 0 }}>Agent Activity</h2>
        <span style={{ fontSize: '12px', opacity: 0.7 }}>
          Live status for {agentStatuses.length} agents
        </span>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '12px',
        }}
      >
        {agentStatuses.map((agent) => (
          <div
            key={agent.role}
            style={{
              background: '#f8f9fa',
              border: '1px solid #e0e0e0',
              borderRadius: '10px',
              padding: '12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: '12px', opacity: 0.7 }}>Role</div>
                <div style={{ fontWeight: 700, textTransform: 'capitalize' }}>{agent.role}</div>
              </div>
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '4px 8px',
                  borderRadius: '999px',
                  background: '#fff',
                  border: '1px solid #e0e0e0',
                  fontWeight: 700,
                }}
              >
                <span
                  style={{
                    display: 'inline-block',
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    background: STATUS_COLOR[agent.status],
                  }}
                />
                <span style={{ textTransform: 'capitalize' }}>{agent.status}</span>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: '12px', opacity: 0.7 }}>Current task</div>
                <div style={{ fontWeight: 600 }}>{agent.currentTask || '—'}</div>
              </div>
              <div>
                <div style={{ fontSize: '12px', opacity: 0.7 }}>Model</div>
                <div style={{ fontWeight: 600 }}>{agent.model || '—'}</div>
              </div>
            </div>

            <div style={{ fontSize: '12px', opacity: 0.6 }}>
              Last update: {formatTimestamp(agent.lastUpdated)}
            </div>
          </div>
        ))}
      </div>

      {events.length === 0 && (
        <p style={{ marginTop: '12px', opacity: 0.6 }}>
          Listening for session events. Agent cards will populate once tasks start executing.
        </p>
      )}
    </section>
  )
}
