"""Orchestrator for high-level build coordination (VF-073, VF-074, VF-075)."""

from typing import Optional
from jinja2 import Template

from models.base.llm_client import LlmClient, LlmRequest, LlmMessage
from models.router import get_model_router, RoutingContext
from models.validation import OutputValidator
from models.repair import OutputRepair, RepairFailedError

from orchestration.prompts import (
    CONCEPT_GENERATION_TEMPLATE,
    TASKGRAPH_GENERATION_TEMPLATE,
    RUN_SUMMARY_TEMPLATE,
)
from orchestration.schemas import (
    CONCEPT_SCHEMA,
    TASKGRAPH_SCHEMA,
    RUN_SUMMARY_SCHEMA,
)
from orchestration.models import ConceptDoc, TaskGraph, RunSummary


class Orchestrator:
    """High-level orchestrator for generating concepts, task graphs, and summaries."""

    def __init__(self, llm_client: LlmClient, max_repair_attempts: int = 2):
        """
        Initialize orchestrator.

        Args:
            llm_client: LLM client for making model requests
            max_repair_attempts: Maximum repair attempts for invalid outputs
        """
        self.llm_client = llm_client
        self.router = get_model_router()
        self.validator = OutputValidator()
        self.repair = OutputRepair(llm_client, max_repair_attempts)

    async def generateConcept(self, build_spec: dict) -> ConceptDoc:
        """
        Generate concept document from BuildSpec (VF-073).

        Args:
            build_spec: BuildSpec dictionary with stack, ideaSeed, etc.

        Returns:
            ConceptDoc with idea description, features, tech stack, etc.

        Raises:
            ValueError: If concept generation fails after repair attempts
        """
        # Extract BuildSpec fields for template
        session_id = build_spec["sessionId"]
        stack = build_spec["stack"]
        idea_seed = build_spec["ideaSeed"]
        target = build_spec["target"]

        # Prepare template context
        context = {
            "stack_preset": stack.get("preset", "UNKNOWN"),
            "runtime": stack.get("runtime", "UNKNOWN"),
            "platform": target.get("platform", "UNKNOWN"),
            "audience": target.get("audience", "General users"),
            "idea_genre": idea_seed.get("genre", "General application"),
            "idea_seed": idea_seed.get("seed", "A useful application"),
            "twist": idea_seed.get("twist", "With a unique approach"),
            "complexity": idea_seed.get("complexity", "simple"),
        }

        # Render prompt template
        template = Template(CONCEPT_GENERATION_TEMPLATE)
        prompt = template.render(**context)

        # Select model based on complexity
        routing_context = RoutingContext(
            role="orchestrator",
            complexity=context["complexity"],
            metadata={"operation": "concept_generation"},
        )
        provider, model = self.router.select_model(routing_context)

        # Make LLM request
        request = LlmRequest(
            messages=[
                LlmMessage(
                    role="system",
                    content="You are an expert software architect. You generate structured, practical concepts for software projects.",
                ),
                LlmMessage(role="user", content=prompt),
            ],
            model=model,
            temperature=0.7,
            metadata={"session_id": session_id, "operation": "concept_generation"},
        )

        response = await self.llm_client.complete(request)

        # Validate response
        result = self.validator.validate(response, CONCEPT_SCHEMA)

        # Repair if validation failed
        if not result.valid:
            try:
                response = await self.repair.repair(
                    request, response, result.errors, CONCEPT_SCHEMA
                )
                result = self.validator.validate(response, CONCEPT_SCHEMA)
            except RepairFailedError as e:
                raise ValueError(
                    f"Failed to generate valid concept after {len(e.attempts)} attempts. "
                    f"Last errors: {result.errors}"
                ) from e

        if not result.valid:
            raise ValueError(f"Concept validation failed: {result.errors}")

        # Parse into ConceptDoc
        return ConceptDoc.from_dict(session_id, result.parsed_output)

    async def createTaskGraph(
        self, build_spec: dict, concept: ConceptDoc
    ) -> TaskGraph:
        """
        Generate TaskGraph from BuildSpec and ConceptDoc (VF-074).

        Args:
            build_spec: BuildSpec dictionary
            concept: ConceptDoc from generateConcept

        Returns:
            TaskGraph with tasks, dependencies, and metadata

        Raises:
            ValueError: If task graph generation or validation fails
        """
        session_id = build_spec["sessionId"]
        stack = build_spec["stack"]
        target = build_spec["target"]
        idea_seed = build_spec["ideaSeed"]

        # Prepare template context
        context = {
            "idea_description": concept.idea_description,
            "features": concept.features,
            "tech_stack": concept.tech_stack,
            "file_structure": concept.file_structure,
            "stack_preset": stack.get("preset", "UNKNOWN"),
            "platform": target.get("platform", "UNKNOWN"),
            "complexity": idea_seed.get("complexity", "simple"),
        }

        # Render prompt template
        template = Template(TASKGRAPH_GENERATION_TEMPLATE)
        prompt = template.render(**context)

        # Select model (orchestrator role, slightly higher complexity)
        routing_context = RoutingContext(
            role="orchestrator",
            complexity="medium",  # Task planning is inherently complex
            metadata={"operation": "taskgraph_generation"},
        )
        provider, model = self.router.select_model(routing_context)

        # Make LLM request
        request = LlmRequest(
            messages=[
                LlmMessage(
                    role="system",
                    content="You are an expert task planner. You break down software projects into dependency-ordered tasks that form a valid DAG.",
                ),
                LlmMessage(role="user", content=prompt),
            ],
            model=model,
            temperature=0.6,  # Slightly lower for more structured output
            metadata={"session_id": session_id, "operation": "taskgraph_generation"},
        )

        response = await self.llm_client.complete(request)

        # Validate response
        result = self.validator.validate(response, TASKGRAPH_SCHEMA)

        # Repair if validation failed
        if not result.valid:
            try:
                response = await self.repair.repair(
                    request, response, result.errors, TASKGRAPH_SCHEMA
                )
                result = self.validator.validate(response, TASKGRAPH_SCHEMA)
            except RepairFailedError as e:
                raise ValueError(
                    f"Failed to generate valid task graph after {len(e.attempts)} attempts. "
                    f"Last errors: {result.errors}"
                ) from e

        if not result.valid:
            raise ValueError(f"TaskGraph validation failed: {result.errors}")

        # Parse into TaskGraph
        task_graph = TaskGraph.from_dict(session_id, result.parsed_output)

        # Validate DAG structure
        is_valid_dag, dag_errors = task_graph.validate_dag()
        if not is_valid_dag:
            raise ValueError(f"TaskGraph DAG validation failed: {dag_errors}")

        return task_graph

    async def summarize(
        self,
        session_id: str,
        files_generated: list[str],
        completed_tasks: list[dict],
        verification_results: dict[str, str],
    ) -> RunSummary:
        """
        Generate run summary from build artifacts (VF-075).

        Args:
            session_id: Session identifier
            files_generated: List of all files created during build
            completed_tasks: List of completed tasks with status
            verification_results: Dict of verification step results

        Returns:
            RunSummary with status, summary, run instructions, and limitations

        Raises:
            ValueError: If summary generation fails
        """
        # Prepare template context
        context = {
            "session_id": session_id,
            "files_generated": files_generated,
            "completed_tasks": completed_tasks,
            "verification_results": verification_results,
        }

        # Render prompt template
        template = Template(RUN_SUMMARY_TEMPLATE)
        prompt = template.render(**context)

        # Select model (orchestrator role, simple complexity)
        routing_context = RoutingContext(
            role="orchestrator",
            complexity="simple",
            metadata={"operation": "run_summary"},
        )
        provider, model = self.router.select_model(routing_context)

        # Make LLM request
        request = LlmRequest(
            messages=[
                LlmMessage(
                    role="system",
                    content="You are a technical writer. You document completed software builds with clear, accurate summaries and run instructions.",
                ),
                LlmMessage(role="user", content=prompt),
            ],
            model=model,
            temperature=0.5,  # Lower for factual, consistent summaries
            metadata={"session_id": session_id, "operation": "run_summary"},
        )

        response = await self.llm_client.complete(request)

        # Validate response
        result = self.validator.validate(response, RUN_SUMMARY_SCHEMA)

        # Repair if validation failed
        if not result.valid:
            try:
                response = await self.repair.repair(
                    request, response, result.errors, RUN_SUMMARY_SCHEMA
                )
                result = self.validator.validate(response, RUN_SUMMARY_SCHEMA)
            except RepairFailedError as e:
                raise ValueError(
                    f"Failed to generate valid summary after {len(e.attempts)} attempts. "
                    f"Last errors: {result.errors}"
                ) from e

        if not result.valid:
            raise ValueError(f"Summary validation failed: {result.errors}")

        # Parse into RunSummary
        return RunSummary.from_dict(session_id, result.parsed_output)


def get_orchestrator(llm_client: LlmClient) -> Orchestrator:
    """
    Factory function for creating Orchestrator instance.

    Args:
        llm_client: LLM client to use

    Returns:
        Configured Orchestrator instance
    """
    return Orchestrator(llm_client)
