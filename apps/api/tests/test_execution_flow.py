"""Integration tests for execution flow after plan approval."""

import time

import pytest
from fastapi.testclient import TestClient

from vibeforge_api.main import app
from vibeforge_api.core.session import session_store

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_session_store():
    """Reset session store before each test."""
    session_store._sessions.clear()
    yield


def test_plan_approval_executes_to_completion(monkeypatch):
    """Plan approval should kick off execution and reach COMPLETE."""
    monkeypatch.setenv("VIBEFORGE_LLM_MODE", "stub")

    create_response = client.post("/sessions")
    session_id = create_response.json()["session_id"]

    questions = [
        {"question_id": "q1_audience", "answer": "general"},
        {"question_id": "q2_platform", "answer": "web"},
        {"question_id": "q3_complexity", "answer": "simple"},
    ]

    for q in questions:
        response = client.post(f"/sessions/{session_id}/answers", json=q)
        assert response.status_code == 200

    decision = client.post(
        f"/sessions/{session_id}/plan/decision", json={"approved": True}
    )
    assert decision.status_code == 200

    progress = None
    for _ in range(100):
        progress_response = client.get(f"/sessions/{session_id}/progress")
        assert progress_response.status_code == 200
        progress = progress_response.json()
        if progress["phase"] == "COMPLETE":
            break
        time.sleep(0.05)

    assert progress is not None
    assert progress["phase"] == "COMPLETE"
    assert progress["completed_tasks"]
