"""Tests for session endpoints."""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from vibeforge_api.main import app
from vibeforge_api.core.session import session_store
from vibeforge_api.core.artifacts import artifact_store
from vibeforge_api.core.event_log import Event, EventLog, EventType
from vibeforge_api.core.workspace import workspace_manager
from vibeforge_api.models.types import SessionPhase
from orchestration.models import Task, TaskGraph

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_session_store():
    """Reset session store before each test."""
    session_store._sessions.clear()
    yield


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_session():
    """Test VF-021: POST /sessions creates a new session."""
    response = client.post("/sessions")
    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data
    assert data["phase"] == "QUESTIONNAIRE"


def test_get_first_question():
    """Test VF-022: GET /sessions/{id}/question returns first question."""
    # Create session
    create_response = client.post("/sessions")
    session_id = create_response.json()["session_id"]

    # Get question
    response = client.get(f"/sessions/{session_id}/question")
    assert response.status_code == 200
    data = response.json()
    assert data["question_id"] == "q1_audience"
    assert "text" in data
    assert "options" in data


def test_submit_valid_answer():
    """Test VF-023: POST /sessions/{id}/answers accepts valid answer."""
    # Create session
    create_response = client.post("/sessions")
    session_id = create_response.json()["session_id"]

    # Submit answer
    response = client.post(
        f"/sessions/{session_id}/answers",
        json={"question_id": "q1_audience", "answer": "general"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"


def test_submit_invalid_answer():
    """Test VF-023: POST /sessions/{id}/answers rejects invalid answer."""
    # Create session
    create_response = client.post("/sessions")
    session_id = create_response.json()["session_id"]

    # Submit invalid answer
    response = client.post(
        f"/sessions/{session_id}/answers",
        json={"question_id": "q1_audience", "answer": "invalid_option"},
    )
    assert response.status_code == 400


def test_questionnaire_flow_completion():
    """Test complete questionnaire flow."""
    # Create session
    create_response = client.post("/sessions")
    session_id = create_response.json()["session_id"]

    # Answer all questions
    questions = [
        {"question_id": "q1_audience", "answer": "general"},
        {"question_id": "q2_platform", "answer": "web"},
        {"question_id": "q3_complexity", "answer": "simple"},
    ]

    for q in questions:
        response = client.post(f"/sessions/{session_id}/answers", json=q)
        assert response.status_code == 200

    # After last question, phase should advance to PLAN_REVIEW (real pipeline)
    final_response = response.json()
    assert final_response["next_phase"] == "PLAN_REVIEW"
    assert final_response["is_complete"] is True


def test_get_question_wrong_phase():
    """Test VF-029: Cannot get question in wrong phase."""
    # Create session and complete questionnaire
    create_response = client.post("/sessions")
    session_id = create_response.json()["session_id"]

    # Complete questionnaire
    questions = [
        {"question_id": "q1_audience", "answer": "general"},
        {"question_id": "q2_platform", "answer": "web"},
        {"question_id": "q3_complexity", "answer": "simple"},
    ]
    for q in questions:
        client.post(f"/sessions/{session_id}/answers", json=q)

    # Try to get question in BUILD_SPEC phase
    response = client.get(f"/sessions/{session_id}/question")
    assert response.status_code == 400
    assert "QUESTIONNAIRE phase" in response.json()["detail"]


def test_get_progress():
    """Test VF-026: GET /sessions/{id}/progress returns progress info."""
    # Create session
    create_response = client.post("/sessions")
    session_id = create_response.json()["session_id"]

    # Get progress
    response = client.get(f"/sessions/{session_id}/progress")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert data["phase"] == "QUESTIONNAIRE"
    assert "logs" in data


def test_get_plan_summary_from_task_graph():
    """Plan summary should reflect TaskGraph artifacts."""
    create_response = client.post("/sessions")
    session_id = create_response.json()["session_id"]

    session = session_store.get_session(session_id)
    session.update_phase(SessionPhase.PLAN_REVIEW)
    session.build_spec = {
        "scopeBudget": {"maxTotalFiles": 12, "maxScreens": 5},
        "stack": {"preset": "WEB_VITE_REACT_TS"},
        "target": {"platform": "WEB_APP"},
    }
    session_store.update_session(session)

    task_graph = TaskGraph(
        session_id=session_id,
        tasks=[
            Task(
                task_id="task_001",
                description="Set up project scaffold",
                role="worker",
                dependencies=[],
                inputs={},
                expected_outputs=[],
                verification={"type": "build"},
                constraints={},
            ),
            Task(
                task_id="task_002",
                description="Add UI layout",
                role="worker",
                dependencies=["task_001"],
                inputs={},
                expected_outputs=[],
                verification={"type": "test"},
                constraints={},
            ),
        ],
    )
    artifact_store.save_artifact(session_id, "task_graph.json", task_graph.to_dict())

    response = client.get(f"/sessions/{session_id}/plan")
    assert response.status_code == 200
    data = response.json()
    assert data["task_count"] == 2
    assert "Set up project scaffold" in data["features"]
    assert "build" in data["verification_steps"]
    assert "max files 12" in data["estimated_scope"]
    assert "Stack preset: WEB_VITE_REACT_TS" in data["constraints"]


def test_get_plan_summary_empty_state():
    """Plan summary should return empty state when no TaskGraph exists."""
    create_response = client.post("/sessions")
    session_id = create_response.json()["session_id"]

    session = session_store.get_session(session_id)
    session.update_phase(SessionPhase.PLAN_REVIEW)
    session_store.update_session(session)

    response = client.get(f"/sessions/{session_id}/plan")
    assert response.status_code == 200
    data = response.json()
    assert data["task_count"] == 0
    assert data["features"] == []
    assert "Plan not generated yet." in data["constraints"]


def test_get_progress_from_events():
    """Progress should reflect TaskGraph events."""
    create_response = client.post("/sessions")
    session_id = create_response.json()["session_id"]

    task_graph = TaskGraph(
        session_id=session_id,
        tasks=[
            Task(
                task_id="task_001",
                description="Bootstrap repo",
                role="worker",
                dependencies=[],
                inputs={},
                expected_outputs=[],
                verification={"type": "build"},
                constraints={},
            ),
            Task(
                task_id="task_002",
                description="Wire API",
                role="worker",
                dependencies=["task_001"],
                inputs={},
                expected_outputs=[],
                verification={"type": "test"},
                constraints={},
            ),
        ],
    )
    artifact_store.save_artifact(session_id, "task_graph.json", task_graph.to_dict())

    event_log = EventLog(workspace_manager.workspace_root)
    now = datetime.now(timezone.utc)
    event_log.append(
        Event(
            event_type=EventType.TASK_STARTED,
            timestamp=now,
            session_id=session_id,
            message="Task started",
            task_id="task_001",
        )
    )
    event_log.append(
        Event(
            event_type=EventType.TASK_COMPLETED,
            timestamp=now,
            session_id=session_id,
            message="Task completed",
            task_id="task_001",
        )
    )
    event_log.append(
        Event(
            event_type=EventType.TASK_STARTED,
            timestamp=now,
            session_id=session_id,
            message="Task started",
            task_id="task_002",
        )
    )

    response = client.get(f"/sessions/{session_id}/progress")
    assert response.status_code == 200
    data = response.json()
    assert data["active_task"]["task_id"] == "task_002"
    assert len(data["completed_tasks"]) == 1
    assert data["completed_tasks"][0]["task_id"] == "task_001"


def test_session_not_found():
    """Test VF-029: Proper error for non-existent session."""
    response = client.get("/sessions/nonexistent-id/question")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_plan_summary_wrong_phase():
    """Test VF-024: Cannot get plan summary in wrong phase."""
    # Create session
    create_response = client.post("/sessions")
    session_id = create_response.json()["session_id"]

    # Try to get plan while in QUESTIONNAIRE phase
    response = client.get(f"/sessions/{session_id}/plan")
    assert response.status_code == 400
    assert "PLAN_REVIEW phase" in response.json()["detail"]


def test_get_clarification_when_pending():
    """Test GET /sessions/{id}/clarification returns pending question."""
    from vibeforge_api.core.session import session_store

    # Create session
    create_response = client.post("/sessions")
    session_id = create_response.json()["session_id"]

    # Manually set a pending clarification (simulating gate warning)
    session = session_store.get_session(session_id)
    session.pending_clarification = {
        "question": "Warning: High complexity detected. How would you like to proceed?",
        "context": "The requested feature may exceed recommended scope.",
        "options": [
            {"value": "proceed", "label": "Proceed anyway"},
            {"value": "modify", "label": "Modify the request"},
            {"value": "cancel", "label": "Cancel this operation"},
        ],
    }
    session_store.update_session(session)

    # Get clarification
    response = client.get(f"/sessions/{session_id}/clarification")
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "Warning: High complexity detected. How would you like to proceed?"
    assert data["context"] == "The requested feature may exceed recommended scope."
    assert len(data["options"]) == 3
    assert data["options"][0]["value"] == "proceed"
    assert data["options"][0]["label"] == "Proceed anyway"


def test_get_clarification_no_pending():
    """Test GET /sessions/{id}/clarification returns error when no pending question."""
    # Create session
    create_response = client.post("/sessions")
    session_id = create_response.json()["session_id"]

    # Try to get clarification when none pending
    response = client.get(f"/sessions/{session_id}/clarification")
    assert response.status_code == 400
    assert "No pending clarification" in response.json()["detail"]


def test_get_clarification_session_not_found():
    """Test GET /sessions/{id}/clarification returns 404 for non-existent session."""
    response = client.get("/sessions/nonexistent-id/clarification")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_submit_clarification_valid_answer():
    """Test VF-027: POST /sessions/{id}/clarification accepts valid answer."""
    from vibeforge_api.core.session import session_store

    # Create session
    create_response = client.post("/sessions")
    session_id = create_response.json()["session_id"]

    # Set pending clarification
    session = session_store.get_session(session_id)
    session.pending_clarification = {
        "question": "How to proceed?",
        "options": [
            {"value": "proceed", "label": "Proceed"},
            {"value": "cancel", "label": "Cancel"},
        ],
    }
    session_store.update_session(session)

    # Submit valid answer
    response = client.post(
        f"/sessions/{session_id}/clarification",
        json={"answer": "proceed"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["next_phase"] == "EXECUTION"

    # Verify clarification was cleared
    session = session_store.get_session(session_id)
    assert session.pending_clarification is None
    assert session.clarification_answer == "proceed"


def test_submit_clarification_invalid_answer():
    """Test VF-027: POST /sessions/{id}/clarification rejects invalid answer."""
    from vibeforge_api.core.session import session_store

    # Create session
    create_response = client.post("/sessions")
    session_id = create_response.json()["session_id"]

    # Set pending clarification
    session = session_store.get_session(session_id)
    session.pending_clarification = {
        "question": "How to proceed?",
        "options": [
            {"value": "proceed", "label": "Proceed"},
            {"value": "cancel", "label": "Cancel"},
        ],
    }
    session_store.update_session(session)

    # Submit invalid answer
    response = client.post(
        f"/sessions/{session_id}/clarification",
        json={"answer": "invalid_choice"},
    )
    assert response.status_code == 400
    assert "Invalid answer" in response.json()["detail"]


def test_submit_clarification_no_pending():
    """Test POST /sessions/{id}/clarification returns error when no pending question."""
    # Create session
    create_response = client.post("/sessions")
    session_id = create_response.json()["session_id"]

    # Try to submit clarification when none pending
    response = client.post(
        f"/sessions/{session_id}/clarification",
        json={"answer": "proceed"},
    )
    assert response.status_code == 400
    assert "No pending clarification" in response.json()["detail"]


def test_submit_clarification_session_not_found():
    """Test POST /sessions/{id}/clarification returns 404 for non-existent session."""
    response = client.post(
        "/sessions/nonexistent-id/clarification",
        json={"answer": "proceed"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
