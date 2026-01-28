"""Tests for control panel API endpoints."""

import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from vibeforge_api.core.event_log import EventLog, Event, EventType
from vibeforge_api.core.workspace import WorkspaceManager
from vibeforge_api.core.session import Session, SessionPhase


class TestControlContext:
    """Tests for /control/context endpoint."""

    @pytest.mark.asyncio
    async def test_get_control_context_stable(self):
        """Ensure control context session id is stable across calls."""
        from vibeforge_api.routers import control

        control._control_context_session_id = None
        session = Session()
        session.session_id = "control-session"

        with patch("vibeforge_api.core.session.session_store") as mock_store:
            mock_store.get_session.return_value = None
            mock_store.create_session.return_value = session

            first = await control.get_control_context()
            assert first["control_session_id"] == "control-session"

            mock_store.get_session.return_value = session
            second = await control.get_control_context()
            assert second["control_session_id"] == "control-session"
            assert mock_store.create_session.call_count == 1

        control._control_context_session_id = None


class TestControlEventStream:
    """Tests for /control/sessions/{id}/events endpoint (SSE)."""

    @pytest.mark.asyncio
    async def test_stream_session_events_not_found(self, tmp_path):
        """Test streaming events for session with no event log."""
        from vibeforge_api.routers.control import stream_session_events
        from fastapi import HTTPException

        # Mock WorkspaceManager with non-existent session
        with patch("vibeforge_api.core.workspace.WorkspaceManager") as mock_wm_class:
            mock_wm = Mock()
            mock_wm.workspace_root = tmp_path
            mock_wm_class.return_value = mock_wm

            # Call endpoint - should raise 404
            with pytest.raises(HTTPException) as exc_info:
                await stream_session_events("nonexistent")

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_stream_session_events_initial_events(self, tmp_path):
        """Test that SSE returns initial events from log."""
        from vibeforge_api.routers.control import stream_session_events

        # Create session workspace with event log
        session_id = "test-session"
        event_log = EventLog(tmp_path)

        # Add test events
        event_log.append(Event(
            event_type=EventType.PHASE_TRANSITION,
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            message="Test event 1",
            phase="IDEA",
        ))
        event_log.append(Event(
            event_type=EventType.TASK_STARTED,
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            message="Test event 2",
            phase="EXECUTION",
            task_id="task-1",
        ))

        # Mock WorkspaceManager
        with patch("vibeforge_api.core.workspace.WorkspaceManager") as mock_wm_class:
            mock_wm = Mock()
            mock_wm.workspace_root = tmp_path
            mock_wm_class.return_value = mock_wm

            # Call endpoint
            event_source = await stream_session_events(session_id)

            # Extract generator
            generator = event_source.body_iterator

            # Collect first 2 events (skip polling part)
            events = []
            for _ in range(2):
                event = await anext(generator)
                events.append(event)

            # Verify events were streamed
            assert len(events) == 2
            assert events[0]["event"] == "session_event"
            assert events[1]["event"] == "session_event"

            # Parse event data
            event1_data = json.loads(events[0]["data"])
            event2_data = json.loads(events[1]["data"])

            assert event1_data["event_type"] == "phase_transition"
            assert event2_data["event_type"] == "task_started"
            assert event2_data["task_id"] == "task-1"


class TestControlPrompts:
    """Tests for /control/sessions/{id}/prompts endpoint."""

    @pytest.mark.asyncio
    async def test_get_session_prompts(self, tmp_path):
        """Test prompt retrieval endpoint."""
        from vibeforge_api.routers.control import get_session_prompts

        session_id = "test-session"
        event_log = EventLog(tmp_path)
        event_log.append(
            Event(
                event_type=EventType.LLM_REQUEST_SENT,
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
                message="LLM request",
                task_id="task-1",
                metadata={
                    "agent_role": "worker",
                    "model": "gpt-4o-mini",
                    "prompt": "Write a Python function to add two numbers",
                    "system_message": "You are a helpful coding assistant",
                    "max_tokens": 1000,
                    "temperature": 0.7,
                },
            )
        )

        with patch("vibeforge_api.core.workspace.WorkspaceManager") as mock_wm_class:
            mock_wm = Mock()
            mock_wm.workspace_root = tmp_path
            mock_wm_class.return_value = mock_wm

            response = await get_session_prompts(session_id)

        assert response["total"] == 1
        prompt = response["prompts"][0]
        assert prompt["model"] == "gpt-4o-mini"
        assert "add two numbers" in prompt["prompt"]


class TestControlLlmTrace:
    """Tests for /control/sessions/{id}/llm-trace endpoint."""

    @pytest.mark.asyncio
    async def test_get_session_llm_trace(self, tmp_path):
        """Ensure LLM trace combines prompts and responses."""
        from vibeforge_api.routers.control import get_session_llm_trace

        session_id = "trace-session"
        request_id = "req-123"
        event_log = EventLog(tmp_path)
        event_log.append(
            Event(
                event_type=EventType.LLM_REQUEST_SENT,
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
                message="LLM request",
                task_id="task-1",
                metadata={
                    "agent_role": "worker",
                    "model": "gpt-4o-mini",
                    "prompt": "Write a Python function to add two numbers",
                    "system_message": "You are a helpful coding assistant",
                    "max_tokens": 1000,
                    "temperature": 0.7,
                    "request_id": request_id,
                },
            )
        )
        event_log.append(
            Event(
                event_type=EventType.LLM_RESPONSE_RECEIVED,
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
                message="LLM response",
                task_id="task-1",
                metadata={
                    "agent_role": "worker",
                    "model": "gpt-4o-mini",
                    "response": "Here is the function...",
                    "prompt_tokens": 12,
                    "completion_tokens": 8,
                    "total_tokens": 20,
                    "request_id": request_id,
                },
            )
        )

        with patch("vibeforge_api.core.workspace.WorkspaceManager") as mock_wm_class:
            mock_wm = Mock()
            mock_wm.workspace_root = tmp_path
            mock_wm_class.return_value = mock_wm

            response = await get_session_llm_trace(session_id)

        assert response["total"] == 1
        trace = response["traces"][0]
        assert trace["response"] == "Here is the function..."
        assert "add two numbers" in trace["prompt"]


class TestWorkflowEndpoints:
    """Tests for VF-193: Agent workflow API endpoints."""

    @pytest.mark.asyncio
    async def test_initialize_agents(self):
        """Test POST /control/sessions/{id}/agents/init."""
        from vibeforge_api.routers.control import initialize_agents
        from vibeforge_api.models import InitializeAgentsRequest
        from vibeforge_api.core.session import session_store

        session = session_store.create_session()
        request = InitializeAgentsRequest(agent_count=3)

        response = await initialize_agents(session.session_id, request)

        assert len(response.agent_ids) == 3
        assert response.agent_ids == ["agent-1", "agent-2", "agent-3"]
        assert "Initialized 3 agents" in response.message

        # Verify session was updated
        updated_session = session_store.get_session(session.session_id)
        assert len(updated_session.agents) == 3
        assert updated_session.agents[0]["agent_id"] == "agent-1"

    @pytest.mark.asyncio
    async def test_initialize_agents_session_not_found(self):
        """Test initialize_agents with non-existent session."""
        from vibeforge_api.routers.control import initialize_agents
        from vibeforge_api.models import InitializeAgentsRequest

        request = InitializeAgentsRequest(agent_count=2)

        with pytest.raises(HTTPException) as exc_info:
            await initialize_agents("nonexistent", request)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_initialize_agents_terminal_phase(self):
        """Test initialize_agents rejects terminal phases."""
        from vibeforge_api.routers.control import initialize_agents
        from vibeforge_api.models import InitializeAgentsRequest
        from vibeforge_api.core.session import session_store
        from vibeforge_api.models.types import SessionPhase

        session = session_store.create_session()
        session.phase = SessionPhase.COMPLETE
        session_store.update_session(session)

        request = InitializeAgentsRequest(agent_count=2)

        with pytest.raises(HTTPException) as exc_info:
            await initialize_agents(session.session_id, request)

        assert exc_info.value.status_code == 400
        assert "Cannot initialize agents" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_assign_agent_role(self):
        """Test POST /control/sessions/{id}/agents/assign."""
        from vibeforge_api.routers.control import initialize_agents, assign_agent_role
        from vibeforge_api.models import (
            InitializeAgentsRequest,
            AssignAgentRoleRequest,
        )
        from vibeforge_api.core.session import session_store

        # Setup: create session with agents
        session = session_store.create_session()
        init_req = InitializeAgentsRequest(agent_count=2)
        await initialize_agents(session.session_id, init_req)

        # Assign role and model
        assign_req = AssignAgentRoleRequest(
            agent_id="agent-1", role="worker", model_id="gpt-4"
        )
        response = await assign_agent_role(session.session_id, assign_req)

        assert response.agent_id == "agent-1"
        assert response.role == "worker"
        assert response.model_id == "gpt-4"

        # Verify session was updated
        updated_session = session_store.get_session(session.session_id)
        assert updated_session.agent_roles["agent-1"] == "worker"
        assert updated_session.agent_models["agent-1"] == "gpt-4"

    @pytest.mark.asyncio
    async def test_initialize_agents_duplicate_ids_rejected(self):
        """Test initialize_agents rejects duplicate agent IDs."""
        from vibeforge_api.routers.control import initialize_agents
        from vibeforge_api.models import InitializeAgentsRequest
        from vibeforge_api.core.session import session_store

        session = session_store.create_session()
        request = InitializeAgentsRequest(
            agents=[
                {"agent_id": "agent-1"},
                {"agent_id": "agent-1"},
            ]
        )

        with pytest.raises(HTTPException) as exc_info:
            await initialize_agents(session.session_id, request)

        assert exc_info.value.status_code == 400
        assert "Duplicate agent IDs" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_initialize_agents_empty_ids_rejected(self):
        """Test initialize_agents rejects empty agent IDs."""
        from vibeforge_api.routers.control import initialize_agents
        from vibeforge_api.models import InitializeAgentsRequest
        from vibeforge_api.core.session import session_store

        session = session_store.create_session()
        request = InitializeAgentsRequest(
            agents=[
                {"agent_id": " "},
                {"agent_id": "agent-2"},
            ]
        )

        with pytest.raises(HTTPException) as exc_info:
            await initialize_agents(session.session_id, request)

        assert exc_info.value.status_code == 400
        assert "empty or whitespace" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_simulation_state_returns_agent_roster(self):
        """Test simulation state includes roster with labels."""
        from vibeforge_api.routers.control import (
            initialize_agents,
            assign_agent_role,
            get_simulation_state,
        )
        from vibeforge_api.models import InitializeAgentsRequest, AssignAgentRoleRequest
        from vibeforge_api.core.session import session_store
        from orchestration.models import AgentRole

        session = session_store.create_session()
        init_req = InitializeAgentsRequest(
            agents=[
                {"agent_id": "agent-1", "display_name": "Alpha"},
                {"agent_id": "agent-2", "display_name": "Beta"},
            ]
        )
        await initialize_agents(session.session_id, init_req)

        await assign_agent_role(
            session.session_id,
            AssignAgentRoleRequest(agent_id="agent-1", role="worker", model_id="gpt-4"),
        )
        await assign_agent_role(
            session.session_id,
            AssignAgentRoleRequest(agent_id="agent-2", role="reviewer", model_id="gpt-4o-mini"),
        )

        response = await get_simulation_state(session.session_id)
        roster_by_id = {agent["agent_id"]: agent for agent in response.agents}

        assert roster_by_id["agent-1"]["display_name"] == "Alpha"
        assert roster_by_id["agent-1"]["role"] == "worker"
        assert roster_by_id["agent-1"]["model_id"] == "gpt-4"
        assert roster_by_id["agent-2"]["display_name"] == "Beta"
        assert roster_by_id["agent-2"]["role"] == "reviewer"
        assert roster_by_id["agent-2"]["model_id"] == "gpt-4o-mini"
        assert set(response.available_roles) == {role.value for role in AgentRole}

    @pytest.mark.asyncio
    async def test_simulation_state_empty_roster(self):
        """Test simulation state returns empty roster when no agents configured."""
        from vibeforge_api.routers.control import get_simulation_state
        from vibeforge_api.core.session import session_store

        session = session_store.create_session()
        response = await get_simulation_state(session.session_id)

        assert response.agents == []

    @pytest.mark.asyncio
    async def test_assign_agent_role_unknown_agent(self):
        """Test assign_agent_role with unknown agent."""
        from vibeforge_api.routers.control import assign_agent_role
        from vibeforge_api.models import AssignAgentRoleRequest
        from vibeforge_api.core.session import session_store

        session = session_store.create_session()
        request = AssignAgentRoleRequest(agent_id="unknown", role="worker")

        with pytest.raises(HTTPException) as exc_info:
            await assign_agent_role(session.session_id, request)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_set_main_task(self):
        """Test POST /control/sessions/{id}/task."""
        from vibeforge_api.routers.control import set_main_task
        from vibeforge_api.models import SetMainTaskRequest
        from vibeforge_api.core.session import session_store

        session = session_store.create_session()
        request = SetMainTaskRequest(main_task="Build a web app")

        response = await set_main_task(session.session_id, request)

        assert response.main_task == "Build a web app"
        assert "successfully" in response.message

        # Verify session was updated
        updated_session = session_store.get_session(session.session_id)
        assert updated_session.main_task == "Build a web app"

    @pytest.mark.asyncio
    async def test_configure_agent_flow(self):
        """Test POST /control/sessions/{id}/flows."""
        from vibeforge_api.routers.control import (
            initialize_agents,
            configure_agent_flow,
        )
        from vibeforge_api.models import (
            InitializeAgentsRequest,
            ConfigureAgentFlowRequest,
        )
        from vibeforge_api.core.session import session_store

        # Setup: create session with agents
        session = session_store.create_session()
        init_req = InitializeAgentsRequest(agent_count=3)
        await initialize_agents(session.session_id, init_req)

        # Configure flow
        flow_req = ConfigureAgentFlowRequest(
            edges=[
                {"from_agent": "agent-1", "to_agent": "agent-2"},
                {"from_agent": "agent-2", "to_agent": "agent-3"},
            ]
        )
        response = await configure_agent_flow(session.session_id, flow_req)

        assert response.edge_count == 2
        assert "Configured flow" in response.message

        # Verify session was updated
        updated_session = session_store.get_session(session.session_id)
        assert updated_session.agent_graph is not None
        assert len(updated_session.agent_graph["edges"]) == 2

    @pytest.mark.asyncio
    async def test_configure_agent_flow_bidirectional_round_trip(self):
        """Test bidirectional edges are stored and returned in state."""
        from vibeforge_api.routers.control import (
            initialize_agents,
            configure_agent_flow,
            get_simulation_state,
        )
        from vibeforge_api.models import (
            InitializeAgentsRequest,
            ConfigureAgentFlowRequest,
        )
        from vibeforge_api.core.session import session_store

        session = session_store.create_session()
        await initialize_agents(session.session_id, InitializeAgentsRequest(agent_count=2))

        flow_req = ConfigureAgentFlowRequest(
            edges=[
                {
                    "from_agent": "agent-1",
                    "to_agent": "agent-2",
                    "bidirectional": True,
                }
            ]
        )
        await configure_agent_flow(session.session_id, flow_req)

        state = await get_simulation_state(session.session_id)
        assert state.agent_graph is not None
        assert len(state.agent_graph["edges"]) == 1
        assert state.agent_graph["edges"][0]["from_agent"] == "agent-1"
        assert state.agent_graph["edges"][0]["to_agent"] == "agent-2"
        assert state.agent_graph["edges"][0]["bidirectional"] is True

    @pytest.mark.asyncio
    async def test_configure_agent_flow_allows_cycles(self):
        """Test configure_agent_flow allows cycles."""
        from vibeforge_api.routers.control import (
            initialize_agents,
            configure_agent_flow,
        )
        from vibeforge_api.models import (
            InitializeAgentsRequest,
            ConfigureAgentFlowRequest,
        )
        from vibeforge_api.core.session import session_store

        # Setup
        session = session_store.create_session()
        init_req = InitializeAgentsRequest(agent_count=2)
        await initialize_agents(session.session_id, init_req)

        # Configure cycle
        flow_req = ConfigureAgentFlowRequest(
            edges=[
                {"from_agent": "agent-1", "to_agent": "agent-2"},
                {"from_agent": "agent-2", "to_agent": "agent-1"},  # cycle!
            ]
        )

        response = await configure_agent_flow(session.session_id, flow_req)

        assert response.edge_count == 2
        assert "Configured flow" in response.message

        updated_session = session_store.get_session(session.session_id)
        assert updated_session.agent_graph is not None
        assert len(updated_session.agent_graph["edges"]) == 2

    @pytest.mark.asyncio
    async def test_get_workflow_config(self):
        """Test GET /control/sessions/{id}/workflow."""
        from vibeforge_api.routers.control import (
            initialize_agents,
            assign_agent_role,
            set_main_task,
            get_workflow_config,
        )
        from vibeforge_api.models import (
            InitializeAgentsRequest,
            AssignAgentRoleRequest,
            SetMainTaskRequest,
        )
        from vibeforge_api.core.session import session_store

        # Setup: create full workflow config
        session = session_store.create_session()

        # Initialize agents
        await initialize_agents(
            session.session_id, InitializeAgentsRequest(agent_count=2)
        )

        # Assign roles
        await assign_agent_role(
            session.session_id,
            AssignAgentRoleRequest(agent_id="agent-1", role="worker", model_id="gpt-4"),
        )

        # Set task
        await set_main_task(
            session.session_id, SetMainTaskRequest(main_task="Test workflow")
        )

        # Get config
        response = await get_workflow_config(session.session_id)

        assert len(response.agents) == 2
        assert response.agent_roles == {"agent-1": "worker"}
        assert response.agent_models == {"agent-1": "gpt-4"}
        assert response.main_task == "Test workflow"


class TestAgentWorkflowIntegration:
    """Integration tests for VF-199: full agent workflow lifecycle."""

    @pytest.mark.asyncio
    async def test_full_workflow_init_to_configured(self):
        """Test complete workflow: init → assign → task → flows → verify configured."""
        from vibeforge_api.routers.control import (
            initialize_agents,
            assign_agent_role,
            set_main_task,
            configure_agent_flow,
            get_workflow_config,
        )
        from vibeforge_api.models import (
            InitializeAgentsRequest,
            AssignAgentRoleRequest,
            SetMainTaskRequest,
            ConfigureAgentFlowRequest,
        )
        from vibeforge_api.core.session import session_store

        # Step 1: Create session
        session = session_store.create_session()
        session_id = session.session_id

        # Step 2: Initialize 3 agents
        init_resp = await initialize_agents(
            session_id, InitializeAgentsRequest(agent_count=3)
        )
        assert len(init_resp.agent_ids) == 3
        agent_ids = init_resp.agent_ids

        # Step 3: Assign roles to all agents
        roles = ["orchestrator", "worker", "reviewer"]
        for agent_id, role in zip(agent_ids, roles):
            resp = await assign_agent_role(
                session_id,
                AssignAgentRoleRequest(agent_id=agent_id, role=role, model_id="gpt-4"),
            )
            assert resp.role == role

        # Step 4: Set main task
        task_resp = await set_main_task(
            session_id,
            SetMainTaskRequest(main_task="Build a calculator app"),
        )
        assert task_resp.main_task == "Build a calculator app"

        # Step 5: Configure flow (orchestrator → worker → reviewer)
        flow_resp = await configure_agent_flow(
            session_id,
            ConfigureAgentFlowRequest(
                edges=[
                    {"from_agent": agent_ids[0], "to_agent": agent_ids[1]},
                    {"from_agent": agent_ids[1], "to_agent": agent_ids[2]},
                ]
            ),
        )
        assert flow_resp.edge_count == 2

        # Step 6: Verify workflow is fully configured
        config = await get_workflow_config(session_id)

        assert len(config.agents) == 3
        assert len(config.agent_roles) == 3
        assert config.agent_roles[agent_ids[0]] == "orchestrator"
        assert config.agent_roles[agent_ids[1]] == "worker"
        assert config.agent_roles[agent_ids[2]] == "reviewer"
        assert config.main_task == "Build a calculator app"
        assert config.agent_graph is not None
        assert len(config.agent_graph["edges"]) == 2

    @pytest.mark.asyncio
    async def test_workflow_config_empty_before_init(self):
        """Workflow config shows empty state before initialization."""
        from vibeforge_api.routers.control import get_workflow_config
        from vibeforge_api.core.session import session_store

        session = session_store.create_session()

        config = await get_workflow_config(session.session_id)

        assert len(config.agents) == 0
        assert len(config.agent_roles) == 0
        assert config.main_task is None
        assert config.agent_graph is None

    @pytest.mark.asyncio
    async def test_workflow_reinitialize_clears_assignments(self):
        """Re-initializing agents clears previous role assignments."""
        from vibeforge_api.routers.control import (
            initialize_agents,
            assign_agent_role,
            get_workflow_config,
        )
        from vibeforge_api.models import (
            InitializeAgentsRequest,
            AssignAgentRoleRequest,
        )
        from vibeforge_api.core.session import session_store

        session = session_store.create_session()
        session_id = session.session_id

        # Initialize and assign
        await initialize_agents(session_id, InitializeAgentsRequest(agent_count=2))
        await assign_agent_role(
            session_id,
            AssignAgentRoleRequest(agent_id="agent-1", role="worker"),
        )

        # Verify assignment exists
        config1 = await get_workflow_config(session_id)
        assert "agent-1" in config1.agent_roles

        # Re-initialize with different count
        await initialize_agents(session_id, InitializeAgentsRequest(agent_count=3))

        # Verify: new agents, roles cleared
        config2 = await get_workflow_config(session_id)
        assert len(config2.agents) == 3
        assert len(config2.agent_roles) == 0  # roles should be cleared

    @pytest.mark.asyncio
    async def test_workflow_partial_config_state(self):
        """Test workflow shows correct state when only partially configured."""
        from vibeforge_api.routers.control import (
            initialize_agents,
            assign_agent_role,
            set_main_task,
            get_workflow_config,
        )
        from vibeforge_api.models import (
            InitializeAgentsRequest,
            AssignAgentRoleRequest,
            SetMainTaskRequest,
        )
        from vibeforge_api.core.session import session_store

        session = session_store.create_session()
        session_id = session.session_id

        # Initialize agents only
        await initialize_agents(session_id, InitializeAgentsRequest(agent_count=2))

        config1 = await get_workflow_config(session_id)
        assert len(config1.agents) == 2
        assert len(config1.agent_roles) == 0  # no roles assigned yet
        assert config1.main_task is None
        assert config1.agent_graph is None

        # Add one role assignment
        await assign_agent_role(
            session_id,
            AssignAgentRoleRequest(agent_id="agent-1", role="worker", model_id="gpt-4o"),
        )

        config2 = await get_workflow_config(session_id)
        assert config2.agent_roles == {"agent-1": "worker"}
        assert config2.agent_models == {"agent-1": "gpt-4o"}

        # Set main task
        await set_main_task(
            session_id,
            SetMainTaskRequest(main_task="Test task"),
        )

        config3 = await get_workflow_config(session_id)
        assert config3.main_task == "Test task"

    @pytest.mark.asyncio
    async def test_workflow_flow_validation_rejects_unknown_agents(self):
        """Flow configuration should reject edges with unknown agent IDs."""
        from vibeforge_api.routers.control import (
            initialize_agents,
            configure_agent_flow,
        )
        from vibeforge_api.models import (
            InitializeAgentsRequest,
            ConfigureAgentFlowRequest,
        )
        from vibeforge_api.core.session import session_store

        session = session_store.create_session()
        session_id = session.session_id

        # Initialize 2 agents
        await initialize_agents(session_id, InitializeAgentsRequest(agent_count=2))

        # Try to configure flow with unknown agent
        with pytest.raises(HTTPException) as exc_info:
            await configure_agent_flow(
                session_id,
                ConfigureAgentFlowRequest(
                    edges=[
                        {"from_agent": "agent-1", "to_agent": "unknown-agent"},
                    ]
                ),
            )

        assert exc_info.value.status_code == 400
        assert "Unknown target agent" in exc_info.value.detail
        assert "unknown-agent" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_workflow_flow_validation_rejects_unknown_sources(self):
        """Flow configuration should reject edges with unknown source IDs."""
        from vibeforge_api.routers.control import (
            initialize_agents,
            configure_agent_flow,
        )
        from vibeforge_api.models import (
            InitializeAgentsRequest,
            ConfigureAgentFlowRequest,
        )
        from vibeforge_api.core.session import session_store

        session = session_store.create_session()
        session_id = session.session_id

        await initialize_agents(session_id, InitializeAgentsRequest(agent_count=2))

        with pytest.raises(HTTPException) as exc_info:
            await configure_agent_flow(
                session_id,
                ConfigureAgentFlowRequest(
                    edges=[
                        {"from_agent": "unknown-agent", "to_agent": "agent-1"},
                    ]
                ),
            )

        assert exc_info.value.status_code == 400
        assert "Unknown source agent" in exc_info.value.detail
        assert "unknown-agent" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_workflow_flow_validation_reports_multiple_invalid_agents(self):
        """Flow configuration should report all invalid agent references."""
        from vibeforge_api.routers.control import (
            initialize_agents,
            configure_agent_flow,
        )
        from vibeforge_api.models import (
            InitializeAgentsRequest,
            ConfigureAgentFlowRequest,
        )
        from vibeforge_api.core.session import session_store

        session = session_store.create_session()
        session_id = session.session_id

        await initialize_agents(session_id, InitializeAgentsRequest(agent_count=2))

        with pytest.raises(HTTPException) as exc_info:
            await configure_agent_flow(
                session_id,
                ConfigureAgentFlowRequest(
                    edges=[
                        {"from_agent": "unknown-source", "to_agent": "agent-1"},
                        {"from_agent": "agent-2", "to_agent": "unknown-target"},
                    ]
                ),
            )

        assert exc_info.value.status_code == 400
        assert "Unknown source agent" in exc_info.value.detail
        assert "unknown-source" in exc_info.value.detail
        assert "Unknown target agent" in exc_info.value.detail
        assert "unknown-target" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_workflow_multiple_role_updates(self):
        """Test updating agent roles multiple times."""
        from vibeforge_api.routers.control import (
            initialize_agents,
            assign_agent_role,
            get_workflow_config,
        )
        from vibeforge_api.models import (
            InitializeAgentsRequest,
            AssignAgentRoleRequest,
        )
        from vibeforge_api.core.session import session_store

        session = session_store.create_session()
        session_id = session.session_id

        await initialize_agents(session_id, InitializeAgentsRequest(agent_count=2))

        # First assignment
        await assign_agent_role(
            session_id,
            AssignAgentRoleRequest(agent_id="agent-1", role="worker"),
        )

        config1 = await get_workflow_config(session_id)
        assert config1.agent_roles["agent-1"] == "worker"

        # Update to different role
        await assign_agent_role(
            session_id,
            AssignAgentRoleRequest(agent_id="agent-1", role="orchestrator"),
        )

        config2 = await get_workflow_config(session_id)
        assert config2.agent_roles["agent-1"] == "orchestrator"
