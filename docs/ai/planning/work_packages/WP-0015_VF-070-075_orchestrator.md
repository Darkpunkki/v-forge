# WP-0015 — Orchestrator prompt templates and implementation

## VF Tasks Included
- VF-070: Orchestrator prompt templates: Concept generation (JSON + Markdown)
- VF-071: Orchestrator prompt templates: TaskGraph generation (DAG + constraints)
- VF-072: Orchestrator prompt templates: Run summary
- VF-073: Implement Orchestrator.generateConcept(BuildSpec)
- VF-074: Implement Orchestrator.createTaskGraph(BuildSpec, ConceptDoc)
- VF-075: Implement Orchestrator.summarize(artifacts)

## Goal
Enable the orchestrator to generate concepts, task graphs, and run summaries by implementing prompt templates and orchestrator methods with proper validation and integration into the model layer.

## Dependencies
- WP-0012 ✓ (base model layer: LlmClient interface, OpenAiProvider, ModelProviderRegistry)
- WP-0014 ✓ (model routing, validation, repair)

## Current State Analysis

From previous work packages, we have:
- ✓ LlmClient interface with complete() method
- ✓ OpenAiProvider implementation
- ✓ ModelProviderRegistry for config-driven provider selection
- ✓ ModelRouter for role/complexity-based routing
- ✓ OutputValidator for JSON schema validation
- ✓ OutputRepair for automatic repair of malformed outputs
- ✓ BuildSpec model (from spec_builder.py) with stack/seed/idea information
- ✓ Session model with phase management

**Gaps identified:**
1. **No orchestrator implementation** - Need Orchestrator class to generate concepts and task graphs
2. **No prompt templates** - Need templates for concept generation, task graph generation, and run summary
3. **No output schemas** - Need JSON schemas for concept and task graph validation
4. **No integration** - Need to wire orchestrator into session flow

## Execution Plan

### 1. Define Data Models (Prerequisites)

Before implementing templates and orchestrator, define the domain models:

**ConceptDoc** (output of VF-073):
```python
@dataclass
class ConceptDoc:
    """Structured concept for a build."""
    session_id: str
    idea_description: str
    features: list[str]
    tech_stack: dict[str, str]
    file_structure: dict[str, str]
    verification_steps: list[str]
    constraints: list[str]
```

**TaskGraph** (output of VF-074):
```python
@dataclass
class Task:
    task_id: str
    description: str
    role: str  # "worker", "foreman", "fixer", "reviewer"
    dependencies: list[str]
    inputs: dict[str, Any]
    expected_outputs: list[str]
    verification: dict[str, Any]
    constraints: dict[str, Any]

@dataclass
class TaskGraph:
    """DAG of tasks for executing a build."""
    session_id: str
    tasks: list[Task]
    metadata: dict[str, Any]
```

**RunSummary** (output of VF-075):
```python
@dataclass
class RunSummary:
    """Summary of completed build execution."""
    session_id: str
    status: str  # "success", "partial", "failed"
    summary: str
    files_generated: list[str]
    verification_results: dict[str, Any]
    how_to_run: list[str]
    limitations: list[str]
```

### 2. Implement Prompt Templates (VF-070, VF-071, VF-072)

Create `orchestration/prompts.py` with Jinja2 templates:

**VF-070: Concept Generation Template**
```python
CONCEPT_GENERATION_TEMPLATE = """
You are an expert software architect. Generate a detailed concept for building the following application.

## Build Specification
- **Stack Preset:** {{ build_spec.stack_preset }}
- **Idea Genre:** {{ build_spec.idea_genre }}
- **Idea Seed:** {{ build_spec.idea_seed }}
- **Twist:** {{ build_spec.twist }}
- **Complexity:** {{ build_spec.complexity }}

## Your Task
Generate a concept document that includes:
1. **idea_description**: A 2-3 sentence description of what this application does
2. **features**: List of 3-8 specific features to implement (keep simple for {{ build_spec.complexity }} complexity)
3. **tech_stack**: Technology choices based on stack preset (framework, language, testing, build tools)
4. **file_structure**: Key files and directories to create with brief descriptions
5. **verification_steps**: Commands to run to verify the build works
6. **constraints**: Important limitations or scope boundaries

Return ONLY valid JSON matching this schema:
{
  "idea_description": "string",
  "features": ["string"],
  "tech_stack": {"category": "technology"},
  "file_structure": {"path": "description"},
  "verification_steps": ["command"],
  "constraints": ["constraint"]
}
"""
```

**VF-071: TaskGraph Generation Template**
```python
TASKGRAPH_GENERATION_TEMPLATE = """
You are an expert task planner. Generate a dependency-ordered task graph for implementing this concept.

## Concept
{{ concept_summary }}

## Build Specification
- **Stack:** {{ build_spec.stack_preset }}
- **Complexity:** {{ build_spec.complexity }}

## Your Task
Create a DAG (directed acyclic graph) of tasks. Each task should:
- Have a unique task_id (e.g., "task_001")
- Specify a role: "worker" (implementation), "foreman" (planning/coordination), "reviewer" (validation)
- List dependencies (task_ids that must complete first)
- Define inputs (data needed) and expected_outputs (files/results produced)
- Include verification (how to test this task's output)
- Specify constraints (resource limits, command allowlists, scope boundaries)

For {{ build_spec.complexity }} complexity:
- Simple: 3-5 tasks
- Medium: 5-8 tasks
- Complex: 8-12 tasks

Return ONLY valid JSON matching this schema:
{
  "tasks": [
    {
      "task_id": "string",
      "description": "string",
      "role": "worker|foreman|reviewer",
      "dependencies": ["task_id"],
      "inputs": {},
      "expected_outputs": ["path or description"],
      "verification": {"type": "build|test|lint", "commands": ["cmd"]},
      "constraints": {"max_files": 10, "allowed_commands": ["npm", "pytest"]}
    }
  ],
  "metadata": {"total_tasks": 0, "estimated_complexity": "simple|medium|complex"}
}
"""
```

**VF-072: Run Summary Template**
```python
RUN_SUMMARY_TEMPLATE = """
You are a technical writer. Summarize the completed build execution.

## Artifacts
{{ artifacts_summary }}

## Your Task
Generate a summary that includes:
1. **status**: "success", "partial", or "failed"
2. **summary**: 2-3 sentence overview of what was built
3. **files_generated**: List of created files
4. **verification_results**: Summary of build/test/lint outcomes
5. **how_to_run**: Step-by-step instructions to run the application
6. **limitations**: Known issues or scope limitations

Return ONLY valid JSON matching this schema:
{
  "status": "success|partial|failed",
  "summary": "string",
  "files_generated": ["path"],
  "verification_results": {"step": "result"},
  "how_to_run": ["instruction"],
  "limitations": ["limitation"]
}
"""
```

### 3. Implement Orchestrator Class (VF-073, VF-074, VF-075)

Create `orchestration/orchestrator.py`:

```python
from dataclasses import asdict
from typing import Optional
from jinja2 import Template

from models.base.llm_client import LlmClient, LlmRequest, LlmMessage
from models.router import get_model_router, RoutingContext
from models.validation import OutputValidator, ValidationResult
from models.repair import OutputRepair
from orchestration.prompts import (
    CONCEPT_GENERATION_TEMPLATE,
    TASKGRAPH_GENERATION_TEMPLATE,
    RUN_SUMMARY_TEMPLATE
)

class Orchestrator:
    """High-level orchestrator for generating concepts, task graphs, and summaries."""

    def __init__(self, llm_client: LlmClient):
        self.llm_client = llm_client
        self.router = get_model_router()
        self.validator = OutputValidator()
        self.repair = OutputRepair(llm_client)

    async def generateConcept(self, build_spec: BuildSpec) -> ConceptDoc:
        """VF-073: Generate concept from BuildSpec."""
        # Render prompt template
        template = Template(CONCEPT_GENERATION_TEMPLATE)
        prompt = template.render(build_spec=build_spec)

        # Select model based on complexity
        context = RoutingContext(
            role="orchestrator",
            complexity=build_spec.complexity
        )
        provider, model = self.router.select_model(context)

        # Make LLM request
        request = LlmRequest(
            messages=[
                LlmMessage(role="system", content="You are an expert software architect."),
                LlmMessage(role="user", content=prompt)
            ],
            model=model,
            temperature=0.7
        )

        response = await self.llm_client.complete(request)

        # Validate and repair if needed
        schema = CONCEPT_SCHEMA  # JSON schema definition
        result = self.validator.validate(response, schema)

        if not result.valid:
            response = await self.repair.repair(request, response, result.errors, schema)
            result = self.validator.validate(response, schema)
            if not result.valid:
                raise ValueError(f"Failed to generate valid concept: {result.errors}")

        # Parse into ConceptDoc
        data = result.parsed_output
        return ConceptDoc(
            session_id=build_spec.session_id,
            idea_description=data["idea_description"],
            features=data["features"],
            tech_stack=data["tech_stack"],
            file_structure=data["file_structure"],
            verification_steps=data["verification_steps"],
            constraints=data["constraints"]
        )

    async def createTaskGraph(self, build_spec: BuildSpec, concept: ConceptDoc) -> TaskGraph:
        """VF-074: Generate TaskGraph from BuildSpec and ConceptDoc."""
        # Similar implementation to generateConcept
        # Uses TASKGRAPH_GENERATION_TEMPLATE
        # Routes to orchestrator role with build_spec.complexity
        # Validates against TASKGRAPH_SCHEMA
        # Returns TaskGraph instance
        pass

    async def summarize(self, artifacts: dict) -> RunSummary:
        """VF-075: Generate run summary from artifacts."""
        # Similar implementation to generateConcept
        # Uses RUN_SUMMARY_TEMPLATE
        # Routes to orchestrator role with "simple" complexity
        # Validates against RUN_SUMMARY_SCHEMA
        # Returns RunSummary instance
        pass
```

### 4. Define JSON Schemas

Create `orchestration/schemas.py` with JSON schemas for validation:

```python
CONCEPT_SCHEMA = {
    "type": "object",
    "properties": {
        "idea_description": {"type": "string", "minLength": 20},
        "features": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 8},
        "tech_stack": {"type": "object", "minProperties": 1},
        "file_structure": {"type": "object", "minProperties": 1},
        "verification_steps": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "constraints": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["idea_description", "features", "tech_stack", "file_structure", "verification_steps", "constraints"]
}

TASKGRAPH_SCHEMA = {
    "type": "object",
    "properties": {
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "pattern": "^task_\\d+$"},
                    "description": {"type": "string"},
                    "role": {"type": "string", "enum": ["worker", "foreman", "reviewer"]},
                    "dependencies": {"type": "array", "items": {"type": "string"}},
                    "inputs": {"type": "object"},
                    "expected_outputs": {"type": "array", "items": {"type": "string"}},
                    "verification": {"type": "object"},
                    "constraints": {"type": "object"}
                },
                "required": ["task_id", "description", "role", "dependencies", "expected_outputs"]
            },
            "minItems": 3
        },
        "metadata": {"type": "object"}
    },
    "required": ["tasks", "metadata"]
}

RUN_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["success", "partial", "failed"]},
        "summary": {"type": "string", "minLength": 20},
        "files_generated": {"type": "array", "items": {"type": "string"}},
        "verification_results": {"type": "object"},
        "how_to_run": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "limitations": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["status", "summary", "files_generated", "how_to_run"]
}
```

### 5. Write Comprehensive Tests

**test_orchestrator.py:**
- Test generateConcept with valid BuildSpec
- Test concept validation against schema
- Test repair on invalid concept output
- Test createTaskGraph with concept
- Test DAG validation (no cycles)
- Test summarize with artifacts
- Test model routing for orchestrator role
- Test error handling for all methods
- Test integration with model layer

## Done Means
- [x] VF-070: Prompt templates implemented
  - **File:** `orchestration/prompts.py` (CONCEPT_GENERATION_TEMPLATE, TASKGRAPH_GENERATION_TEMPLATE, RUN_SUMMARY_TEMPLATE)
  - **Features:** Comprehensive Jinja2 templates with BuildSpec/ConceptDoc context, detailed JSON output instructions, complexity-specific guidance
  - **Tests:** All 3 templates tested through Orchestrator integration tests

- [x] VF-071: TaskGraph prompt template
  - **File:** `orchestration/prompts.py` (TASKGRAPH_GENERATION_TEMPLATE)
  - **Features:** DAG structure with dependencies, role assignment (worker/foreman/reviewer), verification specs, constraints
  - **Tests:** Template generates valid task graphs validated against schema with DAG cycle detection

- [x] VF-072: Run summary prompt template
  - **File:** `orchestration/prompts.py` (RUN_SUMMARY_TEMPLATE)
  - **Features:** Status (success/partial/failed), summary, files generated, verification results, run instructions, limitations
  - **Tests:** Template produces complete summaries with all required fields

- [x] VF-073: Orchestrator.generateConcept() implemented
  - **File:** `orchestration/orchestrator.py` (Orchestrator class with generateConcept method)
  - **Features:** Jinja2 template rendering, ModelRouter integration, OutputValidator validation, OutputRepair retry logic, ConceptDoc parsing
  - **Tests:** 3 tests - successful concept generation, validation failure handling, full integration with model layer

- [x] VF-074: Orchestrator.createTaskGraph() implemented
  - **File:** `orchestration/orchestrator.py` (createTaskGraph method)
  - **Features:** TaskGraph generation from concept + BuildSpec, JSON schema validation, DAG cycle detection, dependency validation
  - **Tests:** 2 tests - successful task graph generation, DAG cycle detection raises ValueError

- [x] VF-075: Orchestrator.summarize() implemented
  - **File:** `orchestration/orchestrator.py` (summarize method)
  - **Features:** Run summary from artifacts (files, tasks, verification results), lower temperature for consistency
  - **Tests:** 2 tests - successful summary generation, temperature setting verification

**Total tests:** 304 (was 279, added 25 new tests)
**All tests passing:** ✓ (1 skipped for schema edge case)
**New test files:**
- `apps/api/tests/test_orchestrator.py` (8 tests)
- `apps/api/tests/test_orchestration_models.py` (17 tests)

## Verification Commands
```bash
cd apps/api && pytest tests/test_orchestrator.py -v
cd apps/api && pytest -v
```

## Notes
- Orchestrator uses ModelRouter to select appropriate models based on complexity
- OutputValidator + OutputRepair ensure reliable JSON outputs
- All prompt templates request JSON-only responses for deterministic parsing
- Jinja2 dependency required (add to requirements.txt)
