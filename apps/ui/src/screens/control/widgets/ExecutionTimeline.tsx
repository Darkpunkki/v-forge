import { useMemo } from 'react'

import type { SessionEvent } from '../../../api/controlClient'
import './ExecutionTimeline.css'

type TimelineStatus = 'running' | 'complete' | 'failed'

type TimelineEntry = {
  taskId: string
  agentRole: string
  status: TimelineStatus
  start: Date
  end?: Date
}

interface ExecutionTimelineProps {
  events: SessionEvent[]
}

const STATUS_COLOR: Record<TimelineStatus, string> = {
  running: '#f97316',
  complete: '#22c55e',
  failed: '#ef4444',
}

const DEFAULT_ROLES = ['orchestrator', 'taskmaster', 'distributor', 'worker', 'foreman', 'fixer', 'reviewer']

function parseTimestamp(value?: string) {
  return value ? new Date(value) : null
}

export default function ExecutionTimeline({ events }: ExecutionTimelineProps) {
  const entries = useMemo(() => {
    const taskMap = new Map<string, TimelineEntry>()
    const ordered = [...events].sort((a, b) =>
      (parseTimestamp(a.timestamp)?.getTime() ?? 0) - (parseTimestamp(b.timestamp)?.getTime() ?? 0)
    )

    ordered.forEach((event) => {
      if (!event.task_id) return
      const agentRole = (event.metadata?.agent_role as string) || 'orchestrator'
      const startTime = parseTimestamp(event.timestamp) ?? new Date()

      if (!taskMap.has(event.task_id)) {
        taskMap.set(event.task_id, {
          taskId: event.task_id,
          agentRole,
          status: 'running',
          start: startTime,
        })
      }

      const current = taskMap.get(event.task_id)!

      switch (event.event_type) {
        case 'task_started':
        case 'agent_invoked': {
          taskMap.set(event.task_id, {
            ...current,
            agentRole,
            start: startTime,
            status: 'running',
          })
          break
        }
        case 'task_completed': {
          taskMap.set(event.task_id, {
            ...current,
            agentRole,
            end: parseTimestamp(event.timestamp) ?? new Date(),
            status: 'complete',
          })
          break
        }
        case 'task_failed': {
          taskMap.set(event.task_id, {
            ...current,
            agentRole,
            end: parseTimestamp(event.timestamp) ?? new Date(),
            status: 'failed',
          })
          break
        }
        default:
          break
      }
    })

    return Array.from(taskMap.values()).sort(
      (a, b) => a.start.getTime() - b.start.getTime()
    )
  }, [events])

  const roles = useMemo(() => {
    const set = new Set<string>(DEFAULT_ROLES)
    entries.forEach((entry) => set.add(entry.agentRole))
    return Array.from(set)
  }, [entries])

  const startTime = entries.reduce<number | null>((min, entry) => {
    const time = entry.start.getTime()
    if (min === null) return time
    return Math.min(min, time)
  }, null)

  const endTime = entries.reduce<number | null>((max, entry) => {
    const end = (entry.end ?? new Date()).getTime()
    if (max === null) return end
    return Math.max(max, end)
  }, startTime)

  const totalDuration = endTime && startTime ? Math.max(endTime - startTime, 1) : 1

  return (
    <section className="execution-timeline">
      <div className="widget-header">
        <div>
          <h2>Execution Timeline</h2>
          <p>Swim lanes show task duration per agent role.</p>
        </div>
      </div>

      <div className="timeline-body">
        {entries.length === 0 && (
          <p className="timeline-empty">Waiting for task events to build the timeline.</p>
        )}

        {roles.map((role) => (
          <div key={role} className="timeline-lane">
            <div className="lane-label">{role}</div>
            <div className="lane-bars">
              {entries
                .filter((entry) => entry.agentRole === role)
                .map((entry) => {
                  const left = startTime
                    ? ((entry.start.getTime() - startTime) / totalDuration) * 100
                    : 0
                  const endPoint = (entry.end ?? new Date()).getTime()
                  const width = ((endPoint - entry.start.getTime()) / totalDuration) * 100

                  return (
                    <div
                      key={`${entry.taskId}-${entry.agentRole}`}
                      className={`timeline-bar status-${entry.status}`}
                      style={{
                        left: `${left}%`,
                        width: `${Math.max(width, 3)}%`,
                        background: STATUS_COLOR[entry.status],
                      }}
                      title={`${entry.taskId} (${entry.status})`}
                    >
                      <span className="bar-label">{entry.taskId}</span>
                    </div>
                  )
                })}
            </div>
          </div>
        ))}
      </div>

      <div className="timeline-footer">
        <div className="legend-item">
          <span className="legend-swatch" style={{ background: STATUS_COLOR.running }} />
          <span>Running</span>
        </div>
        <div className="legend-item">
          <span className="legend-swatch" style={{ background: STATUS_COLOR.complete }} />
          <span>Complete</span>
        </div>
        <div className="legend-item">
          <span className="legend-swatch" style={{ background: STATUS_COLOR.failed }} />
          <span>Failed</span>
        </div>
        {startTime && endTime && (
          <div className="duration">
            Span: {Math.round((endTime - startTime) / 1000)}s across {entries.length} tasks
          </div>
        )}
      </div>
    </section>
  )
}
