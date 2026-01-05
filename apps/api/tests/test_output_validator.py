"""Tests for OutputValidator (VF-064)."""

import pytest

from models.base.llm_client import LlmResponse, LlmUsage
from models.validation import OutputValidator, ValidationResult, validate_response


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_validation_result_valid(self):
        """Test creating a valid validation result."""
        result = ValidationResult(
            valid=True,
            parsed_output={"key": "value"},
            errors=[],
            raw_content='{"key": "value"}'
        )

        assert result.valid is True
        assert result.parsed_output == {"key": "value"}
        assert result.errors == []

    def test_validation_result_invalid(self):
        """Test creating an invalid validation result."""
        result = ValidationResult(
            valid=False,
            parsed_output=None,
            errors=["JSON parsing error"],
            raw_content='invalid json'
        )

        assert result.valid is False
        assert result.parsed_output is None
        assert len(result.errors) == 1


class TestOutputValidator:
    """Test OutputValidator implementation."""

    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = OutputValidator(strict_mode=True)
        assert validator.strict_mode is True

    def test_validate_valid_json(self):
        """Test VF-064: validation passes for valid JSON."""
        validator = OutputValidator()
        response = LlmResponse(
            content='{"name": "John", "age": 30}',
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

        result = validator.validate(response, schema)

        assert result.valid is True
        assert result.parsed_output == {"name": "John", "age": 30}
        assert result.errors == []

    def test_validate_invalid_json_syntax(self):
        """Test VF-064: validation fails for malformed JSON."""
        validator = OutputValidator()
        response = LlmResponse(
            content='{"name": "John", "age": }',  # Invalid JSON
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        schema = {"type": "object"}

        result = validator.validate(response, schema)

        assert result.valid is False
        assert result.parsed_output is None
        assert len(result.errors) > 0
        assert "JSON parsing error" in result.errors[0]

    def test_validate_missing_required_field(self):
        """Test VF-064: validation catches missing required fields."""
        validator = OutputValidator()
        response = LlmResponse(
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

        result = validator.validate(response, schema)

        assert result.valid is False
        assert result.parsed_output == {"name": "John"}  # Still provides parsed output
        assert len(result.errors) > 0
        assert any("age" in err.lower() for err in result.errors)

    def test_validate_wrong_type(self):
        """Test VF-064: validation catches type mismatches."""
        validator = OutputValidator()
        response = LlmResponse(
            content='{"name": "John", "age": "thirty"}',  # age should be number
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

        result = validator.validate(response, schema)

        assert result.valid is False
        assert len(result.errors) > 0
        assert any("type" in err.lower() or "number" in err.lower() for err in result.errors)

    def test_validate_enum_violation(self):
        """Test validation catches enum violations."""
        validator = OutputValidator()
        response = LlmResponse(
            content='{"status": "pending"}',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["active", "inactive"]}
            },
            "required": ["status"]
        }

        result = validator.validate(response, schema)

        assert result.valid is False
        assert len(result.errors) > 0

    def test_validate_nested_object(self):
        """Test validation works with nested objects."""
        validator = OutputValidator()
        response = LlmResponse(
            content='{"user": {"name": "John", "email": "john@example.com"}}',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"}
                    },
                    "required": ["name", "email"]
                }
            },
            "required": ["user"]
        }

        result = validator.validate(response, schema)

        assert result.valid is True
        assert result.parsed_output["user"]["name"] == "John"

    def test_extract_json_from_markdown_code_block(self):
        """Test extracting JSON from markdown code block."""
        validator = OutputValidator()
        response = LlmResponse(
            content='Here is the result:\n```json\n{"key": "value"}\n```',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        schema = {
            "type": "object",
            "properties": {"key": {"type": "string"}},
            "required": ["key"]
        }

        result = validator.validate(response, schema)

        assert result.valid is True
        assert result.parsed_output == {"key": "value"}

    def test_extract_json_from_generic_code_block(self):
        """Test extracting JSON from generic code block."""
        validator = OutputValidator()
        response = LlmResponse(
            content='```\n{"key": "value"}\n```',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        schema = {
            "type": "object",
            "properties": {"key": {"type": "string"}},
            "required": ["key"]
        }

        result = validator.validate(response, schema)

        assert result.valid is True
        assert result.parsed_output == {"key": "value"}

    def test_extract_json_from_text_with_braces(self):
        """Test extracting JSON from explanatory text."""
        validator = OutputValidator()
        response = LlmResponse(
            content='The output is: {"name": "test", "count": 5} as requested.',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "count": {"type": "number"}
            },
            "required": ["name", "count"]
        }

        result = validator.validate(response, schema)

        assert result.valid is True
        assert result.parsed_output == {"name": "test", "count": 5}

    def test_extract_json_array(self):
        """Test extracting JSON array."""
        validator = OutputValidator()
        response = LlmResponse(
            content='[{"id": 1}, {"id": 2}]',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "number"}},
                "required": ["id"]
            }
        }

        result = validator.validate(response, schema)

        assert result.valid is True
        assert len(result.parsed_output) == 2

    def test_no_json_found(self):
        """Test error when no JSON found in content."""
        validator = OutputValidator()
        response = LlmResponse(
            content='This is just plain text with no JSON.',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        schema = {"type": "object"}

        result = validator.validate(response, schema)

        assert result.valid is False
        assert any("No valid JSON found" in err for err in result.errors)

    def test_validate_response_convenience_function(self):
        """Test the convenience function validate_response."""
        response = LlmResponse(
            content='{"status": "ok"}',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        schema = {
            "type": "object",
            "properties": {"status": {"type": "string"}},
            "required": ["status"]
        }

        result = validate_response(response, schema)

        assert result.valid is True
        assert result.parsed_output == {"status": "ok"}

    def test_validate_complex_schema(self):
        """Test validation with complex nested schema."""
        validator = OutputValidator()
        response = LlmResponse(
            content='''{
                "task_graph": {
                    "tasks": [
                        {"id": "t1", "title": "Setup", "dependencies": []},
                        {"id": "t2", "title": "Build", "dependencies": ["t1"]}
                    ]
                }
            }''',
            model="gpt-4o-mini",
            finish_reason="stop"
        )
        schema = {
            "type": "object",
            "properties": {
                "task_graph": {
                    "type": "object",
                    "properties": {
                        "tasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "title": {"type": "string"},
                                    "dependencies": {"type": "array", "items": {"type": "string"}}
                                },
                                "required": ["id", "title", "dependencies"]
                            }
                        }
                    },
                    "required": ["tasks"]
                }
            },
            "required": ["task_graph"]
        }

        result = validator.validate(response, schema)

        assert result.valid is True
        assert len(result.parsed_output["task_graph"]["tasks"]) == 2
