import { useEffect, useState } from 'react'
import {
  listAllSessions,
  getActiveSessions,
  getSessionStatus,
  streamSessionEvents,
  type SessionListItem,
  type ActiveSessionItem,
  type SessionStatusResponse,
  type SessionEvent,
} from '../api/controlClient'

export function ControlPanelScreen() {
  const [allSessions, setAllSessions] = useState<SessionListItem[]>([])
  const [activeSessions, setActiveSessions] = useState<ActiveSessionItem[]>([])
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
  const [sessionStatus, setSessionStatus] = useState<SessionStatusResponse | null>(null)
  const [sessionEvents, setSessionEvents] = useState<SessionEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingSession, setLoadingSession] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sseError, setSseError] = useState<string | null>(null)

  // Load all sessions and active sessions on mount
  useEffect(() => {
    async function loadData() {
      setLoading(true)
      setError(null)
      try {
        const [allData, activeData] = await Promise.all([
          listAllSessions(),
          getActiveSessions(),
        ])
        setAllSessions(allData.sessions)
        setActiveSessions(activeData.active_sessions)
      } catch (err: any) {
        setError(err.message || String(err))
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  // Load session status and events when a session is selected
  useEffect(() => {
    if (!selectedSessionId) {
      setSessionStatus(null)
      setSessionEvents([])
      setSseError(null)
      setLoadingSession(false)
      return
    }

    // Clear events immediately when switching sessions
    setSessionEvents([])
    setSseError(null)
    setLoadingSession(true)

    // Capture sessionId to fix TypeScript null error and prevent race conditions
    const sessionId = selectedSessionId
    let cancelled = false

    async function loadSessionDetails() {
      try {
        const status = await getSessionStatus(sessionId)
        if (!cancelled) {
          setSessionStatus(status)
          setLoadingSession(false)
        }
      } catch (err: any) {
        console.error('Failed to load session status:', err)
        if (!cancelled) {
          setLoadingSession(false)
        }
      }
    }

    loadSessionDetails()

    // Set up SSE for real-time events
    const eventSource = streamSessionEvents(sessionId)

    const handleEvent = (e: MessageEvent) => {
      if (!cancelled) {
        const event: SessionEvent = JSON.parse(e.data)
        setSessionEvents((prev) => [...prev, event])
      }
    }

    eventSource.addEventListener('session_event', handleEvent)

    eventSource.onerror = (err) => {
      console.error('SSE error:', err)
      if (!cancelled) {
        setSseError('Real-time updates disconnected')
      }
      eventSource.close()
    }

    return () => {
      cancelled = true
      eventSource.removeEventListener('session_event', handleEvent)
      eventSource.close()
    }
  }, [selectedSessionId])

  if (loading) {
    return (
      <div style={{ padding: '24px' }}>
        <h1>Control Panel</h1>
        <p>Loading sessions...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ padding: '24px' }}>
        <h1>Control Panel</h1>
        <pre style={{ background: '#fee', padding: 12 }}>{error}</pre>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      {/* Sidebar */}
      <aside style={{
        width: '300px',
        borderRight: '1px solid #ddd',
        padding: '16px',
        overflowY: 'auto',
      }}>
        <h2 style={{ marginTop: 0 }}>Sessions</h2>

        <section style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '14px', opacity: 0.7, textTransform: 'uppercase' }}>
            Active ({activeSessions.length})
          </h3>
          {activeSessions.length === 0 ? (
            <p style={{ fontSize: '14px', opacity: 0.6 }}>No active sessions</p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {activeSessions.map((session) => (
                <li
                  key={session.session_id}
                  style={{
                    padding: '8px',
                    marginBottom: '4px',
                    background: selectedSessionId === session.session_id ? '#e3f2fd' : '#f5f5f5',
                    cursor: 'pointer',
                    borderRadius: '4px',
                  }}
                  onClick={() => setSelectedSessionId(session.session_id)}
                >
                  <div style={{ fontSize: '12px', fontWeight: 'bold' }}>
                    {session.session_id}
                  </div>
                  <div style={{ fontSize: '11px', opacity: 0.7 }}>
                    {session.phase}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section>
          <h3 style={{ fontSize: '14px', opacity: 0.7, textTransform: 'uppercase' }}>
            All Sessions ({allSessions.length})
          </h3>
          {allSessions.length === 0 ? (
            <p style={{ fontSize: '14px', opacity: 0.6 }}>No sessions found</p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {allSessions.map((session) => (
                <li
                  key={session.session_id}
                  style={{
                    padding: '8px',
                    marginBottom: '4px',
                    background: selectedSessionId === session.session_id ? '#e3f2fd' : '#f5f5f5',
                    cursor: 'pointer',
                    borderRadius: '4px',
                  }}
                  onClick={() => setSelectedSessionId(session.session_id)}
                >
                  <div style={{ fontSize: '12px', fontWeight: 'bold' }}>
                    {session.session_id}
                  </div>
                  <div style={{ fontSize: '11px', opacity: 0.7 }}>
                    {session.phase}
                  </div>
                  <div style={{ fontSize: '10px', opacity: 0.5 }}>
                    {new Date(session.updated_at).toLocaleString()}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </aside>

      {/* Main content */}
      <main style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
        <header style={{ marginBottom: '24px' }}>
          <h1 style={{ marginTop: 0 }}>Control Panel</h1>
          <p style={{ opacity: 0.7 }}>
            Real-time session monitoring and observability
          </p>
        </header>

        {!selectedSessionId ? (
          <div style={{ padding: '48px', textAlign: 'center', opacity: 0.6 }}>
            <p>Select a session from the sidebar to view details</p>
          </div>
        ) : (
          <>
            {/* SSE Error Notification */}
            {sseError && (
              <div style={{
                background: '#fff3cd',
                border: '1px solid #ffc107',
                color: '#856404',
                padding: '12px 16px',
                borderRadius: '4px',
                marginBottom: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}>
                <span>⚠️</span>
                <span>{sseError}</span>
              </div>
            )}

            {/* Loading State */}
            {loadingSession ? (
              <div style={{ padding: '48px', textAlign: 'center', opacity: 0.6 }}>
                <p>Loading session details...</p>
              </div>
            ) : (
              <>
                {/* Session Status */}
                {sessionStatus && (
                  <section style={{ marginBottom: '32px' }}>
                    <h2>Session Status</h2>
                <div style={{
                  background: '#f5f5f5',
                  padding: '16px',
                  borderRadius: '8px',
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '16px',
                }}>
                  <div>
                    <div style={{ fontSize: '12px', opacity: 0.7, textTransform: 'uppercase' }}>
                      Session ID
                    </div>
                    <div style={{ fontWeight: 'bold' }}>{sessionStatus.session_id}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', opacity: 0.7, textTransform: 'uppercase' }}>
                      Phase
                    </div>
                    <div style={{ fontWeight: 'bold' }}>{sessionStatus.phase}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', opacity: 0.7, textTransform: 'uppercase' }}>
                      Active Task
                    </div>
                    <div style={{ fontWeight: 'bold' }}>
                      {sessionStatus.active_task_id || '—'}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', opacity: 0.7, textTransform: 'uppercase' }}>
                      Completed Tasks
                    </div>
                    <div style={{ fontWeight: 'bold' }}>{sessionStatus.completed_tasks}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', opacity: 0.7, textTransform: 'uppercase' }}>
                      Failed Tasks
                    </div>
                    <div style={{ fontWeight: 'bold', color: sessionStatus.failed_tasks > 0 ? '#d32f2f' : 'inherit' }}>
                      {sessionStatus.failed_tasks}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', opacity: 0.7, textTransform: 'uppercase' }}>
                      Updated At
                    </div>
                    <div style={{ fontSize: '14px' }}>
                      {new Date(sessionStatus.updated_at).toLocaleString()}
                    </div>
                  </div>
                </div>
              </section>
            )}

            {/* Event Stream */}
            <section>
              <h2>Event Stream</h2>
              {sessionEvents.length === 0 ? (
                <p style={{ opacity: 0.6 }}>No events yet (listening for real-time updates...)</p>
              ) : (
                <div style={{
                  background: '#fafafa',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  maxHeight: '500px',
                  overflowY: 'auto',
                }}>
                  {sessionEvents.map((event, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '12px 16px',
                        borderBottom: idx < sessionEvents.length - 1 ? '1px solid #eee' : 'none',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span style={{
                          fontSize: '11px',
                          fontWeight: 'bold',
                          textTransform: 'uppercase',
                          color: '#1976d2',
                        }}>
                          {event.event_type.replace(/_/g, ' ')}
                        </span>
                        <span style={{ fontSize: '11px', opacity: 0.6 }}>
                          {new Date(event.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <div style={{ fontSize: '14px', marginBottom: '4px' }}>
                        {event.message}
                      </div>
                      {(event.phase || event.task_id) && (
                        <div style={{ fontSize: '12px', opacity: 0.7 }}>
                          {event.phase && <span>Phase: {event.phase}</span>}
                          {event.phase && event.task_id && <span> | </span>}
                          {event.task_id && <span>Task: {event.task_id}</span>}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>
              </>
            )}
          </>
        )}
      </main>
    </div>
  )
}
