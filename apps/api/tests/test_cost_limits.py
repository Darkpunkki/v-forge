"""Tests for cost limits on control dispatch endpoints."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from vibeforge_api.core.connection_manager import AgentConnection, get_connection_manager, reset_connection_manager
from vibeforge_api.core.cost_tracker import get_cost_tracker, reset_cost_tracker
from vibeforge_api.main import app


@pytest.fixture(autouse=True)
def reset_state():
    reset_connection_manager()
    reset_cost_tracker()
    yield
    reset_connection_manager()
    reset_cost_tracker()


def register_agent(client: TestClient) -> str:
    response = client.post(
        "/control/agents/register",
        json={"name": "Agent Alpha", "endpoint_url": "ws://localhost:8000/ws/agent-bridge"},
    )
    assert response.status_code == 200
    return response.json()["agent"]["agent_id"]


def connect_agent(agent_id: str) -> None:
    manager = get_connection_manager()
    manager._connections[agent_id] = AgentConnection(
        agent_id=agent_id,
        websocket=AsyncMock(),
        auth_token="token",
        session_id="session-1",
    )


def test_control_context_includes_cost_status(auth_headers):
    client = TestClient(app, headers=auth_headers)
    response = client.get("/control/context")

    assert response.status_code == 200
    payload = response.json()
    assert "session_cost_usd" in payload
    assert "daily_cost_usd" in payload
    assert "session_limit_usd" in payload
    assert "daily_limit_usd" in payload


def test_dispatch_blocked_when_session_limit_exceeded(monkeypatch, auth_headers):
    monkeypatch.setenv("VIBEFORGE_SESSION_COST_LIMIT_USD", "1")
    monkeypatch.setenv("VIBEFORGE_DAILY_COST_LIMIT_USD", "100")

    client = TestClient(app, headers=auth_headers)
    session_id = client.get("/control/context").json()["control_session_id"]

    tracker = get_cost_tracker()
    tracker.record_usage(session_id, {"cost_usd": 2.0})

    agent_id = register_agent(client)
    connect_agent(agent_id)

    response = client.post(
        f"/control/agents/{agent_id}/dispatch",
        json={"content": "Run diagnostics"},
    )

    assert response.status_code == 402


def test_dispatch_blocked_when_daily_limit_exceeded(monkeypatch, auth_headers):
    monkeypatch.setenv("VIBEFORGE_SESSION_COST_LIMIT_USD", "100")
    monkeypatch.setenv("VIBEFORGE_DAILY_COST_LIMIT_USD", "1")

    client = TestClient(app, headers=auth_headers)
    session_id = client.get("/control/context").json()["control_session_id"]

    tracker = get_cost_tracker()
    tracker.record_usage(session_id, {"cost_usd": 2.0})

    agent_id = register_agent(client)
    connect_agent(agent_id)

    response = client.post(
        f"/control/agents/{agent_id}/dispatch",
        json={"content": "Run diagnostics"},
    )

    assert response.status_code == 402
