/**
 * TypeScript types for VibeForge Local UI API.
 * These match the Pydantic models from apps/api/vibeforge_api/models/
 */

// Session phases
export type SessionPhase =
  | 'QUESTIONNAIRE'
  | 'BUILD_SPEC'
  | 'IDEA'
  | 'PLAN_REVIEW'
  | 'EXECUTION'
  | 'CLARIFICATION'
  | 'VERIFICATION'
  | 'COMPLETE'
  | 'FAILED'


// Question types
export interface QuestionOption {
  value: string
  label: string
}

export interface QuestionResponse {
  question_id: string
  text: string
  question_type: 'radio' | 'checkbox' | 'select' | 'slider'
  options?: QuestionOption[]
  min_value?: number
  max_value?: number
  is_final: boolean
}

// Session creation response
export interface SessionResponse {
  session_id: string
  phase: SessionPhase
}

// Answer request
export interface AnswerRequest {
  question_id: string
  answer: string
}

// Answer response
export interface AnswerResponse {
  status: string
  next_phase: SessionPhase
  is_complete: boolean
}

// Task progress
export interface TaskProgress {
  task_id: string
  title: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
}

// Progress response
export interface ProgressResponse {
  session_id: string
  phase: SessionPhase
  active_task?: TaskProgress
  completed_tasks: TaskProgress[]
  failed_tasks: TaskProgress[]
  logs: string[]
}

// Plan summary response
export interface PlanResponse {
  features: string[]
  task_count: number
  verification_steps: string[]
  estimated_scope: string
  constraints: string[]
}

// Result response
export interface ResultResponse {
  session_id: string
  status: 'success' | 'failed'
  workspace_path: string
  generated_files: string[]
  run_instructions: string
  summary: string
  artifacts: Record<string, string>
}

// Clarification option
export interface ClarificationOption {
  label: string
  value: string
  description?: string
}

// Clarification response
export interface ClarificationResponse {
  question: string
  context?: string
  options: ClarificationOption[]
}

// Clarification answer request
export interface ClarificationAnswerRequest {
  answer: string
}

// Error response
export interface ErrorResponse {
  detail: string
}

// Workflow configuration types (VF-199)
export interface AgentInfo {
  agent_id: string
  role?: string
  model_id?: string
  display_name?: string
}

export interface AgentFlowEdge {
  from_agent: string
  to_agent: string
  label?: string
}

export interface WorkflowConfig {
  session_id: string
  agents: AgentInfo[]
  agent_roles: Record<string, string>
  agent_models: Record<string, string>
  main_task?: string
  flow_edges: AgentFlowEdge[]
  is_configured: boolean
}
