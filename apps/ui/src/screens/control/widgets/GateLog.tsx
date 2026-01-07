import { useMemo, useState } from 'react'

import type { SessionEvent } from '../../../api/controlClient'
import './GateLog.css'

type GateStatus = 'BLOCK' | 'WARN' | 'PASS'

type GateDecision = {
  timestamp: string
  taskId: string
  gateName: string
  status: GateStatus
  message: string
  details?: Record<string, unknown>
}

type GateLogProps = {
  events: SessionEvent[]
}

const STATUS_LABELS: Record<GateStatus, string> = {
  BLOCK: 'Blocked',
  WARN: 'Warnings',
  PASS: 'Passed',
}

const STATUS_ICONS: Record<GateStatus, string> = {
  BLOCK: '🚫',
  WARN: '⚠️',
  PASS: '✅',
}

function normalizeStatus(status?: string): GateStatus {
  const value = status?.toUpperCase()
  if (value === 'BLOCK') return 'BLOCK'
  if (value === 'WARN') return 'WARN'
  return 'PASS'
}

export default function GateLog({ events }: GateLogProps) {
  const [filter, setFilter] = useState<'ALL' | GateStatus>('ALL')

  const decisions = useMemo(() => {
    return events
      .filter((event) => event.event_type === 'gate_evaluated')
      .map((event) => ({
        timestamp: event.timestamp,
        taskId: event.task_id || 'unknown',
        gateName: (event.metadata?.gate_name as string) || 'UnknownGate',
        status: normalizeStatus(event.metadata?.status as string | undefined),
        message: event.message,
        details: event.metadata?.details as Record<string, unknown> | undefined,
      }))
      .sort(
        (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      )
  }, [events])

  const counts = useMemo(() => {
    return decisions.reduce(
      (acc, decision) => {
        acc[decision.status] += 1
        return acc
      },
      { BLOCK: 0, WARN: 0, PASS: 0 }
    )
  }, [decisions])

  const filteredDecisions = useMemo(() => {
    if (filter === 'ALL') {
      return decisions
    }
    return decisions.filter((decision) => decision.status === filter)
  }, [decisions, filter])

  return (
    <section className="gate-log">
      <header className="gate-log__header">
        <div>
          <h2>Gate Decision Log</h2>
          <p>Track policy, feasibility, and diff safety checks in real time.</p>
        </div>
        <div className="gate-log__filters">
          <button
            type="button"
            className={filter === 'ALL' ? 'active' : ''}
            onClick={() => setFilter('ALL')}
          >
            All ({decisions.length})
          </button>
          {(Object.keys(STATUS_LABELS) as GateStatus[]).map((status) => (
            <button
              key={status}
              type="button"
              className={filter === status ? 'active' : ''}
              onClick={() => setFilter(status)}
            >
              {STATUS_LABELS[status]} ({counts[status]})
            </button>
          ))}
        </div>
      </header>

      <div className="gate-log__body">
        {filteredDecisions.length === 0 ? (
          <div className="gate-log__empty">No gate evaluations yet.</div>
        ) : (
          <ul className="gate-log__list">
            {filteredDecisions.map((decision, index) => (
              <li
                key={`${decision.taskId}-${decision.timestamp}-${index}`}
                className={`gate-log__item gate-log__item--${decision.status.toLowerCase()}`}
              >
                <div className="gate-log__item-header">
                  <span className="gate-log__status">{STATUS_ICONS[decision.status]}</span>
                  <span className="gate-log__gate">{decision.gateName}</span>
                  <span className="gate-log__time">
                    {new Date(decision.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div className="gate-log__item-body">
                  <div className="gate-log__task">Task: {decision.taskId}</div>
                  <div className="gate-log__message">{decision.message}</div>
                  {decision.details && Object.keys(decision.details).length > 0 && (
                    <details className="gate-log__details">
                      <summary>Details</summary>
                      <pre>{JSON.stringify(decision.details, null, 2)}</pre>
                    </details>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
