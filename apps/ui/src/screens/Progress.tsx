import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getProgress } from '../api/client'
import type { ProgressResponse } from '../types/api'

export function ProgressScreen() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [progress, setProgress] = useState<ProgressResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function loadProgress() {
    if (!sessionId) return

    setError(null)
    setLoading(true)

    try {
      const p = await getProgress(sessionId)
      setProgress(p)
    } catch (err: any) {
      setError(err.message || String(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProgress()
    // Poll for updates every 2 seconds
    const interval = setInterval(loadProgress, 2000)
    return () => clearInterval(interval)
  }, [sessionId])

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

  return (
    <div>
      <div style={{ border: '1px solid #ddd', borderRadius: 12, padding: 16 }}>
        <h2 style={{ marginTop: 0 }}>Session Progress</h2>
        <p>
          <strong>Phase:</strong> {progress.phase}
        </p>

        {progress.active_task && (
          <div style={{ background: '#fff3cd', padding: 12, borderRadius: 6, marginBottom: 16 }}>
            <h3 style={{ marginTop: 0 }}>Active Task</h3>
            <p>
              <strong>{progress.active_task.title}</strong> ({progress.active_task.status})
            </p>
          </div>
        )}

        {progress.completed_tasks.length > 0 && (
          <div>
            <h3>Completed Tasks ({progress.completed_tasks.length})</h3>
            <ul>
              {progress.completed_tasks.map((task) => (
                <li key={task.task_id} style={{ color: 'green' }}>
                  {task.title}
                </li>
              ))}
            </ul>
          </div>
        )}

        {progress.failed_tasks.length > 0 && (
          <div>
            <h3>Failed Tasks ({progress.failed_tasks.length})</h3>
            <ul>
              {progress.failed_tasks.map((task) => (
                <li key={task.task_id} style={{ color: 'red' }}>
                  {task.title}
                </li>
              ))}
            </ul>
          </div>
        )}

        {progress.logs.length > 0 && (
          <div>
            <h3>Logs</h3>
            <pre style={{ background: '#f5f5f5', padding: 12, fontSize: '0.9em', maxHeight: 300, overflow: 'auto' }}>
              {progress.logs.join('\n')}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}
