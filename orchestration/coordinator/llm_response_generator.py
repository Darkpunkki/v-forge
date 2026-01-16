"""LLM response generator for simulation agent replies."""

from __future__ import annotations

import json
import logging
from typing import Any, Iterable

from models.base.llm_client import LlmClient, LlmMessage, LlmRequest, LlmResponse
from orchestration.prompts import AGENT_ROLE_PROMPTS

logger = logging.getLogger(__name__)


class LlmResponseGenerator:
    """Builds role-aware LLM responses for simulation agents."""

    def __init__(self, llm_client: LlmClient) -> None:
        self.llm_client = llm_client
        self.default_temperature = 0.7
        self.default_model = "gpt-4o-mini"

    async def generate_response(
        self,
        agent_id: str,
        agent_role: str | None,
        agent_model: str | None,
        message_history: Iterable[dict[str, Any]],
        incoming_message: dict[str, Any] | str,
    ) -> LlmResponse:
        system_prompt = AGENT_ROLE_PROMPTS.get(
            agent_role or "", AGENT_ROLE_PROMPTS["worker"]
        )

        messages: list[LlmMessage] = [LlmMessage(role="system", content=system_prompt)]
        for entry in message_history:
            role = str(entry.get("role", "user"))
            content = self._normalize_content(entry.get("content", ""))
            messages.append(LlmMessage(role=role, content=content))

        incoming_text = self._normalize_content(incoming_message)
        messages.append(LlmMessage(role="user", content=incoming_text))

        request = LlmRequest(
            messages=messages,
            model=agent_model or self.default_model,
            temperature=self.default_temperature,
            metadata={
                "agent_id": agent_id,
                "agent_role": agent_role,
            },
        )

        try:
            response = await self.llm_client.complete(request)
        except Exception:
            logger.exception(
                "LLM response generation failed for agent %s (%s)",
                agent_id,
                agent_role or "unknown-role",
            )
            raise
        response.metadata = {
            **response.metadata,
            "content": self._build_response_payload(response.content),
        }
        return response

    def _build_response_payload(self, content: str) -> dict[str, Any]:
        return {
            "text": content,
            "is_stub": False,
            "expect_response": False,
        }

    def _normalize_content(self, content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, dict) and "text" in content:
            value = content.get("text")
            if isinstance(value, str):
                return value
        try:
            return json.dumps(content, ensure_ascii=True, sort_keys=True)
        except TypeError:
            return str(content)
