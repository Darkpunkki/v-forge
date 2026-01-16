import { useMemo, useState } from 'react'
import type { SessionEvent } from '../../../api/controlClient'

type MultiAgentMessagesProps = {
  events: SessionEvent[]
}

type AgentMessage = {
  timestamp: string
  tick?: number
  fromAgent: string
  toAgent: string
  role?: string
  model?: string
  messageType?: string
  content: string
  blocked?: boolean
  blockReason?: string
  isStub?: boolean
}

function getAgentColor(agentId: string): string {
  // Simple hash to get consistent colors for agents
  let hash = 0
  for (let i = 0; i < agentId.length; i++) {
    hash = agentId.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue = Math.abs(hash % 360)
  return `hsl(${hue}, 70%, 45%)`
}

type ContentPayload = {
  text?: unknown
  is_stub?: unknown
}

function extractContent(
  metaContent: unknown,
  fallbackMessage: string | undefined
) {
  let contentText = ''
  let isStub = false

  if (typeof metaContent === 'string') {
    contentText = metaContent
  } else if (metaContent && typeof metaContent === 'object') {
    const payload = metaContent as ContentPayload
    if (typeof payload.text === 'string') {
      contentText = payload.text
    } else {
      try {
        contentText = JSON.stringify(metaContent)
      } catch {
        contentText = String(metaContent)
      }
    }
    if (payload.is_stub === true) {
      isStub = true
    }
  }

  if (!contentText && fallbackMessage) {
    contentText = fallbackMessage
  }

  if (contentText.includes('[STUB]')) {
    isStub = true
  }

  return { contentText, isStub }
}

function parseMessage(event: SessionEvent): AgentMessage | null {
  // Extract MESSAGE_SENT and MESSAGE_BLOCKED_BY_GRAPH events
  const eventType = event.event_type.toUpperCase()

  if (eventType === 'MESSAGE_SENT' || eventType === 'MESSAGE_BLOCKED_BY_GRAPH') {
    const meta = event.metadata || {}
    const { contentText, isStub: contentStub } = extractContent(meta.content, event.message)
    const isStub = Boolean(meta.is_stub) || contentStub
    return {
      timestamp: event.timestamp,
      tick: meta.tick_index as number | undefined,
      fromAgent: (meta.from_agent as string) || (meta.sender as string) || 'unknown',
      toAgent: (meta.to_agent as string) || (meta.recipient as string) || 'unknown',
      role: meta.role as string | undefined,
      model: meta.model as string | undefined,
      messageType: meta.message_type as string | undefined,
      content: contentText,
      blocked: eventType === 'MESSAGE_BLOCKED_BY_GRAPH',
      blockReason:
        (meta.reason as string | undefined) ||
        (meta.block_reason as string | undefined),
      isStub,
    }
  }

  return null
}

export function MultiAgentMessages({ events }: MultiAgentMessagesProps) {
  const [filterAgent, setFilterAgent] = useState<string>('ALL')
  const [showBlocked, setShowBlocked] = useState(true)

  // Extract messages from events
  const messages = useMemo(() => {
    return events
      .map(parseMessage)
      .filter((m): m is AgentMessage => m !== null)
      .reverse() // Show newest first
  }, [events])

  // Get unique agents for filter
  const agents = useMemo(() => {
    const agentSet = new Set<string>()
    messages.forEach((m) => {
      agentSet.add(m.fromAgent)
      agentSet.add(m.toAgent)
    })
    return Array.from(agentSet).sort()
  }, [messages])

  // Apply filters
  const filteredMessages = useMemo(() => {
    return messages.filter((m) => {
      if (filterAgent !== 'ALL' && m.fromAgent !== filterAgent && m.toAgent !== filterAgent) {
        return false
      }
      if (!showBlocked && m.blocked) {
        return false
      }
      return true
    })
  }, [messages, filterAgent, showBlocked])

  const hasMessages = messages.length > 0

  return (
    <div
      style={{
        background: '#f5f5f5',
        padding: '16px',
        borderRadius: '8px',
        minHeight: '200px',
        maxHeight: '500px',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <div>
          <h3 style={{ marginTop: 0, marginBottom: '4px' }}>Multi-Agent Messages</h3>
          <p style={{ fontSize: '12px', opacity: 0.7, margin: 0 }}>
            Agent-to-agent communication log
          </p>
        </div>

        {hasMessages && (
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <select
              value={filterAgent}
              onChange={(e) => setFilterAgent(e.target.value)}
              style={{
                padding: '6px 10px',
                border: '1px solid #ccc',
                borderRadius: '4px',
                fontSize: '13px',
              }}
            >
              <option value="ALL">All agents</option>
              {agents.map((agent) => (
                <option key={agent} value={agent}>
                  {agent}
                </option>
              ))}
            </select>
            <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '13px' }}>
              <input
                type="checkbox"
                checked={showBlocked}
                onChange={(e) => setShowBlocked(e.target.checked)}
              />
              Show blocked
            </label>
          </div>
        )}
      </div>

      {!hasMessages ? (
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            opacity: 0.6,
            padding: '24px',
          }}
        >
          <div style={{ fontSize: '32px', marginBottom: '12px' }}>💬</div>
          <p style={{ textAlign: 'center', margin: 0 }}>
            No agent messages yet.
          </p>
          <p style={{ textAlign: 'center', fontSize: '13px', marginTop: '8px' }}>
            Messages will appear here as agents communicate during simulation.
          </p>
        </div>
      ) : filteredMessages.length === 0 ? (
        <div
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            opacity: 0.6,
          }}
        >
          No messages match the current filters.
        </div>
      ) : (
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}
        >
          {filteredMessages.map((msg, idx) => (
            <div
              key={`${msg.timestamp}-${idx}`}
              style={{
                background: msg.blocked ? '#ffebee' : msg.isStub ? '#e3f2fd' : '#fff',
                border: msg.blocked
                  ? '1px solid #ef9a9a'
                  : msg.isStub
                    ? '1px solid #90caf9'
                    : '1px solid #e0e0e0',
                borderRadius: '8px',
                padding: '12px',
                position: 'relative',
              }}
            >
              {/* Header row */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  marginBottom: '8px',
                  flexWrap: 'wrap',
                }}
              >
                {/* From agent */}
                <span
                  style={{
                    background: getAgentColor(msg.fromAgent),
                    color: '#fff',
                    padding: '2px 8px',
                    borderRadius: '12px',
                    fontSize: '12px',
                    fontWeight: 600,
                  }}
                >
                  {msg.fromAgent}
                </span>

                {/* Arrow */}
                <span style={{ fontSize: '14px', opacity: 0.6 }}>
                  {msg.blocked ? '✕' : '→'}
                </span>

                {/* To agent */}
                <span
                  style={{
                    background: getAgentColor(msg.toAgent),
                    color: '#fff',
                    padding: '2px 8px',
                    borderRadius: '12px',
                    fontSize: '12px',
                    fontWeight: 600,
                  }}
                >
                  {msg.toAgent}
                </span>

                {/* Blocked badge */}
                {msg.blocked && (
                  <span
                    style={{
                      background: '#f97316',
                      color: '#fff',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontSize: '10px',
                      fontWeight: 600,
                    }}
                  >
                    (BLOCKED)
                  </span>
                )}

                {msg.isStub && (
                  <span
                    style={{
                      background: '#1976d2',
                      color: '#fff',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontSize: '10px',
                      fontWeight: 600,
                    }}
                  >
                    [STUB]
                  </span>
                )}

                {/* Spacer */}
                <div style={{ flex: 1 }} />

                {/* Tick */}
                {msg.tick !== undefined && (
                  <span
                    style={{
                      background: '#e3f2fd',
                      color: '#1565c0',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontSize: '11px',
                    }}
                  >
                    Tick {msg.tick}
                  </span>
                )}

                {/* Timestamp */}
                <span style={{ fontSize: '11px', opacity: 0.6 }}>
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </span>
              </div>

              {/* Meta row */}
              {(msg.role || msg.model || msg.messageType) && (
                <div
                  style={{
                    display: 'flex',
                    gap: '12px',
                    marginBottom: '8px',
                    fontSize: '12px',
                    opacity: 0.7,
                  }}
                >
                  {msg.role && <span>Role: {msg.role}</span>}
                  {msg.model && <span>Model: {msg.model}</span>}
                  {msg.messageType && <span>Type: {msg.messageType}</span>}
                </div>
              )}

              {/* Content */}
              <div
                style={{
                  fontSize: '14px',
                  lineHeight: 1.5,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {msg.content}
              </div>

              {/* Block reason */}
              {msg.blocked && msg.blockReason && (
                <div
                  style={{
                    marginTop: '8px',
                    fontSize: '12px',
                    color: '#c62828',
                    fontStyle: 'italic',
                  }}
                >
                  Reason: {msg.blockReason}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Footer */}
      <div
        style={{
          marginTop: '12px',
          paddingTop: '12px',
          borderTop: '1px solid #e0e0e0',
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '12px',
          opacity: 0.7,
        }}
      >
        <span>
          Showing {filteredMessages.length} of {messages.length} messages
        </span>
        {messages.some((m) => m.blocked) && (
          <span style={{ color: '#f44336' }}>
            {messages.filter((m) => m.blocked).length} blocked
          </span>
        )}
      </div>
    </div>
  )
}

export default MultiAgentMessages
