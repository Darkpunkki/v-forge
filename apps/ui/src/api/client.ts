/**
 * Typed API client for VibeForge Local UI API.
 * Communicates with FastAPI backend at http://localhost:8000
 */

import type {
  SessionResponse,
  QuestionResponse,
  AnswerRequest,
  AnswerResponse,
  ProgressResponse,
  ResultResponse,
  PlanResponse,
  ClarificationResponse,
  ClarificationAnswerRequest,
  ErrorResponse,
  SessionPhase,
} from '../types/api'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function fetchJson<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!response.ok) {
    let detail: string | undefined
    try {
      const errorData: ErrorResponse = await response.json()
      detail = errorData.detail
    } catch {
      detail = await response.text()
    }

    throw new ApiError(
      `API request failed: ${response.statusText}`,
      response.status,
      detail
    )
  }

  return response.json()
}

/**
 * Create a new session
 */
export async function createSession(): Promise<SessionResponse> {
  return fetchJson<SessionResponse>('/sessions', {
    method: 'POST',
  })
}

/**
 * Get the next question for a session
 */
export async function getQuestion(
  sessionId: string
): Promise<QuestionResponse> {
  return fetchJson<QuestionResponse>(`/sessions/${sessionId}/question`)
}

/**
 * Submit an answer to the current question
 */
export async function submitAnswer(
  sessionId: string,
  answer: AnswerRequest
): Promise<AnswerResponse> {
  return fetchJson<AnswerResponse>(`/sessions/${sessionId}/answers`, {
    method: 'POST',
    body: JSON.stringify(answer),
  })
}

/**
 * Get session progress
 */
export async function getProgress(
  sessionId: string
): Promise<ProgressResponse> {
  return fetchJson<ProgressResponse>(`/sessions/${sessionId}/progress`)
}

/**
 * Get the final result for a completed session
 */
export async function getResult(sessionId: string): Promise<ResultResponse> {
  console.groupCollapsed('[api] getResult called', sessionId)
  console.trace()
  console.groupEnd()
  return fetchJson<ResultResponse>(`/sessions/${sessionId}/result`)
}


/**
 * Get plan summary (for PLAN_REVIEW phase)
 */
export async function getPlan(sessionId: string): Promise<PlanResponse> {
  return fetchJson<PlanResponse>(`/sessions/${sessionId}/plan`)
}

/**
 * Submit plan decision (approve or reject)
 */
export async function decidePlan(
  sessionId: string,
  decision: 'approve' | 'reject',
  reason?: string
): Promise<{ status: string; next_phase: SessionPhase }> {
  return fetchJson(`/sessions/${sessionId}/plan/decision`, {
    method: 'POST',
    body: JSON.stringify({ approved: decision === 'approve', reason }),
  })
}

/**
 * Get clarification question (when gates/agents need user input)
 */
export async function getClarification(
  sessionId: string
): Promise<ClarificationResponse> {
  return fetchJson<ClarificationResponse>(
    `/sessions/${sessionId}/clarification`
  )
}

/**
 * Submit clarification answer
 */
export async function submitClarification(
  sessionId: string,
  answer: ClarificationAnswerRequest
): Promise<{ status: string; next_phase: SessionPhase }> {
  return fetchJson(`/sessions/${sessionId}/clarification`, {
    method: 'POST',
    body: JSON.stringify(answer),
  })
}

// Export the error class for error handling
export { ApiError }
