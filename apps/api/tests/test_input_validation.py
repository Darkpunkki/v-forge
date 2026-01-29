"""Input validation tests for control dispatch endpoints."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from vibeforge_api.core.connection_manager import AgentConnection, get_connection_manager, reset_connection_manager
from vibeforge_api.main import app


@pytest.fixture(autouse=True)
def reset_manager():
    reset_connection_manager()
    yield
    reset_connection_manager()


@pytest.fixture()
def client(auth_headers):
    return TestClient(app, headers=auth_headers)


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


def test_invalid_agent_id_rejected(client: TestClient) -> None:
    response = client.get("/control/agents/bad_agent")
    assert response.status_code == 400
    assert "agent_id" in response.json().get("detail", "")


def test_dispatch_rejects_long_content(client: TestClient) -> None:
    agent_id = register_agent(client)
    connect_agent(agent_id)

    response = client.post(
        f"/control/agents/{agent_id}/dispatch",
        json={"content": "a" * 10001},
    )

    assert response.status_code == 400
    assert "10000" in response.json().get("detail", "")


def test_dispatch_sanitizes_null_bytes(client: TestClient) -> None:
    agent_id = register_agent(client)
    connect_agent(agent_id)

    response = client.post(
        f"/control/agents/{agent_id}/dispatch",
        json={"content": "hello\x00world"},
    )

    assert response.status_code == 200
    message_id = response.json()["message_id"]

    manager = get_connection_manager()
    pending = manager._pending_dispatches[message_id]
    assert "\x00" not in pending.content
