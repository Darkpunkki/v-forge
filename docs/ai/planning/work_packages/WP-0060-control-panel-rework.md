# WP-0060 - Control Panel Layout Rework

- Goal: Rework ControlPanel.tsx to an agent-centric layout: sidebar with AgentConnectionDashboard + AgentRegistrationPanel, main area with TaskDispatchPanel + StreamingOutputView, collapsible monitoring panels.
- Idea-ID: IDEA-0003-vibeforge-is-pivoting
- Tasks: TASK-034

## Plan

1. Review current ControlPanel layout and related widgets (AgentConnectionDashboard, AgentRegistrationPanel, TaskDispatchPanel, StreamingOutputView, EventStream, CostAnalytics).
2. Rework ControlPanel layout to agent-centric sidebar + main area, keeping responsive behavior.
3. Wire agent selection from dashboard into task panel focus.
4. Ensure monitoring panels remain accessible and collapsible.

## Done means

- Left sidebar shows AgentConnectionDashboard + AgentRegistrationPanel
- Main area shows TaskDispatchPanel + StreamingOutputView for selected agent
- Selecting an agent in dashboard focuses task panel on that agent
- EventStream and CostAnalytics accessible as collapsible panels
- Layout responsive (sidebar collapses on small screens)
- `cd apps/ui; npm run build` succeeds

## Tasks

- [x] TASK-034 - Rework ControlPanel.tsx layout for agent-centric experience
  - Files: apps/ui/src/screens/ControlPanel.tsx, apps/ui/src/screens/ControlPanel.css
  - Verified: cd apps/ui; npm run build

## Notes / Decisions

- None yet.
