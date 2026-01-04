# Architecture docs

- Start with `docs/architecture/diagrams.md` (Mermaid diagrams) to visualize questionnaire→plan→execution flow.
- Keep schemas in `/schemas` (e.g., BuildSpec, TaskGraph) and version them when prompt/plan formats change.
- Keep stack presets and policies in `/configs`; future command-runner rules should live here.
- Cross-link AI phase docs in `docs/ai/` for requirements, design, implementation, testing, deployment, and monitoring updates tied to VF tasks.
