"""Prompt templates for orchestrator LLM interactions (VF-070, VF-071, VF-072)."""

# VF-070: Concept generation prompt template
CONCEPT_GENERATION_TEMPLATE = """You are an expert software architect. Generate a detailed technical concept for building the following application.

## Build Specification
- **Stack Preset:** {{ stack_preset }}
- **Runtime:** {{ runtime }}
- **Platform:** {{ platform }}
- **Idea Genre:** {{ idea_genre }}
- **Idea Seed:** {{ idea_seed }}
- **Twist:** {{ twist }}
- **Complexity:** {{ complexity }}
- **Audience:** {{ audience }}

## Context
The goal is to create a {{ complexity }} complexity {{ platform }} application using {{ stack_preset }}.
The application should embody the theme "{{ idea_seed }}" with a twist of "{{ twist }}".
Target audience: {{ audience }}.

## Your Task
Generate a structured concept document that includes:

1. **idea_description** (string): A clear 2-3 sentence description of what this application does and its core purpose. Be specific about functionality.

2. **features** (array of strings): List 3-8 specific, concrete features to implement. Match feature count to complexity:
   - simple: 3-4 features
   - medium: 5-6 features
   - complex: 7-8 features
   Each feature should be a single, well-defined capability (e.g., "User authentication with email/password", "Real-time chat between users").

3. **tech_stack** (object): Technology choices based on the stack preset. Include:
   - framework: Primary framework/library (e.g., "React", "FastAPI")
   - language: Programming language (e.g., "TypeScript", "Python")
   - testing: Testing framework (e.g., "Vitest", "pytest")
   - build: Build tool (e.g., "Vite", "setuptools")
   - database: Database if needed (e.g., "SQLite", "none")
   - runtime: Runtime environment (e.g., "Node.js 20", "Python 3.12")

4. **file_structure** (object): Key files and directories to create, with path as key and brief description as value. Include:
   - Entry point files (e.g., "src/main.ts", "app.py")
   - Core module directories (e.g., "src/components/", "src/api/")
   - Configuration files (e.g., "package.json", "requirements.txt")
   - Test directories (e.g., "tests/")
   Aim for 8-15 entries matching {{ complexity }} complexity.

5. **verification_steps** (array of strings): Specific commands to run to verify the build works. Include:
   - Dependency installation command (e.g., "npm install", "pip install -r requirements.txt")
   - Build command if applicable (e.g., "npm run build")
   - Test command (e.g., "npm test", "pytest")
   - Run command (e.g., "npm run dev", "python app.py")
   List 3-5 verification steps.

6. **constraints** (array of strings): Important limitations or scope boundaries to maintain simplicity. Include:
   - Scope limitations (e.g., "No user authentication for MVP", "Single-page application only")
   - Technical constraints (e.g., "No external API calls", "Local storage only, no database")
   - Complexity guards (e.g., "Maximum 5 React components", "No more than 3 API endpoints")
   List 3-5 constraints matching {{ complexity }} level.

## Important Guidelines
- Keep the concept aligned with {{ complexity }} complexity - don't overengineer
- Ensure all features are realistic for a small demonstration project
- Use technologies compatible with {{ stack_preset }}
- File structure should be practical and runnable
- Verification steps must be concrete, executable commands
- Constraints should prevent scope creep

## Output Format
Return ONLY a valid JSON object (no markdown code blocks, no explanatory text). The JSON must match this exact structure:

{
  "idea_description": "A clear description of the application...",
  "features": [
    "Specific feature 1",
    "Specific feature 2",
    "Specific feature 3"
  ],
  "tech_stack": {
    "framework": "Framework name",
    "language": "Language name",
    "testing": "Test framework",
    "build": "Build tool",
    "database": "Database or 'none'",
    "runtime": "Runtime environment"
  },
  "file_structure": {
    "path/to/file1": "Brief description of file1",
    "path/to/file2": "Brief description of file2"
  },
  "verification_steps": [
    "command to install dependencies",
    "command to build (if applicable)",
    "command to run tests",
    "command to run application"
  ],
  "constraints": [
    "Scope constraint 1",
    "Technical constraint 2",
    "Complexity guard 3"
  ]
}
"""

# VF-071: TaskGraph generation prompt template
TASKGRAPH_GENERATION_TEMPLATE = """You are an expert task planner and software architect. Generate a dependency-ordered task graph (DAG) for implementing the following concept.

## Concept Summary
**Idea:** {{ idea_description }}

**Features to Implement:**
{% for feature in features %}
- {{ feature }}
{% endfor %}

**Technology Stack:**
{% for key, value in tech_stack.items() %}
- {{ key }}: {{ value }}
{% endfor %}

**File Structure:**
{% for path, desc in file_structure.items() %}
- {{ path }}: {{ desc }}
{% endfor %}

## Build Specification
- **Stack Preset:** {{ stack_preset }}
- **Complexity:** {{ complexity }}
- **Platform:** {{ platform }}

## Your Task
Create a directed acyclic graph (DAG) of tasks that will implement this concept. Each task represents a discrete unit of work.

### Task Count Guidelines
Match task count to complexity:
- **simple**: 3-5 tasks (minimal implementation path)
- **medium**: 6-8 tasks (moderate breakdown with some parallelization)
- **complex**: 9-12 tasks (comprehensive breakdown with dependencies)

### Task Structure
Each task must include:

1. **task_id** (string): Unique identifier in format "task_001", "task_002", etc. (sequential numbering)

2. **description** (string): Clear, specific description of what this task accomplishes (e.g., "Set up project structure and install dependencies", "Implement user authentication API endpoints")

3. **role** (string): Agent role for this task:
   - **"worker"**: Implementation tasks (writing code, creating files, installing dependencies)
   - **"foreman"**: Planning/coordination tasks (designing architecture, breaking down features)
   - **"reviewer"**: Validation tasks (code review, testing, quality checks)
   Most tasks should be "worker". Use "foreman" for initial setup/planning. Use "reviewer" for final validation.

4. **dependencies** (array of task_ids): Tasks that must complete before this one can start. Use empty array [] for tasks with no dependencies. Create a realistic dependency chain.

5. **inputs** (object): Data or context needed to execute this task:
   - concept: Reference to concept document
   - previous_outputs: Files or data from dependent tasks
   - config: Configuration values needed
   Example: {"concept": "full_concept_doc", "dependencies_installed": true}

6. **expected_outputs** (array of strings): Files, directories, or results this task produces:
   - File paths (e.g., "src/App.tsx", "tests/test_api.py")
   - Directories (e.g., "src/components/")
   - Results (e.g., "authentication system functional", "all tests passing")
   List 1-5 outputs per task.

7. **verification** (object): How to verify this task completed successfully:
   - type: "build", "test", "lint", "manual", or "integration"
   - commands: Array of shell commands to run
   - success_criteria: What indicates success
   Example: {"type": "test", "commands": ["npm test"], "success_criteria": "All tests pass"}

8. **constraints** (object): Resource and scope limits for this task:
   - max_files: Maximum number of files to create/modify (e.g., 5, 10, 20)
   - allowed_commands: Allowlist of command families (e.g., ["npm", "node"], ["pytest", "python"])
   - timeout_seconds: Maximum execution time (e.g., 300, 600)
   - scope: Specific boundaries (e.g., "single component only", "API endpoints only")

### DAG Requirements
- **No cycles**: Task dependencies must form a valid DAG (directed acyclic graph)
- **Logical ordering**: Dependencies should reflect realistic build order (e.g., setup before implementation, implementation before testing)
- **Parallelization opportunities**: Independent tasks should have no dependencies on each other
- **Progressive complexity**: Start with simple setup tasks, build up to implementation, end with verification

### Typical Task Flow Pattern
A good task graph often follows this pattern:
1. Initial setup (foreman role): Project structure, dependencies
2. Core implementation (worker role): Parallel feature implementations
3. Integration (worker role): Connecting components
4. Testing (worker role): Writing and running tests
5. Final review (reviewer role): Quality validation

## Output Format
Return ONLY a valid JSON object (no markdown code blocks, no explanatory text). The JSON must match this exact structure:

{
  "tasks": [
    {
      "task_id": "task_001",
      "description": "Detailed task description",
      "role": "worker",
      "dependencies": [],
      "inputs": {
        "concept": "full_concept_doc"
      },
      "expected_outputs": [
        "path/to/output1",
        "path/to/output2"
      ],
      "verification": {
        "type": "build",
        "commands": ["npm run build"],
        "success_criteria": "Build completes without errors"
      },
      "constraints": {
        "max_files": 10,
        "allowed_commands": ["npm", "node"],
        "timeout_seconds": 300,
        "scope": "Project setup only"
      }
    }
  ],
  "metadata": {
    "total_tasks": 5,
    "estimated_complexity": "simple",
    "parallel_opportunities": ["task_003", "task_004"]
  }
}
"""

# VF-072: Run summary prompt template
RUN_SUMMARY_TEMPLATE = """You are a technical writer documenting a completed software build. Generate a comprehensive summary of what was built and how to use it.

## Build Artifacts
**Session ID:** {{ session_id }}

**Generated Files:**
{% for file in files_generated %}
- {{ file }}
{% endfor %}

**Tasks Completed:**
{% for task in completed_tasks %}
- {{ task.task_id }}: {{ task.description }} ({{ task.status }})
{% endfor %}

**Verification Results:**
{% for step, result in verification_results.items() %}
- {{ step }}: {{ result }}
{% endfor %}

## Your Task
Generate a run summary that documents:

1. **status** (string): Overall build status:
   - "success": All tasks completed, all verifications passed
   - "partial": Some tasks completed but verifications had issues or some features incomplete
   - "failed": Build did not complete or critical verifications failed

2. **summary** (string): A clear 2-4 sentence summary of:
   - What was built
   - Key technologies used
   - Main functionality delivered
   - Overall quality/completeness

3. **files_generated** (array of strings): Complete list of all files created during the build. Include:
   - Source code files
   - Configuration files
   - Test files
   - Documentation files
   List all files from the artifacts.

4. **verification_results** (object): Summary of all verification steps run and their outcomes:
   - Key: verification step name (e.g., "install_dependencies", "run_tests", "build")
   - Value: result description (e.g., "✓ Installed 45 packages successfully", "✓ 12/12 tests passing", "✗ Build failed with 3 TypeScript errors")
   Include all verification steps from artifacts.

5. **how_to_run** (array of strings): Step-by-step instructions for running the application. Be specific and include:
   - Navigation commands (e.g., "cd workspace/session_xxx/repo")
   - Dependency installation if needed (e.g., "npm install")
   - Build commands if needed (e.g., "npm run build")
   - Run command (e.g., "npm run dev" or "python app.py")
   - Where to access the app (e.g., "Open http://localhost:5173 in browser")
   - How to stop the app if needed
   List 4-7 clear steps.

6. **limitations** (array of strings): Known limitations, issues, or scope boundaries. Include:
   - Features not implemented or incomplete
   - Known bugs or issues
   - Scope constraints (e.g., "No user authentication", "Local storage only")
   - Technical limitations (e.g., "No error handling for network failures")
   - Future enhancements that were out of scope
   List 3-6 limitations.

## Important Guidelines
- Be honest about build status - don't claim success if verifications failed
- Provide complete, accurate run instructions - they should work exactly as written
- List all generated files from the artifacts
- Clearly communicate any limitations or incomplete features
- Make the summary useful for someone unfamiliar with the project

## Output Format
Return ONLY a valid JSON object (no markdown code blocks, no explanatory text). The JSON must match this exact structure:

{
  "status": "success",
  "summary": "Built a simple task manager web application using React and TypeScript. The app allows users to create, edit, and delete tasks with local storage persistence. All core features are implemented and tested.",
  "files_generated": [
    "src/App.tsx",
    "src/components/TaskList.tsx",
    "package.json",
    "tests/App.test.tsx"
  ],
  "verification_results": {
    "install_dependencies": "✓ Installed 45 packages successfully",
    "run_tests": "✓ 12/12 tests passing",
    "build": "✓ Build completed in 2.3s"
  },
  "how_to_run": [
    "Navigate to the workspace: cd workspace/session_xxx/repo",
    "Install dependencies: npm install",
    "Start development server: npm run dev",
    "Open http://localhost:5173 in your browser",
    "To stop the server, press Ctrl+C in the terminal"
  ],
  "limitations": [
    "No user authentication - tasks are not user-specific",
    "Local storage only - tasks are not persisted to a backend",
    "No task prioritization or categorization features",
    "No due dates or reminders functionality",
    "Limited to single browser/device (no sync across devices)"
  ]
}
"""
