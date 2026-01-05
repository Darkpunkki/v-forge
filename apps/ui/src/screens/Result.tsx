import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getResult } from '../api/client'
import type { ResultResponse } from '../types/api'

export function ResultScreen() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [result, setResult] = useState<ResultResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function loadResult() {
    if (!sessionId) return

    setError(null)
    setLoading(true)

    try {
      const r = await getResult(sessionId)
      setResult(r)
    } catch (err: any) {
      setError(err.message || String(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadResult()
  }, [sessionId])

  if (loading) {
    return <div>Loading result...</div>
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

  if (!result) {
    return <div>No result available</div>
  }

  return (
    <div>
      <div style={{ border: '1px solid #ddd', borderRadius: 12, padding: 16 }}>
        <h2 style={{ marginTop: 0 }}>Session Complete!</h2>

        <div style={{ background: result.status === 'success' ? '#d4edda' : '#f8d7da', padding: 12, borderRadius: 6, marginBottom: 16 }}>
          <p style={{ margin: 0 }}>
            <strong>Status:</strong> {result.status}
          </p>
        </div>

        <h3>Summary</h3>
        <p style={{ whiteSpace: 'pre-wrap' }}>{result.summary}</p>

        <h3>Workspace</h3>
        <p>
          <code>{result.workspace_path}</code>
        </p>

        <h3>Generated Files ({result.generated_files.length})</h3>
        <ul>
          {result.generated_files.map((file, idx) => (
            <li key={idx}>
              <code>{file}</code>
            </li>
          ))}
        </ul>

        <h3>Run Instructions</h3>
        <div style={{ background: '#f5f5f5', padding: 12, borderRadius: 6 }}>
          <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{result.run_instructions}</pre>
        </div>

        {Object.keys(result.artifacts).length > 0 && (
          <>
            <h3>Artifacts</h3>
            <ul>
              {Object.entries(result.artifacts).map(([name, path]) => (
                <li key={name}>
                  <strong>{name}:</strong> <code>{path}</code>
                </li>
              ))}
            </ul>
          </>
        )}

        <div style={{ marginTop: 24 }}>
          <button onClick={() => navigate('/')} style={{ padding: '10px 20px' }}>
            Start New Session
          </button>
        </div>
      </div>
    </div>
  )
}
