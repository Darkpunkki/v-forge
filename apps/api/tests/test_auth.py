"""Authentication tests for control and agent bridge endpoints."""

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from vibeforge_api.main import app


def test_control_requires_auth():
    client = TestClient(app)
    response = client.get("/control/context")

    assert response.status_code == 401
    assert "authentication" in response.json().get("detail", "").lower()


def test_control_accepts_valid_auth(auth_headers):
    client = TestClient(app, headers=auth_headers)
    response = client.get("/control/context")

    assert response.status_code == 200
    assert "control_session_id" in response.json()


def test_websocket_rejects_invalid_token():
    client = TestClient(app)

    with client.websocket_connect("/ws/agent-bridge") as ws:
        ws.send_json(
            {
                "type": "register",
                "agent_id": "bad-agent",
                "auth_token": "invalid-token",
            }
        )

        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()
