"""Integration tests for LLM simulation flow (FEAT-016)."""

import pytest

from models.base.llm_client import LlmClient, LlmRequest, LlmResponse, LlmUsage
from orchestration.coordinator.tick_engine import TickEngine
from orchestration.models import AgentConfig, AgentFlowEdge, AgentFlowGraph
from vibeforge_api.core.session import session_store
from vibeforge_api.models import SimulationStartRequest
from vibeforge_api.routers.control import advance_tick, start_simulation


class FakeLlmClient(LlmClient):
    """Fake LLM client for integration tests."""

    def __init__(self) -> None:
        self.call_count = 0

    async def complete(self, request: LlmRequest) -> LlmResponse:
        self.call_count += 1
        return LlmResponse(
            content="ok",
            model=request.model,
            finish_reason="stop",
            usage=LlmUsage(prompt_tokens=500, completion_tokens=250, total_tokens=750),
        )

    def get_provider_name(self) -> str:
        return "fake"


@pytest.mark.asyncio
async def test_llm_simulation_integration(monkeypatch):
    fake_client = FakeLlmClient()
    monkeypatch.setattr(
        "orchestration.coordinator.tick_engine.get_llm_client",
        lambda: fake_client,
    )

    session = session_store.create_session()
    session.agents = [
        AgentConfig(agent_id="orchestrator").model_dump(),
        AgentConfig(agent_id="worker-1").model_dump(),
    ]
    session.agent_roles = {
        "orchestrator": "orchestrator",
        "worker-1": "worker",
    }
    session.agent_models = {
        "orchestrator": "gpt-4o-mini",
        "worker-1": "gpt-4o-mini",
    }
    session.agent_graph = AgentFlowGraph(
        edges=[
            AgentFlowEdge(from_agent="orchestrator", to_agent="worker-1", bidirectional=True),
        ]
    ).model_dump()
    session.main_task = "Resolve a simple math question."
    session.use_real_llm = True
    session.max_cost_usd = 10.0
    session.tick_rate_limit_ms = 0
    session_store.update_session(session)

    await start_simulation(
        session.session_id,
        SimulationStartRequest(
            initial_prompt="Solve 3 + 3 * 3.",
            first_agent_id="orchestrator",
        ),
    )

    costs: list[float] = []

    await advance_tick(session.session_id)
    session = session_store.get_session(session.session_id)
    costs.append(session.simulation_cost_usd)

    await advance_tick(session.session_id)
    session = session_store.get_session(session.session_id)
    costs.append(session.simulation_cost_usd)

    engine = TickEngine(session, llm_client=fake_client)
    engine.send_message(
        "orchestrator",
        "worker-1",
        {"text": "Follow up with a second check.", "expect_response": True},
        bypass_validation=True,
    )
    engine.sync_session_state()
    session_store.update_session(session)

    await advance_tick(session.session_id)
    session = session_store.get_session(session.session_id)
    costs.append(session.simulation_cost_usd)

    await advance_tick(session.session_id)
    session = session_store.get_session(session.session_id)
    costs.append(session.simulation_cost_usd)

    await advance_tick(session.session_id)
    session = session_store.get_session(session.session_id)
    costs.append(session.simulation_cost_usd)

    assert fake_client.call_count >= 2
    assert costs[0] > 0
    assert costs[2] > costs[0]
    assert all(next_cost >= prev for prev, next_cost in zip(costs, costs[1:]))

    messages = session.simulation_message_queue or []
    non_stub_messages = [
        msg for msg in messages
        if isinstance(msg.get("content"), dict)
        and msg["content"].get("is_stub") is False
    ]
    assert non_stub_messages

    conversations = session.simulation_agent_conversations or {}
    assert conversations.get("orchestrator")
    assert conversations.get("worker-1")
