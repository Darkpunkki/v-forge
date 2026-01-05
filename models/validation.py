"""Output validation for LLM responses.

VF-064: Strict JSON schema validation for model outputs.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Optional

import jsonschema
from jsonschema import Draft7Validator, ValidationError as JsonSchemaValidationError

from models.base.llm_client import LlmResponse


@dataclass
class ValidationResult:
    """Result of output validation.

    Attributes:
        valid: Whether validation passed
        parsed_output: Parsed JSON output (if valid)
        errors: List of validation error messages
        raw_content: Original response content
    """
    valid: bool
    parsed_output: Optional[dict] = None
    errors: list[str] = field(default_factory=list)
    raw_content: str = ""


class OutputValidator:
    """Validates LLM outputs against JSON schemas.

    VF-064: Provides strict JSON schema validation with detailed error reporting.
    Helps ensure model outputs conform to expected structure before use.
    """

    def __init__(self, strict_mode: bool = True):
        """Initialize validator.

        Args:
            strict_mode: If True, require exact schema compliance (no extra fields)
        """
        self.strict_mode = strict_mode

    def validate(self, response: LlmResponse, schema: dict) -> ValidationResult:
        """Validate LLM response against JSON schema.

        Args:
            response: LLM response to validate
            schema: JSON schema to validate against

        Returns:
            ValidationResult with validation status and any errors
        """
        content = response.content.strip()
        errors = []

        # Step 1: Parse JSON
        try:
            parsed = self._extract_json(content)
        except json.JSONDecodeError as e:
            return ValidationResult(
                valid=False,
                parsed_output=None,
                errors=[f"JSON parsing error: {str(e)}"],
                raw_content=content
            )
        except ValueError as e:
            return ValidationResult(
                valid=False,
                parsed_output=None,
                errors=[str(e)],
                raw_content=content
            )

        # Step 2: Validate against schema
        try:
            validator = Draft7Validator(schema)
            validator.validate(parsed)

            # Validation passed
            return ValidationResult(
                valid=True,
                parsed_output=parsed,
                errors=[],
                raw_content=content
            )
        except JsonSchemaValidationError as e:
            # Collect all validation errors
            errors = self._collect_validation_errors(validator, parsed)
            return ValidationResult(
                valid=False,
                parsed_output=parsed,  # Still provide parsed output for inspection
                errors=errors,
                raw_content=content
            )

    def _extract_json(self, content: str) -> dict:
        """Extract JSON from response content.

        Handles cases where JSON is wrapped in markdown code blocks or explanatory text.

        Args:
            content: Response content

        Returns:
            Parsed JSON dict

        Raises:
            json.JSONDecodeError: If JSON cannot be parsed
            ValueError: If no valid JSON found in content
        """
        # Try direct parse first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try to extract from markdown code block
        if "```json" in content:
            # Extract content between ```json and ```
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end != -1:
                json_str = content[start:end].strip()
                return json.loads(json_str)

        # Try to extract from generic code block
        if "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end != -1:
                json_str = content[start:end].strip()
                # Skip language identifier if present
                if json_str.startswith("json\n"):
                    json_str = json_str[5:]
                return json.loads(json_str)

        # Try to find JSON object boundaries
        brace_start = content.find("{")
        brace_end = content.rfind("}")
        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            json_str = content[brace_start:brace_end+1]
            return json.loads(json_str)

        # Try to find JSON array boundaries
        bracket_start = content.find("[")
        bracket_end = content.rfind("]")
        if bracket_start != -1 and bracket_end != -1 and bracket_end > bracket_start:
            json_str = content[bracket_start:bracket_end+1]
            return json.loads(json_str)

        raise ValueError("No valid JSON found in response content")

    def _collect_validation_errors(self, validator: Draft7Validator, instance: Any) -> list[str]:
        """Collect all validation errors with detailed messages.

        Args:
            validator: JSON schema validator
            instance: Instance to validate

        Returns:
            List of human-readable error messages
        """
        errors = []
        for error in validator.iter_errors(instance):
            path = ".".join(str(p) for p in error.path) if error.path else "root"
            message = f"At '{path}': {error.message}"

            # Add more context for specific error types
            if error.validator == "required":
                message += f" (missing required field)"
            elif error.validator == "type":
                expected = error.validator_value
                actual = type(error.instance).__name__
                message += f" (expected {expected}, got {actual})"
            elif error.validator == "enum":
                allowed = ", ".join(str(v) for v in error.validator_value)
                message += f" (allowed values: {allowed})"

            errors.append(message)

        return errors


def validate_response(response: LlmResponse, schema: dict) -> ValidationResult:
    """Convenience function to validate a response.

    Args:
        response: LLM response to validate
        schema: JSON schema to validate against

    Returns:
        ValidationResult
    """
    validator = OutputValidator()
    return validator.validate(response, schema)
