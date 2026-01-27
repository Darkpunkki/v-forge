"""LLM provider selection for the API layer."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from ..models import LlmClient, LlmRequest, LlmResponse, LlmUsage

from models.openai import OpenAiProvider


class DynamicLlmClient(LlmClient):
    """LLM client that resolves the active provider at call time.

    This keeps test-time env overrides (e.g. VIBEFORGE_LLM_MODE=stub) effective
    even when modules import and cache a client instance at startup.
    """

    def __init__(self) -> None:
        self._cache: dict[str, LlmClient] = {}

    def _select(self) -> LlmClient:
        llm_mode = (os.getenv("VIBEFORGE_LLM_MODE") or "").strip().lower()
        no_spend = (os.getenv("VIBEFORGE_NO_SPEND") or "").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        if llm_mode in {"stub", "dry_run", "dry-run"} or no_spend:
            key = "stub"
            if key not in self._cache:
                self._cache[key] = DeterministicStubClient()
            return self._cache[key]

        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL") or ""
        if api_key:
            key = f"openai::{base_url}::{api_key}"
            if key not in self._cache:
                self._cache[key] = OpenAiProvider(api_key=api_key, base_url=base_url or None)
            return self._cache[key]

        key = "stub"
        if key not in self._cache:
            self._cache[key] = DeterministicStubClient()
        return self._cache[key]

    async def complete(self, request: LlmRequest) -> LlmResponse:
        return await self._select().complete(request)

    def get_provider_name(self) -> str:
        return self._select().get_provider_name()


class DeterministicStubClient(LlmClient):
    """Deterministic stub client for local orchestration flows.

    Used when no model credentials are configured so the pipeline can
    still produce valid Concept/TaskGraph artifacts for UI integration.
    """

    def __init__(self, model_name: str = "stub-model"):
        self.model_name = model_name

    async def complete(self, request: LlmRequest) -> LlmResponse:
        operation = None
        if request.metadata:
            operation = request.metadata.get("operation")

        payload = self._build_payload(operation, request.metadata or {})

        return LlmResponse(
            content=json.dumps(payload),
            model=self.model_name,
            finish_reason="stop",
            usage=LlmUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
            metadata={"operation": operation, "provider": self.get_provider_name()},
        )

    def get_provider_name(self) -> str:
        return "stub"

    def _build_payload(self, operation: Optional[str], metadata: dict[str, Any]) -> dict[str, Any]:
        if operation == "taskgraph_generation":
            return self._taskgraph_payload(metadata)
        if operation == "run_summary":
            return self._run_summary_payload()
        return self._concept_payload(metadata)

    def _concept_payload(self, metadata: dict[str, Any]) -> dict[str, Any]:
        return {
            "idea_description": (
                "Build a focused productivity dashboard that helps users track a small set of goals. "
                "The app highlights progress, keeps the scope lightweight, and prioritizes fast setup."
            ),
            "features": [
                "Create and track a handful of daily goals with clear status indicators.",
                "View a summary dashboard that surfaces progress and focus areas.",
                "Adjust goal settings with structured controls and saved defaults.",
            ],
            "tech_stack": {
                "framework": "Vite + React",
                "language": "TypeScript",
                "testing": "Vitest",
                "build": "Vite",
                "database": "None (local storage)",
                "runtime": "Node.js",
            },
            "file_structure": {
                "README.md": "Project overview, setup, and run instructions.",
                "package.json": "Scripts and dependency declarations.",
                "src/main.tsx": "Application entry point.",
                "src/App.tsx": "Primary app shell and routes.",
                "src/components/GoalCard.tsx": "Reusable goal status card.",
                "src/state/useGoals.ts": "Goal state management logic.",
            },
            "verification_steps": [
                "npm install",
                "npm run build",
                "npm test",
            ],
            "constraints": [
                "Keep the feature set limited to a small number of goals.",
                "Avoid external network calls or third-party APIs.",
            ],
        }

    def _taskgraph_payload(self, metadata: dict[str, Any]) -> dict[str, Any]:
        return {
            "tasks": [
                {
                    "task_id": "task_001",
                    "description": "Scaffold the base project structure and core layout components.",
                    "role": "worker",
                    "dependencies": [],
                    "inputs": {},
                    "expected_outputs": ["src/App.tsx", "src/components/Layout.tsx"],
                    "verification": {
                        "type": "manual",
                        "success_criteria": "Scaffold renders the base layout.",
                    },
                    "constraints": {
                        "max_files": 10,
                        "allowed_commands": ["npm run build"],
                        "timeout_seconds": 900,
                        "scope": "layout",
                    },
                },
                {
                    "task_id": "task_002",
                    "description": "Implement goal tracking components and state management hooks.",
                    "role": "worker",
                    "dependencies": ["task_001"],
                    "inputs": {},
                    "expected_outputs": ["src/components/GoalCard.tsx", "src/state/useGoals.ts"],
                    "verification": {
                        "type": "manual",
                        "success_criteria": "Goal components render and update correctly.",
                    },
                    "constraints": {
                        "max_files": 10,
                        "allowed_commands": ["npm test"],
                        "timeout_seconds": 900,
                        "scope": "state+ui",
                    },
                },
                {
                    "task_id": "task_003",
                    "description": "Wire the dashboard view and verify the overall experience.",
                    "role": "reviewer",
                    "dependencies": ["task_002"],
                    "inputs": {},
                    "expected_outputs": ["src/screens/Dashboard.tsx", "src/App.tsx"],
                    "verification": {
                        "type": "manual",
                        "success_criteria": "Dashboard renders and goals update correctly.",
                    },
                    "constraints": {
                        "max_files": 8,
                        "allowed_commands": ["npm run dev"],
                        "timeout_seconds": 900,
                        "scope": "dashboard",
                    },
                },
            ],
            "metadata": {
                "total_tasks": 3,
                "estimated_complexity": "simple",
                "parallel_opportunities": ["task_001"],
            },
        }

    def _run_summary_payload(self) -> dict[str, Any]:
        return {
            "status": "success",
            "summary": (
                "The build produced a lightweight productivity dashboard with goal tracking and a "
                "clear summary view. The feature set stays small and focused while providing a "
                "usable starting point for future expansion."
            ),
            "files_generated": [
                "README.md",
                "src/App.tsx",
                "src/components/GoalCard.tsx",
                "src/state/useGoals.ts",
            ],
            "verification_results": {
                "build": {"status": "passed", "details": "npm run build"},
            },
            "next_steps": [
                "Run `npm run dev` to start the dashboard locally.",
                "Adjust goal defaults in the settings panel.",
            ],
        }


def get_llm_client() -> LlmClient:
    """Return an LLM client that respects environment overrides at call time."""
    return DynamicLlmClient()
