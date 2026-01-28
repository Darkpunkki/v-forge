# WP-0059 - Control UI: API Client + Agent Components

## Goal
Build the frontend components for agent control: API client functions, AgentRegistrationPanel, TaskDispatchPanel, StreamingOutputView, and AgentConnectionDashboard.

## Idea-ID
IDEA-0003-vibeforge-is-pivoting

## Included Tasks
- TASK-028 - Add agent registration API functions to controlClient.ts
- TASK-029 - Build AgentRegistrationPanel widget
- TASK-030 - Add task dispatch + follow-up API functions
- TASK-031 - Build TaskDispatchPanel chat-style widget
- TASK-032 - Build StreamingOutputView with SSE subscription
- TASK-033 - Build AgentConnectionDashboard grid widget

## Ordered Execution Steps
1. Implement TASK-028 (control client agent registration/list/status functions + types)
2. Implement TASK-029 (AgentRegistrationPanel component)
3. Implement TASK-030 (dispatch/follow-up/status functions + types)
4. Implement TASK-031 (TaskDispatchPanel component)
5. Implement TASK-032 (StreamingOutputView component)
6. Implement TASK-033 (AgentConnectionDashboard component)

## Done Means
- Verification commands:
  - cd apps/ui && npm run build

## Checklist
- [x] TASK-028 - Add agent registration API functions to controlClient.ts
  - Files: `apps/ui/src/api/controlClient.ts`
  - Verified: `cd apps/ui && npm run build`
- [x] TASK-029 - Build AgentRegistrationPanel widget
  - Files: `apps/ui/src/screens/control/widgets/AgentRegistrationPanel.tsx`
  - Verified: `cd apps/ui && npm run build`
- [x] TASK-030 - Add task dispatch + follow-up API functions
  - Files: `apps/ui/src/api/controlClient.ts`
  - Verified: `cd apps/ui && npm run build`
- [x] TASK-031 - Build TaskDispatchPanel chat-style widget
  - Files: `apps/ui/src/screens/control/widgets/TaskDispatchPanel.tsx`
  - Verified: `cd apps/ui && npm run build`
- [x] TASK-032 - Build StreamingOutputView with SSE subscription
  - Files: `apps/ui/src/screens/control/widgets/StreamingOutputView.tsx`
  - Verified: `cd apps/ui && npm run build`
- [x] TASK-033 - Build AgentConnectionDashboard grid widget
  - Files: `apps/ui/src/screens/control/widgets/AgentConnectionDashboard.tsx`
  - Verified: `cd apps/ui && npm run build`

## Notes / Decisions
- None yet.
