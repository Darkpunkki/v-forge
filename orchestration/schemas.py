"""JSON schemas for validating orchestrator LLM outputs."""

# VF-070: Concept document schema
CONCEPT_SCHEMA = {
    "type": "object",
    "properties": {
        "idea_description": {
            "type": "string",
            "minLength": 20,
            "maxLength": 500,
            "description": "Clear description of the application (2-3 sentences)",
        },
        "features": {
            "type": "array",
            "items": {"type": "string", "minLength": 10},
            "minItems": 3,
            "maxItems": 8,
            "description": "List of specific features to implement",
        },
        "tech_stack": {
            "type": "object",
            "properties": {
                "framework": {"type": "string"},
                "language": {"type": "string"},
                "testing": {"type": "string"},
                "build": {"type": "string"},
                "database": {"type": "string"},
                "runtime": {"type": "string"},
            },
            "required": ["framework", "language", "testing", "build", "runtime"],
            "additionalProperties": True,
            "description": "Technology choices",
        },
        "file_structure": {
            "type": "object",
            "minProperties": 5,
            "maxProperties": 30,
            "additionalProperties": {"type": "string", "minLength": 5, "maxLength": 200},
            "description": "Key files and directories with descriptions",
        },
        "verification_steps": {
            "type": "array",
            "items": {"type": "string", "minLength": 5},
            "minItems": 3,
            "maxItems": 10,
            "description": "Commands to verify the build",
        },
        "constraints": {
            "type": "array",
            "items": {"type": "string", "minLength": 10},
            "minItems": 2,
            "maxItems": 10,
            "description": "Scope boundaries and limitations",
        },
    },
    "required": [
        "idea_description",
        "features",
        "tech_stack",
        "file_structure",
        "verification_steps",
        "constraints",
    ],
    "additionalProperties": False,
}

# VF-071: TaskGraph schema
TASKGRAPH_SCHEMA = {
    "type": "object",
    "properties": {
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "pattern": "^task_\\d{3}$",
                        "description": "Unique task identifier (task_001, task_002, etc.)",
                    },
                    "description": {
                        "type": "string",
                        "minLength": 20,
                        "maxLength": 300,
                        "description": "Clear description of task purpose",
                    },
                    "role": {
                        "type": "string",
                        "enum": ["worker", "foreman", "reviewer"],
                        "description": "Agent role for this task",
                    },
                    "dependencies": {
                        "type": "array",
                        "items": {"type": "string", "pattern": "^task_\\d{3}$"},
                        "description": "Task IDs that must complete first",
                    },
                    "inputs": {
                        "type": "object",
                        "description": "Context and data needed for task",
                    },
                    "expected_outputs": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 3},
                        "minItems": 1,
                        "maxItems": 20,
                        "description": "Files or results this task produces",
                    },
                    "verification": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["build", "test", "lint", "manual", "integration"],
                            },
                            "commands": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 0,
                            },
                            "success_criteria": {"type": "string"},
                        },
                        "required": ["type"],
                        "description": "How to verify task completion",
                    },
                    "constraints": {
                        "type": "object",
                        "properties": {
                            "max_files": {"type": "integer", "minimum": 1, "maximum": 100},
                            "allowed_commands": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "timeout_seconds": {
                                "type": "integer",
                                "minimum": 60,
                                "maximum": 3600,
                            },
                            "scope": {"type": "string"},
                        },
                        "description": "Resource and scope limits",
                    },
                },
                "required": [
                    "task_id",
                    "description",
                    "role",
                    "dependencies",
                    "expected_outputs",
                    "verification",
                ],
                "additionalProperties": False,
            },
            "minItems": 3,
            "maxItems": 20,
        },
        "metadata": {
            "type": "object",
            "properties": {
                "total_tasks": {"type": "integer", "minimum": 3},
                "estimated_complexity": {
                    "type": "string",
                    "enum": ["simple", "medium", "complex"],
                },
                "parallel_opportunities": {
                    "type": "array",
                    "items": {"type": "string", "pattern": "^task_\\d{3}$"},
                },
            },
            "description": "Task graph metadata",
        },
    },
    "required": ["tasks", "metadata"],
    "additionalProperties": False,
}

# VF-072: Run summary schema
RUN_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["success", "partial", "failed"],
            "description": "Overall build status",
        },
        "summary": {
            "type": "string",
            "minLength": 50,
            "maxLength": 1000,
            "description": "2-4 sentence summary of what was built",
        },
        "files_generated": {
            "type": "array",
            "items": {"type": "string", "minLength": 3},
            "minItems": 1,
            "maxItems": 100,
            "description": "All files created during build",
        },
        "verification_results": {
            "type": "object",
            "minProperties": 1,
            "patternProperties": {
                "^[a-zA-Z0-9_]+$": {
                    "type": "string",
                    "minLength": 5,
                }
            },
            "description": "Verification step outcomes",
        },
        "how_to_run": {
            "type": "array",
            "items": {"type": "string", "minLength": 10},
            "minItems": 3,
            "maxItems": 15,
            "description": "Step-by-step run instructions",
        },
        "limitations": {
            "type": "array",
            "items": {"type": "string", "minLength": 10},
            "minItems": 2,
            "maxItems": 15,
            "description": "Known limitations and scope boundaries",
        },
    },
    "required": [
        "status",
        "summary",
        "files_generated",
        "verification_results",
        "how_to_run",
        "limitations",
    ],
    "additionalProperties": False,
}
