import { useEffect, useMemo, useState } from 'react'

import {
  getSessionStatus,
  streamSessionEvents,
  type SessionEvent,
  type SessionListItem,
  type SessionStatusResponse,
} from '../../../api/controlClient'
import './SessionComparison.css'

type SessionMetrics = {
  sessionId: string
  createdAt: Date
  phase: string
  totalTasks: number
  completedTasks: number
  failedTasks: number
  totalTokens: number
  totalCost: number
  durationSeconds: number
  avgTaskDuration: number
  escalationCount: number
  gateBlockCount: number
  failureRate: number
  tokenTimeline: Array<{ timestamp: Date; cumulativeTokens: number }>
}

type SessionComparisonProps = {
  sessions: SessionListItem[]
  selectedSessionId: string | null
}

const MODEL_PRICING: Record<string, { prompt: number; completion: number }> = {
  default: { prompt: 0.002, completion: 0.004 },
  'gpt-4o-mini': { prompt: 0.00015, completion: 0.0006 },
  'gpt-4o': { prompt: 0.0025, completion: 0.005 },
}

function calculateCost(model: string | undefined, prompt: number, completion: number) {
  const pricing = MODEL_PRICING[model ?? ''] ?? MODEL_PRICING.default
  return (prompt / 1000) * pricing.prompt + (completion / 1000) * pricing.completion
}

function normalizeEventType(eventType: string) {
  return eventType.toLowerCase()
}

function collectSessionEvents(sessionId: string, timeoutMs = 1500): Promise<SessionEvent[]> {
  return new Promise((resolve) => {
    const events: SessionEvent[] = []
    const eventSource = streamSessionEvents(sessionId)

    const handleEvent = (event: MessageEvent) => {
      try {
        events.push(JSON.parse(event.data) as SessionEvent)
      } catch (error) {
        console.error('Failed to parse session event', error)
      }
    }

    const stop = () => {
      eventSource.removeEventListener('session_event', handleEvent)
      eventSource.close()
      resolve(events)
    }

    eventSource.addEventListener('session_event', handleEvent)
    eventSource.onerror = stop

    setTimeout(stop, timeoutMs)
  })
}

function buildMetrics(
  sessionId: string,
  status: SessionStatusResponse,
  events: SessionEvent[]
): SessionMetrics {
  const createdAt = new Date(status.created_at)
  const updatedAt = new Date(status.updated_at)
  const durationSeconds = Math.max(
    0,
    (updatedAt.getTime() - createdAt.getTime()) / 1000
  )

  let totalTokens = 0
  let totalCost = 0
  const tokenTimeline: Array<{ timestamp: Date; cumulativeTokens: number }> = []

  const llmEvents = events
    .filter((event) => normalizeEventType(event.event_type) === 'llm_response_received')
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())

  llmEvents.forEach((event) => {
    const promptTokens = Number(event.metadata?.prompt_tokens ?? 0)
    const completionTokens = Number(event.metadata?.completion_tokens ?? 0)
    const totalEventTokens = Number(event.metadata?.total_tokens ?? promptTokens + completionTokens)
    totalTokens += totalEventTokens
    totalCost += calculateCost(event.metadata?.model as string | undefined, promptTokens, completionTokens)
    tokenTimeline.push({ timestamp: new Date(event.timestamp), cumulativeTokens: totalTokens })
  })

  const escalationCount = events.filter((event) => {
    const type = normalizeEventType(event.event_type)
    if (type !== 'agent_invoked') return false
    return Number(event.metadata?.failure_count ?? 0) > 0
  }).length

  const gateBlockCount = events.filter((event) => {
    const type = normalizeEventType(event.event_type)
    if (type !== 'gate_evaluated') return false
    const statusValue = String(event.metadata?.status ?? event.metadata?.decision ?? '').toUpperCase()
    return statusValue === 'BLOCK'
  }).length

  const taskDurations: number[] = []
  const taskStartTimes: Record<string, number> = {}

  events.forEach((event) => {
    const type = normalizeEventType(event.event_type)
    if (type === 'task_started' && event.task_id) {
      taskStartTimes[event.task_id] = new Date(event.timestamp).getTime()
    }
    if ((type === 'task_completed' || type === 'task_failed') && event.task_id && taskStartTimes[event.task_id]) {
      const duration = (new Date(event.timestamp).getTime() - taskStartTimes[event.task_id]) / 1000
      taskDurations.push(Math.max(0, duration))
    }
  })

  const avgTaskDuration = taskDurations.length
    ? taskDurations.reduce((sum, value) => sum + value, 0) / taskDurations.length
    : 0

  const totalTasks = status.completed_tasks + status.failed_tasks + (status.active_task_id ? 1 : 0)
  const failureRate = totalTasks > 0 ? status.failed_tasks / totalTasks : 0

  return {
    sessionId,
    createdAt,
    phase: status.phase,
    totalTasks,
    completedTasks: status.completed_tasks,
    failedTasks: status.failed_tasks,
    totalTokens,
    totalCost,
    durationSeconds,
    avgTaskDuration,
    escalationCount,
    gateBlockCount,
    failureRate,
    tokenTimeline,
  }
}

function buildSparkline(points: Array<{ timestamp: Date; cumulativeTokens: number }>) {
  if (points.length < 2) return ''
  const minTime = points[0].timestamp.getTime()
  const maxTime = points[points.length - 1].timestamp.getTime()
  const maxTokens = Math.max(...points.map((point) => point.cumulativeTokens), 1)

  return points
    .map((point) => {
      const x = maxTime === minTime ? 0 : (point.timestamp.getTime() - minTime) / (maxTime - minTime)
      const y = 1 - point.cumulativeTokens / maxTokens
      return `${(x * 100).toFixed(1)},${(y * 100).toFixed(1)}`
    })
    .join(' ')
}

export default function SessionComparison({ sessions, selectedSessionId }: SessionComparisonProps) {
  const [selectedSessionIds, setSelectedSessionIds] = useState<string[]>([])
  const [metrics, setMetrics] = useState<SessionMetrics[]>([])
  const [loading, setLoading] = useState(false)
  const [sortBy, setSortBy] = useState<keyof SessionMetrics>('createdAt')
  const [sortDesc, setSortDesc] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const sortedSessions = useMemo(() => {
    return [...sessions].sort(
      (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    )
  }, [sessions])

  useEffect(() => {
    if (sortedSessions.length === 0) return

    setSelectedSessionIds((prev) => {
      let next = [...prev]
      if (selectedSessionId && !next.includes(selectedSessionId)) {
        next = [selectedSessionId, ...next]
      }

      if (next.length === 0) {
        next = sortedSessions.slice(0, 2).map((session) => session.session_id)
      }

      return next.slice(0, 4)
    })
  }, [selectedSessionId, sortedSessions])

  useEffect(() => {
    let cancelled = false

    async function loadMetrics() {
      if (selectedSessionIds.length < 2) {
        setMetrics([])
        return
      }

      setLoading(true)
      setErrorMessage(null)

      try {
        const results = await Promise.all(
          selectedSessionIds.map(async (sessionId) => {
            const [status, events] = await Promise.all([
              getSessionStatus(sessionId),
              collectSessionEvents(sessionId),
            ])
            return buildMetrics(sessionId, status, events)
          })
        )

        if (!cancelled) {
          setMetrics(results)
        }
      } catch (error: any) {
        if (!cancelled) {
          setErrorMessage(error.message || 'Failed to load session metrics')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadMetrics()

    return () => {
      cancelled = true
    }
  }, [selectedSessionIds])

  const sortedMetrics = useMemo(() => {
    return [...metrics].sort((a, b) => {
      const aValue = a[sortBy]
      const bValue = b[sortBy]
      if (aValue < bValue) return sortDesc ? 1 : -1
      if (aValue > bValue) return sortDesc ? -1 : 1
      return 0
    })
  }, [metrics, sortBy, sortDesc])

  const handleSort = (column: keyof SessionMetrics) => {
    if (sortBy === column) {
      setSortDesc(!sortDesc)
    } else {
      setSortBy(column)
      setSortDesc(true)
    }
  }

  const toggleSession = (sessionId: string) => {
    setSelectedSessionIds((prev) => {
      if (prev.includes(sessionId)) {
        return prev.filter((id) => id !== sessionId)
      }

      if (prev.length >= 4) return prev
      return [...prev, sessionId]
    })
  }

  return (
    <section className="session-comparison">
      <header className="session-comparison__header">
        <div>
          <h2>Session Comparison</h2>
          <p>Compare metrics across multiple sessions (select 2-4).</p>
        </div>
        <div className="session-comparison__controls">
          {sortedSessions.map((session) => {
            const checked = selectedSessionIds.includes(session.session_id)
            return (
              <label key={session.session_id} className={`session-chip ${checked ? 'active' : ''}`}>
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggleSession(session.session_id)}
                  disabled={!checked && selectedSessionIds.length >= 4}
                />
                <span>{session.session_id.slice(0, 8)}</span>
              </label>
            )
          })}
        </div>
      </header>

      {errorMessage && <div className="session-comparison__error">{errorMessage}</div>}

      {selectedSessionIds.length < 2 ? (
        <div className="session-comparison__empty">
          Select at least two sessions to compare metrics.
        </div>
      ) : loading ? (
        <div className="session-comparison__empty">Loading metrics...</div>
      ) : metrics.length === 0 ? (
        <div className="session-comparison__empty">No metrics available yet.</div>
      ) : (
        <div className="session-comparison__table-wrapper">
          <table className="session-comparison__table">
            <thead>
              <tr>
                <th onClick={() => handleSort('sessionId')}>Session</th>
                <th onClick={() => handleSort('phase')}>Phase</th>
                <th onClick={() => handleSort('completedTasks')}>Tasks</th>
                <th onClick={() => handleSort('failedTasks')}>Failed</th>
                <th onClick={() => handleSort('durationSeconds')}>Duration</th>
                <th onClick={() => handleSort('totalTokens')}>Tokens</th>
                <th onClick={() => handleSort('totalCost')}>Cost</th>
                <th onClick={() => handleSort('failureRate')}>Failure rate</th>
                <th onClick={() => handleSort('escalationCount')}>Escalations</th>
                <th onClick={() => handleSort('gateBlockCount')}>Gate blocks</th>
                <th>Token trend</th>
              </tr>
            </thead>
            <tbody>
              {sortedMetrics.map((session) => (
                <tr key={session.sessionId}>
                  <td className="session-id">{session.sessionId.slice(0, 8)}</td>
                  <td className="session-phase">{session.phase}</td>
                  <td>
                    {session.completedTasks}/{session.totalTasks}
                  </td>
                  <td className={session.failedTasks > 0 ? 'session-failed' : ''}>
                    {session.failedTasks}
                  </td>
                  <td>{Math.round(session.durationSeconds)}s</td>
                  <td>{session.totalTokens.toLocaleString()}</td>
                  <td>${session.totalCost.toFixed(4)}</td>
                  <td>{(session.failureRate * 100).toFixed(1)}%</td>
                  <td>{session.escalationCount}</td>
                  <td>{session.gateBlockCount}</td>
                  <td>
                    {session.tokenTimeline.length > 1 ? (
                      <svg viewBox="0 0 100 40" className="token-sparkline" aria-hidden="true">
                        <polyline
                          fill="none"
                          stroke="#1d4ed8"
                          strokeWidth="3"
                          points={buildSparkline(session.tokenTimeline)}
                        />
                      </svg>
                    ) : (
                      <span className="session-muted">No token data</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
