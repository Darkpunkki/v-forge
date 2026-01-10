import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getProgress, getResult } from '../api/client'
import type { ResultResponse } from '../types/api'

export function ResultScreen() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [result, setResult] = useState<ResultResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)

  async function loadResult() {
    if (!sessionId) return

    setError(null)
    setLoading(true)

    try {
      // Check phase first
      const progress = await getProgress(sessionId)
      const phase = progress.phase

      if (phase === 'PLAN_REVIEW') {
        navigate(`/plan/${sessionId}`, { replace: true })
        return
      }
      if (phase === 'CLARIFICATION') {
        navigate(`/clarification/${sessionId}`, { replace: true })
        return
      }
      if (phase !== 'COMPLETE') {
        navigate(`/progress/${sessionId}`, { replace: true })
        return
      }

      // Only now fetch the result
      const r = await getResult(sessionId)
      setResult(r)
    } catch (err: any) {
      // ApiError has .detail; fall back to message
      setError(err.detail || err.message || String(err))
    } finally {
      setLoading(false)
    }
  }


  async function copyToClipboard(text: string) {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  function openWorkspace() {
    if (!result) return
    // Try to open the workspace folder using file:// protocol
    // This may not work in all browsers due to security restrictions
    window.open(`file://${result.workspace_path}`, '_blank')
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

  const isSuccess = result.status === 'success'

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      {/* Success Banner */}
      <div
        style={{
          background: isSuccess ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : '#f44336',
          color: 'white',
          padding: 32,
          borderRadius: 12,
          marginBottom: 24,
          textAlign: 'center',
        }}
      >
        <h1 style={{ margin: 0, fontSize: 32 }}>
          {isSuccess ? '🎉 Session Complete!' : '❌ Session Failed'}
        </h1>
        <p style={{ fontSize: 18, margin: '8px 0 0 0', opacity: 0.9 }}>
          {isSuccess
            ? 'Your app has been generated successfully'
            : 'Something went wrong during generation'}
        </p>
      </div>

      {/* Summary Section */}
      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 24, color: '#333', marginBottom: 12 }}>Summary</h2>
        <div style={{ background: '#fafafa', padding: 20, borderRadius: 8, border: '1px solid #ddd' }}>
          <p style={{ whiteSpace: 'pre-wrap', margin: 0, lineHeight: 1.6 }}>{result.summary}</p>
        </div>
      </section>

      {/* Workspace Location Section */}
      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 24, color: '#333', marginBottom: 12 }}>Workspace Location</h2>
        <div style={{ background: '#f0f7ff', padding: 20, borderRadius: 8, border: '1px solid #b3d9ff' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
            <code style={{ flex: 1, background: 'white', padding: 12, borderRadius: 6, fontSize: 14 }}>
              {result.workspace_path}
            </code>
            <button
              onClick={() => copyToClipboard(result.workspace_path)}
              style={{
                padding: '10px 16px',
                background: copied ? '#4caf50' : '#0070f3',
                color: 'white',
                border: 'none',
                borderRadius: 6,
                cursor: 'pointer',
                fontSize: 14,
                fontWeight: 600,
                whiteSpace: 'nowrap',
              }}
            >
              {copied ? '✓ Copied' : 'Copy Path'}
            </button>
          </div>
          <p style={{ margin: '12px 0 0 0', fontSize: 14, color: '#666' }}>
            Navigate to this folder in your file explorer to view the generated files.
          </p>
        </div>
      </section>

      {/* Run Instructions Section */}
      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 24, color: '#333', marginBottom: 12 }}>How to Run Your App</h2>
        <div style={{ background: '#1e1e1e', padding: 20, borderRadius: 8, color: '#d4d4d4' }}>
          <pre style={{ whiteSpace: 'pre-wrap', margin: 0, fontFamily: 'monospace', fontSize: 14, lineHeight: 1.6 }}>
            {result.run_instructions}
          </pre>
        </div>
      </section>

      {/* Generated Files Section */}
      {result.generated_files.length > 0 && (
        <section style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 24, color: '#333', marginBottom: 12 }}>
            Generated Files ({result.generated_files.length})
          </h2>
          <div style={{ background: '#fafafa', padding: 20, borderRadius: 8, border: '1px solid #ddd' }}>
            <ul style={{ margin: 0, paddingLeft: 20, lineHeight: 1.8 }}>
              {result.generated_files.map((file, idx) => (
                <li key={idx}>
                  <code style={{ fontSize: 14 }}>{file}</code>
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      {/* Artifacts Section */}
      {Object.keys(result.artifacts).length > 0 && (
        <section style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 24, color: '#333', marginBottom: 12 }}>Artifacts</h2>
          <div style={{ background: '#fafafa', padding: 20, borderRadius: 8, border: '1px solid #ddd' }}>
            <ul style={{ margin: 0, paddingLeft: 20, lineHeight: 1.8 }}>
              {Object.entries(result.artifacts).map(([name, path]) => (
                <li key={name}>
                  <strong>{name}:</strong> <code style={{ fontSize: 14, marginLeft: 8 }}>{path}</code>
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      {/* Next Steps Section */}
      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 24, color: '#333', marginBottom: 12 }}>Next Steps</h2>
        <div style={{ background: '#f0fff4', padding: 20, borderRadius: 8, border: '1px solid #9ae6b4' }}>
          <ul style={{ margin: 0, paddingLeft: 20, lineHeight: 1.8 }}>
            <li>Navigate to the workspace folder shown above</li>
            <li>Follow the run instructions to start your app</li>
            <li>Explore the generated files and customize them as needed</li>
            <li>Refer to the stack documentation for advanced features</li>
          </ul>
        </div>
      </section>

      {/* Actions */}
      <div style={{ display: 'flex', gap: 12, justifyContent: 'center', paddingTop: 24 }}>
        <button
          onClick={() => navigate('/')}
          style={{
            padding: '12px 32px',
            background: '#0070f3',
            color: 'white',
            border: 'none',
            borderRadius: 6,
            fontSize: 16,
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Start New Session
        </button>
      </div>
    </div>
  )
}
