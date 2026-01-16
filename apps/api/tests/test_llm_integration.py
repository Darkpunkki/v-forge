"""Tests for LLM integration helpers (FEAT-016)."""

from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from models.base.llm_client import LlmClient, LlmMessage, LlmRequest, LlmResponse, LlmUsage
from orchestration.coordinator.llm_response_generator import LlmResponseGenerator
from orchestration.coordinator.tick_engine import (
    MODEL_PRICING_USD_PER_M_TOKEN,
    TickEngine,
)
from orchestration.models import AgentConfig
from orchestration.prompts import AGENT_ROLE_PROMPTS
from vibeforge_api.core.event_log import EventType
from vibeforge_api.core.session import session_store
from vibeforge_api.routers.control import advance_tick


class FakeLlmClient(LlmClient):
    """Fake LLM client that captures requests."""

    def __init__(
        self,
        response: LlmResponse | None = None,
        raise_error: Exception | None = None,
    ) -> None:
        self.last_request: LlmRequest | None = None
        self.call_count = 0
        self.response = response
        self.raise_error = raise_error

    async def complete(self, request: LlmRequest) -> LlmResponse:
        self.call_count += 1
        self.last_request = request
        if self.raise_error is not None:
            raise self.raise_error
        if self.response is not None:
            return self.response
        return LlmResponse(
            content="ok",
            model=request.model,
            finish_reason="stop",
            usage=LlmUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        )

    def get_provider_name(self) -> str:
        return "fake"


def _create_running_session(use_real_llm: bool = False, max_history_depth: int | None = None):
    session = session_store.create_session()
    session.agents = [
        AgentConfig(agent_id="orchestrator").model_dump(),
        AgentConfig(agent_id="worker-1").model_dump(),
    ]
    session.agent_roles = {
        "orchestrator": "orchestrator",
        "worker-1": "worker",
    }
    session.agent_models = {"worker-1": "gpt-4o-mini"}
    session.tick_status = "running"
    session.use_real_llm = use_real_llm
    session.default_model = "gpt-4o-mini"
    session.default_temperature = 0.7
    if max_history_depth is not None:
        session.max_history_depth = max_history_depth
    session_store.update_session(session)
    return session


@pytest.mark.asyncio
@pytest.mark.parametrize("role", sorted(AGENT_ROLE_PROMPTS.keys()))
async def test_generate_response_uses_role_prompt(role: str):
    client = FakeLlmClient()
    generator = LlmResponseGenerator(client)

    await generator.generate_response(
        agent_id="agent-1",
        agent_role=role,
        agent_model="gpt-4o-mini",
        message_history=[],
        incoming_message={"text": "ping"},
    )

    assert client.last_request is not None
    assert client.last_request.messages[0] == LlmMessage(
        role="system",
        content=AGENT_ROLE_PROMPTS[role],
    )


@pytest.mark.asyncio
async def test_generate_response_falls_back_to_worker_prompt():
    client = FakeLlmClient()
    generator = LlmResponseGenerator(client)

    await generator.generate_response(
        agent_id="agent-1",
        agent_role="unknown",
        agent_model="gpt-4o-mini",
        message_history=[],
        incoming_message="hello",
    )

    assert client.last_request is not None
    assert client.last_request.messages[0].content == AGENT_ROLE_PROMPTS["worker"]


@pytest.mark.asyncio
async def test_generate_response_builds_history():
    client = FakeLlmClient()
    generator = LlmResponseGenerator(client)

    await generator.generate_response(
        agent_id="agent-1",
        agent_role="worker",
        agent_model="gpt-4o-mini",
        message_history=[
            {"role": "user", "content": {"text": "first"}},
            {"role": "assistant", "content": "second"},
        ],
        incoming_message={"text": "third"},
    )

    assert client.last_request is not None
    assert len(client.last_request.messages) == 4
    assert client.last_request.messages[1].content == "first"
    assert client.last_request.messages[2].content == "second"
    assert client.last_request.messages[3].content == "third"


@pytest.mark.asyncio
async def test_tick_engine_tracks_conversation_history_per_agent():
    session = _create_running_session(use_real_llm=False)
    engine = TickEngine(session, llm_client=FakeLlmClient())

    engine.send_message(
        "orchestrator",
        "worker-1",
        {"text": "ping", "expect_response": True},
    )
    await engine.advance_tick()

    history = engine.agent_conversations.get("worker-1", [])
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"]["text"] == "ping"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"]["is_stub"] is True


@pytest.mark.asyncio
async def test_tick_engine_limits_history_depth():
    session = _create_running_session(use_real_llm=False, max_history_depth=2)
    engine = TickEngine(session, llm_client=FakeLlmClient())

    engine.send_message(
        "orchestrator",
        "worker-1",
        {"text": "first", "expect_response": True},
    )
    await engine.advance_tick()

    engine.send_message(
        "orchestrator",
        "worker-1",
        {"text": "second", "expect_response": True},
    )
    await engine.advance_tick()
    await engine.advance_tick()

    history = engine.agent_conversations.get("worker-1", [])
    assert len(history) == 2
    assert history[0]["content"]["text"] == "second"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"]["is_stub"] is True


@pytest.mark.asyncio
async def test_tick_engine_tracks_cost_from_llm_usage():
    usage = LlmUsage(prompt_tokens=1000, completion_tokens=500, total_tokens=1500)
    response = LlmResponse(
        content="ok",
        model="gpt-4o-mini",
        finish_reason="stop",
        usage=usage,
    )
    client = FakeLlmClient(response=response)
    session = _create_running_session(use_real_llm=True)
    engine = TickEngine(session, llm_client=client)

    engine.send_message(
        "orchestrator",
        "worker-1",
        {"text": "ping", "expect_response": True},
    )
    result = await engine.advance_tick()

    rates = MODEL_PRICING_USD_PER_M_TOKEN["gpt-4o-mini"]
    expected_cost = (
        usage.prompt_tokens / 1_000_000 * rates["prompt"]
        + usage.completion_tokens / 1_000_000 * rates["completion"]
    )

    assert session.simulation_cost_usd == pytest.approx(expected_cost)
    cost_events = [
        event for event in result.events if event.event_type == EventType.COST_TRACKING
    ]
    assert len(cost_events) == 1
    assert cost_events[0].metadata["cost_usd"] == pytest.approx(expected_cost)
    assert result.messages_sent[0].content.get("is_stub") is False


@pytest.mark.asyncio
async def test_llm_failure_falls_back_to_stub_response():
    client = FakeLlmClient(raise_error=RuntimeError("boom"))
    session = _create_running_session(use_real_llm=True)
    engine = TickEngine(session, llm_client=client)

    engine.send_message(
        "orchestrator",
        "worker-1",
        {"text": "ping", "expect_response": True},
    )
    result = await engine.advance_tick()

    assert client.call_count == 1
    assert any(event.event_type == EventType.LLM_FAILURE for event in result.events)
    assert result.messages_sent[0].content.get("is_stub") is True


@pytest.mark.asyncio
async def test_stub_used_when_real_llm_disabled():
    client = FakeLlmClient(raise_error=RuntimeError("should not be called"))
    session = _create_running_session(use_real_llm=False)
    engine = TickEngine(session, llm_client=client)

    engine.send_message(
        "orchestrator",
        "worker-1",
        {"text": "ping", "expect_response": True},
    )
    result = await engine.advance_tick()

    assert client.call_count == 0
    assert result.messages_sent[0].content.get("is_stub") is True


@pytest.mark.asyncio
async def test_advance_tick_blocks_when_cost_budget_exceeded():
    session = session_store.create_session()
    session.tick_status = "running"
    session.simulation_cost_usd = 2.0
    session.max_cost_usd = 1.0
    session_store.update_session(session)

    with pytest.raises(HTTPException) as excinfo:
        await advance_tick(session.session_id)

    assert excinfo.value.status_code == 429
    assert "Cost budget exceeded" in excinfo.value.detail


@pytest.mark.asyncio
async def test_advance_tick_blocks_when_rate_limited():
    session = session_store.create_session()
    session.tick_status = "running"
    session.use_real_llm = True
    session.tick_rate_limit_ms = 1000
    session.last_tick_timestamp = datetime.now(timezone.utc)
    session_store.update_session(session)

    with pytest.raises(HTTPException) as excinfo:
        await advance_tick(session.session_id)

    assert excinfo.value.status_code == 429
    assert "Rate limit" in excinfo.value.detail
