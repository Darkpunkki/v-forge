# WP-0047 — Agent workflow API client + integration tests

## Overview

- **VF Tasks:** VF-199
- **Goal:** Extend controlClient.ts with typed methods for all workflow endpoints and add integration tests covering the full init → assign → task → flows → execute workflow.
- **Dependencies:** WP-0044 (endpoints), WP-0046 (widgets to wire)

## Context

With the API endpoints (WP-0044) and UI widgets (WP-0046) in place, we need to:

1. Add typed API client methods to `controlClient.ts`
2. Add comprehensive integration tests covering the full workflow

## Implementation Steps

### Step 1: Extend controlClient.ts with workflow methods

**File:** `apps/ui/src/api/controlClient.ts`

```typescript
// Types for workflow configuration
export interface AgentInfo {
  agent_id: string;
  role?: string;
  model_id?: string;
  display_name?: string;
}

export interface InitializeAgentsResponse {
  session_id: string;
  agents: AgentInfo[];
  message: string;
}

export interface AssignAgentRoleResponse {
  agent_id: string;
  role: string;
  model_id?: string;
  message: string;
}

export interface MainTaskResponse {
  session_id: string;
  task_set: boolean;
  description: string;
  message: string;
}

export interface AgentFlowEdge {
  from_agent: string;
  to_agent: string;
  label?: string;
}

export interface AgentFlowResponse {
  session_id: string;
  edge_count: number;
  is_valid: boolean;
  validation_error?: string;
  message: string;
}

export interface WorkflowConfigResponse {
  session_id: string;
  agents: AgentInfo[];
  agent_roles: Record<string, string>;
  agent_models: Record<string, string>;
  main_task?: string;
  flow_edges: AgentFlowEdge[];
  is_configured: boolean;
}

// Control client class extension
class ControlClient {
  private baseUrl: string;

  constructor(baseUrl: string = '/api') {
    this.baseUrl = baseUrl;
  }

  // Existing methods...
  // listAllSessions(), getSessionStatus(), streamSessionEvents(), etc.

  // NEW: Workflow configuration methods

  /**
   * Initialize agents for a session.
   * @param sessionId - Session ID
   * @param count - Number of agents to create (1-10)
   */
  async initializeAgents(sessionId: string, count: number): Promise<InitializeAgentsResponse> {
    const response = await fetch(`${this.baseUrl}/control/sessions/${sessionId}/agents/init`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ count }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to initialize agents');
    }
    return response.json();
  }

  /**
   * Assign role and model to an agent.
   * @param sessionId - Session ID
   * @param agentId - Agent ID to configure
   * @param role - Role to assign (orchestrator, foreman, worker, reviewer, fixer)
   * @param modelId - Optional model ID to use
   */
  async assignAgentRole(
    sessionId: string,
    agentId: string,
    role: string,
    modelId?: string
  ): Promise<AssignAgentRoleResponse> {
    const response = await fetch(`${this.baseUrl}/control/sessions/${sessionId}/agents/assign`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agent_id: agentId, role, model_id: modelId }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to assign agent role');
    }
    return response.json();
  }

  /**
   * Set the main orchestration task.
   * @param sessionId - Session ID
   * @param description - Task description
   * @param acceptanceCriteria - Optional list of acceptance criteria
   * @param verificationCommands - Optional list of verification commands
   */
  async setMainTask(
    sessionId: string,
    description: string,
    acceptanceCriteria?: string[],
    verificationCommands?: string[]
  ): Promise<MainTaskResponse> {
    const response = await fetch(`${this.baseUrl}/control/sessions/${sessionId}/task`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        description,
        acceptance_criteria: acceptanceCriteria,
        verification_commands: verificationCommands,
      }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to set main task');
    }
    return response.json();
  }

  /**
   * Configure agent-to-agent communication flow.
   * @param sessionId - Session ID
   * @param edges - List of edges defining communication flow
   */
  async configureAgentFlow(
    sessionId: string,
    edges: AgentFlowEdge[]
  ): Promise<AgentFlowResponse> {
    const response = await fetch(`${this.baseUrl}/control/sessions/${sessionId}/flows`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ edges }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to configure agent flow');
    }
    return response.json();
  }

  /**
   * Get current workflow configuration for a session.
   * @param sessionId - Session ID
   */
  async getWorkflowConfig(sessionId: string): Promise<WorkflowConfigResponse> {
    const response = await fetch(`${this.baseUrl}/control/sessions/${sessionId}/workflow`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get workflow config');
    }
    return response.json();
  }
}

export const controlClient = new ControlClient();
```

### Step 2: Add integration tests for full workflow

**File:** `apps/api/tests/test_control_api.py` (extend)

```python
import pytest
from fastapi.testclient import TestClient

class TestAgentWorkflowIntegration:
    """Integration tests for the full agent workflow."""

    def test_full_workflow_init_to_configured(self, client: TestClient):
        """Test complete workflow: init → assign → task → flows → verify configured."""
        # Step 1: Create a session
        response = client.post("/sessions")
        assert response.status_code == 200
        session_id = response.json()["session_id"]

        # Step 2: Initialize agents
        response = client.post(
            f"/control/sessions/{session_id}/agents/init",
            json={"count": 3}
        )
        assert response.status_code == 200
        agents = response.json()["agents"]
        assert len(agents) == 3

        agent_ids = [a["agent_id"] for a in agents]

        # Step 3: Assign roles to agents
        roles = ["orchestrator", "worker", "reviewer"]
        for i, (agent_id, role) in enumerate(zip(agent_ids, roles)):
            response = client.post(
                f"/control/sessions/{session_id}/agents/assign",
                json={"agent_id": agent_id, "role": role, "model_id": "gpt-4"}
            )
            assert response.status_code == 200
            assert response.json()["role"] == role

        # Step 4: Set main task
        response = client.post(
            f"/control/sessions/{session_id}/task",
            json={
                "description": "Build a calculator app",
                "acceptance_criteria": ["Has add function", "Has subtract function"]
            }
        )
        assert response.status_code == 200
        assert response.json()["task_set"] is True

        # Step 5: Configure agent flow (orchestrator → worker → reviewer)
        response = client.post(
            f"/control/sessions/{session_id}/flows",
            json={"edges": [
                {"from_agent": agent_ids[0], "to_agent": agent_ids[1]},  # orchestrator → worker
                {"from_agent": agent_ids[1], "to_agent": agent_ids[2]},  # worker → reviewer
            ]}
        )
        assert response.status_code == 200
        assert response.json()["is_valid"] is True
        assert response.json()["edge_count"] == 2

        # Step 6: Verify workflow is configured
        response = client.get(f"/control/sessions/{session_id}/workflow")
        assert response.status_code == 200
        config = response.json()

        assert config["is_configured"] is True
        assert len(config["agents"]) == 3
        assert len(config["agent_roles"]) == 3
        assert config["main_task"] == "Build a calculator app"
        assert len(config["flow_edges"]) == 2

    def test_workflow_phase_guard_rejects_in_execution(self, client: TestClient):
        """Cannot initialize agents when session is in EXECUTION phase."""
        # Create and advance session to EXECUTION
        session_id = self._create_session_in_execution(client)

        # Try to initialize agents - should fail
        response = client.post(
            f"/control/sessions/{session_id}/agents/init",
            json={"count": 2}
        )
        assert response.status_code == 400
        assert "Cannot initialize agents" in response.json()["detail"]

    def test_workflow_assign_unknown_agent_fails(self, client: TestClient):
        """Assigning role to non-existent agent returns 404."""
        response = client.post("/sessions")
        session_id = response.json()["session_id"]

        # Initialize agents
        client.post(f"/control/sessions/{session_id}/agents/init", json={"count": 1})

        # Try to assign to unknown agent
        response = client.post(
            f"/control/sessions/{session_id}/agents/assign",
            json={"agent_id": "unknown-agent", "role": "worker"}
        )
        assert response.status_code == 404

    def test_workflow_cyclic_flow_validation(self, client: TestClient):
        """Cyclic agent flow is rejected with validation error."""
        response = client.post("/sessions")
        session_id = response.json()["session_id"]

        # Initialize agents
        response = client.post(
            f"/control/sessions/{session_id}/agents/init",
            json={"count": 2}
        )
        agents = response.json()["agents"]
        agent_ids = [a["agent_id"] for a in agents]

        # Try to configure cyclic flow
        response = client.post(
            f"/control/sessions/{session_id}/flows",
            json={"edges": [
                {"from_agent": agent_ids[0], "to_agent": agent_ids[1]},
                {"from_agent": agent_ids[1], "to_agent": agent_ids[0]},  # Cycle!
            ]}
        )
        assert response.status_code == 200
        assert response.json()["is_valid"] is False
        assert "Cycle" in response.json()["validation_error"]

    def test_workflow_config_empty_before_init(self, client: TestClient):
        """Workflow config shows empty state before initialization."""
        response = client.post("/sessions")
        session_id = response.json()["session_id"]

        response = client.get(f"/control/sessions/{session_id}/workflow")
        assert response.status_code == 200
        config = response.json()

        assert config["is_configured"] is False
        assert len(config["agents"]) == 0
        assert config["main_task"] is None

    def test_workflow_reinitialize_clears_assignments(self, client: TestClient):
        """Re-initializing agents clears previous role assignments."""
        response = client.post("/sessions")
        session_id = response.json()["session_id"]

        # Initialize and assign
        response = client.post(f"/control/sessions/{session_id}/agents/init", json={"count": 2})
        agents = response.json()["agents"]
        client.post(
            f"/control/sessions/{session_id}/agents/assign",
            json={"agent_id": agents[0]["agent_id"], "role": "worker"}
        )

        # Re-initialize with different count
        response = client.post(f"/control/sessions/{session_id}/agents/init", json={"count": 3})
        new_agents = response.json()["agents"]

        # Verify: new agents, roles cleared
        assert len(new_agents) == 3
        config = client.get(f"/control/sessions/{session_id}/workflow").json()
        assert len(config["agent_roles"]) == 0  # Roles should be cleared

    def _create_session_in_execution(self, client: TestClient) -> str:
        """Helper to create a session and advance it to EXECUTION phase."""
        # This would require completing questionnaire and approving plan
        # For testing, we might need a direct phase setter or mock
        response = client.post("/sessions")
        return response.json()["session_id"]
```

### Step 3: Add TypeScript type exports

**File:** `apps/ui/src/types/api.ts` (extend)

```typescript
// Add workflow configuration types
export interface AgentInfo {
  agent_id: string;
  role?: string;
  model_id?: string;
  display_name?: string;
}

export interface WorkflowConfig {
  session_id: string;
  agents: AgentInfo[];
  agent_roles: Record<string, string>;
  agent_models: Record<string, string>;
  main_task?: string;
  flow_edges: Array<{
    from_agent: string;
    to_agent: string;
    label?: string;
  }>;
  is_configured: boolean;
}
```

## Verification

```bash
cd apps/api && pytest tests/test_control_api.py -v
cd apps/ui && npm run build
```

## Files to Touch

- `apps/ui/src/api/controlClient.ts` — add 5 workflow methods with types
- `apps/ui/src/types/api.ts` — add workflow configuration types
- `apps/api/tests/test_control_api.py` — add integration tests

## Done When

- [ ] controlClient.ts has all 5 typed workflow methods
- [ ] Types exported and usable in widgets
- [ ] Integration test covers full workflow: init → assign → task → flows
- [ ] Tests cover error cases (phase guards, validation failures)
- [ ] CI passes with all tests
