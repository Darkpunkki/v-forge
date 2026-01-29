"""Tests for agent bridge protocol message models (WP-0054 / TASK-006)."""

import pytest
from pydantic import ValidationError

from vibeforge_api.models.bridge_protocol import (
    RegisterMessage,
    RegisteredMessage,
    DispatchMessage,
    ProgressMessage,
    ResponseMessage,
    HeartbeatMessage,
    parse_bridge_message,
)


# ── RegisterMessage ──────────────────────────────────────────────


class TestRegisterMessage:
    def test_round_trip(self):
        msg = RegisterMessage(
            agent_id="worker-1",
            auth_token="test-token",
            capabilities=["code", "review"],
            workdir="/home/user/project",
            metadata={"os": "linux"},
        )
        data = msg.model_dump()
        restored = RegisterMessage.model_validate(data)
        assert restored.type == "register"
        assert restored.agent_id == "worker-1"
        assert restored.auth_token == "test-token"
        assert restored.capabilities == ["code", "review"]
        assert restored.workdir == "/home/user/project"
        assert restored.metadata == {"os": "linux"}

    def test_defaults(self):
        msg = RegisterMessage(agent_id="w1", auth_token="tok")
        assert msg.capabilities == []
        assert msg.workdir is None
        assert msg.metadata == {}

    def test_rejects_empty_agent_id(self):
        with pytest.raises(ValidationError):
            RegisterMessage(agent_id="", auth_token="tok")

    def test_rejects_empty_auth_token(self):
        with pytest.raises(ValidationError):
            RegisterMessage(agent_id="w1", auth_token="")

    def test_type_literal(self):
        msg = RegisterMessage(agent_id="w1", auth_token="tok")
        assert msg.type == "register"


# ── RegisteredMessage ────────────────────────────────────────────


class TestRegisteredMessage:
    def test_round_trip(self):
        msg = RegisteredMessage(
            session_id="sess-abc",
            agent_id="worker-1",
            message="OK",
        )
        data = msg.model_dump()
        restored = RegisteredMessage.model_validate(data)
        assert restored.type == "registered"
        assert restored.session_id == "sess-abc"
        assert restored.agent_id == "worker-1"
        assert restored.message == "OK"

    def test_default_message(self):
        msg = RegisteredMessage(session_id="s1", agent_id="w1")
        assert msg.message == "Registration successful"

    def test_rejects_empty_session_id(self):
        with pytest.raises(ValidationError):
            RegisteredMessage(session_id="", agent_id="w1")


# ── DispatchMessage ──────────────────────────────────────────────


class TestDispatchMessage:
    def test_round_trip(self):
        msg = DispatchMessage(
            message_id="msg-001",
            agent_id="worker-1",
            content="Build the auth module",
            context={"repo": "myapp", "branch": "main"},
            session_id="sess-abc",
        )
        data = msg.model_dump()
        restored = DispatchMessage.model_validate(data)
        assert restored.type == "dispatch"
        assert restored.message_id == "msg-001"
        assert restored.content == "Build the auth module"
        assert restored.context["repo"] == "myapp"
        assert restored.session_id == "sess-abc"

    def test_defaults(self):
        msg = DispatchMessage(
            message_id="m1", agent_id="w1", content="task"
        )
        assert msg.context == {}
        assert msg.session_id is None

    def test_rejects_empty_content(self):
        with pytest.raises(ValidationError):
            DispatchMessage(message_id="m1", agent_id="w1", content="")

    def test_rejects_empty_message_id(self):
        with pytest.raises(ValidationError):
            DispatchMessage(message_id="", agent_id="w1", content="task")


# ── ProgressMessage ──────────────────────────────────────────────


class TestProgressMessage:
    def test_round_trip(self):
        msg = ProgressMessage(
            message_id="msg-001",
            agent_id="worker-1",
            status="running",
            progress_text="Writing tests...",
            metadata={"percent": 50},
        )
        data = msg.model_dump()
        restored = ProgressMessage.model_validate(data)
        assert restored.type == "progress"
        assert restored.status == "running"
        assert restored.progress_text == "Writing tests..."
        assert restored.metadata["percent"] == 50

    def test_defaults(self):
        msg = ProgressMessage(
            message_id="m1", agent_id="w1", status="running"
        )
        assert msg.progress_text == ""
        assert msg.metadata == {}

    def test_rejects_empty_status(self):
        with pytest.raises(ValidationError):
            ProgressMessage(message_id="m1", agent_id="w1", status="")


# ── ResponseMessage ──────────────────────────────────────────────


class TestResponseMessage:
    def test_round_trip(self):
        msg = ResponseMessage(
            message_id="msg-001",
            agent_id="worker-1",
            content="Auth module complete",
            usage={"input_tokens": 500, "output_tokens": 1200},
        )
        data = msg.model_dump()
        restored = ResponseMessage.model_validate(data)
        assert restored.type == "response"
        assert restored.content == "Auth module complete"
        assert restored.usage["input_tokens"] == 500
        assert restored.error is None

    def test_error_response(self):
        msg = ResponseMessage(
            message_id="msg-001",
            agent_id="worker-1",
            error="Claude Code crashed",
        )
        assert msg.content == ""
        assert msg.error == "Claude Code crashed"

    def test_defaults(self):
        msg = ResponseMessage(message_id="m1", agent_id="w1")
        assert msg.content == ""
        assert msg.usage == {}
        assert msg.error is None


# ── HeartbeatMessage ─────────────────────────────────────────────


class TestHeartbeatMessage:
    def test_round_trip(self):
        msg = HeartbeatMessage(
            agent_id="worker-1",
            timestamp="2026-01-28T10:00:00+00:00",
        )
        data = msg.model_dump()
        restored = HeartbeatMessage.model_validate(data)
        assert restored.type == "heartbeat"
        assert restored.agent_id == "worker-1"
        assert restored.timestamp == "2026-01-28T10:00:00+00:00"

    def test_auto_timestamp(self):
        msg = HeartbeatMessage(agent_id="w1")
        assert msg.timestamp  # non-empty default

    def test_rejects_empty_agent_id(self):
        with pytest.raises(ValidationError):
            HeartbeatMessage(agent_id="")


# ── Discriminated union (parse_bridge_message) ───────────────────


class TestParseBridgeMessage:
    def test_parse_register(self):
        raw = {"type": "register", "agent_id": "w1", "auth_token": "tok"}
        msg = parse_bridge_message(raw)
        assert isinstance(msg, RegisterMessage)

    def test_parse_registered(self):
        raw = {"type": "registered", "session_id": "s1", "agent_id": "w1"}
        msg = parse_bridge_message(raw)
        assert isinstance(msg, RegisteredMessage)

    def test_parse_dispatch(self):
        raw = {
            "type": "dispatch",
            "message_id": "m1",
            "agent_id": "w1",
            "content": "do it",
        }
        msg = parse_bridge_message(raw)
        assert isinstance(msg, DispatchMessage)

    def test_parse_progress(self):
        raw = {
            "type": "progress",
            "message_id": "m1",
            "agent_id": "w1",
            "status": "running",
        }
        msg = parse_bridge_message(raw)
        assert isinstance(msg, ProgressMessage)

    def test_parse_response(self):
        raw = {
            "type": "response",
            "message_id": "m1",
            "agent_id": "w1",
            "content": "done",
        }
        msg = parse_bridge_message(raw)
        assert isinstance(msg, ResponseMessage)

    def test_parse_heartbeat(self):
        raw = {"type": "heartbeat", "agent_id": "w1"}
        msg = parse_bridge_message(raw)
        assert isinstance(msg, HeartbeatMessage)

    def test_rejects_unknown_type(self):
        with pytest.raises(ValidationError):
            parse_bridge_message({"type": "unknown", "agent_id": "w1"})

    def test_rejects_missing_type(self):
        with pytest.raises(ValidationError):
            parse_bridge_message({"agent_id": "w1"})

    def test_rejects_invalid_fields(self):
        with pytest.raises(ValidationError):
            parse_bridge_message({"type": "register", "agent_id": ""})
