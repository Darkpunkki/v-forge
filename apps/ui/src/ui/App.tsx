import React, { useEffect, useMemo, useState } from 'react'
import { startSession, getNextQuestion, submitAnswer, getPlan, decidePlan, getResult } from './api'

type Phase = 'QUESTIONNAIRE' | 'BUILD_SPEC' | 'IDEA' | 'PLAN_REVIEW' | 'EXECUTION' | 'VERIFICATION' | 'COMPLETE' | 'FAILED'

export function App() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [question, setQuestion] = useState<any | null>(null)
  const [status, setStatus] = useState<string>('idle')
  const [plan, setPlan] = useState<any | null>(null)
  const [result, setResult] = useState<any | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function boot() {
    setError(null)
    setStatus('starting')
    const { sessionId } = await startSession()
    setSessionId(sessionId)
    setStatus('questionnaire')
  }

  async function loadQuestion(sid: string) {
    setError(null)
    const q = await getNextQuestion(sid)
    if (q.status === 'question') {
      setQuestion(q.question)
    } else {
      setQuestion(null)
      setStatus('plan')
      const p = await getPlan(sid)
      setPlan(p)
    }
  }

  async function answer(choiceId: string) {
    if (!sessionId || !question) return
    setError(null)
    await submitAnswer(sessionId, { questionId: question.id, choiceId })
    await loadQuestion(sessionId)
  }

  async function approve(decision: 'approve' | 'reject') {
    if (!sessionId) return
    setError(null)
    await decidePlan(sessionId, decision)
    const r = await getResult(sessionId)
    setResult(r)
    setStatus('done')
  }

  useEffect(() => {
    if (sessionId && status === 'questionnaire') {
      loadQuestion(sessionId).catch(e => setError(String(e)))
    }
  }, [sessionId, status])

  return (
    <div style={{ fontFamily: 'system-ui', padding: 24, maxWidth: 820, margin: '0 auto' }}>
      <h1>VibeForge</h1>
      <p style={{ opacity: 0.75 }}>Cloud-first MVP skeleton. Questionnaire → concept → plan decision.</p>

      {!sessionId && (
        <button onClick={() => boot().catch(e => setError(String(e)))}>
          Start
        </button>
      )}

      {error && <pre style={{ background: '#fee', padding: 12 }}>{error}</pre>}

      {status === 'questionnaire' && question && (
        <div style={{ border: '1px solid #ddd', borderRadius: 12, padding: 16 }}>
          <h2 style={{ marginTop: 0 }}>{question.prompt}</h2>
          <div style={{ display: 'grid', gap: 8 }}>
            {question.choices.map((c: any) => (
              <button key={c.id} onClick={() => answer(c.id)} style={{ textAlign: 'left' }}>
                {c.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {status === 'plan' && plan && (
        <div style={{ border: '1px solid #ddd', borderRadius: 12, padding: 16 }}>
          <h2 style={{ marginTop: 0 }}>Plan review (skeleton)</h2>
          <p>This step advances BuildSpec + Concept generation on the backend.</p>
          <pre style={{ whiteSpace: 'pre-wrap', background: '#f7f7f7', padding: 12 }}>
            {JSON.stringify(plan, null, 2)}
          </pre>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={() => approve('approve').catch(e => setError(String(e)))}>Approve</button>
            <button onClick={() => approve('reject').catch(e => setError(String(e)))}>Reject</button>
          </div>
        </div>
      )}

      {status === 'done' && result && (
        <div style={{ border: '1px solid #ddd', borderRadius: 12, padding: 16 }}>
          <h2 style={{ marginTop: 0 }}>Result</h2>
          <pre style={{ whiteSpace: 'pre-wrap', background: '#f7f7f7', padding: 12 }}>
            {JSON.stringify(result, null, 2)}
          </pre>
          <p style={{ opacity: 0.8 }}>Next: implement execution loop (TaskMaster → AgentResult diffs → PatchApplier → VerifierSuite).</p>
        </div>
      )}
    </div>
  )
}
