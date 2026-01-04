const API_BASE = 'http://localhost:8000'

export async function startSession(): Promise<{ sessionId: string }> {
  const r = await fetch(`${API_BASE}/sessions`, { method: 'POST' })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function getNextQuestion(sessionId: string): Promise<any> {
  const r = await fetch(`${API_BASE}/sessions/${sessionId}/question`)
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function submitAnswer(sessionId: string, answer: { questionId: string; choiceId: string }): Promise<any> {
  const r = await fetch(`${API_BASE}/sessions/${sessionId}/answers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(answer),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function getPlan(sessionId: string): Promise<any> {
  const r = await fetch(`${API_BASE}/sessions/${sessionId}/plan`)
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function decidePlan(sessionId: string, decision: 'approve' | 'reject'): Promise<any> {
  const r = await fetch(`${API_BASE}/sessions/${sessionId}/plan/decision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision }),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function getResult(sessionId: string): Promise<any> {
  const r = await fetch(`${API_BASE}/sessions/${sessionId}/result`)
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}
