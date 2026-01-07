/**
 * Typed API client for VibeForge Control Panel endpoints.
 * Provides admin/observability API for monitoring sessions.
 */

import type { SessionPhase } from '../types/api'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

/**
 * Control panel API types
 */

export interface SessionListItem {
  session_id: string
  phase: string
  created_at: string
  updated_at: string
  has_concept?: boolean
  has_build_spec?: boolean
  has_task_graph?: boolean
}

export interface SessionsListResponse {
  sessions: SessionListItem[]
  total: number
}

export interface ActiveSessionItem {
  session_id: string
  phase: string
  active_task_id: string | null
  updated_at: string
}

export interface ActiveSessionsResponse {
  active_sessions: ActiveSessionItem[]
  total: number
}

export interface SessionStatusResponse {
  session_id: string
  phase: string
  active_task_id: string | null
  completed_tasks: number
  failed_tasks: number
  created_at: string
  updated_at: string
}

export interface SessionEvent {
  event_type: string
  timestamp: string
  session_id: string
  message: string
  phase?: string
  task_id?: string
  metadata?: Record<string, any>
}

export interface SessionPrompt {
  timestamp: string
  task_id: string | null
  agent_role: string | null
  model: string | null
  prompt: string
  system_message: string
  max_tokens: number | null
  temperature: number | null
}

/**
 * API client class
 */
class ControlApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: string
  ) {
    super(message)
    this.name = 'ControlApiError'
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
      const errorData = await response.json()
      detail = errorData.detail
    } catch {
      detail = await response.text()
    }

    throw new ControlApiError(
      `Control API request failed: ${response.statusText}`,
      response.status,
      detail
    )
  }

  return response.json()
}

/**
 * List all sessions with metadata
 */
export async function listAllSessions(): Promise<SessionsListResponse> {
  return fetchJson<SessionsListResponse>('/control/sessions')
}

/**
 * Get all active sessions (not in COMPLETE or FAILED state)
 */
export async function getActiveSessions(): Promise<ActiveSessionsResponse> {
  return fetchJson<ActiveSessionsResponse>('/control/active')
}

/**
 * Get detailed status for a specific session
 */
export async function getSessionStatus(
  sessionId: string
): Promise<SessionStatusResponse> {
  return fetchJson<SessionStatusResponse>(`/control/sessions/${sessionId}/status`)
}

/**
 * Create an EventSource for streaming session events via SSE
 */
export function streamSessionEvents(sessionId: string): EventSource {
  return new EventSource(`${API_BASE}/control/sessions/${sessionId}/events`)
}

/**
 * Get prompt data for a session.
 */
export async function getSessionPrompts(
  sessionId: string
): Promise<{ prompts: SessionPrompt[]; total: number }> {
  return fetchJson<{ prompts: SessionPrompt[]; total: number }>(
    `/control/sessions/${sessionId}/prompts`
  )
}

// Export error class for error handling
export { ControlApiError }
