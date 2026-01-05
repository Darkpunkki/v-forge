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
      const { session_id } = await createSession()
      navigate(`/questionnaire/${session_id}`)
    } catch (err: any) {
      setError(err.message || String(err))
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
