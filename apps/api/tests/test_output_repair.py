"""Tests for OutputRepair (VF-065)."""

import pytest
from unittest.mock import AsyncMock, Mock

from models.base.llm_client import LlmRequest, LlmResponse, LlmMessage
from models.repair import OutputRepair, RepairFailedError, repair_response


class MockLlmClient:
    """Mock LLM client for testing."""

    def __init__(self, responses: list[LlmResponse]):
        """Initialize with sequence of responses to return."""
        self.responses = responses
        self.call_count = 0
        self.requests = []

    async def complete(self, request: LlmRequest) -> LlmResponse:
        """Return next mock response."""
        self.requests.append(request)
        response = self.responses[self.call_count]
        self.call_count += 1
        return response

    def get_provider_name(self) -> str:
        return "mock"


class TestOutputRepair:
    """Test OutputRepair implementation."""

    def test_repair_initialization(self):
        """Test repair strategy initialization."""
        client = MockLlmClient([])
        repair = OutputRepair(client, max_repair_attempts=3)

        assert repair.llm_client is client
        assert repair.max_repair_attempts == 3

    @pytest.mark.asyncio
    async def test_successful_repair_first_attempt(self):
        """Test VF-065: successful repair on first attempt."""
        # Setup: First response is valid JSON
        valid_response = LlmResponse(
            content='{"name": "John", "age": 30}',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        client = MockLlmClient([valid_response])
        repair = OutputRepair(client, max_repair_attempts=2)

        original_request = LlmRequest(
            messages=[LlmMessage(role="user", content="Generate a person")],
            model="gpt-4o-mini"
        )
        failed_response = LlmResponse(
            content='{"name": "John"}',  # Missing "age"
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"}
            },
            "required": ["name", "age"]
        }

        result = await repair.repair(
            original_request,
            failed_response,
            ["Missing required field: age"],
            schema
        )

        assert result.content == '{"name": "John", "age": 30}'
        assert client.call_count == 1

    @pytest.mark.asyncio
    async def test_repair_includes_error_context(self):
        """Test that repair request includes validation errors."""
        valid_response = LlmResponse(
            content='{"status": "active"}',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        client = MockLlmClient([valid_response])
        repair = OutputRepair(client)

        original_request = LlmRequest(
            messages=[LlmMessage(role="user", content="Generate status")],
            model="gpt-4o-mini"
        )
        failed_response = LlmResponse(
            content='{"status": "pending"}',  # Invalid enum value
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["active", "inactive"]}
            }
        }

        await repair.repair(
            original_request,
            failed_response,
            ["'pending' is not one of ['active', 'inactive']"],
            schema
        )

        # Check that repair request mentions the error
        repair_request = client.requests[0]
        repair_content = repair_request.messages[-1].content
        assert "pending" in repair_content or "validation" in repair_content.lower()

    @pytest.mark.asyncio
    async def test_repair_includes_schema(self):
        """Test that repair request includes the expected schema."""
        valid_response = LlmResponse(
            content='{"count": 5}',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        client = MockLlmClient([valid_response])
        repair = OutputRepair(client)

        original_request = LlmRequest(
            messages=[LlmMessage(role="user", content="Generate count")],
            model="gpt-4o-mini"
        )
        failed_response = LlmResponse(
            content='{"count": "five"}',  # Wrong type
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        schema = {
            "type": "object",
            "properties": {"count": {"type": "number"}},
            "required": ["count"]
        }

        await repair.repair(
            original_request,
            failed_response,
            ["'five' is not of type 'number'"],
            schema
        )

        repair_request = client.requests[0]
        repair_content = repair_request.messages[-1].content
        assert "schema" in repair_content.lower()

    @pytest.mark.asyncio
    async def test_repair_preserves_conversation_history(self):
        """Test that repair includes original conversation context."""
        valid_response = LlmResponse(
            content='{"result": "ok"}',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        client = MockLlmClient([valid_response])
        repair = OutputRepair(client)

        original_request = LlmRequest(
            messages=[
                LlmMessage(role="system", content="You are a helpful assistant."),
                LlmMessage(role="user", content="Generate result")
            ],
            model="gpt-4o-mini"
        )
        failed_response = LlmResponse(
            content='invalid',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        schema = {"type": "object"}

        await repair.repair(
            original_request,
            failed_response,
            ["Invalid JSON"],
            schema
        )

        repair_request = client.requests[0]
        # Should include system message, user message, failed assistant message, and repair instruction
        assert len(repair_request.messages) >= 4
        assert repair_request.messages[0].role == "system"
        assert repair_request.messages[1].role == "user"

    @pytest.mark.asyncio
    async def test_repair_increases_temperature(self):
        """Test that repair increases temperature slightly."""
        valid_response = LlmResponse(
            content='{"x": 1}',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        client = MockLlmClient([valid_response])
        repair = OutputRepair(client)

        original_request = LlmRequest(
            messages=[LlmMessage(role="user", content="test")],
            model="gpt-4o-mini",
            temperature=0.7
        )
        failed_response = LlmResponse(
            content='invalid',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        schema = {"type": "object"}

        await repair.repair(
            original_request,
            failed_response,
            ["Invalid"],
            schema
        )

        repair_request = client.requests[0]
        assert repair_request.temperature > original_request.temperature
        assert abs(repair_request.temperature - 0.8) < 0.01  # 0.7 + 0.1 (with floating point tolerance)

    @pytest.mark.asyncio
    async def test_repair_caps_temperature_at_one(self):
        """Test that temperature doesn't exceed 1.0."""
        valid_response = LlmResponse(
            content='{"x": 1}',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        client = MockLlmClient([valid_response])
        repair = OutputRepair(client)

        original_request = LlmRequest(
            messages=[LlmMessage(role="user", content="test")],
            model="gpt-4o-mini",
            temperature=0.95
        )
        failed_response = LlmResponse(
            content='invalid',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        schema = {"type": "object"}

        await repair.repair(
            original_request,
            failed_response,
            ["Invalid"],
            schema
        )

        repair_request = client.requests[0]
        assert repair_request.temperature <= 1.0

    @pytest.mark.asyncio
    async def test_repair_failure_after_max_attempts(self):
        """Test VF-065: raises error after max repair attempts exhausted."""
        # All responses are invalid
        invalid_response1 = LlmResponse(
            content='{"name": "John"}',  # Missing age
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        invalid_response2 = LlmResponse(
            content='{"name": "Jane"}',  # Still missing age
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        client = MockLlmClient([invalid_response1, invalid_response2])
        repair = OutputRepair(client, max_repair_attempts=2)

        original_request = LlmRequest(
            messages=[LlmMessage(role="user", content="Generate person")],
            model="gpt-4o-mini"
        )
        failed_response = LlmResponse(
            content='{"name": "Bob"}',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"}
            },
            "required": ["name", "age"]
        }

        with pytest.raises(RepairFailedError) as exc_info:
            await repair.repair(
                original_request,
                failed_response,
                ["Missing age"],
                schema
            )

        assert "Failed to repair output after 2 attempts" in str(exc_info.value)
        assert len(exc_info.value.attempts) == 3  # Original + 2 repair attempts

    @pytest.mark.asyncio
    async def test_repair_adds_metadata(self):
        """Test that repair adds attempt number to metadata."""
        valid_response = LlmResponse(
            content='{"x": 1}',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        client = MockLlmClient([valid_response])
        repair = OutputRepair(client)

        original_request = LlmRequest(
            messages=[LlmMessage(role="user", content="test")],
            model="gpt-4o-mini",
            metadata={"task_id": "task-123"}
        )
        failed_response = LlmResponse(
            content='invalid',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        schema = {"type": "object"}

        await repair.repair(
            original_request,
            failed_response,
            ["Invalid"],
            schema
        )

        repair_request = client.requests[0]
        assert repair_request.metadata["repair_attempt"] == 1
        assert repair_request.metadata["task_id"] == "task-123"  # Preserves original metadata

    @pytest.mark.asyncio
    async def test_repair_second_attempt_different_strategy(self):
        """Test that second repair attempt uses different strategy hint."""
        invalid_response = LlmResponse(
            content='{"x": 1}',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        valid_response = LlmResponse(
            content='{"x": 1, "y": 2}',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        client = MockLlmClient([invalid_response, valid_response])
        repair = OutputRepair(client, max_repair_attempts=2)

        original_request = LlmRequest(
            messages=[LlmMessage(role="user", content="test")],
            model="gpt-4o-mini"
        )
        failed_response = LlmResponse(
            content='invalid',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        schema = {
            "type": "object",
            "properties": {"x": {"type": "number"}, "y": {"type": "number"}},
            "required": ["x", "y"]
        }

        await repair.repair(
            original_request,
            failed_response,
            ["Missing y"],
            schema
        )

        # Second attempt should mention "Previous repair attempt also failed"
        second_repair_request = client.requests[1]
        second_content = second_repair_request.messages[-1].content
        assert "previous" in second_content.lower() or "repair" in second_content.lower()

    @pytest.mark.asyncio
    async def test_repair_response_convenience_function(self):
        """Test the convenience function repair_response."""
        valid_response = LlmResponse(
            content='{"status": "ok"}',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        client = MockLlmClient([valid_response])

        original_request = LlmRequest(
            messages=[LlmMessage(role="user", content="test")],
            model="gpt-4o-mini"
        )
        failed_response = LlmResponse(
            content='invalid',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        schema = {"type": "object"}

        result = await repair_response(
            client,
            original_request,
            failed_response,
            ["Invalid"],
            schema,
            max_attempts=1
        )

        assert result.content == '{"status": "ok"}'
