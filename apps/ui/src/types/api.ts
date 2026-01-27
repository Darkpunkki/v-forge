/**
 * Shared TypeScript types for VibeForge API.
 */

// Session phases (used by controlClient.ts)
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
