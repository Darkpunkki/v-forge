import { useNavigate } from 'react-router-dom'
import { createSession } from '../api/client'
import { useState } from 'react'

export function HomeScreen() {
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function handleStart() {
    setError(null)
    setLoading(true)
    try {
      const { session_id, phase } = await createSession()

      switch (phase) {
        case 'QUESTIONNAIRE':
          navigate(`/questionnaire/${session_id}`)
          break
        case 'PLAN_REVIEW':
          navigate(`/plan/${session_id}`)
          break
        case 'CLARIFICATION':
          navigate(`/clarification/${session_id}`)
          break
        case 'COMPLETE':
        case 'FAILED':
          navigate(`/result/${session_id}`)
          break
        default:
          navigate(`/progress/${session_id}`)
          break
      }
    } catch (err: any) {
      setError(err?.detail || err?.message || String(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1>VibeForge</h1>
      <p style={{ opacity: 0.75 }}>
        Cloud-first MVP skeleton. Questionnaire → concept → plan decision.
      </p>

      {error && (
        <pre style={{ background: '#fee', padding: 12, marginBottom: 16 }}>
          {error}
        </pre>
      )}

      <button onClick={handleStart} disabled={loading}>
        {loading ? 'Starting...' : 'Start New Session'}
      </button>
    </div>
  )
}
