"""Tests for simulation API endpoints (VF-200, VF-201)."""

import pytest
from fastapi import HTTPException

from vibeforge_api.core.session import session_store, Session
from vibeforge_api.models.types import SessionPhase


class TestSimulationConfig:
    """Tests for VF-200: POST /control/sessions/{id}/simulation/config."""

    @pytest.mark.asyncio
    async def test_configure_simulation_success(self):
        """Test successful simulation configuration."""
        from vibeforge_api.routers.control import configure_simulation
        from vibeforge_api.models import SimulationConfigRequest

        session = session_store.create_session()
        request = SimulationConfigRequest(
            simulation_mode="auto",
            auto_delay_ms=1000,
            tick_budget=50,
        )

        response = await configure_simulation(session.session_id, request)

        assert response.simulation_mode == "auto"
        assert response.auto_delay_ms == 1000
        assert response.tick_budget == 50
        assert "updated" in response.message

    @pytest.mark.asyncio
    async def test_configure_simulation_session_not_found(self):
        """Test configuration with non-existent session."""
        from vibeforge_api.routers.control import configure_simulation
        from vibeforge_api.models import SimulationConfigRequest

        request = SimulationConfigRequest(simulation_mode="manual")

        with pytest.raises(HTTPException) as exc_info:
            await configure_simulation("nonexistent", request)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_configure_simulation_terminal_phase_rejected(self):
        """Test configuration rejected in terminal phases."""
        from vibeforge_api.routers.control import configure_simulation
        from vibeforge_api.models import SimulationConfigRequest

        session = session_store.create_session()
        session.phase = SessionPhase.COMPLETE
        session_store.update_session(session)

        request = SimulationConfigRequest(simulation_mode="auto")

        with pytest.raises(HTTPException) as exc_info:
            await configure_simulation(session.session_id, request)

        assert exc_info.value.status_code == 400
        assert "COMPLETE" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_configure_simulation_while_running_rejected(self):
        """Test configuration rejected while simulation is running."""
        from vibeforge_api.routers.control import configure_simulation
        from vibeforge_api.models import SimulationConfigRequest

        session = session_store.create_session()
        session.tick_status = "running"
        session_store.update_session(session)

        request = SimulationConfigRequest(simulation_mode="auto")

        with pytest.raises(HTTPException) as exc_info:
            await configure_simulation(session.session_id, request)

        assert exc_info.value.status_code == 400
        assert "running" in exc_info.value.detail.lower()


class TestSimulationStart:
    """Tests for VF-200: POST /control/sessions/{id}/simulation/start."""

    def _build_start_request(
        self,
        initial_prompt: str | None = "Begin simulation",
        first_agent_id: str | None = "agent-1",
    ):
        from vibeforge_api.models import SimulationStartRequest

        return SimulationStartRequest(
            initial_prompt=initial_prompt,
            first_agent_id=first_agent_id,
        )

    def _setup_complete_workflow(self, session: Session) -> None:
        """Helper to set up a complete workflow configuration."""
        from orchestration.models import AgentConfig, AgentFlowGraph, AgentFlowEdge

        # Initialize agents
        session.agents = [
            AgentConfig(agent_id="agent-1").model_dump(),
            AgentConfig(agent_id="agent-2").model_dump(),
        ]
        # Assign roles
        session.agent_roles = {"agent-1": "worker", "agent-2": "reviewer"}
        # Configure flow
        session.agent_graph = AgentFlowGraph(
            edges=[AgentFlowEdge(from_agent="agent-1", to_agent="agent-2")]
        ).model_dump()
        # Set main task
        session.main_task = "Test task"
        session_store.update_session(session)

    @pytest.mark.asyncio
    async def test_start_simulation_success(self):
        """Test successful simulation start with complete workflow."""
        from vibeforge_api.routers.control import start_simulation

        session = session_store.create_session()
        self._setup_complete_workflow(session)

        response = await start_simulation(
            session.session_id, self._build_start_request()
        )

        assert response.tick_status == "running"
        assert response.tick_index == 0
        assert "started" in response.message.lower()

    @pytest.mark.asyncio
    async def test_start_simulation_missing_initial_prompt(self):
        """Test start rejected when initial prompt is missing."""
        from vibeforge_api.routers.control import start_simulation

        session = session_store.create_session()
        self._setup_complete_workflow(session)

        request = self._build_start_request(initial_prompt=None)
        with pytest.raises(HTTPException) as exc_info:
            await start_simulation(session.session_id, request)

        assert exc_info.value.status_code == 400
        assert "initial_prompt" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_start_simulation_missing_first_agent(self):
        """Test start rejected when first agent is missing."""
        from vibeforge_api.routers.control import start_simulation

        session = session_store.create_session()
        self._setup_complete_workflow(session)

        request = self._build_start_request(first_agent_id=None)
        with pytest.raises(HTTPException) as exc_info:
            await start_simulation(session.session_id, request)

        assert exc_info.value.status_code == 400
        assert "first_agent_id" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_start_simulation_invalid_first_agent(self):
        """Test start rejected when first agent is not in roster."""
        from vibeforge_api.routers.control import start_simulation

        session = session_store.create_session()
        self._setup_complete_workflow(session)

        request = self._build_start_request(first_agent_id="unknown-agent")
        with pytest.raises(HTTPException) as exc_info:
            await start_simulation(session.session_id, request)

        assert exc_info.value.status_code == 400
        assert "unknown-agent" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_start_simulation_session_not_found(self):
        """Test start with non-existent session."""
        from vibeforge_api.routers.control import start_simulation

        request = self._build_start_request()
        with pytest.raises(HTTPException) as exc_info:
            await start_simulation("nonexistent", request)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_start_simulation_no_agents(self):
        """Test start rejected when no agents initialized."""
        from vibeforge_api.routers.control import start_simulation

        session = session_store.create_session()
        # Don't set up agents

        request = self._build_start_request()
        with pytest.raises(HTTPException) as exc_info:
            await start_simulation(session.session_id, request)

        assert exc_info.value.status_code == 400
        assert "no agents" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_start_simulation_agents_without_roles(self):
        """Test start rejected when agents don't have roles."""
        from vibeforge_api.routers.control import start_simulation
        from orchestration.models import AgentConfig

        session = session_store.create_session()
        session.agents = [AgentConfig(agent_id="agent-1").model_dump()]
        # Don't assign roles
        session_store.update_session(session)

        request = self._build_start_request()
        with pytest.raises(HTTPException) as exc_info:
            await start_simulation(session.session_id, request)

        assert exc_info.value.status_code == 400
        assert "without roles" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_start_simulation_no_flow_graph(self):
        """Test start rejected when flow graph not configured."""
        from vibeforge_api.routers.control import start_simulation
        from orchestration.models import AgentConfig

        session = session_store.create_session()
        session.agents = [AgentConfig(agent_id="agent-1").model_dump()]
        session.agent_roles = {"agent-1": "worker"}
        # Don't configure flow graph
        session_store.update_session(session)

        request = self._build_start_request()
        with pytest.raises(HTTPException) as exc_info:
            await start_simulation(session.session_id, request)

        assert exc_info.value.status_code == 400
        assert "flow graph" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_start_simulation_no_main_task(self):
        """Test start rejected when main task not set."""
        from vibeforge_api.routers.control import start_simulation
        from orchestration.models import AgentConfig, AgentFlowGraph, AgentFlowEdge

        session = session_store.create_session()
        session.agents = [AgentConfig(agent_id="agent-1").model_dump()]
        session.agent_roles = {"agent-1": "worker"}
        session.agent_graph = AgentFlowGraph(
            edges=[AgentFlowEdge(from_agent="agent-1", to_agent="agent-1")]
        ).model_dump()
        # Don't set main task
        session_store.update_session(session)

        request = self._build_start_request()
        with pytest.raises(HTTPException) as exc_info:
            await start_simulation(session.session_id, request)

        assert exc_info.value.status_code == 400
        assert "main task" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_start_simulation_already_running(self):
        """Test start rejected when simulation already running."""
        from vibeforge_api.routers.control import start_simulation

        session = session_store.create_session()
        self._setup_complete_workflow(session)
        session.tick_status = "running"
        session_store.update_session(session)

        request = self._build_start_request()
        with pytest.raises(HTTPException) as exc_info:
            await start_simulation(session.session_id, request)

        assert exc_info.value.status_code == 400
        assert "already running" in exc_info.value.detail.lower()


class TestSimulationReset:
    """Tests for VF-200: POST /control/sessions/{id}/simulation/reset."""

    @pytest.mark.asyncio
    async def test_reset_simulation_preserve_workflow(self):
        """Test reset preserves workflow config when requested."""
        from vibeforge_api.routers.control import reset_simulation
        from vibeforge_api.models import SimulationResetRequest
        from orchestration.models import AgentConfig

        session = session_store.create_session()
        session.agents = [AgentConfig(agent_id="agent-1").model_dump()]
        session.agent_roles = {"agent-1": "worker"}
        session.main_task = "Test task"
        session.tick_index = 10
        session.tick_status = "running"
        session.initial_prompt = "Seed prompt"
        session.first_agent_id = "agent-1"
        session_store.update_session(session)

        request = SimulationResetRequest(preserve_workflow=True)
        response = await reset_simulation(session.session_id, request)

        assert response.tick_index == 0
        assert response.tick_status == "idle"
        assert response.workflow_preserved is True

        # Verify workflow still exists
        updated = session_store.get_session(session.session_id)
        assert len(updated.agents) == 1
        assert updated.main_task == "Test task"
        assert updated.initial_prompt is None
        assert updated.first_agent_id is None

    @pytest.mark.asyncio
    async def test_reset_simulation_clear_workflow(self):
        """Test reset clears workflow config when requested."""
        from vibeforge_api.routers.control import reset_simulation
        from vibeforge_api.models import SimulationResetRequest
        from orchestration.models import AgentConfig

        session = session_store.create_session()
        session.agents = [AgentConfig(agent_id="agent-1").model_dump()]
        session.agent_roles = {"agent-1": "worker"}
        session.main_task = "Test task"
        session.tick_index = 10
        session.tick_status = "running"
        session_store.update_session(session)

        request = SimulationResetRequest(preserve_workflow=False)
        response = await reset_simulation(session.session_id, request)

        assert response.tick_index == 0
        assert response.tick_status == "idle"
        assert response.workflow_preserved is False

        # Verify workflow cleared
        updated = session_store.get_session(session.session_id)
        assert len(updated.agents) == 0
        assert updated.main_task is None

    @pytest.mark.asyncio
    async def test_reset_simulation_session_not_found(self):
        """Test reset with non-existent session."""
        from vibeforge_api.routers.control import reset_simulation
        from vibeforge_api.models import SimulationResetRequest

        request = SimulationResetRequest(preserve_workflow=True)

        with pytest.raises(HTTPException) as exc_info:
            await reset_simulation("nonexistent", request)

        assert exc_info.value.status_code == 404


class TestTickAdvance:
    """Tests for VF-201: POST /control/sessions/{id}/simulation/tick."""

    @pytest.mark.asyncio
    async def test_advance_tick_success(self):
        """Test successful single tick advance."""
        from vibeforge_api.routers.control import advance_tick

        session = session_store.create_session()
        session.tick_status = "running"
        session.tick_index = 5
        session_store.update_session(session)

        response = await advance_tick(session.session_id)

        assert response.tick_index == 6
        assert response.new_tick_index == 6
        assert response.tick_status == "running"
        assert "tick 6" in response.message
        assert response.processed_event_count == len(response.processed_events)
        assert len(response.tick_summaries) == 1
        assert response.tick_summaries[0].new_tick_index == 6

    @pytest.mark.asyncio
    async def test_advance_tick_not_started(self):
        """Test tick advance rejected when simulation not started."""
        from vibeforge_api.routers.control import advance_tick

        session = session_store.create_session()
        # tick_status defaults to "idle"

        with pytest.raises(HTTPException) as exc_info:
            await advance_tick(session.session_id)

        assert exc_info.value.status_code == 400
        assert "not started" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_advance_tick_session_not_found(self):
        """Test tick advance with non-existent session."""
        from vibeforge_api.routers.control import advance_tick

        with pytest.raises(HTTPException) as exc_info:
            await advance_tick("nonexistent")

        assert exc_info.value.status_code == 404


class TestTicksAdvance:
    """Tests for VF-201: POST /control/sessions/{id}/simulation/ticks."""

    @pytest.mark.asyncio
    async def test_advance_ticks_success(self):
        """Test successful multi-tick advance."""
        from vibeforge_api.routers.control import advance_ticks
        from vibeforge_api.models import TickRequest

        session = session_store.create_session()
        session.tick_status = "running"
        session.tick_index = 0
        session_store.update_session(session)

        request = TickRequest(tick_count=10)
        response = await advance_ticks(session.session_id, request)

        assert response.tick_index == 10
        assert response.new_tick_index == 10
        assert "10 ticks" in response.message
        assert "0 -> 10" in response.message
        assert response.processed_event_count == len(response.processed_events)
        assert len(response.tick_summaries) == 10
        assert response.tick_summaries[-1].new_tick_index == 10

    @pytest.mark.asyncio
    async def test_advance_ticks_emits_per_tick_events(self):
        """Multi-tick advance should emit per-tick events with tick metadata."""
        from vibeforge_api.routers.control import advance_ticks
        from vibeforge_api.models import TickRequest
        from orchestration.coordinator.tick_engine import TickEngine
        from orchestration.models import AgentConfig, AgentFlowGraph, AgentFlowEdge

        session = session_store.create_session()
        session.tick_status = "running"
        session.tick_index = 0
        session.agents = [
            AgentConfig(agent_id="agent-1").model_dump(),
            AgentConfig(agent_id="agent-2").model_dump(),
        ]
        session.agent_roles = {
            "agent-1": "orchestrator",
            "agent-2": "worker",
        }
        session.agent_graph = AgentFlowGraph(
            edges=[AgentFlowEdge(from_agent="agent-1", to_agent="agent-2")]
        ).model_dump()
        session_store.update_session(session)

        engine = TickEngine(session)
        success, _ = engine.send_message(
            "agent-1",
            "agent-2",
            {"text": "ping", "expect_response": True},
        )
        assert success
        engine.sync_session_state()
        session_store.update_session(session)

        request = TickRequest(tick_count=3)
        response = await advance_ticks(session.session_id, request)

        tick_events = [
            event for event in response.processed_events
            if event.get("event_type") == "tick_advanced"
        ]
        assert len(tick_events) == 3
        assert tick_events[0]["metadata"]["old_tick_index"] == 0
        assert tick_events[0]["metadata"]["new_tick_index"] == 1
        assert tick_events[-1]["metadata"]["new_tick_index"] == 3

        message_events = [
            event for event in response.processed_events
            if event.get("event_type") == "message_sent"
        ]
        assert any(
            event.get("metadata", {}).get("tick_index") == 1
            for event in message_events
        )

    @pytest.mark.asyncio
    async def test_advance_ticks_not_started(self):
        """Test multi-tick advance rejected when simulation not started."""
        from vibeforge_api.routers.control import advance_ticks
        from vibeforge_api.models import TickRequest

        session = session_store.create_session()
        request = TickRequest(tick_count=5)

        with pytest.raises(HTTPException) as exc_info:
            await advance_ticks(session.session_id, request)

        assert exc_info.value.status_code == 400
        assert "not started" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_advance_ticks_session_not_found(self):
        """Test multi-tick advance with non-existent session."""
        from vibeforge_api.routers.control import advance_ticks
        from vibeforge_api.models import TickRequest

        request = TickRequest(tick_count=5)

        with pytest.raises(HTTPException) as exc_info:
            await advance_ticks("nonexistent", request)

        assert exc_info.value.status_code == 404


class TestSimulationPause:
    """Tests for VF-201: POST /control/sessions/{id}/simulation/pause."""

    @pytest.mark.asyncio
    async def test_pause_simulation_success(self):
        """Test successful simulation pause."""
        from vibeforge_api.routers.control import pause_simulation

        session = session_store.create_session()
        session.tick_status = "running"
        session.tick_index = 5
        session_store.update_session(session)

        response = await pause_simulation(session.session_id)

        assert response.tick_status == "paused"
        assert response.tick_index == 5
        assert "paused" in response.message.lower()

    @pytest.mark.asyncio
    async def test_pause_simulation_not_running(self):
        """Test pause rejected when simulation not running."""
        from vibeforge_api.routers.control import pause_simulation

        session = session_store.create_session()
        session.tick_status = "idle"
        session_store.update_session(session)

        with pytest.raises(HTTPException) as exc_info:
            await pause_simulation(session.session_id)

        assert exc_info.value.status_code == 400
        assert "not running" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_pause_simulation_session_not_found(self):
        """Test pause with non-existent session."""
        from vibeforge_api.routers.control import pause_simulation

        with pytest.raises(HTTPException) as exc_info:
            await pause_simulation("nonexistent")

        assert exc_info.value.status_code == 404


class TestSimulationState:
    """Tests for VF-201: GET /control/sessions/{id}/simulation/state."""

    @pytest.mark.asyncio
    async def test_get_simulation_state_success(self):
        """Test successful state retrieval."""
        from vibeforge_api.routers.control import get_simulation_state
        from orchestration.models import AgentConfig

        session = session_store.create_session()
        session.simulation_mode = "auto"
        session.tick_index = 10
        session.tick_status = "running"
        session.auto_delay_ms = 500
        session.tick_budget = 25
        session.initial_prompt = "Kickoff"
        session.first_agent_id = "agent-1"
        session.agents = [AgentConfig(agent_id="agent-1").model_dump()]
        session_store.update_session(session)

        response = await get_simulation_state(session.session_id)

        assert response.simulation_mode == "auto"
        assert response.tick_index == 10
        assert response.tick_status == "running"
        assert response.auto_delay_ms == 500
        assert response.tick_budget == 25
        assert response.initial_prompt == "Kickoff"
        assert response.first_agent_id == "agent-1"
        assert "1 agents" in response.pending_work_summary

    @pytest.mark.asyncio
    async def test_get_simulation_state_empty_agents(self):
        """Test state retrieval with no agents configured."""
        from vibeforge_api.routers.control import get_simulation_state

        session = session_store.create_session()

        response = await get_simulation_state(session.session_id)

        assert response.simulation_mode == "manual"  # default
        assert response.tick_index == 0
        assert response.tick_status == "idle"
        assert response.initial_prompt is None
        assert response.first_agent_id is None
        assert response.pending_work_summary is None

    @pytest.mark.asyncio
    async def test_get_simulation_state_session_not_found(self):
        """Test state retrieval with non-existent session."""
        from vibeforge_api.routers.control import get_simulation_state

        with pytest.raises(HTTPException) as exc_info:
            await get_simulation_state("nonexistent")

        assert exc_info.value.status_code == 404


class TestSimulationIntegration:
    """Integration tests for full simulation lifecycle."""

    @pytest.mark.asyncio
    async def test_full_lifecycle_config_start_tick_pause_reset(self):
        """Test complete simulation lifecycle: config → start → tick → pause → reset."""
        from vibeforge_api.routers.control import (
            initialize_agents,
            assign_agent_role,
            set_main_task,
            configure_agent_flow,
            configure_simulation,
            start_simulation,
            advance_tick,
            pause_simulation,
            reset_simulation,
            get_simulation_state,
        )
        from vibeforge_api.models import (
            InitializeAgentsRequest,
            AssignAgentRoleRequest,
            SetMainTaskRequest,
            ConfigureAgentFlowRequest,
            SimulationConfigRequest,
            SimulationStartRequest,
            SimulationResetRequest,
        )

        # Step 1: Create session and configure workflow
        session = session_store.create_session()
        session_id = session.session_id

        # Initialize 2 agents
        await initialize_agents(session_id, InitializeAgentsRequest(agent_count=2))

        # Assign roles
        await assign_agent_role(
            session_id, AssignAgentRoleRequest(agent_id="agent-1", role="worker")
        )
        await assign_agent_role(
            session_id, AssignAgentRoleRequest(agent_id="agent-2", role="reviewer")
        )

        # Set task
        await set_main_task(session_id, SetMainTaskRequest(main_task="Integration test"))

        # Configure flow
        await configure_agent_flow(
            session_id,
            ConfigureAgentFlowRequest(
                edges=[{"from_agent": "agent-1", "to_agent": "agent-2"}]
            ),
        )

        # Step 2: Configure simulation
        config_resp = await configure_simulation(
            session_id,
            SimulationConfigRequest(simulation_mode="manual", auto_delay_ms=100),
        )
        assert config_resp.simulation_mode == "manual"

        # Step 3: Start simulation
        start_resp = await start_simulation(
            session_id,
            SimulationStartRequest(
                initial_prompt="Integration test kickoff",
                first_agent_id="agent-1",
            ),
        )
        assert start_resp.tick_status == "running"
        assert start_resp.tick_index == 0

        # Step 4: Advance ticks
        tick1 = await advance_tick(session_id)
        assert tick1.tick_index == 1

        tick2 = await advance_tick(session_id)
        assert tick2.tick_index == 2

        # Step 5: Pause
        pause_resp = await pause_simulation(session_id)
        assert pause_resp.tick_status == "paused"
        assert pause_resp.tick_index == 2

        # Step 6: Check state
        state = await get_simulation_state(session_id)
        assert state.tick_status == "paused"
        assert state.tick_index == 2

        # Step 7: Reset (preserving workflow)
        reset_resp = await reset_simulation(
            session_id, SimulationResetRequest(preserve_workflow=True)
        )
        assert reset_resp.tick_index == 0
        assert reset_resp.tick_status == "idle"
        assert reset_resp.workflow_preserved is True

        # Verify workflow still intact
        final_state = await get_simulation_state(session_id)
        assert final_state.tick_index == 0
        assert "2 agents" in final_state.pending_work_summary


class TestFilteredEventsEndpoint:
    """Tests for VF-206: GET /control/sessions/{id}/events/filter endpoint.

    Note: The EventLog.get_events_filtered() method is thoroughly tested in
    test_event_log.py::TestEventLogFiltering. These tests verify the endpoint
    interface and error handling.
    """

    @pytest.mark.asyncio
    async def test_get_filtered_events_session_not_found(self):
        """Test filter with non-existent session."""
        from vibeforge_api.routers.control import get_filtered_events

        with pytest.raises(HTTPException) as exc_info:
            await get_filtered_events("nonexistent")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_filtered_events_endpoint_signature(self):
        """Test the endpoint accepts all filter parameters."""
        from vibeforge_api.routers.control import get_filtered_events
        import inspect

        sig = inspect.signature(get_filtered_events)
        params = list(sig.parameters.keys())

        # Verify all filter parameters exist
        assert "session_id" in params
        assert "event_type" in params
        assert "tick_index" in params
        assert "tick_min" in params
        assert "tick_max" in params
        assert "agent_id" in params
        assert "limit" in params
