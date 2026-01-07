import { useEffect, useMemo, useRef, useState } from 'react'

import type { SessionEvent } from '../../../api/controlClient'
import './EventStream.css'

type EventStreamProps = {
  events: SessionEvent[]
  sessionId: string | null
  onClear?: () => void
}

type Severity = 'all' | 'info' | 'success' | 'warning' | 'error'

type FilterOption = {
  label: string
  value: string
}

function normalizeValue(value?: string | null) {
  return value?.trim() || ''
}

function getSeverity(event: SessionEvent): Exclude<Severity, 'all'> {
  const type = event.event_type.toLowerCase()
  const status = String(event.metadata?.status ?? event.metadata?.decision ?? '').toLowerCase()

  if (type.includes('fail') || type.includes('error') || status === 'block') return 'error'
  if (type.includes('warn') || status === 'warn') return 'warning'
  if (type.includes('complete') || type.includes('pass') || status === 'pass') return 'success'
  return 'info'
}

function buildOptions(values: string[], placeholder: string): FilterOption[] {
  return [{ label: placeholder, value: 'ALL' }].concat(
    values.map((value) => ({ label: value, value }))
  )
}

export default function EventStream({ events, sessionId, onClear }: EventStreamProps) {
  const [typeFilter, setTypeFilter] = useState('ALL')
  const [phaseFilter, setPhaseFilter] = useState('ALL')
  const [agentFilter, setAgentFilter] = useState('ALL')
  const [severityFilter, setSeverityFilter] = useState<Severity>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [autoScroll, setAutoScroll] = useState(true)
  const logRef = useRef<HTMLDivElement>(null)

  const eventTypes = useMemo(() => {
    const types = Array.from(new Set(events.map((event) => event.event_type))).sort()
    return buildOptions(types, 'All event types')
  }, [events])

  const phaseOptions = useMemo(() => {
    const phases = Array.from(
      new Set(
        events
          .map((event) => normalizeValue(event.phase || (event.metadata?.phase as string)))
          .filter(Boolean)
      )
    ).sort()
    return buildOptions(phases, 'All phases')
  }, [events])

  const agentOptions = useMemo(() => {
    const agents = Array.from(
      new Set(
        events
          .map((event) =>
            normalizeValue(
              (event.metadata?.agent_role as string) || (event.metadata?.role as string)
            )
          )
          .filter(Boolean)
      )
    ).sort()
    return buildOptions(agents, 'All agents')
  }, [events])

  const filteredEvents = useMemo(() => {
    const query = searchQuery.trim().toLowerCase()

    return events.filter((event) => {
      if (typeFilter !== 'ALL' && event.event_type !== typeFilter) return false

      if (phaseFilter !== 'ALL') {
        const phase = normalizeValue(event.phase || (event.metadata?.phase as string))
        if (phase !== phaseFilter) return false
      }

      if (agentFilter !== 'ALL') {
        const agent = normalizeValue(
          (event.metadata?.agent_role as string) || (event.metadata?.role as string)
        )
        if (agent !== agentFilter) return false
      }

      if (severityFilter !== 'all' && getSeverity(event) !== severityFilter) return false

      if (!query) return true

      const metadataText = JSON.stringify(event.metadata ?? {}).toLowerCase()
      return [event.message, event.task_id, event.session_id, metadataText]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(query))
    })
  }, [events, typeFilter, phaseFilter, agentFilter, severityFilter, searchQuery])

  useEffect(() => {
    if (autoScroll && logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [filteredEvents, autoScroll])

  const handleExport = () => {
    const blob = new Blob([JSON.stringify(filteredEvents, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `event-stream-${sessionId ?? 'session'}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <section className="event-stream">
      <header className="event-stream__header">
        <div>
          <h2>Event Stream</h2>
          <p>Filter and search real-time events for the selected session.</p>
        </div>
        <div className="event-stream__controls">
          <select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}>
            {eventTypes.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <select value={phaseFilter} onChange={(event) => setPhaseFilter(event.target.value)}>
            {phaseOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <select value={agentFilter} onChange={(event) => setAgentFilter(event.target.value)}>
            {agentOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <select
            value={severityFilter}
            onChange={(event) => setSeverityFilter(event.target.value as Severity)}
          >
            <option value="all">All severities</option>
            <option value="info">Info</option>
            <option value="success">Success</option>
            <option value="warning">Warning</option>
            <option value="error">Error</option>
          </select>
          <input
            type="search"
            placeholder="Search events"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
          />
          <label className="event-stream__toggle">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(event) => setAutoScroll(event.target.checked)}
            />
            Auto-scroll
          </label>
          <button type="button" onClick={() => onClear?.()}>
            Clear
          </button>
          <button type="button" onClick={handleExport} disabled={filteredEvents.length === 0}>
            Export JSON
          </button>
        </div>
      </header>

      {sessionId === null ? (
        <div className="event-stream__empty">Select a session to view events.</div>
      ) : (
        <div className="event-stream__body" ref={logRef}>
          {filteredEvents.length === 0 ? (
            <div className="event-stream__empty">
              {events.length === 0 ? 'Waiting for events...' : 'No events match the current filters.'}
            </div>
          ) : (
            <ul className="event-stream__list">
              {filteredEvents.map((event, index) => (
                <li key={`${event.timestamp}-${index}`} className={`event-stream__item ${getSeverity(event)}`}>
                  <div className="event-stream__item-header">
                    <span className="event-stream__type">
                      {event.event_type.replace(/_/g, ' ')}
                    </span>
                    <span className="event-stream__time">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="event-stream__message">{event.message}</div>
                  <div className="event-stream__meta">
                    {event.phase && <span>Phase: {event.phase}</span>}
                    {(event.metadata?.agent_role || event.metadata?.role) && (
                      <span>
                        Agent: {event.metadata?.agent_role ?? event.metadata?.role}
                      </span>
                    )}
                    {event.task_id && <span>Task: {event.task_id}</span>}
                  </div>
                  {event.metadata && Object.keys(event.metadata).length > 0 && (
                    <details className="event-stream__details">
                      <summary>Metadata</summary>
                      <pre>{JSON.stringify(event.metadata, null, 2)}</pre>
                    </details>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      <footer className="event-stream__footer">
        <span>
          Showing {filteredEvents.length} of {events.length} events
        </span>
      </footer>
    </section>
  )
}
