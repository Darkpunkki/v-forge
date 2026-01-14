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
  artifacts: string[]
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

export interface SessionLlmTrace {
  request_id: string
  timestamp: string
  task_id: string | null
  agent_role: string | null
  model: string | null
  prompt: string
  system_message: string
  max_tokens: number | null
  temperature: number | null
  response: string | null
  response_model: string | null
  response_timestamp: string | null
  prompt_tokens: number | null
  completion_tokens: number | null
  total_tokens: number | null
}

/**
 * Workflow configuration types (VF-192, VF-193)
 */
export interface AgentConfig {
  agent_id: string
  role?: string
  model_id?: string
  display_name?: string
}

export interface AgentFlowEdge {
  from_agent: string
  to_agent: string
}

export interface InitializeAgentsResponse {
  agent_ids: string[]
  message: string
}

export interface AssignAgentRoleResponse {
  agent_id: string
  role?: string
  model_id?: string
  message: string
}

export interface SetMainTaskResponse {
  main_task: string
  message: string
}

export interface ConfigureAgentFlowResponse {
  edge_count: number
  message: string
  is_valid?: boolean
  validation_error?: string
}

export interface WorkflowConfigResponse {
  agents: AgentConfig[]
  agent_roles: Record<string, string>
  agent_models: Record<string, string>
  agent_graph: { edges: AgentFlowEdge[] } | null
  main_task: string | null
}

/**
 * Simulation types (VF-204, VF-205)
 */
export interface SimulationConfigRequest {
  simulation_mode: 'manual' | 'auto'
  auto_delay_ms?: number | null
  tick_budget?: number | null
}

export interface SimulationConfigResponse {
  simulation_mode: string
  auto_delay_ms: number | null
  tick_budget: number | null
  message: string
}

export interface SimulationStartResponse {
  tick_index: number
  tick_status: string
  message: string
}

export interface TickResponse {
  tick_index: number
  tick_status: string
  events_processed: number
  message: string
}

export interface SimulationStateResponse {
  simulation_mode: string
  tick_index: number
  tick_status: string
  auto_delay_ms: number | null
  tick_budget: number | null
  pending_work_summary: string | null
}

export interface SimulationResetResponse {
  tick_index: number
  tick_status: string
  workflow_preserved: boolean
  message: string
}

export interface SimulationPauseResponse {
  tick_index: number
  tick_status: string
  message: string
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

/**
 * Get prompts and responses for a session.
 */
export async function getSessionLlmTrace(
  sessionId: string
): Promise<{ traces: SessionLlmTrace[]; total: number }> {
  return fetchJson<{ traces: SessionLlmTrace[]; total: number }>(
    `/control/sessions/${sessionId}/llm-trace`
  )
}

/**
 * Initialize N agents for a session (VF-193)
 */
export async function initializeAgents(
  sessionId: string,
  agentCount: number
): Promise<InitializeAgentsResponse> {
  return fetchJson<InitializeAgentsResponse>(
    `/control/sessions/${sessionId}/agents/init`,
    {
      method: 'POST',
      body: JSON.stringify({ agent_count: agentCount }),
    }
  )
}

/**
 * Assign role and model to an agent (VF-193)
 */
export async function assignAgentRole(
  sessionId: string,
  agentId: string,
  role?: string,
  modelId?: string
): Promise<AssignAgentRoleResponse> {
  return fetchJson<AssignAgentRoleResponse>(
    `/control/sessions/${sessionId}/agents/assign`,
    {
      method: 'POST',
      body: JSON.stringify({
        agent_id: agentId,
        role: role || null,
        model_id: modelId || null,
      }),
    }
  )
}

/**
 * Set the main orchestration task (VF-193)
 */
export async function setMainTask(
  sessionId: string,
  mainTask: string
): Promise<SetMainTaskResponse> {
  return fetchJson<SetMainTaskResponse>(
    `/control/sessions/${sessionId}/task`,
    {
      method: 'POST',
      body: JSON.stringify({ main_task: mainTask }),
    }
  )
}

/**
 * Configure agent-to-agent communication flow (VF-193)
 */
export async function configureAgentFlow(
  sessionId: string,
  edges: AgentFlowEdge[]
): Promise<ConfigureAgentFlowResponse> {
  return fetchJson<ConfigureAgentFlowResponse>(
    `/control/sessions/${sessionId}/flows`,
    {
      method: 'POST',
      body: JSON.stringify({ edges }),
    }
  )
}

/**
 * Get current workflow configuration (VF-193)
 */
export async function getWorkflowConfig(
  sessionId: string
): Promise<WorkflowConfigResponse> {
  return fetchJson<WorkflowConfigResponse>(
    `/control/sessions/${sessionId}/workflow`
  )
}

/**
 * Configure simulation mode and parameters (VF-204)
 */
export async function configureSimulation(
  sessionId: string,
  config: SimulationConfigRequest
): Promise<SimulationConfigResponse> {
  return fetchJson<SimulationConfigResponse>(
    `/control/sessions/${sessionId}/simulation/config`,
    {
      method: 'POST',
      body: JSON.stringify(config),
    }
  )
}

/**
 * Start simulation (VF-204)
 */
export async function startSimulation(
  sessionId: string
): Promise<SimulationStartResponse> {
  return fetchJson<SimulationStartResponse>(
    `/control/sessions/${sessionId}/simulation/start`,
    {
      method: 'POST',
    }
  )
}

/**
 * Reset simulation state (VF-204)
 */
export async function resetSimulation(
  sessionId: string,
  preserveWorkflow: boolean = true
): Promise<SimulationResetResponse> {
  return fetchJson<SimulationResetResponse>(
    `/control/sessions/${sessionId}/simulation/reset`,
    {
      method: 'POST',
      body: JSON.stringify({ preserve_workflow: preserveWorkflow }),
    }
  )
}

/**
 * Advance simulation by one tick (VF-204)
 */
export async function advanceTick(
  sessionId: string
): Promise<TickResponse> {
  return fetchJson<TickResponse>(
    `/control/sessions/${sessionId}/simulation/tick`,
    {
      method: 'POST',
    }
  )
}

/**
 * Advance simulation by N ticks (VF-204)
 */
export async function advanceTicks(
  sessionId: string,
  tickCount: number
): Promise<TickResponse> {
  return fetchJson<TickResponse>(
    `/control/sessions/${sessionId}/simulation/ticks`,
    {
      method: 'POST',
      body: JSON.stringify({ tick_count: tickCount }),
    }
  )
}

/**
 * Pause auto-run simulation (VF-204)
 */
export async function pauseSimulation(
  sessionId: string
): Promise<SimulationPauseResponse> {
  return fetchJson<SimulationPauseResponse>(
    `/control/sessions/${sessionId}/simulation/pause`,
    {
      method: 'POST',
    }
  )
}

/**
 * Get current simulation state (VF-204)
 */
export async function getSimulationState(
  sessionId: string
): Promise<SimulationStateResponse> {
  return fetchJson<SimulationStateResponse>(
    `/control/sessions/${sessionId}/simulation/state`
  )
}

// Export error class for error handling
export { ControlApiError }
