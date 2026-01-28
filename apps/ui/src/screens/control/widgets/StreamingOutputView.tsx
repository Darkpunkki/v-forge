import { useEffect, useMemo, useRef, useState } from 'react'
import { streamAgentEvents, type SessionEvent } from '../../../api/controlClient'

type StreamingOutputViewProps = {
  agentId: string | null
  height?: number | string
}

type EventKind = 'message' | 'tool' | 'status' | 'error' | 'info'

type StatusBadge = {
  label: string
  tone: 'connected' | 'busy' | 'idle' | 'disconnected' | 'error'
}

const STATUS_COLORS: Record<StatusBadge['tone'], { bg: string; fg: string }> = {
  connected: { bg: '#e8f5e9', fg: '#2e7d32' },
  busy: { bg: '#e3f2fd', fg: '#0d47a1' },
  idle: { bg: '#f5f5f5', fg: '#424242' },
  disconnected: { bg: '#ffebee', fg: '#c62828' },
  error: { bg: '#ffebee', fg: '#b71c1c' },
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return ''
  if (typeof value === 'string') return value
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

function getAgentLabel(event: SessionEvent): string {
  const metadata = event.metadata || {}
  return (
    (metadata.agent_id as string) ||
    (metadata.from_agent as string) ||
    (metadata.sender as string) ||
    'agent'
  )
}

function getEventKind(event: SessionEvent): EventKind {
  const type = event.event_type.toLowerCase()
  if (type.includes('error') || type.includes('failed')) return 'error'
  if (type.includes('tool')) return 'tool'
  if (type.includes('connected') || type.includes('disconnected') || type.includes('progress') || type.includes('dispatch')) {
    return 'status'
  }
  if (type.includes('response') || type.includes('message')) return 'message'
  return 'info'
}

function getStatusBadge(event: SessionEvent): StatusBadge | null {
  const type = event.event_type.toLowerCase()
  if (type.includes('connected')) return { label: 'connected', tone: 'connected' }
  if (type.includes('disconnected')) return { label: 'disconnected', tone: 'disconnected' }
  if (type.includes('task_dispatched') || type.includes('progress')) return { label: 'busy', tone: 'busy' }
  if (type.includes('agent_response')) return { label: 'idle', tone: 'idle' }
  if (type.includes('agent_error')) return { label: 'error', tone: 'error' }
  return null
}

function extractToolInfo(event: SessionEvent): { name?: string; result?: string } | null {
  const metadata = event.metadata || {}
  const name =
    (metadata.tool_name as string) ||
    (metadata.tool as string) ||
    (metadata.name as string)
  const result =
    (metadata.result as string) ||
    (metadata.output as string) ||
    (metadata.response as string)
  if (!name && !result) return null
  return { name, result }
}

export function StreamingOutputView({ agentId, height = 360 }: StreamingOutputViewProps) {
  const [events, setEvents] = useState<SessionEvent[]>([])
  const [error, setError] = useState<string | null>(null)
  const [autoScroll, setAutoScroll] = useState(true)
  const logRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!agentId) {
      setEvents([])
      setError(null)
      return
    }

    let cancelled = false
    setEvents([])
    setError(null)

    const eventSource = streamAgentEvents(agentId)

    const handleEvent = (event: MessageEvent) => {
      if (cancelled) return
      try {
        const parsed: SessionEvent = JSON.parse(event.data)
        setEvents((prev) => {
          const next = [...prev, parsed]
          return next.length > 500 ? next.slice(next.length - 500) : next
        })
      } catch (parseErr) {
        console.error('Failed to parse SSE event:', parseErr, event.data)
      }
    }

    eventSource.addEventListener('agent_event', handleEvent)

    eventSource.onerror = () => {
      if (!cancelled) {
        setError('Live stream disconnected')
      }
      eventSource.close()
    }

    return () => {
      cancelled = true
      eventSource.removeEventListener('agent_event', handleEvent)
      eventSource.close()
    }
  }, [agentId])

  useEffect(() => {
    if (autoScroll && logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [events, autoScroll])

  const eventSummaries = useMemo(() => {
    return events.map((event) => {
      const kind = getEventKind(event)
      const agentLabel = getAgentLabel(event)
      const badge = getStatusBadge(event)
      const toolInfo = kind === 'tool' ? extractToolInfo(event) : null
      const metadata = event.metadata || {}
      const content =
        metadata.content ??
        metadata.progress_text ??
        metadata.error ??
        metadata.message ??
        event.message

      return {
        event,
        kind,
        agentLabel,
        badge,
        toolInfo,
        content: formatValue(content),
      }
    })
  }, [events])

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
          <h3 style={{ margin: 0 }}>Streaming Output</h3>
          <p style={{ margin: 0, fontSize: '12px', opacity: 0.7 }}>
            Real-time agent events and responses.
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            type="button"
            onClick={() => setAutoScroll((prev) => !prev)}
            style={{
              fontSize: '12px',
              padding: '4px 8px',
              borderRadius: '6px',
              border: '1px solid #ccc',
              background: '#fff',
              cursor: 'pointer',
            }}
          >
            {autoScroll ? 'Pause' : 'Resume'}
          </button>
        </div>
      </header>

      {!agentId && (
        <div style={{ opacity: 0.7, fontSize: '13px' }}>
          Select an agent to view live output.
        </div>
      )}

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
        ref={logRef}
        style={{
          minHeight: typeof height === 'number' ? `${height}px` : height,
          maxHeight: typeof height === 'number' ? `${height}px` : height,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
          paddingRight: '4px',
        }}
      >
        {agentId && eventSummaries.length === 0 ? (
          <div style={{ opacity: 0.6, fontSize: '13px' }}>
            Waiting for agent events...
          </div>
        ) : (
          eventSummaries.map(({ event, kind, agentLabel, badge, toolInfo, content }) => (
            <div
              key={`${event.timestamp}-${event.event_type}`}
              style={{
                background: kind === 'error' ? '#ffebee' : '#fff',
                border: '1px solid #e0e0e0',
                borderRadius: '8px',
                padding: '10px 12px',
                display: 'flex',
                flexDirection: 'column',
                gap: '6px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                  <span
                    style={{
                      fontSize: '11px',
                      textTransform: 'uppercase',
                      letterSpacing: '0.4px',
                      background: '#e0e0e0',
                      padding: '2px 6px',
                      borderRadius: '999px',
                    }}
                  >
                    {event.event_type.replace(/_/g, ' ')}
                  </span>
                  <span style={{ fontSize: '12px', fontWeight: 600 }}>{agentLabel}</span>
                  {badge && (
                    <span
                      style={{
                        fontSize: '11px',
                        padding: '2px 6px',
                        borderRadius: '999px',
                        background: STATUS_COLORS[badge.tone].bg,
                        color: STATUS_COLORS[badge.tone].fg,
                        fontWeight: 600,
                        textTransform: 'uppercase',
                      }}
                    >
                      {badge.label}
                    </span>
                  )}
                </div>
                <span style={{ fontSize: '11px', opacity: 0.6 }}>
                  {new Date(event.timestamp).toLocaleTimeString()}
                </span>
              </div>

              {kind === 'tool' && toolInfo ? (
                <div
                  style={{
                    background: '#f1f8e9',
                    border: '1px solid #dcedc8',
                    borderRadius: '6px',
                    padding: '8px',
                    fontSize: '13px',
                  }}
                >
                  <div style={{ fontWeight: 600, marginBottom: '4px' }}>
                    Tool call: {toolInfo.name || 'unnamed'}
                  </div>
                  {toolInfo.result && (
                    <div style={{ whiteSpace: 'pre-wrap' }}>{toolInfo.result}</div>
                  )}
                </div>
              ) : (
                content && (
                  <div style={{ fontSize: '14px', whiteSpace: 'pre-wrap' }}>{content}</div>
                )
              )}

              {event.metadata && Object.keys(event.metadata).length > 0 && (
                <details style={{ fontSize: '12px', opacity: 0.8 }}>
                  <summary>Metadata</summary>
                  <pre style={{ margin: 0 }}>{formatValue(event.metadata)}</pre>
                </details>
              )}
            </div>
          ))
        )}
      </div>

      {agentId && (
        <div style={{ fontSize: '12px', opacity: 0.6 }}>
          Showing {eventSummaries.length} events
        </div>
      )}
    </section>
  )
}

export default StreamingOutputView
