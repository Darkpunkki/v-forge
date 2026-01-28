import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import * as controlClient from '../../../api/controlClient'
import type { SessionEvent, TaskStatusResponse } from '../../../api/controlClient'

type ChatMessage = {
  id: string
  sender: 'user' | 'agent' | 'system'
  content: string
  timestamp: string
  status?: 'sending' | 'sent' | 'error'
}

type TaskDispatchPanelProps = {
  agentId: string | null
  agentName?: string
  agentStatus?: TaskStatusResponse | null
  agentEvents?: SessionEvent[]
  onMessageSent?: (message: ChatMessage) => void
}

function formatContent(value: unknown): string {
  if (value === null || value === undefined) return ''
  if (typeof value === 'string') return value
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

function getEventAgentId(event: SessionEvent): string | undefined {
  const metadata = event.metadata || {}
  return (metadata.agent_id as string) || (metadata.from_agent as string) || (metadata.sender as string)
}

function eventToChatMessage(event: SessionEvent, targetAgentId: string | null): ChatMessage | null {
  const type = event.event_type.toLowerCase()
  if (!type.includes('agent_response') && !type.includes('agent_error') && !type.includes('agent_progress')) {
    return null
  }

  const eventAgentId = getEventAgentId(event)
  if (targetAgentId && eventAgentId && targetAgentId !== eventAgentId) {
    return null
  }

  const metadata = event.metadata || {}
  const content =
    metadata.content ??
    metadata.progress_text ??
    metadata.error ??
    event.message

  const messageText = formatContent(content)
  if (!messageText) return null

  return {
    id: `event-${event.timestamp}-${event.event_type}-${String(metadata.message_id || '')}`,
    sender: type.includes('agent_error') ? 'system' : 'agent',
    content: messageText,
    timestamp: event.timestamp,
    status: 'sent',
  }
}

export function TaskDispatchPanel({
  agentId,
  agentName,
  agentStatus,
  agentEvents,
  onMessageSent,
}: TaskDispatchPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [draft, setDraft] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [sending, setSending] = useState(false)
  const [autoScroll, setAutoScroll] = useState(true)
  const [hasDispatched, setHasDispatched] = useState(false)
  const logRef = useRef<HTMLDivElement>(null)
  const seenEventIds = useRef<Set<string>>(new Set())

  useEffect(() => {
    setMessages([])
    setDraft('')
    setError(null)
    setHasDispatched(false)
    seenEventIds.current = new Set()
  }, [agentId])

  useEffect(() => {
    if (!agentStatus) return
    const status = agentStatus.status.toLowerCase()
    if (status === 'dispatched' || status === 'running') {
      setHasDispatched(true)
    }
  }, [agentStatus])

  useEffect(() => {
    if (!agentEvents || agentEvents.length === 0) return

    const nextMessages: ChatMessage[] = []
    agentEvents.forEach((event) => {
      const candidate = eventToChatMessage(event, agentId)
      if (!candidate) return
      if (seenEventIds.current.has(candidate.id)) return
      seenEventIds.current.add(candidate.id)
      nextMessages.push(candidate)
    })

    if (nextMessages.length > 0) {
      setMessages((prev) => [...prev, ...nextMessages])
    }
  }, [agentEvents, agentId])

  useEffect(() => {
    if (autoScroll && logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [messages, autoScroll])

  const isBusy = useMemo(() => {
    const status = agentStatus?.status?.toLowerCase() || ''
    return status === 'busy' || status === 'running' || status === 'dispatched'
  }, [agentStatus?.status])

  const statusLabel = agentStatus?.status || 'unknown'

  const handleSend = async (event: FormEvent) => {
    event.preventDefault()
    if (!agentId) return
    const content = draft.trim()
    if (!content) return

    setSending(true)
    setError(null)

    const messageId = `local-${Date.now()}-${Math.floor(Math.random() * 100000)}`
    const outgoing: ChatMessage = {
      id: messageId,
      sender: 'user',
      content,
      timestamp: new Date().toISOString(),
      status: 'sending',
    }

    setMessages((prev) => [...prev, outgoing])
    setDraft('')

    try {
      if (!hasDispatched) {
        await controlClient.dispatchTask(agentId, content)
        setHasDispatched(true)
      } else {
        await controlClient.sendFollowUp(agentId, content)
      }

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId
            ? { ...msg, status: 'sent' }
            : msg
        )
      )
      onMessageSent?.({ ...outgoing, status: 'sent' })
    } catch (err: any) {
      const message = err?.detail || err?.message || 'Failed to send message'
      setError(message)
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId
            ? { ...msg, status: 'error' }
            : msg
        )
      )
    } finally {
      setSending(false)
    }
  }

  if (!agentId) {
    return (
      <section
        style={{
          background: '#f5f5f5',
          border: '1px solid #e0e0e0',
          borderRadius: '10px',
          padding: '16px',
        }}
      >
        <h3 style={{ marginTop: 0 }}>Dispatch Tasks</h3>
        <p style={{ margin: 0, opacity: 0.7 }}>
          Select an agent to start sending tasks.
        </p>
      </section>
    )
  }

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
        minHeight: '360px',
      }}
    >
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ margin: 0 }}>Dispatch Tasks</h3>
          <p style={{ margin: 0, fontSize: '12px', opacity: 0.7 }}>
            Talking to {agentName || agentId}
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              fontSize: '12px',
              padding: '4px 8px',
              borderRadius: '999px',
              background: isBusy ? '#bbdefb' : '#e0e0e0',
              color: isBusy ? '#0d47a1' : '#424242',
              fontWeight: 600,
              textTransform: 'uppercase',
            }}
          >
            {isBusy ? 'busy' : statusLabel}
          </span>
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
          flex: 1,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
          padding: '8px 2px',
        }}
      >
        {messages.length === 0 ? (
          <div style={{ opacity: 0.6, fontSize: '13px' }}>
            No messages yet. Dispatch a task to start the conversation.
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              style={{
                alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '80%',
                background:
                  msg.sender === 'user'
                    ? '#212121'
                    : msg.sender === 'system'
                      ? '#ffebee'
                      : '#fff',
                color: msg.sender === 'user' ? '#fff' : '#1f2937',
                border: '1px solid #e0e0e0',
                borderRadius: '10px',
                padding: '10px 12px',
                boxShadow: '0 1px 2px rgba(0,0,0,0.08)',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              <div style={{ fontSize: '12px', opacity: 0.7, marginBottom: '4px' }}>
                {msg.sender === 'user' ? 'You' : agentName || agentId}
                {' - '}
                {new Date(msg.timestamp).toLocaleTimeString()}
              </div>
              <div style={{ fontSize: '14px', lineHeight: 1.4 }}>{msg.content}</div>
              {msg.status && msg.sender === 'user' && (
                <div style={{ marginTop: '6px', fontSize: '11px', opacity: 0.6 }}>
                  {msg.status}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {isBusy && (
        <div
          style={{
            fontSize: '12px',
            color: '#0d47a1',
            background: '#e3f2fd',
            padding: '6px 10px',
            borderRadius: '6px',
          }}
        >
          Agent is working on the current task...
        </div>
      )}

      <form onSubmit={handleSend} style={{ display: 'flex', gap: '8px' }}>
        <input
          type="text"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder={hasDispatched ? 'Send a follow-up...' : 'Describe the task...'}
          style={{
            flex: 1,
            padding: '10px 12px',
            borderRadius: '6px',
            border: '1px solid #ccc',
          }}
          disabled={sending}
        />
        <button
          type="submit"
          disabled={sending || !draft.trim()}
          style={{
            padding: '10px 14px',
            borderRadius: '6px',
            border: '1px solid #111',
            background: sending ? '#ddd' : '#111',
            color: sending ? '#555' : '#fff',
            fontWeight: 600,
            cursor: sending ? 'not-allowed' : 'pointer',
          }}
        >
          {sending ? 'Sending...' : hasDispatched ? 'Follow up' : 'Dispatch'}
        </button>
      </form>
    </section>
  )
}

export default TaskDispatchPanel
