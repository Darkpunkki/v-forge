"""Tests for rate limiting on dispatch endpoints."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from vibeforge_api.core.connection_manager import AgentConnection, get_connection_manager, reset_connection_manager
from vibeforge_api.main import app
from vibeforge_api.middleware.rate_limiter import reset_rate_limiter_state


@pytest.fixture(autouse=True)
def reset_manager():
    reset_connection_manager()
    reset_rate_limiter_state()
    yield
    reset_connection_manager()
    reset_rate_limiter_state()


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


def test_rate_limit_per_agent(monkeypatch, auth_headers):
    monkeypatch.setenv("VIBEFORGE_RATE_LIMIT_AGENT_PER_MIN", "2")
    monkeypatch.setenv("VIBEFORGE_RATE_LIMIT_IP_PER_MIN", "100")

    client = TestClient(app, headers=auth_headers)
    agent_id = register_agent(client)
    connect_agent(agent_id)

    for _ in range(2):
        response = client.post(
            f"/control/agents/{agent_id}/dispatch",
            json={"content": "Run diagnostics"},
        )
        assert response.status_code == 200
        assert "X-RateLimit-Limit-Agent" in response.headers

    response = client.post(
        f"/control/agents/{agent_id}/dispatch",
        json={"content": "Run diagnostics"},
    )
    assert response.status_code == 429
    assert response.headers.get("X-RateLimit-Limit-Agent") == "2"


def test_rate_limit_per_ip(monkeypatch, auth_headers):
    monkeypatch.setenv("VIBEFORGE_RATE_LIMIT_AGENT_PER_MIN", "100")
    monkeypatch.setenv("VIBEFORGE_RATE_LIMIT_IP_PER_MIN", "2")

    client = TestClient(app, headers=auth_headers)
    agent_a = register_agent(client)
    agent_b = register_agent(client)
    connect_agent(agent_a)
    connect_agent(agent_b)

    response = client.post(
        f"/control/agents/{agent_a}/dispatch",
        json={"content": "Task 1"},
    )
    assert response.status_code == 200

    response = client.post(
        f"/control/agents/{agent_b}/dispatch",
        json={"content": "Task 2"},
    )
    assert response.status_code == 200

    response = client.post(
        f"/control/agents/{agent_a}/dispatch",
        json={"content": "Task 3"},
    )
    assert response.status_code == 429
    assert response.headers.get("X-RateLimit-Limit-Ip") == "2"
