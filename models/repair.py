"""Output repair strategies for malformed LLM responses.

VF-065: Retry/repair strategy for validation failures.
"""

from typing import Optional

from models.base.llm_client import LlmClient, LlmRequest, LlmResponse, LlmMessage
from models.validation import OutputValidator, ValidationResult


class RepairFailedError(Exception):
    """Raised when repair attempts are exhausted without success."""

    def __init__(self, message: str, attempts: list[tuple[LlmResponse, ValidationResult]]):
        super().__init__(message)
        self.attempts = attempts


class OutputRepair:
    """Repairs malformed LLM outputs through structured retry strategies.

    VF-065: When validation fails, constructs repair prompts that explain
    the errors and asks the model to fix them. Tracks attempts and escalates
    strategies on repeated failures.
    """

    def __init__(self, llm_client: LlmClient, max_repair_attempts: int = 2):
        """Initialize repair strategy.

        Args:
            llm_client: LLM client to use for repair attempts
            max_repair_attempts: Maximum number of repair attempts (default: 2)
        """
        self.llm_client = llm_client
        self.max_repair_attempts = max_repair_attempts
        self.validator = OutputValidator()

    async def repair(
        self,
        original_request: LlmRequest,
        failed_response: LlmResponse,
        validation_errors: list[str],
        schema: dict,
    ) -> LlmResponse:
        """Attempt to repair a failed response.

        Args:
            original_request: Original request that produced the failed response
            failed_response: Response that failed validation
            validation_errors: List of validation error messages
            schema: JSON schema that validation failed against

        Returns:
            Repaired response that passes validation

        Raises:
            RepairFailedError: If repair attempts exhausted without success
        """
        attempts: list[tuple[LlmResponse, ValidationResult]] = [
            (failed_response, ValidationResult(valid=False, errors=validation_errors))
        ]

        for attempt_num in range(1, self.max_repair_attempts + 1):
            # Build repair prompt
            repair_request = self._build_repair_request(
                original_request,
                failed_response,
                validation_errors,
                schema,
                attempt_num
            )

            # Execute repair attempt
            repair_response = await self.llm_client.complete(repair_request)

            # Validate repair
            result = self.validator.validate(repair_response, schema)
            attempts.append((repair_response, result))

            if result.valid:
                # Repair successful!
                return repair_response

            # Update errors for next attempt
            validation_errors = result.errors

        # All repair attempts failed
        raise RepairFailedError(
            f"Failed to repair output after {self.max_repair_attempts} attempts",
            attempts=attempts
        )

    def _build_repair_request(
        self,
        original_request: LlmRequest,
        failed_response: LlmResponse,
        validation_errors: list[str],
        schema: dict,
        attempt_num: int
    ) -> LlmRequest:
        """Build a repair request with error context.

        Args:
            original_request: Original request
            failed_response: Failed response
            validation_errors: Validation errors
            schema: Expected schema
            attempt_num: Current attempt number

        Returns:
            LlmRequest for repair attempt
        """
        # Build error explanation
        error_list = "\n".join(f"- {err}" for err in validation_errors)

        # Adjust strategy based on attempt number
        if attempt_num == 1:
            strategy_hint = "Please fix the validation errors and return ONLY valid JSON."
        else:
            strategy_hint = (
                "Previous repair attempt also failed. "
                "Carefully review the schema and return ONLY the JSON object, "
                "with no markdown formatting or explanatory text."
            )

        # Build repair prompt
        repair_prompt = f"""Your previous response failed JSON schema validation with the following errors:

{error_list}

Expected schema:
```json
{schema}
```

Your previous output:
```
{failed_response.content[:500]}{"..." if len(failed_response.content) > 500 else ""}
```

{strategy_hint}
"""

        # Create repair request with conversation history
        repair_messages = [
            # Include original system message if present
            *[msg for msg in original_request.messages if msg.role == "system"],
            # Include original user request
            *[msg for msg in original_request.messages if msg.role == "user"],
            # Add failed assistant response
            LlmMessage(role="assistant", content=failed_response.content),
            # Add repair instruction
            LlmMessage(role="user", content=repair_prompt)
        ]

        return LlmRequest(
            messages=repair_messages,
            model=original_request.model,
            temperature=min(original_request.temperature + 0.1, 1.0),  # Slightly higher temp
            max_tokens=original_request.max_tokens,
            metadata={
                **(original_request.metadata or {}),
                "repair_attempt": attempt_num,
                "original_finish_reason": failed_response.finish_reason
            }
        )


async def repair_response(
    llm_client: LlmClient,
    original_request: LlmRequest,
    failed_response: LlmResponse,
    validation_errors: list[str],
    schema: dict,
    max_attempts: int = 2
) -> LlmResponse:
    """Convenience function to repair a failed response.

    Args:
        llm_client: LLM client to use for repair
        original_request: Original request
        failed_response: Failed response
        validation_errors: Validation errors
        schema: Expected schema
        max_attempts: Maximum repair attempts

    Returns:
        Repaired response

    Raises:
        RepairFailedError: If repair failed
    """
    repairer = OutputRepair(llm_client, max_repair_attempts=max_attempts)
    return await repairer.repair(
        original_request,
        failed_response,
        validation_errors,
        schema
    )
