import { useParams, useNavigate } from 'react-router-dom'

/**
 * Placeholder for clarification screen (gates/agents will use this in future)
 */
export function ClarificationScreen() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()

  return (
    <div>
      <div style={{ border: '1px solid #ddd', borderRadius: 12, padding: 16 }}>
        <h2 style={{ marginTop: 0 }}>Clarification Needed</h2>
        <p>
          This screen will display multiple-choice clarification questions from gates/agents.
        </p>
        <p style={{ opacity: 0.7 }}>
          <em>Placeholder - not yet implemented</em>
        </p>
        <button onClick={() => navigate('/')}>Back to Home</button>
      </div>
    </div>
  )
}
