# Open Questions

1. Should role names be freeform labels, or should the UI offer a default role list? If a default list is desired, which roles?
2. How should the system handle an attempted send that violates the configured graph (block, drop, log error, warn, other)?
3. What are the intended UI specifics for graph visualization and filtering (layout, filters, grouping)?
4. What is the exact rewind behavior (step back one tick vs reset), and how does it affect message log and status?
5. How should stubbed responses be generated and labeled to stay deterministic (fixed templates, per-agent templates, other)?
6. When multiple agents can act in a tick, what is the deterministic scheduling or ordering rule?
