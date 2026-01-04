"""End-to-end test for WP-0006: Questionnaire -> IntentProfile -> BuildSpec -> Mock Generation -> Result."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from vibeforge_api.main import app
from vibeforge_api.core.workspace import workspace_manager


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_e2e_questionnaire_to_result(client, tmp_path, monkeypatch):
    """Test complete flow: create session -> answer questions -> get result."""
    # Patch workspace base path to use tmp_path
    monkeypatch.setattr(workspace_manager, "workspace_root", tmp_path)

    # Step 1: Create session
    response = client.post("/sessions")
    assert response.status_code == 201
    data = response.json()
    session_id = data["session_id"]
    assert data["phase"] == "QUESTIONNAIRE"

    # Step 2: Get first question
    response = client.get(f"/sessions/{session_id}/question")
    assert response.status_code == 200
    question = response.json()
    assert question["question_id"] == "q1_audience"
    assert question["is_final"] is False

    # Step 3: Answer first question
    response = client.post(
        f"/sessions/{session_id}/answers",
        json={"question_id": "q1_audience", "answer": "developers"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert response.json()["is_complete"] is False

    # Step 4: Get second question
    response = client.get(f"/sessions/{session_id}/question")
    assert response.status_code == 200
    question = response.json()
    assert question["question_id"] == "q2_platform"
    assert question["is_final"] is False

    # Step 5: Answer second question
    response = client.post(
        f"/sessions/{session_id}/answers",
        json={"question_id": "q2_platform", "answer": "web"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert response.json()["is_complete"] is False

    # Step 6: Get third (final) question
    response = client.get(f"/sessions/{session_id}/question")
    assert response.status_code == 200
    question = response.json()
    assert question["question_id"] == "q3_complexity"
    assert question["is_final"] is True

    # Step 7: Answer final question (triggers finalization)
    response = client.post(
        f"/sessions/{session_id}/answers",
        json={"question_id": "q3_complexity", "answer": "moderate"},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "accepted"
    assert result["is_complete"] is True
    assert result["next_phase"] == "COMPLETE"

    # Step 8: Verify IntentProfile was created
    artifacts_path = tmp_path / session_id / "artifacts"
    intent_profile_path = artifacts_path / "intent_profile.json"
    assert intent_profile_path.exists()

    with open(intent_profile_path) as f:
        intent_profile = json.load(f)

    assert intent_profile["version"] == "1.0"
    assert intent_profile["sessionId"] == session_id
    assert intent_profile["audience"]["targetUser"] == "TEAM"
    assert intent_profile["platformPreference"] == "WEB_APP"
    assert intent_profile["scope"]["featureBudget"] == "SMALL"

    # Step 9: Verify BuildSpec was created
    build_spec_path = artifacts_path / "build_spec.json"
    assert build_spec_path.exists()

    with open(build_spec_path) as f:
        build_spec = json.load(f)

    assert build_spec["version"] == "1.0"
    assert build_spec["sessionId"] == session_id
    assert build_spec["target"]["platform"] == "WEB_APP"
    assert build_spec["stack"]["preset"] == "WEB_VITE_REACT_TS"
    assert "ideaSeed" in build_spec
    assert "genre" in build_spec["ideaSeed"]

    # Step 10: Verify workspace and files were created
    repo_path = tmp_path / session_id / "repo"
    assert repo_path.exists()
    assert (repo_path / "package.json").exists()
    assert (repo_path / "index.html").exists()
    assert (repo_path / "src" / "main.tsx").exists()
    assert (repo_path / "src" / "App.tsx").exists()
    assert (repo_path / "README.md").exists()

    # Step 11: Get result endpoint
    response = client.get(f"/sessions/{session_id}/result")
    assert response.status_code == 200
    result = response.json()

    assert result["session_id"] == session_id
    assert result["status"] == "success"
    assert str(tmp_path / session_id) in result["workspace_path"]
    assert len(result["generated_files"]) > 0
    assert "package.json" in result["generated_files"]
    assert "README.md" in result["generated_files"]
    assert "npm install" in result["run_instructions"]
    assert "npm run dev" in result["run_instructions"]
    assert "Session completed successfully" in result["summary"]
    assert "intent_profile" in result["artifacts"]
    assert "build_spec" in result["artifacts"]


def test_e2e_cli_platform(client, tmp_path, monkeypatch):
    """Test E2E flow with CLI platform."""
    monkeypatch.setattr(workspace_manager, "workspace_root", tmp_path)

    # Create session
    response = client.post("/sessions")
    assert response.status_code == 201
    session_id = response.json()["session_id"]

    # Answer all questions (CLI platform)
    client.post(
        f"/sessions/{session_id}/answers",
        json={"question_id": "q1_audience", "answer": "general"},
    )
    client.post(
        f"/sessions/{session_id}/answers",
        json={"question_id": "q2_platform", "answer": "cli"},
    )
    response = client.post(
        f"/sessions/{session_id}/answers",
        json={"question_id": "q3_complexity", "answer": "simple"},
    )

    assert response.json()["next_phase"] == "COMPLETE"

    # Verify CLI files were generated
    repo_path = tmp_path / session_id / "repo"
    assert (repo_path / "main.py").exists()
    assert (repo_path / "requirements.txt").exists()
    assert (repo_path / "README.md").exists()

    # Get result
    response = client.get(f"/sessions/{session_id}/result")
    assert response.status_code == 200
    result = response.json()

    assert "main.py" in result["generated_files"]
    assert "python main.py" in result["run_instructions"]
    assert result["status"] == "success"


def test_result_endpoint_wrong_phase(client):
    """Test that result endpoint requires COMPLETE phase."""
    # Create session
    response = client.post("/sessions")
    session_id = response.json()["session_id"]

    # Try to get result while still in QUESTIONNAIRE phase
    response = client.get(f"/sessions/{session_id}/result")
    assert response.status_code == 400
    assert "COMPLETE phase" in response.json()["detail"]


def test_result_endpoint_nonexistent_session(client):
    """Test result endpoint with invalid session ID."""
    response = client.get("/sessions/nonexistent/result")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
