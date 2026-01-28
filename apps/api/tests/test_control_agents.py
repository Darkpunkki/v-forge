"""Integration tests for live agent control endpoints."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from vibeforge_api.main import app
from vibeforge_api.core.connection_manager import (
    AgentConnection,
    get_connection_manager,
    reset_connection_manager,
)


@pytest.fixture(autouse=True)
def reset_manager():
    reset_connection_manager()
    yield
    reset_connection_manager()


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


def test_register_agent_success():
    client = TestClient(app)
    response = client.post(
        "/control/agents/register",
        json={"name": "Agent Alpha", "endpoint_url": "ws://localhost:8000/ws/agent-bridge"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["agent"]["agent_id"]
    assert data["agent"]["name"] == "Agent Alpha"
    assert data["agent"]["endpoint_url"] == "ws://localhost:8000/ws/agent-bridge"
    assert data["agent"]["status"] == "disconnected"


def test_register_agent_validation_error():
    client = TestClient(app)
    response = client.post(
        "/control/agents/register",
        json={"name": " ", "endpoint_url": " "},
    )

    assert response.status_code == 400


def test_list_agents_includes_status():
    client = TestClient(app)
    agent_id = register_agent(client)

    response = client.get("/control/agents")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["agents"][0]["status"] == "disconnected"

    connect_agent(agent_id)
    response = client.get("/control/agents")
    data = response.json()
    statuses = {agent["agent_id"]: agent["status"] for agent in data["agents"]}
    assert statuses[agent_id] == "connected"


def test_get_agent_detail():
    client = TestClient(app)
    agent_id = register_agent(client)

    response = client.get(f"/control/agents/{agent_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["agent"]["agent_id"] == agent_id


def test_dispatch_task_success():
    client = TestClient(app)
    agent_id = register_agent(client)
    connect_agent(agent_id)

    response = client.post(
        f"/control/agents/{agent_id}/dispatch",
        json={"content": "Run diagnostics"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "dispatched"

    status_response = client.get(f"/control/agents/{agent_id}/task")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "dispatched"


def test_dispatch_task_agent_not_found():
    client = TestClient(app)

    response = client.post(
        "/control/agents/unknown/dispatch",
        json={"content": "Run diagnostics"},
    )

    assert response.status_code == 404


def test_dispatch_task_agent_disconnected():
    client = TestClient(app)
    agent_id = register_agent(client)

    response = client.post(
        f"/control/agents/{agent_id}/dispatch",
        json={"content": "Run diagnostics"},
    )

    assert response.status_code == 409


def test_followup_requires_active_task():
    client = TestClient(app)
    agent_id = register_agent(client)
    connect_agent(agent_id)

    response = client.post(
        f"/control/agents/{agent_id}/followup",
        json={"content": "Any update?"},
    )
    assert response.status_code == 409

    dispatch_response = client.post(
        f"/control/agents/{agent_id}/dispatch",
        json={"content": "Initial task"},
    )
    assert dispatch_response.status_code == 200

    followup_response = client.post(
        f"/control/agents/{agent_id}/followup",
        json={"content": "Any update?"},
    )
    assert followup_response.status_code == 200
