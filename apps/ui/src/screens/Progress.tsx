import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getProgress } from '../api/client'
import type { ProgressResponse, SessionPhase } from '../types/api'

const TERMINAL_PHASES: SessionPhase[] = ['COMPLETE', 'FAILED']

export function ProgressScreen() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [progress, setProgress] = useState<ProgressResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const logsEndRef = useRef<HTMLDivElement>(null)

  // Prevent repeated navigations on polling ticks
  const hasNavigatedRef = useRef(false)

  async function loadProgress() {
    if (!sessionId) return
    if (hasNavigatedRef.current) return

    setError(null)
    if (!progress) setLoading(true)

    try {
      const p = await getProgress(sessionId)
      setProgress(p)

      // Phase-driven routing
      if (p.phase === 'PLAN_REVIEW') {
        hasNavigatedRef.current = true
        navigate(`/plan/${sessionId}`, { replace: true })
        return
      }

      if (p.phase === 'CLARIFICATION') {
        hasNavigatedRef.current = true
        navigate(`/clarification/${sessionId}`, { replace: true })
        return
      }

      if (TERMINAL_PHASES.includes(p.phase)) {
        hasNavigatedRef.current = true
        navigate(`/result/${sessionId}`, { replace: true })
        return
      }
    } catch (err: any) {
      // ApiError uses .detail; fallback to message
      setError(err?.detail || err?.message || String(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    hasNavigatedRef.current = false

    loadProgress()

    const interval = setInterval(loadProgress, 2000)
    return () => clearInterval(interval)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId])

  // Auto-scroll logs to bottom
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [progress?.logs])

  if (loading && !progress) {
    return <div>Loading progress...</div>
  }

  if (error) {
    return (
      <div>
        <h2>Error</h2>
        <pre style={{ background: '#fee', padding: 12 }}>{error}</pre>
        <button onClick={() => navigate('/')}>Back to Home</button>
      </div>
    )
  }

  if (!progress) {
    return <div>No progress available</div>
  }

  // Basic progress computation (stable & readable)
  const completedCount = progress.completed_tasks.length
  const failedCount = progress.failed_tasks.length
  const activeCount = progress.active_task ? 1 : 0
  const totalKnown = completedCount + failedCount + activeCount
  const progressPercent = totalKnown > 0 ? Math.round((completedCount / totalKnown) * 100) : 0

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      <h1>Building Your App</h1>

      {/* Phase Indicator */}
      <div
        style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          padding: 24,
          borderRadius: 12,
          marginBottom: 24,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: 14, opacity: 0.9, marginBottom: 4 }}>Current Phase</div>
            <div style={{ fontSize: 28, fontWeight: 600 }}>{progress.phase}</div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 14, opacity: 0.9, marginBottom: 4 }}>Progress</div>
            <div style={{ fontSize: 28, fontWeight: 600 }}>{progressPercent}%</div>
          </div>
        </div>

        {totalKnown > 0 && (
          <div style={{ marginTop: 16, background: 'rgba(255,255,255,0.2)', borderRadius: 8, height: 8, overflow: 'hidden' }}>
            <div style={{ background: 'white', height: '100%', width: `${progressPercent}%`, transition: 'width 0.3s ease' }} />
          </div>
        )}
      </div>

      {/* Active Task */}
      {progress.active_task && (
        <div style={{ background: '#fff3cd', border: '2px solid #ffc107', padding: 20, borderRadius: 12, marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ fontSize: 24 }}>⚙️</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 14, color: '#856404', fontWeight: 600, marginBottom: 4 }}>ACTIVE TASK</div>
              <div style={{ fontSize: 18, fontWeight: 600, color: '#333' }}>{progress.active_task.title}</div>
              <div style={{ fontSize: 14, color: '#856404', marginTop: 4 }}>Status: {progress.active_task.status}</div>
            </div>
            <div style={{ fontSize: 32, animation: 'spin 2s linear infinite' }}>⟳</div>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
        {/* Timeline */}
        <div>
          <h2 style={{ fontSize: 20, marginBottom: 16 }}>Task Timeline</h2>
          <div style={{ background: '#fafafa', border: '1px solid #ddd', borderRadius: 12, padding: 20 }}>
            {progress.completed_tasks.length === 0 && !progress.active_task && progress.failed_tasks.length === 0 && (
              <p style={{ color: '#999', fontStyle: 'italic' }}>No tasks yet</p>
            )}

            {progress.completed_tasks.map((task) => (
              <div key={task.task_id} style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 16 }}>
                <div style={{ fontSize: 20, flexShrink: 0 }}>✅</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, color: '#28a745' }}>{task.title}</div>
                  <div style={{ fontSize: 12, color: '#666', marginTop: 2 }}>Completed</div>
                </div>
              </div>
            ))}

            {progress.active_task && (
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 16 }}>
                <div style={{ fontSize: 20, flexShrink: 0, animation: 'pulse 1.5s ease-in-out infinite' }}>🔄</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, color: '#0070f3' }}>{progress.active_task.title}</div>
                  <div style={{ fontSize: 12, color: '#666', marginTop: 2 }}>In Progress...</div>
                </div>
              </div>
            )}

            {progress.failed_tasks.map((task) => (
              <div key={task.task_id} style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 16 }}>
                <div style={{ fontSize: 20, flexShrink: 0 }}>❌</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, color: '#dc3545' }}>{task.title}</div>
                  <div style={{ fontSize: 12, color: '#666', marginTop: 2 }}>Failed</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Logs */}
        <div>
          <h2 style={{ fontSize: 20, marginBottom: 16 }}>Live Logs</h2>
          <div
            style={{
              background: '#1e1e1e',
              color: '#d4d4d4',
              borderRadius: 12,
              padding: 16,
              maxHeight: 500,
              overflow: 'auto',
              fontFamily: 'monospace',
              fontSize: 13,
              lineHeight: 1.6,
            }}
          >
            {progress.logs.length === 0 ? (
              <div style={{ color: '#888', fontStyle: 'italic' }}>No logs yet...</div>
            ) : (
              <>
                {progress.logs.map((log, idx) => (
                  <div key={idx} style={{ marginBottom: 4 }}>
                    {log}
                  </div>
                ))}
                <div ref={logsEndRef} />
              </>
            )}
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
        <div style={{ background: '#d4edda', padding: 16, borderRadius: 8, textAlign: 'center' }}>
          <div style={{ fontSize: 32, fontWeight: 700, color: '#155724' }}>{completedCount}</div>
          <div style={{ fontSize: 14, color: '#155724', marginTop: 4 }}>Completed</div>
        </div>
        <div style={{ background: '#fff3cd', padding: 16, borderRadius: 8, textAlign: 'center' }}>
          <div style={{ fontSize: 32, fontWeight: 700, color: '#856404' }}>{activeCount}</div>
          <div style={{ fontSize: 14, color: '#856404', marginTop: 4 }}>In Progress</div>
        </div>
        <div style={{ background: '#f8d7da', padding: 16, borderRadius: 8, textAlign: 'center' }}>
          <div style={{ fontSize: 32, fontWeight: 700, color: '#721c24' }}>{failedCount}</div>
          <div style={{ fontSize: 14, color: '#721c24', marginTop: 4 }}>Failed</div>
        </div>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}
