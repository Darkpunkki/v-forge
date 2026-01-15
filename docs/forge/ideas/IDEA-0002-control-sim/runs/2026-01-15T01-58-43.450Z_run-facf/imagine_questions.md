# Imagine Questions for IDEA-0002-control-sim

1. Who is the primary audience and intended use for the /control simulation (internal demo, onboarding, customer-facing)?
2. How should the "first agent" be selected at simulation start (user pick, fixed role like orchestrator, or first in list)?
3. Should communication links be directed, bidirectional by default, or configurable per link, and how should invalid sends be handled?
4. What is the minimum role set for v1, and should users be able to define custom role names?
5. What exactly constitutes a tick (single message event, one round per active agent, or a fixed small sequence)?
6. How should agent responses be generated in v1 (deterministic stub, scripted templates, or real LLM calls)? If stubbed, any preferred pattern?
7. What controls are required beyond Start and Tick (pause, stop, reset, rewind), and should reset preserve the configuration?
8. What UI views are must-have in v1 (graph visualization style, per-agent filters, grouping by tick)?
9. Is in-memory-only session persistence acceptable for v1, or should sessions be stored and reloaded?
