# AI DevKit Rules

## Project Context
This project uses ai-devkit for structured AI-assisted development. Phase documentation is located in `docs/ai/`.

## Progress Tracking (Master Checklist)
The canonical backlog and progress tracker for this project is:
- `vibeforge_master_checklist.md`

### Checklist rules (must follow)
- Before starting work, identify the **next** relevant tasks in `vibeforge_master_checklist.md` and reference their **VF IDs** in your plan and commits.
- Work in small, verifiable increments: prefer completing 1–3 VF tasks per iteration rather than large, ambiguous batches.
- When a task is truly complete:
  - change `- [ ]` to `- [x]` for that VF item
  - keep the VF title intact (do not rename IDs)
  - add brief sub-bullets under the task if useful (key decisions, files touched, commands to verify)
- If you discover missing work:
  - add a new VF task at the end of the most appropriate chapter
  - keep numbering consistent and do not reuse IDs
- If a task is partially done, do **not** mark it complete—add a short note under the task describing what remains.

## Documentation Structure
- `docs/ai/requirements/` - Problem understanding and requirements
- `docs/ai/design/` - System architecture and design decisions (include mermaid diagrams)
- `docs/ai/planning/` - Task breakdown and project planning
- `docs/ai/implementation/` - Implementation guides and notes
- `docs/ai/testing/` - Testing strategy and test cases
- `docs/ai/deployment/` - Deployment and infrastructure docs
- `docs/ai/monitoring/` - Monitoring and observability setup

## Code Style & Standards
- Follow the project's established code style and conventions
- Write clear, self-documenting code with meaningful variable names
- Add comments for complex logic or non-obvious decisions

## Development Workflow
1. **Select tasks**: Pick the next VF items from `vibeforge_master_checklist.md` that are feasible given current repo state.
2. **Review docs first**: Read relevant phase docs in `docs/ai/` before implementing.
3. **Implement**: Build the smallest slice that satisfies the VF task’s intent.
4. **Verify**: Run the verification steps relevant to the change (unit/integration/build/smoke as applicable).
5. **Update docs**: If you introduce new constraints, APIs, or architectural decisions, update `docs/ai/design/` and/or `docs/ai/implementation/`.
6. **Update checklist**: Mark the VF task complete only when verification passes and the code is integrated.

### Commit/PR hygiene
- Include VF IDs in commit messages and PR titles (e.g., `VF-020 VF-021: add sessions endpoint`).
- Ensure each commit corresponds to a coherent step that can be reviewed and tested.

## AI Interaction Guidelines
- When implementing features, first check relevant phase documentation in `docs/ai/`
- For new features, start with requirements clarification
- Update phase docs when significant changes or decisions are made
- Use the master checklist to decide “what’s next” and to record completion

## Testing & Quality
- Write tests alongside implementation
- Follow the testing strategy defined in `docs/ai/testing/`
- Use `/writing-test` to generate unit and integration tests targeting high coverage
- Ensure code passes all tests before considering tasks complete
- Record outstanding gaps in `docs/ai/testing/` if coverage is not yet practical

## Documentation
- Update phase documentation when requirements or design changes
- Keep inline code comments focused and relevant
- Document architectural decisions and their rationale
- Use mermaid diagrams for architectural or data-flow visuals (update existing diagrams if needed)
- Record test coverage results and outstanding gaps in `docs/ai/testing/`

## Work Packages (Iteration Queue)
The near-term work queue is tracked in:
- `docs/ai/planning/WORK_PACKAGES.md`

Rules:
- Before starting any implementation, select the next **Queued** Work Package (WP).
- Each WP must reference its VF tasks from `vibeforge_master_checklist.md` (canonical backlog).
- Keep WPs small (typically 1–5 VF tasks). Prefer finishing a WP fully (code + tests + verification) before starting another.
- When a WP is complete:
  - mark WP status as **Done** and record how it was verified (commands run)
  - update `vibeforge_master_checklist.md` by setting the WP’s VF items from `[ ]` to `[x]`
  - add short sub-bullets under completed VF tasks (key files changed + verification commands)


## Key Commands
When working on this project, you can run commands to:
- Understand project requirements and goals (`review-requirements`)
- Review architectural decisions (`review-design`)
- Plan and execute tasks (`execute-plan`)
- Verify implementation against design (`check-implementation`)
- Suggest missing tests (`suggest-tests`)
- Perform structured code reviews (`code-review`)
