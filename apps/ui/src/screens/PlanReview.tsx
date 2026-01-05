import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getPlan, decidePlan } from '../api/client'
import type { PlanResponse } from '../types/api'

export function PlanReviewScreen() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [plan, setPlan] = useState<PlanResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function loadPlan() {
    if (!sessionId) return

    setError(null)
    setLoading(true)

    try {
      const p = await getPlan(sessionId)
      setPlan(p)
    } catch (err: any) {
      setError(err.message || String(err))
    } finally {
      setLoading(false)
    }
  }

  async function handleDecision(decision: 'approve' | 'reject') {
    if (!sessionId) return

    setError(null)
    try {
      await decidePlan(sessionId, decision)
      navigate(`/result/${sessionId}`)
    } catch (err: any) {
      setError(err.message || String(err))
    }
  }

  useEffect(() => {
    loadPlan()
  }, [sessionId])

  if (loading) {
    return <div>Loading plan...</div>
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

  if (!plan) {
    return <div>No plan available</div>
  }

  return (
    <div>
      <div style={{ border: '1px solid #ddd', borderRadius: 12, padding: 16 }}>
        <h2 style={{ marginTop: 0 }}>Plan Review</h2>

        <h3>Features</h3>
        <ul>
          {plan.features.map((feature, idx) => (
            <li key={idx}>{feature}</li>
          ))}
        </ul>

        <h3>Details</h3>
        <p>
          <strong>Task Count:</strong> {plan.task_count}
        </p>
        <p>
          <strong>Estimated Scope:</strong> {plan.estimated_scope}
        </p>

        <h3>Verification Steps</h3>
        <ul>
          {plan.verification_steps.map((step, idx) => (
            <li key={idx}>{step}</li>
          ))}
        </ul>

        <h3>Constraints</h3>
        <ul>
          {plan.constraints.map((constraint, idx) => (
            <li key={idx}>{constraint}</li>
          ))}
        </ul>

        <div style={{ display: 'flex', gap: 8, marginTop: 24 }}>
          <button
            onClick={() => handleDecision('approve')}
            style={{ padding: '10px 20px', background: '#0070f3', color: 'white', border: 'none', borderRadius: 6 }}
          >
            Approve Plan
          </button>
          <button
            onClick={() => handleDecision('reject')}
            style={{ padding: '10px 20px', background: '#f44336', color: 'white', border: 'none', borderRadius: 6 }}
          >
            Reject Plan
          </button>
        </div>
      </div>
    </div>
  )
}
