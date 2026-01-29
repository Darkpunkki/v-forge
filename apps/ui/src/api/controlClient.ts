/**
 * Typed API client for VibeForge Control Panel endpoints.
 */

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const CONTROL_TOKEN = import.meta.env.VITE_CONTROL_TOKEN || ''

/**
 * Control panel API types
 */

export interface ControlContextResponse {
  control_session_id: string
  session_cost_usd?: number
  session_limit_usd?: number
  session_remaining_usd?: number | null
  daily_cost_usd?: number
  daily_limit_usd?: number
  daily_remaining_usd?: number | null
  session_warning?: boolean
  daily_warning?: boolean
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
 * Live agent control types (IDEA-0003)
 */
export type AgentConnectionStatus =
  | 'connected'
  | 'disconnected'
  | 'idle'
  | 'busy'
  | 'error'

export interface RemoteAgent {
  agent_id: string
  name: string
  endpoint_url: string
  status: AgentConnectionStatus
  capabilities: string[]
  workdir?: string | null
  metadata?: Record<string, any>
  connected_at?: string | null
  last_heartbeat?: string | null
}

export interface RegisterAgentRequest {
  name: string
  endpoint_url: string
}

export interface AgentListResponse {
  agents: RemoteAgent[]
  total: number
}

export interface AgentDetailResponse {
  agent: RemoteAgent
}

export interface TaskDispatchRequest {
  content: string
  context?: Record<string, any>
}

export interface TaskDispatchResponse {
  agent_id: string
  message_id: string
  status: string
  message: string
}

export interface TaskStatusResponse {
  agent_id: string
  status: string
  message_id?: string | null
  error?: string | null
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
  bidirectional?: boolean
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
  use_real_llm?: boolean
  llm_provider?: string | null
  default_model?: string | null
  default_temperature?: number | null
  max_cost_usd?: number | null
  tick_rate_limit_ms?: number | null
}

export interface SimulationStartRequest {
  initial_prompt: string
  first_agent_id: string
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

export interface TickSummary {
  new_tick_index: number
  processed_event_count: number
  processed_events: SessionEvent[]
  messages_sent: number
  messages_blocked: number
}

export interface TickResponse {
  tick_index: number
  new_tick_index: number
  tick_status: string
  events_processed: number
  processed_event_count: number
  processed_events: SessionEvent[]
  messages_sent: number
  messages_blocked: number
  tick_summaries: TickSummary[]
  message: string
}

export interface SimulationStateResponse {
  initial_prompt: string | null
  first_agent_id: string | null
  simulation_mode: string
  tick_index: number
  tick_status: string
  auto_delay_ms: number | null
  tick_budget: number | null
  pending_work_summary: string | null
  simulation_expected_responses: string[]
  simulation_final_answer: string | null
  use_real_llm: boolean
  llm_provider: string
  default_model: string
  default_temperature: number
  simulation_cost_usd: number
  max_history_depth: number
  max_cost_usd: number
  tick_rate_limit_ms: number
  last_tick_timestamp: string | null
  agent_graph: { edges: AgentFlowEdge[] } | null
  agents: AgentConfig[]
  available_roles: string[]
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
 * Event filtering types (VF-206, VF-207)
 */
export interface EventsFilter {
  event_type?: string
  tick_index?: number
  tick_min?: number
  tick_max?: number
  agent_id?: string
  limit?: number
}

export interface FilteredEventsResponse {
  events: SessionEvent[]
  total: number
  filters_applied: EventsFilter
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
  const authHeaders: Record<string, string> = {}
  if (CONTROL_TOKEN) {
    authHeaders['Authorization'] = `Bearer ${CONTROL_TOKEN}`
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders,
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
 * Create a new session (used by simulation to get a session_id).
 */
export async function createSession(): Promise<{ session_id: string; phase: string }> {
  return fetchJson<{ session_id: string; phase: string }>('/control/sessions', {
    method: 'POST',
  })
}

/**
 * Get the stable control context session id.
 */
export async function getControlContext(): Promise<ControlContextResponse> {
  return fetchJson<ControlContextResponse>('/control/context')
}

/**
 * Register a remote agent.
 */
export async function registerAgent(
  name: string,
  endpointUrl: string
): Promise<AgentDetailResponse> {
  return fetchJson<AgentDetailResponse>('/control/agents/register', {
    method: 'POST',
    body: JSON.stringify({ name, endpoint_url: endpointUrl }),
  })
}

/**
 * List registered agents.
 */
export async function listAgents(): Promise<AgentListResponse> {
  return fetchJson<AgentListResponse>('/control/agents')
}

/**
 * Get agent status and details.
 */
export async function getAgentStatus(agentId: string): Promise<AgentDetailResponse> {
  return fetchJson<AgentDetailResponse>(`/control/agents/${agentId}`)
}

/**
 * Dispatch a task to a remote agent.
 */
export async function dispatchTask(
  agentId: string,
  content: string,
  context: Record<string, any> = {}
): Promise<TaskDispatchResponse> {
  return fetchJson<TaskDispatchResponse>(`/control/agents/${agentId}/dispatch`, {
    method: 'POST',
    body: JSON.stringify({ content, context }),
  })
}

/**
 * Send a follow-up message to a remote agent.
 */
export async function sendFollowUp(
  agentId: string,
  content: string
): Promise<TaskDispatchResponse> {
  return fetchJson<TaskDispatchResponse>(`/control/agents/${agentId}/followup`, {
    method: 'POST',
    body: JSON.stringify({ content }),
  })
}

/**
 * Get the current task status for a remote agent.
 */
export async function getTaskStatus(agentId: string): Promise<TaskStatusResponse> {
  return fetchJson<TaskStatusResponse>(`/control/agents/${agentId}/task`)
}

/**
 * Create an EventSource for streaming session events via SSE
 */
export function streamSessionEvents(sessionId: string): EventSource {
  const baseUrl = `${API_BASE}/control/sessions/${sessionId}/events`
  const url = CONTROL_TOKEN
    ? `${baseUrl}?token=${encodeURIComponent(CONTROL_TOKEN)}`
    : baseUrl
  return new EventSource(url)
}

/**
 * Create an EventSource for streaming agent events via SSE
 */
export function streamAgentEvents(agentId: string): EventSource {
  const baseUrl = `${API_BASE}/control/agents/${agentId}/events`
  const url = CONTROL_TOKEN
    ? `${baseUrl}?token=${encodeURIComponent(CONTROL_TOKEN)}`
    : baseUrl
  return new EventSource(url)
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
  sessionId: string,
  request: SimulationStartRequest
): Promise<SimulationStartResponse> {
  return fetchJson<SimulationStartResponse>(
    `/control/sessions/${sessionId}/simulation/start`,
    {
      method: 'POST',
      body: JSON.stringify(request),
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

/**
 * Get filtered events for a session (VF-207)
 */
export async function getFilteredEvents(
  sessionId: string,
  filters: EventsFilter = {}
): Promise<FilteredEventsResponse> {
  const params = new URLSearchParams()

  if (filters.event_type !== undefined) {
    params.set('event_type', filters.event_type)
  }
  if (filters.tick_index !== undefined) {
    params.set('tick_index', filters.tick_index.toString())
  }
  if (filters.tick_min !== undefined) {
    params.set('tick_min', filters.tick_min.toString())
  }
  if (filters.tick_max !== undefined) {
    params.set('tick_max', filters.tick_max.toString())
  }
  if (filters.agent_id !== undefined) {
    params.set('agent_id', filters.agent_id)
  }
  if (filters.limit !== undefined) {
    params.set('limit', filters.limit.toString())
  }

  const queryString = params.toString()
  const endpoint = `/control/sessions/${sessionId}/events/filter${
    queryString ? `?${queryString}` : ''
  }`

  return fetchJson<FilteredEventsResponse>(endpoint)
}

// Export error class for error handling
export { ControlApiError }
