---
doc_type: tasks
idea_id: "IDEA-0002-control-sim"
run_id: "2026-01-15T15-29-42.321Z_run-8474"
generated_by: "Task Builder"
generated_at: "2026-01-15T15:29:42Z"
source_inputs:
  - "docs/forge/ideas/IDEA-0002-control-sim/latest/concept_summary.md"
  - "docs/forge/ideas/IDEA-0002-control-sim/latest/features_backlog.md"
  - "docs/forge/ideas/IDEA-0002-control-sim/latest/epics_backlog.md"
  - "docs/forge/ideas/IDEA-0002-control-sim/latest/idea_normalized.md"
  - "docs/forge/ideas/IDEA-0002-control-sim/inputs/idea.md"
  - "docs/forge/ideas/IDEA-0002-control-sim/latest/existing_solution_map.md"
configs: []
release_targets_supported: ["MVP", "V1", "Full", "Later"]
status: "Draft"
---
tasks:
  # ============================================================================
  # EPIC-001: Simulation Session Configuration
  # ============================================================================

  # FEAT-001: Agent roster configuration
  - id: "TASK-001"
    feature_id: "FEAT-001"
    epic_id: "EPIC-001"
    title: "Verify existing agent roster endpoint returns full roster with labels"
    description: "Verify that the existing POST /control/sessions/{id}/agents/init and POST /control/sessions/{id}/agents/assign endpoints store and return the complete agent roster including ids, names, role labels, and model labels. Add integration tests confirming roster retrieval matches input."
    acceptance_criteria:
      - "GET /control/sessions/{id}/simulation/state returns agents array with id, name, role, and model for each agent."
      - "Integration test confirms full roster is retrievable after init and assign calls."
      - "Empty roster returns empty array, not null or error."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["api", "qa", "config"]

  - id: "TASK-002"
    feature_id: "FEAT-001"
    epic_id: "EPIC-001"
    title: "Add validation for duplicate and empty agent IDs"
    description: "Extend the agent initialization endpoint to reject configurations with duplicate agent IDs or empty agent IDs. Return HTTP 400 with clear error messages indicating which IDs are problematic."
    acceptance_criteria:
      - "Given duplicate agent IDs in request, the system returns HTTP 400 with message listing duplicates."
      - "Given empty string or whitespace-only agent ID, the system returns HTTP 400 with message."
      - "Valid unique IDs are accepted and stored."
      - "Unit tests cover duplicate and empty ID rejection."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["api", "validation", "config"]

  - id: "TASK-003"
    feature_id: "FEAT-001"
    epic_id: "EPIC-001"
    title: "Expose default role list constant for assignment UI"
    description: "Define a constant list of default roles (orchestrator, worker, reviewer, fixer, foreman) and expose it via a GET endpoint or include it in the simulation state response so the UI can populate role dropdowns."
    acceptance_criteria:
      - "Default roles are defined in orchestration/models.py (verify AgentRole enum exists)."
      - "GET /control/sessions/{id}/simulation/state or a new endpoint returns available_roles list."
      - "UI can retrieve role list without hardcoding."
    dependencies: []
    release_target: "MVP"
    priority: "P1"
    estimate: "S"
    tags: ["api", "config"]

  # FEAT-002: Communication graph configuration
  - id: "TASK-004"
    feature_id: "FEAT-002"
    epic_id: "EPIC-001"
    title: "Update graph validation to allow cycles and bidirectional links"
    description: "Modify AgentFlowGraph.validate_dag() in orchestration/models.py to remove DAG enforcement. The validation should only check that edge endpoints exist in the agent roster, allowing cycles and bidirectional links."
    acceptance_criteria:
      - "Given bidirectional links (A→B and B→A), validation passes if both agents exist."
      - "Given cyclic links (A→B→C→A), validation passes if all agents exist."
      - "Given edge with unknown agent, validation fails with clear error message."
      - "Unit tests cover cycle and bidirectional acceptance scenarios."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["orchestration", "validation", "config"]

  - id: "TASK-005"
    feature_id: "FEAT-002"
    epic_id: "EPIC-001"
    title: "Store and retrieve link directionality"
    description: "Ensure the POST /control/sessions/{id}/flows endpoint stores directionality (directed vs bidirectional) per link and that GET /control/sessions/{id}/simulation/state returns the communication graph with directionality metadata."
    acceptance_criteria:
      - "AgentFlowEdge model supports bidirectional flag or direction enum."
      - "Flow configuration endpoint accepts directionality per link."
      - "State response includes agent_graph with links showing directionality."
      - "Integration test confirms round-trip storage of bidirectional links."
    dependencies:
      - "TASK-004"
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["api", "config"]

  - id: "TASK-006"
    feature_id: "FEAT-002"
    epic_id: "EPIC-001"
    title: "Return clear error messages for invalid link endpoints"
    description: "Enhance flow configuration endpoint to return HTTP 400 with specific error messages when links reference agent IDs not in the roster. Error should list all invalid references, not just the first."
    acceptance_criteria:
      - "Given link with source agent not in roster, error message names the invalid source."
      - "Given link with target agent not in roster, error message names the invalid target."
      - "Multiple invalid links return all errors in single response."
      - "Unit tests cover multi-error scenarios."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["api", "validation", "config"]

  # FEAT-003: Initial prompt and first agent selection
  - id: "TASK-007"
    feature_id: "FEAT-003"
    epic_id: "EPIC-001"
    title: "Add initial_prompt and first_agent_id fields to Session model"
    description: "Extend the Session model in apps/api/vibeforge_api/core/session.py to include initial_prompt (str) and first_agent_id (str) fields. These fields store the simulation start context."
    acceptance_criteria:
      - "Session dataclass includes initial_prompt: Optional[str] and first_agent_id: Optional[str]."
      - "Fields serialize correctly to JSON in state responses."
      - "Fields persist across session lifecycle until reset."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["model", "api"]

  - id: "TASK-008"
    feature_id: "FEAT-003"
    epic_id: "EPIC-001"
    title: "Extend simulation start endpoint to require initial prompt and first agent"
    description: "Modify POST /control/sessions/{id}/simulation/start to accept initial_prompt and first_agent_id in the request body. Validate that both are provided and first_agent_id exists in the roster before allowing start."
    acceptance_criteria:
      - "Start request schema includes initial_prompt (required string) and first_agent_id (required string)."
      - "Given missing initial_prompt, start returns HTTP 400 with clear error."
      - "Given missing first_agent_id, start returns HTTP 400 with clear error."
      - "Given first_agent_id not in roster, start returns HTTP 400 naming the invalid agent."
      - "Valid start stores prompt and first agent in session."
    dependencies:
      - "TASK-007"
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["api", "validation"]

  - id: "TASK-009"
    feature_id: "FEAT-003"
    epic_id: "EPIC-001"
    title: "Add start context fields to simulation state response"
    description: "Extend the simulation state response to include initial_prompt and first_agent_id so the UI can display current start context."
    acceptance_criteria:
      - "GET /control/sessions/{id}/simulation/state returns initial_prompt and first_agent_id when set."
      - "Fields return null when simulation has not been started."
      - "Client TypeScript types updated in controlClient.ts."
    dependencies:
      - "TASK-007"
    release_target: "MVP"
    priority: "P1"
    estimate: "S"
    tags: ["api", "ui"]

  - id: "TASK-010"
    feature_id: "FEAT-003"
    epic_id: "EPIC-001"
    title: "Add initial prompt and first agent UI inputs to SimulationConfig widget"
    description: "Extend SimulationConfig.tsx to include text input for initial prompt and dropdown for first agent selection (populated from agent roster). These become required fields before start button is enabled."
    acceptance_criteria:
      - "Initial prompt text input is visible in simulation config section."
      - "First agent dropdown shows all agents from current roster."
      - "Start button is disabled until both fields are populated."
      - "Values are sent to start endpoint when user clicks start."
    dependencies:
      - "TASK-008"
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["ui", "config"]

  # ============================================================================
  # EPIC-002: Graph-Gated Tick Progression
  # ============================================================================

  # FEAT-004: Tick advancement with per-agent activity cap
  - id: "TASK-011"
    feature_id: "FEAT-004"
    epic_id: "EPIC-002"
    title: "Wire TickEngine to control API tick endpoints"
    description: "Modify the tick advancement endpoints in control.py to instantiate and use TickEngine instead of just incrementing a counter. Pass the session's agent graph and event log to the engine. Store engine state in session."
    acceptance_criteria:
      - "POST /control/sessions/{id}/simulation/tick uses TickEngine.advance_tick()."
      - "POST /control/sessions/{id}/simulation/ticks uses TickEngine for N iterations."
      - "TickEngine receives correct agent graph configuration from session."
      - "Events emitted by TickEngine are logged to session's EventLog."
    dependencies:
      - "TASK-004"
    release_target: "MVP"
    priority: "P0"
    estimate: "L"
    tags: ["api", "orchestration"]

  - id: "TASK-012"
    feature_id: "FEAT-004"
    epic_id: "EPIC-002"
    title: "Implement FIFO single-event-per-tick processing"
    description: "Modify TickEngine.advance_tick() to process exactly one queued event per tick instead of all pending events. Use collections.deque or list.pop(0) to maintain FIFO order. Return early after processing one event."
    acceptance_criteria:
      - "Given 3 queued events, advance_tick() processes only the first event."
      - "Remaining 2 events stay queued for subsequent ticks."
      - "Event processing order matches queue insertion order (FIFO)."
      - "Unit tests verify single-event-per-tick behavior."
    dependencies:
      - "TASK-011"
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["orchestration"]

  - id: "TASK-013"
    feature_id: "FEAT-004"
    epic_id: "EPIC-002"
    title: "Implement per-agent activity cap tracking"
    description: "Add per-tick tracking of agent activity in TickEngine. Each agent can perform at most one activity per tick. If an agent has already acted this tick, skip subsequent events from that agent until next tick."
    acceptance_criteria:
      - "Given agent A has already sent a message this tick, subsequent A events are deferred."
      - "Activity cap resets at start of each new tick."
      - "Deferred events remain in queue for next tick."
      - "Unit tests verify activity cap enforcement."
    dependencies:
      - "TASK-012"
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["orchestration"]

  - id: "TASK-014"
    feature_id: "FEAT-004"
    epic_id: "EPIC-002"
    title: "Return tick summary from tick endpoints"
    description: "Modify tick endpoint responses to include a summary of activities and messages processed in that tick. Include processed_event_count, messages_sent, messages_blocked, and new_tick_index."
    acceptance_criteria:
      - "Tick response includes new_tick_index integer."
      - "Tick response includes processed_events array with event details."
      - "Tick response includes messages_sent count and messages_blocked count."
      - "Multi-tick endpoint returns array of per-tick summaries."
    dependencies:
      - "TASK-011"
    release_target: "MVP"
    priority: "P1"
    estimate: "S"
    tags: ["api"]

  - id: "TASK-015"
    feature_id: "FEAT-004"
    epic_id: "EPIC-002"
    title: "Add tick engine unit tests for FIFO and activity cap"
    description: "Create comprehensive unit tests in test_tick_engine.py covering FIFO event ordering, single-event-per-tick processing, and per-agent activity cap enforcement."
    acceptance_criteria:
      - "Test: multiple queued events process in insertion order."
      - "Test: only one event processed per advance_tick() call."
      - "Test: agent with prior activity this tick has events deferred."
      - "Test: activity cap resets on new tick."
      - "Tests pass with pytest."
    dependencies:
      - "TASK-012"
      - "TASK-013"
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["qa"]

  # FEAT-005: Graph-gated message validation
  - id: "TASK-016"
    feature_id: "FEAT-005"
    epic_id: "EPIC-002"
    title: "Verify existing validate_message() covers graph constraints"
    description: "Review and test TickEngine.validate_message() to confirm it validates that edges exist in the configured graph. Add tests for directed-only edges (A→B allows send, B→A blocked)."
    acceptance_criteria:
      - "validate_message() returns valid=True for existing directed edge."
      - "validate_message() returns valid=False with reason for missing edge."
      - "Bidirectional edges allow sends in both directions."
      - "Unit tests cover directed and bidirectional scenarios."
    dependencies:
      - "TASK-004"
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["orchestration", "qa"]

  - id: "TASK-017"
    feature_id: "FEAT-005"
    epic_id: "EPIC-002"
    title: "Emit blocked message events with clear format"
    description: "Ensure TickEngine emits MESSAGE_BLOCKED_BY_GRAPH events with metadata including from_agent, to_agent, reason, and tick_index. Format reason as 'A → B not allowed' for clarity."
    acceptance_criteria:
      - "Blocked event metadata includes from_agent, to_agent, tick_index, reason."
      - "Reason format is '{from_agent} → {to_agent} not allowed'."
      - "Blocked events are logged to EventLog."
      - "Unit test verifies blocked event format."
    dependencies:
      - "TASK-011"
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["orchestration", "observability"]

  - id: "TASK-018"
    feature_id: "FEAT-005"
    epic_id: "EPIC-002"
    title: "Ensure blocked messages do not appear as delivered"
    description: "Verify that blocked messages are not added to the delivered message list. Blocked sends create system events but not regular message entries."
    acceptance_criteria:
      - "Blocked message does not appear in session message history."
      - "Blocked message event is recorded separately from delivered messages."
      - "get_events() can filter to show only blocked events."
      - "Integration test confirms separation."
    dependencies:
      - "TASK-017"
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["orchestration", "qa"]

  # FEAT-006: Deterministic stubbed responses
  - id: "TASK-019"
    feature_id: "FEAT-006"
    epic_id: "EPIC-002"
    title: "Implement deterministic stub response generator"
    description: "Add generate_stub_response() method to TickEngine that produces deterministic, labeled responses. Use agent id, message content hash, and tick index as inputs to ensure identical inputs produce identical outputs."
    acceptance_criteria:
      - "Stub responses are prefixed with '[STUB]' or include is_stub metadata flag."
      - "Given same agent, message, and tick, output is identical across calls."
      - "Stub content includes sender and tick context in template."
      - "No LLM API calls are made."
    dependencies:
      - "TASK-011"
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["orchestration"]

  - id: "TASK-020"
    feature_id: "FEAT-006"
    epic_id: "EPIC-002"
    title: "Integrate stub response generation into tick processing"
    description: "When a message is delivered and requires a response, use generate_stub_response() to create the response content. Queue the response as a new event for subsequent tick processing."
    acceptance_criteria:
      - "Delivered messages that expect responses trigger stub response generation."
      - "Generated response is queued as new event with correct from/to agents."
      - "Response events have is_stub=true in metadata."
      - "Unit test verifies stub response flow."
    dependencies:
      - "TASK-019"
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["orchestration"]

  - id: "TASK-021"
    feature_id: "FEAT-006"
    epic_id: "EPIC-002"
    title: "Add stub response tests for determinism"
    description: "Create unit tests verifying that stub responses are deterministic given identical inputs and clearly labeled in output."
    acceptance_criteria:
      - "Test: same inputs produce identical stub content."
      - "Test: stub label is present in content or metadata."
      - "Test: different inputs produce different stub content."
      - "Tests pass with pytest."
    dependencies:
      - "TASK-019"
      - "TASK-020"
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["qa"]

  # FEAT-007: Message event emission with tick metadata
  - id: "TASK-022"
    feature_id: "FEAT-007"
    epic_id: "EPIC-002"
    title: "Verify message events include required metadata"
    description: "Review MESSAGE_SENT and MESSAGE_BLOCKED_BY_GRAPH event emission in TickEngine to confirm metadata includes sender (from_agent), receiver (to_agent), and tick_index. Add missing fields if needed."
    acceptance_criteria:
      - "MESSAGE_SENT events include from_agent, to_agent, tick_index, content."
      - "MESSAGE_BLOCKED_BY_GRAPH events include from_agent, to_agent, tick_index, reason."
      - "Metadata keys are consistent across event types."
      - "Integration test verifies metadata presence."
    dependencies:
      - "TASK-011"
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["orchestration", "observability"]

  - id: "TASK-023"
    feature_id: "FEAT-007"
    epic_id: "EPIC-002"
    title: "Verify tick events include old and new tick indices"
    description: "Review TICK_ADVANCED event emission to confirm metadata includes old_tick_index and new_tick_index. Update emission if fields are missing."
    acceptance_criteria:
      - "TICK_ADVANCED events include old_tick_index and new_tick_index."
      - "old_tick_index equals tick before advancement, new_tick_index equals tick after."
      - "Unit test verifies tick event metadata."
    dependencies:
      - "TASK-011"
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["orchestration", "observability"]

  - id: "TASK-024"
    feature_id: "FEAT-007"
    epic_id: "EPIC-002"
    title: "Ensure event consistency across single and multi-tick advances"
    description: "Verify that event payloads are consistent whether advancing 1 tick or N ticks. Multi-tick should emit N separate TICK_ADVANCED events, not a single combined event."
    acceptance_criteria:
      - "POST /simulation/ticks?count=5 emits 5 TICK_ADVANCED events."
      - "Each TICK_ADVANCED has correct old/new indices for that tick."
      - "Message events during multi-tick have correct tick_index."
      - "Integration test verifies multi-tick event emission."
    dependencies:
      - "TASK-011"
    release_target: "MVP"
    priority: "P1"
    estimate: "S"
    tags: ["api", "qa"]

  # ============================================================================
  # EPIC-003: Simulation Lifecycle Controls
  # ============================================================================

  # FEAT-008: Lifecycle state transitions and guardrails
  - id: "TASK-025"
    feature_id: "FEAT-008"
    epic_id: "EPIC-003"
    title: "Validate start prerequisites include initial prompt and first agent"
    description: "Update the simulation start endpoint to check for initial_prompt and first_agent_id in addition to existing workflow checks (agents, flows, task). Return clear error listing all missing prerequisites."
    acceptance_criteria:
      - "Start fails with HTTP 400 if initial_prompt is missing, message includes 'initial_prompt'."
      - "Start fails with HTTP 400 if first_agent_id is missing, message includes 'first_agent_id'."
      - "Start fails if first_agent_id not in roster, message names the invalid agent."
      - "Existing workflow checks (agents, flows) still enforced."
    dependencies:
      - "TASK-008"
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["api", "validation"]

  - id: "TASK-026"
    feature_id: "FEAT-008"
    epic_id: "EPIC-003"
    title: "Enforce pause only when simulation is running"
    description: "Modify POST /control/sessions/{id}/simulation/pause to return HTTP 400 with clear message when simulation is not in running state. State must be 'running' to allow pause."
    acceptance_criteria:
      - "Given simulation status='running', pause succeeds and sets status='paused'."
      - "Given simulation status='paused', pause returns HTTP 400 'already paused'."
      - "Given simulation status='idle', pause returns HTTP 400 'not running'."
      - "Given simulation status='completed', pause returns HTTP 400 'already completed'."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["api", "validation"]

  - id: "TASK-027"
    feature_id: "FEAT-008"
    epic_id: "EPIC-003"
    title: "Implement reset with configuration preservation"
    description: "Modify POST /control/sessions/{id}/simulation/reset to clear message log and state, reset tick_index to 0, but preserve agent roster, communication graph, and simulation mode settings when preserve_config=true."
    acceptance_criteria:
      - "Reset with preserve_config=true keeps agents, links, mode, delay, budget."
      - "Reset clears message log (no events visible for session post-reset)."
      - "Reset sets tick_index=0."
      - "Reset sets tick_status to idle or configured (not running)."
      - "Reset clears initial_prompt and first_agent_id (must re-provide on next start)."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["api"]

  - id: "TASK-028"
    feature_id: "FEAT-008"
    epic_id: "EPIC-003"
    title: "Implement stop transition and tick rejection"
    description: "Ensure a stop/complete transition sets simulation to non-running state. Subsequent tick requests return HTTP 400 indicating simulation must be restarted."
    acceptance_criteria:
      - "After stop/complete, tick returns HTTP 400 'simulation not running'."
      - "After stop/complete, start can be called again with new prompt/first_agent."
      - "Stop preserves configuration by default."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["api"]

  - id: "TASK-029"
    feature_id: "FEAT-008"
    epic_id: "EPIC-003"
    title: "Add lifecycle guardrail integration tests"
    description: "Create integration tests in test_simulation_api.py covering all lifecycle state transitions and guardrails: start prerequisites, pause restrictions, reset behavior, stop/tick rejection."
    acceptance_criteria:
      - "Test: start without prompt fails."
      - "Test: pause when not running fails."
      - "Test: reset preserves config, clears log."
      - "Test: tick after stop fails."
      - "Tests pass with pytest."
    dependencies:
      - "TASK-025"
      - "TASK-026"
      - "TASK-027"
      - "TASK-028"
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["qa"]

  # FEAT-009: Status and tick state exposure
  - id: "TASK-030"
    feature_id: "FEAT-009"
    epic_id: "EPIC-003"
    title: "Verify simulation state endpoint returns complete status"
    description: "Review GET /control/sessions/{id}/simulation/state to confirm it returns tick_index, tick_status, simulation_mode, auto_delay_ms, and tick_budget. Add any missing fields."
    acceptance_criteria:
      - "Response includes tick_index (integer)."
      - "Response includes tick_status (idle, running, paused, completed)."
      - "Response includes simulation_mode (manual, auto) when configured."
      - "Response includes auto_delay_ms and tick_budget when set."
      - "Unconfigured simulation returns idle/unconfigured status clearly."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["api"]

  - id: "TASK-031"
    feature_id: "FEAT-009"
    epic_id: "EPIC-003"
    title: "Update TypeScript client types for simulation state"
    description: "Update controlClient.ts SimulationStateResponse type to include all status fields: tick_index, tick_status, simulation_mode, auto_delay_ms, tick_budget, initial_prompt, first_agent_id."
    acceptance_criteria:
      - "SimulationStateResponse type matches API response schema."
      - "No TypeScript errors when using state response in UI components."
    dependencies:
      - "TASK-030"
    release_target: "MVP"
    priority: "P1"
    estimate: "S"
    tags: ["ui"]

  # ============================================================================
  # EPIC-004: Event Logging and Streaming
  # ============================================================================

  # FEAT-010: Persisted simulation event log
  - id: "TASK-032"
    feature_id: "FEAT-010"
    epic_id: "EPIC-004"
    title: "Verify tick events are persisted with timestamps"
    description: "Confirm that TICK_ADVANCED events emitted by TickEngine are written to the session's EventLog with timestamps. Review EventLog.append() call path from tick processing."
    acceptance_criteria:
      - "Each advance_tick() call results in TICK_ADVANCED event in JSONL log."
      - "Event includes ISO timestamp, session_id, tick metadata."
      - "Events persist across session state retrieval."
    dependencies:
      - "TASK-011"
    release_target: "MVP"
    priority: "P1"
    estimate: "S"
    tags: ["observability", "qa"]

  - id: "TASK-033"
    feature_id: "FEAT-010"
    epic_id: "EPIC-004"
    title: "Verify message events are persisted with sender/receiver"
    description: "Confirm that MESSAGE_SENT and MESSAGE_BLOCKED_BY_GRAPH events are persisted with from_agent, to_agent, and tick_index metadata. Review event emission in TickEngine."
    acceptance_criteria:
      - "MESSAGE_SENT events in log include from_agent, to_agent, content, tick_index."
      - "MESSAGE_BLOCKED_BY_GRAPH events include from_agent, to_agent, reason, tick_index."
      - "Events retrievable via get_events() or get_events_filtered()."
    dependencies:
      - "TASK-017"
    release_target: "MVP"
    priority: "P1"
    estimate: "S"
    tags: ["observability", "qa"]

  - id: "TASK-034"
    feature_id: "FEAT-010"
    epic_id: "EPIC-004"
    title: "Ensure event logging failures do not block simulation"
    description: "Wrap EventLog.append() calls in try/except to ensure logging failures are logged as warnings but do not raise exceptions that block tick processing."
    acceptance_criteria:
      - "If EventLog.append() raises IOError, warning is logged but tick completes."
      - "Simulation state is updated even if event write fails."
      - "Unit test simulates write failure and confirms tick proceeds."
    dependencies: []
    release_target: "MVP"
    priority: "P1"
    estimate: "S"
    tags: ["observability"]

  # FEAT-011: Event streaming for control panel
  - id: "TASK-035"
    feature_id: "FEAT-011"
    epic_id: "EPIC-004"
    title: "Verify SSE event stream endpoint returns simulation events"
    description: "Review GET /control/sessions/{id}/events SSE endpoint to confirm it streams TICK_ADVANCED, MESSAGE_SENT, and MESSAGE_BLOCKED_BY_GRAPH events with correct metadata."
    acceptance_criteria:
      - "SSE stream emits new events as they are logged."
      - "Event data includes event_type, timestamp, and metadata fields."
      - "Empty session does not error; stream waits for events."
    dependencies: []
    release_target: "MVP"
    priority: "P1"
    estimate: "S"
    tags: ["api", "qa"]

  - id: "TASK-036"
    feature_id: "FEAT-011"
    epic_id: "EPIC-004"
    title: "Ensure stream reconnection maintains event ordering"
    description: "If UI reconnects to SSE stream, events should continue from last known position or replay from start consistently. Add last_event_id support or document expected behavior."
    acceptance_criteria:
      - "Stream reconnection does not produce duplicate events or skip events."
      - "Behavior is documented for UI consumption."
      - "Integration test simulates reconnection scenario."
    dependencies:
      - "TASK-035"
    release_target: "MVP"
    priority: "P1"
    estimate: "M"
    tags: ["api"]

  # ============================================================================
  # EPIC-005: Control Panel Monitoring Views
  # ============================================================================

  # FEAT-012: Agent graph visualization
  - id: "TASK-037"
    feature_id: "FEAT-012"
    epic_id: "EPIC-005"
    title: "Update AgentGraph widget to render simulation communication links"
    description: "Modify AgentGraph.tsx to render the configured communication graph (simulation links) instead of task-based edges. Use agent_graph from simulation state to render nodes and edges with directionality indicators."
    acceptance_criteria:
      - "Graph shows all agents from roster as nodes with labels."
      - "Graph shows communication links with arrows indicating direction."
      - "Bidirectional links show arrows in both directions."
      - "Graph updates when configuration changes."
    dependencies: []
    release_target: "MVP"
    priority: "P1"
    estimate: "M"
    tags: ["ui"]

  - id: "TASK-038"
    feature_id: "FEAT-012"
    epic_id: "EPIC-005"
    title: "Show empty state when no agents configured"
    description: "Update AgentGraph.tsx to display a helpful empty state message when the agent roster is empty, rather than a blank canvas."
    acceptance_criteria:
      - "When agents array is empty, graph shows 'No agents configured' message."
      - "Empty state includes hint to configure agents."
      - "Graph transitions to node view when agents are added."
    dependencies:
      - "TASK-037"
    release_target: "MVP"
    priority: "P1"
    estimate: "S"
    tags: ["ui"]

  - id: "TASK-039"
    feature_id: "FEAT-012"
    epic_id: "EPIC-005"
    title: "Ensure graph remains visible during simulation and after reset"
    description: "Verify that the agent graph widget stays rendered during simulation ticks and after reset. Graph should reflect preserved configuration after reset."
    acceptance_criteria:
      - "Graph is visible while simulation is running."
      - "Graph is visible after reset (shows preserved config)."
      - "No flickering or unmounting during tick advancement."
    dependencies:
      - "TASK-037"
    release_target: "MVP"
    priority: "P1"
    estimate: "S"
    tags: ["ui", "qa"]

  # FEAT-013: Message log view with filters
  - id: "TASK-040"
    feature_id: "FEAT-013"
    epic_id: "EPIC-005"
    title: "Verify MultiAgentMessages displays required fields"
    description: "Review MultiAgentMessages.tsx to confirm it displays sender, receiver, tick index, timestamp, and content for each message. Add any missing fields."
    acceptance_criteria:
      - "Each message row shows fromAgent, toAgent, tick, timestamp, content."
      - "Timestamps are formatted as locale time string."
      - "Content is displayed with proper word wrap."
    dependencies: []
    release_target: "MVP"
    priority: "P1"
    estimate: "S"
    tags: ["ui", "qa"]

  - id: "TASK-041"
    feature_id: "FEAT-013"
    epic_id: "EPIC-005"
    title: "Format blocked messages with system entry style"
    description: "Update MultiAgentMessages.tsx to display blocked messages with the format 'Blocked: A → B not allowed' and visual indicators (red background, blocked badge)."
    acceptance_criteria:
      - "Blocked messages show 'Blocked' badge."
      - "Block reason is displayed below content."
      - "Visual styling differentiates blocked from delivered."
      - "Blocked messages use format 'Blocked: {from} → {to} not allowed' when reason matches."
    dependencies: []
    release_target: "MVP"
    priority: "P1"
    estimate: "S"
    tags: ["ui"]

  - id: "TASK-042"
    feature_id: "FEAT-013"
    epic_id: "EPIC-005"
    title: "Verify agent filter functionality"
    description: "Confirm the agent filter dropdown in MultiAgentMessages.tsx filters messages to show only those where the selected agent is sender or receiver."
    acceptance_criteria:
      - "Filter dropdown includes 'All agents' and each unique agent."
      - "Selecting agent X shows only messages where X is from or to agent."
      - "Message count updates to reflect filtered count."
    dependencies: []
    release_target: "MVP"
    priority: "P1"
    estimate: "S"
    tags: ["ui", "qa"]

  - id: "TASK-043"
    feature_id: "FEAT-013"
    epic_id: "EPIC-005"
    title: "Show empty state when no messages exist"
    description: "Verify MultiAgentMessages.tsx shows a helpful empty state when no messages have been exchanged yet."
    acceptance_criteria:
      - "Empty state shows message icon and 'No agent messages yet' text."
      - "Hint text explains messages will appear during simulation."
      - "Transitions to message list when events arrive."
    dependencies: []
    release_target: "MVP"
    priority: "P1"
    estimate: "S"
    tags: ["ui", "qa"]

  # FEAT-014: Status and tick indicators
  - id: "TASK-044"
    feature_id: "FEAT-014"
    epic_id: "EPIC-005"
    title: "Verify TickControls displays correct status indicator"
    description: "Review TickControls.tsx to confirm status indicator reflects running, paused, idle, and completed states with appropriate colors and labels."
    acceptance_criteria:
      - "Running state: green pulsing indicator, 'Running' label."
      - "Paused state: orange indicator, 'Paused' label."
      - "Idle state: gray indicator, 'Idle' label."
      - "Completed state: blue indicator, 'Complete' label."
    dependencies: []
    release_target: "MVP"
    priority: "P1"
    estimate: "S"
    tags: ["ui", "qa"]

  - id: "TASK-045"
    feature_id: "FEAT-014"
    epic_id: "EPIC-005"
    title: "Verify tick index updates on tick advancement"
    description: "Confirm TickControls.tsx tick index display updates when tick endpoints are called. UI should refresh state after each tick action."
    acceptance_criteria:
      - "Tick index shows current value from simulation state."
      - "After 'Run 1 Tick' button, tick index increments visually."
      - "After 'Run N Ticks', tick index reflects final value."
    dependencies: []
    release_target: "MVP"
    priority: "P1"
    estimate: "S"
    tags: ["ui", "qa"]

  - id: "TASK-046"
    feature_id: "FEAT-014"
    epic_id: "EPIC-005"
    title: "Display errors and connection issues to user"
    description: "Ensure TickControls.tsx displays error messages when API calls fail. Show connection errors clearly so user knows when simulation state may be stale."
    acceptance_criteria:
      - "API error response shows in red error box with message."
      - "Network failure shows connection error message."
      - "Error clears when next action succeeds."
    dependencies: []
    release_target: "MVP"
    priority: "P1"
    estimate: "S"
    tags: ["ui"]

  - id: "TASK-047"
    feature_id: "FEAT-014"
    epic_id: "EPIC-005"
    title: "Ensure status persists when switching sessions"
    description: "Verify that status indicators load correctly when user switches between sessions. Each session should display its own status without stale data from previous session."
    acceptance_criteria:
      - "Switching to different session loads that session's tick/status."
      - "No stale status shown briefly before load completes."
      - "Loading state shown while fetching new session state."
    dependencies: []
    release_target: "MVP"
    priority: "P1"
    estimate: "S"
    tags: ["ui", "qa"]

# Tasks

## EPIC-001: Simulation Session Configuration

### FEAT-001: Agent roster configuration

#### TASK-001: Verify existing agent roster endpoint returns full roster with labels

**Release Target:** MVP **Priority:** P0 **Estimate:** S  
**Description:** Verify that the existing POST /control/sessions/{id}/agents/init and POST /control/sessions/{id}/agents/assign endpoints store and return the complete agent roster including ids, names, role labels, and model labels. Add integration tests confirming roster retrieval matches input.

**Acceptance Criteria:**

- GET /control/sessions/{id}/simulation/state returns agents array with id, name, role, and model for each agent.
- Integration test confirms full roster is retrievable after init and assign calls.
- Empty roster returns empty array, not null or error.

**Dependencies:**

- None

#### TASK-002: Add validation for duplicate and empty agent IDs

**Release Target:** MVP **Priority:** P0 **Estimate:** S  
**Description:** Extend the agent initialization endpoint to reject configurations with duplicate agent IDs or empty agent IDs. Return HTTP 400 with clear error messages indicating which IDs are problematic.

**Acceptance Criteria:**

- Given duplicate agent IDs in request, the system returns HTTP 400 with message listing duplicates.
- Given empty string or whitespace-only agent ID, the system returns HTTP 400 with message.
- Valid unique IDs are accepted and stored.
- Unit tests cover duplicate and empty ID rejection.

**Dependencies:**

- None

#### TASK-003: Expose default role list constant for assignment UI

**Release Target:** MVP **Priority:** P1 **Estimate:** S  
**Description:** Define a constant list of default roles (orchestrator, worker, reviewer, fixer, foreman) and expose it via a GET endpoint or include it in the simulation state response so the UI can populate role dropdowns.

**Acceptance Criteria:**

- Default roles are defined in orchestration/models.py (verify AgentRole enum exists).
- GET /control/sessions/{id}/simulation/state or a new endpoint returns available_roles list.
- UI can retrieve role list without hardcoding.

**Dependencies:**

- None

### FEAT-002: Communication graph configuration

#### TASK-004: Update graph validation to allow cycles and bidirectional links

**Release Target:** MVP **Priority:** P0 **Estimate:** M  
**Description:** Modify AgentFlowGraph.validate_dag() in orchestration/models.py to remove DAG enforcement. The validation should only check that edge endpoints exist in the agent roster, allowing cycles and bidirectional links.

**Acceptance Criteria:**

- Given bidirectional links (A→B and B→A), validation passes if both agents exist.
- Given cyclic links (A→B→C→A), validation passes if all agents exist.
- Given edge with unknown agent, validation fails with clear error message.
- Unit tests cover cycle and bidirectional acceptance scenarios.

**Dependencies:**

- None

#### TASK-005: Store and retrieve link directionality

**Release Target:** MVP **Priority:** P0 **Estimate:** S  
**Description:** Ensure the POST /control/sessions/{id}/flows endpoint stores directionality (directed vs bidirectional) per link and that GET /control/sessions/{id}/simulation/state returns the communication graph with directionality metadata.

**Acceptance Criteria:**

- AgentFlowEdge model supports bidirectional flag or direction enum.
- Flow configuration endpoint accepts directionality per link.
- State response includes agent_graph with links showing directionality.
- Integration test confirms round-trip storage of bidirectional links.

**Dependencies:**

- TASK-004

#### TASK-006: Return clear error messages for invalid link endpoints

**Release Target:** MVP **Priority:** P0 **Estimate:** S  
**Description:** Enhance flow configuration endpoint to return HTTP 400 with specific error messages when links reference agent IDs not in the roster. Error should list all invalid references, not just the first.

**Acceptance Criteria:**

- Given link with source agent not in roster, error message names the invalid source.
- Given link with target agent not in roster, error message names the invalid target.
- Multiple invalid links return all errors in single response.
- Unit tests cover multi-error scenarios.

**Dependencies:**

- None

### FEAT-003: Initial prompt and first agent selection

#### TASK-007: Add initial_prompt and first_agent_id fields to Session model

**Release Target:** MVP **Priority:** P0 **Estimate:** S  
**Description:** Extend the Session model in apps/api/vibeforge_api/core/session.py to include initial_prompt (str) and first_agent_id (str) fields. These fields store the simulation start context.

**Acceptance Criteria:**

- Session dataclass includes initial_prompt: Optional[str] and first_agent_id: Optional[str].
- Fields serialize correctly to JSON in state responses.
- Fields persist across session lifecycle until reset.

**Dependencies:**

- None

#### TASK-008: Extend simulation start endpoint to require initial prompt and first agent

**Release Target:** MVP **Priority:** P0 **Estimate:** M  
**Description:** Modify POST /control/sessions/{id}/simulation/start to accept initial_prompt and first_agent_id in the request body. Validate that both are provided and first_agent_id exists in the roster before allowing start.

**Acceptance Criteria:**

- Start request schema includes initial_prompt (required string) and first_agent_id (required string).
- Given missing initial_prompt, start returns HTTP 400 with clear error.
- Given missing first_agent_id, start returns HTTP 400 with clear error.
- Given first_agent_id not in roster, start returns HTTP 400 naming the invalid agent.
- Valid start stores prompt and first agent in session.

**Dependencies:**

- TASK-007

#### TASK-009: Add start context fields to simulation state response

**Release Target:** MVP **Priority:** P1 **Estimate:** S  
**Description:** Extend the simulation state response to include initial_prompt and first_agent_id so the UI can display current start context.

**Acceptance Criteria:**

- GET /control/sessions/{id}/simulation/state returns initial_prompt and first_agent_id when set.
- Fields return null when simulation has not been started.
- Client TypeScript types updated in controlClient.ts.

**Dependencies:**

- TASK-007

#### TASK-010: Add initial prompt and first agent UI inputs to SimulationConfig widget

**Release Target:** MVP **Priority:** P0 **Estimate:** M  
**Description:** Extend SimulationConfig.tsx to include text input for initial prompt and dropdown for first agent selection (populated from agent roster). These become required fields before start button is enabled.

**Acceptance Criteria:**

- Initial prompt text input is visible in simulation config section.
- First agent dropdown shows all agents from current roster.
- Start button is disabled until both fields are populated.
- Values are sent to start endpoint when user clicks start.

**Dependencies:**

- TASK-008

## EPIC-002: Graph-Gated Tick Progression

### FEAT-004: Tick advancement with per-agent activity cap

#### TASK-011: Wire TickEngine to control API tick endpoints

**Release Target:** MVP **Priority:** P0 **Estimate:** L  
**Description:** Modify the tick advancement endpoints in control.py to instantiate and use TickEngine instead of just incrementing a counter. Pass the session's agent graph and event log to the engine. Store engine state in session.

**Acceptance Criteria:**

- POST /control/sessions/{id}/simulation/tick uses TickEngine.advance_tick().
- POST /control/sessions/{id}/simulation/ticks uses TickEngine for N iterations.
- TickEngine receives correct agent graph configuration from session.
- Events emitted by TickEngine are logged to session's EventLog.

**Dependencies:**

- TASK-004

#### TASK-012: Implement FIFO single-event-per-tick processing

**Release Target:** MVP **Priority:** P0 **Estimate:** M  
**Description:** Modify TickEngine.advance_tick() to process exactly one queued event per tick instead of all pending events. Use collections.deque or list.pop(0) to maintain FIFO order. Return early after processing one event.

**Acceptance Criteria:**

- Given 3 queued events, advance_tick() processes only the first event.
- Remaining 2 events stay queued for subsequent ticks.
- Event processing order matches queue insertion order (FIFO).
- Unit tests verify single-event-per-tick behavior.

**Dependencies:**

- TASK-011

#### TASK-013: Implement per-agent activity cap tracking

**Release Target:** MVP **Priority:** P0 **Estimate:** M  
**Description:** Add per-tick tracking of agent activity in TickEngine. Each agent can perform at most one activity per tick. If an agent has already acted this tick, skip subsequent events from that agent until next tick.

**Acceptance Criteria:**

- Given agent A has already sent a message this tick, subsequent A events are deferred.
- Activity cap resets at start of each new tick.
- Deferred events remain in queue for next tick.
- Unit tests verify activity cap enforcement.

**Dependencies:**

- TASK-012

#### TASK-014: Return tick summary from tick endpoints

**Release Target:** MVP **Priority:** P1 **Estimate:** S  
**Description:** Modify tick endpoint responses to include a summary of activities and messages processed in that tick. Include processed_event_count, messages_sent, messages_blocked, and new_tick_index.

**Acceptance Criteria:**

- Tick response includes new_tick_index integer.
- Tick response includes processed_events array with event details.
- Tick response includes messages_sent count and messages_blocked count.
- Multi-tick endpoint returns array of per-tick summaries.

**Dependencies:**

- TASK-011

#### TASK-015: Add tick engine unit tests for FIFO and activity cap

**Release Target:** MVP **Priority:** P0 **Estimate:** M  
**Description:** Create comprehensive unit tests in test_tick_engine.py covering FIFO event ordering, single-event-per-tick processing, and per-agent activity cap enforcement.

**Acceptance Criteria:**

- Test: multiple queued events process in insertion order.
- Test: only one event processed per advance_tick() call.
- Test: agent with prior activity this tick has events deferred.
- Test: activity cap resets on new tick.
- Tests pass with pytest.

**Dependencies:**

- TASK-012
- TASK-013

### FEAT-005: Graph-gated message validation

#### TASK-016: Verify existing validate_message() covers graph constraints

**Release Target:** MVP **Priority:** P0 **Estimate:** S  
**Description:** Review and test TickEngine.validate_message() to confirm it validates that edges exist in the configured graph. Add tests for directed-only edges (A→B allows send, B→A blocked).

**Acceptance Criteria:**

- validate_message() returns valid=True for existing directed edge.
- validate_message() returns valid=False with reason for missing edge.
- Bidirectional edges allow sends in both directions.
- Unit tests cover directed and bidirectional scenarios.

**Dependencies:**

- TASK-004

#### TASK-017: Emit blocked message events with clear format

**Release Target:** MVP **Priority:** P0 **Estimate:** S  
**Description:** Ensure TickEngine emits MESSAGE_BLOCKED_BY_GRAPH events with metadata including from_agent, to_agent, reason, and tick_index. Format reason as 'A → B not allowed' for clarity.

**Acceptance Criteria:**

- Blocked event metadata includes from_agent, to_agent, tick_index, reason.
- Reason format is '{from_agent} → {to_agent} not allowed'.
- Blocked events are logged to EventLog.
- Unit test verifies blocked event format.

**Dependencies:**

- TASK-011

#### TASK-018: Ensure blocked messages do not appear as delivered

**Release Target:** MVP **Priority:** P0 **Estimate:** S  
**Description:** Verify that blocked messages are not added to the delivered message list. Blocked sends create system events but not regular message entries.

**Acceptance Criteria:**

- Blocked message does not appear in session message history.
- Blocked message event is recorded separately from delivered messages.
- get_events() can filter to show only blocked events.
- Integration test confirms separation.

**Dependencies:**

- TASK-017

### FEAT-006: Deterministic stubbed responses

#### TASK-019: Implement deterministic stub response generator

**Release Target:** MVP **Priority:** P0 **Estimate:** M  
**Description:** Add generate_stub_response() method to TickEngine that produces deterministic, labeled responses. Use agent id, message content hash, and tick index as inputs to ensure identical inputs produce identical outputs.

**Acceptance Criteria:**

- Stub responses are prefixed with '[STUB]' or include is_stub metadata flag.
- Given same agent, message, and tick, output is identical across calls.
- Stub content includes sender and tick context in template.
- No LLM API calls are made.

**Dependencies:**

- TASK-011

#### TASK-020: Integrate stub response generation into tick processing

**Release Target:** MVP **Priority:** P0 **Estimate:** M  
**Description:** When a message is delivered and requires a response, use generate_stub_response() to create the response content. Queue the response as a new event for subsequent tick processing.

**Acceptance Criteria:**

- Delivered messages that expect responses trigger stub response generation.
- Generated response is queued as new event with correct from/to agents.
- Response events have is_stub=true in metadata.
- Unit test verifies stub response flow.

**Dependencies:**

- TASK-019

#### TASK-021: Add stub response tests for determinism

**Release Target:** MVP **Priority:** P0 **Estimate:** S  
**Description:** Create unit tests verifying that stub responses are deterministic given identical inputs and clearly labeled in output.

**Acceptance Criteria:**

- Test: same inputs produce identical stub content.
- Test: stub label is present in content or metadata.
- Test: different inputs produce different stub content.
- Tests pass with pytest.

**Dependencies:**

- TASK-019
- TASK-020

### FEAT-007: Message event emission with tick metadata

#### TASK-022: Verify message events include required metadata

**Release Target:** MVP **Priority:** P0 **Estimate:** S  
**Description:** Review MESSAGE_SENT and MESSAGE_BLOCKED_BY_GRAPH event emission in TickEngine to confirm metadata includes sender (from_agent), receiver (to_agent), and tick_index. Add missing fields if needed.

**Acceptance Criteria:**

- MESSAGE_SENT events include from_agent, to_agent, tick_index, content.
- MESSAGE_BLOCKED_BY_GRAPH events include from_agent, to_agent, tick_index, reason.
- Metadata keys are consistent across event types.
- Integration test verifies metadata presence.

**Dependencies:**

- TASK-011

#### TASK-023: Verify tick events include old and new tick indices

**Release Target:** MVP **Priority:** P0 **Estimate:** S  
**Description:** Review TICK_ADVANCED event emission to confirm metadata includes old_tick_index and new_tick_index. Update emission if fields are missing.

**Acceptance Criteria:**

- TICK_ADVANCED events include old_tick_index and new_tick_index.
- old_tick_index equals tick before advancement, new_tick_index equals tick after.
- Unit test verifies tick event metadata.

**Dependencies:**

- TASK-011

#### TASK-024: Ensure event consistency across single and multi-tick advances

**Release Target:** MVP **Priority:** P1 **Estimate:** S  
**Description:** Verify that event payloads are consistent whether advancing 1 tick or N ticks. Multi-tick should emit N separate TICK_ADVANCED events, not a single combined event.

**Acceptance Criteria:**

- POST /simulation/ticks?count=5 emits 5 TICK_ADVANCED events.
- Each TICK_ADVANCED has correct old/new indices for that tick.
- Message events during multi-tick have correct tick_index.
- Integration test verifies multi-tick event emission.

**Dependencies:**

- TASK-011

## EPIC-003: Simulation Lifecycle Controls

### FEAT-008: Lifecycle state transitions and guardrails

#### TASK-025: Validate start prerequisites include initial prompt and first agent

**Release Target:** MVP **Priority:** P0 **Estimate:** S  
**Description:** Update the simulation start endpoint to check for initial_prompt and first_agent_id in addition to existing workflow checks (agents, flows, task). Return clear error listing all missing prerequisites.

**Acceptance Criteria:**

- Start fails with HTTP 400 if initial_prompt is missing, message includes 'initial_prompt'.
- Start fails with HTTP 400 if first_agent_id is missing, message includes 'first_agent_id'.
- Start fails if first_agent_id not in roster, message names the invalid agent.
- Existing workflow checks (agents, flows) still enforced.

**Dependencies:**

- TASK-008

#### TASK-026: Enforce pause only when simulation is running

**Release Target:** MVP **Priority:** P0 **Estimate:** S  
**Description:** Modify POST /control/sessions/{id}/simulation/pause to return HTTP 400 with clear message when simulation is not in running state. State must be 'running' to allow pause.

**Acceptance Criteria:**

- Given simulation status='running', pause succeeds and sets status='paused'.
- Given simulation status='paused', pause returns HTTP 400 'already paused'.
- Given simulation status='idle', pause returns HTTP 400 'not running'.
- Given simulation status='completed', pause returns HTTP 400 'already completed'.

**Dependencies:**

- None

#### TASK-027: Implement reset with configuration preservation

**Release Target:** MVP **Priority:** P0 **Estimate:** M  
**Description:** Modify POST /control/sessions/{id}/simulation/reset to clear message log and state, reset tick_index to 0, but preserve agent roster, communication graph, and simulation mode settings when preserve_config=true.

**Acceptance Criteria:**

- Reset with preserve_config=true keeps agents, links, mode, delay, budget.
- Reset clears message log (no events visible for session post-reset).
- Reset sets tick_index=0.
- Reset sets tick_status to idle or configured (not running).
- Reset clears initial_prompt and first_agent_id (must re-provide on next start).

**Dependencies:**

- None

#### TASK-028: Implement stop transition and tick rejection

**Release Target:** MVP **Priority:** P0 **Estimate:** S  
**Description:** Ensure a stop/complete transition sets simulation to non-running state. Subsequent tick requests return HTTP 400 indicating simulation must be restarted.

**Acceptance Criteria:**

- After stop/complete, tick returns HTTP 400 'simulation not running'.
- After stop/complete, start can be called again with new prompt/first_agent.
- Stop preserves configuration by default.

**Dependencies:**

- None

#### TASK-029: Add lifecycle guardrail integration tests

**Release Target:** MVP **Priority:** P0 **Estimate:** M  
**Description:** Create integration tests in test_simulation_api.py covering all lifecycle state transitions and guardrails: start prerequisites, pause restrictions, reset behavior, stop/tick rejection.

**Acceptance Criteria:**

- Test: start without prompt fails.
- Test: pause when not running fails.
- Test: reset preserves config, clears log.
- Test: tick after stop fails.
- Tests pass with pytest.

**Dependencies:**

- TASK-025
- TASK-026
- TASK-027
- TASK-028

### FEAT-009: Status and tick state exposure

#### TASK-030: Verify simulation state endpoint returns complete status

**Release Target:** MVP **Priority:** P0 **Estimate:** S  
**Description:** Review GET /control/sessions/{id}/simulation/state to confirm it returns tick_index, tick_status, simulation_mode, auto_delay_ms, and tick_budget. Add any missing fields.

**Acceptance Criteria:**

- Response includes tick_index (integer).
- Response includes tick_status (idle, running, paused, completed).
- Response includes simulation_mode (manual, auto) when configured.
- Response includes auto_delay_ms and tick_budget when set.
- Unconfigured simulation returns idle/unconfigured status clearly.

**Dependencies:**

- None

#### TASK-031: Update TypeScript client types for simulation state

**Release Target:** MVP **Priority:** P1 **Estimate:** S  
**Description:** Update controlClient.ts SimulationStateResponse type to include all status fields: tick_index, tick_status, simulation_mode, auto_delay_ms, tick_budget, initial_prompt, first_agent_id.

**Acceptance Criteria:**

- SimulationStateResponse type matches API response schema.
- No TypeScript errors when using state response in UI components.

**Dependencies:**

- TASK-030

## EPIC-004: Event Logging and Streaming

### FEAT-010: Persisted simulation event log

#### TASK-032: Verify tick events are persisted with timestamps

**Release Target:** MVP **Priority:** P1 **Estimate:** S  
**Description:** Confirm that TICK_ADVANCED events emitted by TickEngine are written to the session's EventLog with timestamps. Review EventLog.append() call path from tick processing.

**Acceptance Criteria:**

- Each advance_tick() call results in TICK_ADVANCED event in JSONL log.
- Event includes ISO timestamp, session_id, tick metadata.
- Events persist across session state retrieval.

**Dependencies:**

- TASK-011

#### TASK-033: Verify message events are persisted with sender/receiver

**Release Target:** MVP **Priority:** P1 **Estimate:** S  
**Description:** Confirm that MESSAGE_SENT and MESSAGE_BLOCKED_BY_GRAPH events are persisted with from_agent, to_agent, and tick_index metadata. Review event emission in TickEngine.

**Acceptance Criteria:**

- MESSAGE_SENT events in log include from_agent, to_agent, content, tick_index.
- MESSAGE_BLOCKED_BY_GRAPH events include from_agent, to_agent, reason, tick_index.
- Events retrievable via get_events() or get_events_filtered().

**Dependencies:**

- TASK-017

#### TASK-034: Ensure event logging failures do not block simulation

**Release Target:** MVP **Priority:** P1 **Estimate:** S  
**Description:** Wrap EventLog.append() calls in try/except to ensure logging failures are logged as warnings but do not raise exceptions that block tick processing.

**Acceptance Criteria:**

- If EventLog.append() raises IOError, warning is logged but tick completes.
- Simulation state is updated even if event write fails.
- Unit test simulates write failure and confirms tick proceeds.

**Dependencies:**

- None

### FEAT-011: Event streaming for control panel

#### TASK-035: Verify SSE event stream endpoint returns simulation events

**Release Target:** MVP **Priority:** P1 **Estimate:** S  
**Description:** Review GET /control/sessions/{id}/events SSE endpoint to confirm it streams TICK_ADVANCED, MESSAGE_SENT, and MESSAGE_BLOCKED_BY_GRAPH events with correct metadata.

**Acceptance Criteria:**

- SSE stream emits new events as they are logged.
- Event data includes event_type, timestamp, and metadata fields.
- Empty session does not error; stream waits for events.

**Dependencies:**

- None

#### TASK-036: Ensure stream reconnection maintains event ordering

**Release Target:** MVP **Priority:** P1 **Estimate:** M  
**Description:** If UI reconnects to SSE stream, events should continue from last known position or replay from start consistently. Add last_event_id support or document expected behavior.

**Acceptance Criteria:**

- Stream reconnection does not produce duplicate events or skip events.
- Behavior is documented for UI consumption.
- Integration test simulates reconnection scenario.

**Dependencies:**

- TASK-035

## EPIC-005: Control Panel Monitoring Views

### FEAT-012: Agent graph visualization

#### TASK-037: Update AgentGraph widget to render simulation communication links

**Release Target:** MVP **Priority:** P1 **Estimate:** M  
**Description:** Modify AgentGraph.tsx to render the configured communication graph (simulation links) instead of task-based edges. Use agent_graph from simulation state to render nodes and edges with directionality indicators.

**Acceptance Criteria:**

- Graph shows all agents from roster as nodes with labels.
- Graph shows communication links with arrows indicating direction.
- Bidirectional links show arrows in both directions.
- Graph updates when configuration changes.

**Dependencies:**

- None

#### TASK-038: Show empty state when no agents configured

**Release Target:** MVP **Priority:** P1 **Estimate:** S  
**Description:** Update AgentGraph.tsx to display a helpful empty state message when the agent roster is empty, rather than a blank canvas.

**Acceptance Criteria:**

- When agents array is empty, graph shows 'No agents configured' message.
- Empty state includes hint to configure agents.
- Graph transitions to node view when agents are added.

**Dependencies:**

- TASK-037

#### TASK-039: Ensure graph remains visible during simulation and after reset

**Release Target:** MVP **Priority:** P1 **Estimate:** S  
**Description:** Verify that the agent graph widget stays rendered during simulation ticks and after reset. Graph should reflect preserved configuration after reset.

**Acceptance Criteria:**

- Graph is visible while simulation is running.
- Graph is visible after reset (shows preserved config).
- No flickering or unmounting during tick advancement.

**Dependencies:**

- TASK-037

### FEAT-013: Message log view with filters

#### TASK-040: Verify MultiAgentMessages displays required fields

**Release Target:** MVP **Priority:** P1 **Estimate:** S  
**Description:** Review MultiAgentMessages.tsx to confirm it displays sender, receiver, tick index, timestamp, and content for each message. Add any missing fields.

**Acceptance Criteria:**

- Each message row shows fromAgent, toAgent, tick, timestamp, content.
- Timestamps are formatted as locale time string.
- Content is displayed with proper word wrap.

**Dependencies:**

- None

#### TASK-041: Format blocked messages with system entry style

**Release Target:** MVP **Priority:** P1 **Estimate:** S  
**Description:** Update MultiAgentMessages.tsx to display blocked messages with the format 'Blocked: A → B not allowed' and visual indicators (red background, blocked badge).

**Acceptance Criteria:**

- Blocked messages show 'Blocked' badge.
- Block reason is displayed below content.
- Visual styling differentiates blocked from delivered.
- Blocked messages use format 'Blocked: {from} → {to} not allowed' when reason matches.

**Dependencies:**

- None

#### TASK-042: Verify agent filter functionality

**Release Target:** MVP **Priority:** P1 **Estimate:** S  
**Description:** Confirm the agent filter dropdown in MultiAgentMessages.tsx filters messages to show only those where the selected agent is sender or receiver.

**Acceptance Criteria:**

- Filter dropdown includes 'All agents' and each unique agent.
- Selecting agent X shows only messages where X is from or to agent.
- Message count updates to reflect filtered count.

**Dependencies:**

- None

#### TASK-043: Show empty state when no messages exist

**Release Target:** MVP **Priority:** P1 **Estimate:** S  
**Description:** Verify MultiAgentMessages.tsx shows a helpful empty state when no messages have been exchanged yet.

**Acceptance Criteria:**

- Empty state shows message icon and 'No agent messages yet' text.
- Hint text explains messages will appear during simulation.
- Transitions to message list when events arrive.

**Dependencies:**

- None

### FEAT-014: Status and tick indicators

#### TASK-044: Verify TickControls displays correct status indicator

**Release Target:** MVP **Priority:** P1 **Estimate:** S  
**Description:** Review TickControls.tsx to confirm status indicator reflects running, paused, idle, and completed states with appropriate colors and labels.

**Acceptance Criteria:**

- Running state: green pulsing indicator, 'Running' label.
- Paused state: orange indicator, 'Paused' label.
- Idle state: gray indicator, 'Idle' label.
- Completed state: blue indicator, 'Complete' label.

**Dependencies:**

- None

#### TASK-045: Verify tick index updates on tick advancement

**Release Target:** MVP **Priority:** P1 **Estimate:** S  
**Description:** Confirm TickControls.tsx tick index display updates when tick endpoints are called. UI should refresh state after each tick action.

**Acceptance Criteria:**

- Tick index shows current value from simulation state.
- After 'Run 1 Tick' button, tick index increments visually.
- After 'Run N Ticks', tick index reflects final value.

**Dependencies:**

- None

#### TASK-046: Display errors and connection issues to user

**Release Target:** MVP **Priority:** P1 **Estimate:** S  
**Description:** Ensure TickControls.tsx displays error messages when API calls fail. Show connection errors clearly so user knows when simulation state may be stale.

**Acceptance Criteria:**

- API error response shows in red error box with message.
- Network failure shows connection error message.
- Error clears when next action succeeds.

**Dependencies:**

- None

#### TASK-047: Ensure status persists when switching sessions

**Release Target:** MVP **Priority:** P1 **Estimate:** S  
**Description:** Verify that status indicators load correctly when user switches between sessions. Each session should display its own status without stale data from previous session.

**Acceptance Criteria:**

- Switching to different session loads that session's tick/status.
- No stale status shown briefly before load completes.
- Loading state shown while fetching new session state.

**Dependencies:**

- None

  # ============================================================================
  # EPIC-006: Real LLM Agent Responses
  # ============================================================================

  # FEAT-015: UI Testing Verification
  - id: "TASK-048"
    feature_id: "FEAT-015"
    epic_id: "EPIC-005"
    title: "Manual UI workflow verification with stub responses"
    description: "Manually test the complete simulation workflow via the browser UI at http://localhost:5173/control. Document each step, verify stub responses appear correctly, and identify any broken flows or UX issues. This validates the simulation works before adding real LLM integration."
    acceptance_criteria:
      - "Can initialize agents via UI (set count, prefix)."
      - "Can assign roles and models to each agent."
      - "Can configure communication graph using AgentFlowEditor."
      - "Can set initial prompt and select first agent."
      - "Can start simulation successfully."
      - "Can advance ticks and see stub responses in message log."
      - "Stub responses are clearly labeled with [STUB] marker."
      - "Blocked messages show appropriate error messages."
      - "Can pause simulation."
      - "Can reset simulation (config preserved, messages cleared)."
      - "Document any bugs or UX issues found during testing."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["ui", "qa", "manual-test"]

  - id: "TASK-049"
    feature_id: "FEAT-015"
    epic_id: "EPIC-005"
    title: "Add polling fallback for simulation state updates"
    description: "Add a 2-second polling interval to ControlPanel.tsx to fetch simulation state when status is 'running'. This provides 'live enough' updates until SSE is implemented (FEAT-011). Polling automatically stops when simulation is paused or completed."
    acceptance_criteria:
      - "When simulation status is 'running', ControlPanel polls simulation state every 2000ms."
      - "Polling stops when status changes to 'paused', 'idle', or 'completed'."
      - "Polling clears when user switches sessions."
      - "New messages appear within 2 seconds of tick advancement."
      - "No duplicate requests (clear interval before setting new one)."
      - "useEffect cleanup prevents memory leaks."
    dependencies:
      - "TASK-048"
    release_target: "MVP"
    priority: "P1"
    estimate: "S"
    tags: ["ui", "polling", "workaround"]

  - id: "TASK-050"
    feature_id: "FEAT-015"
    epic_id: "EPIC-005"
    title: "Update AgentGraph to render simulation communication links"
    description: "Modify AgentGraph.tsx to display the configured agent communication graph from simulationState.agent_graph instead of task-based edges. Show directionality with arrows, support bidirectional links. This fixes the current issue where the graph shows irrelevant task edges instead of the configured agent communication topology."
    acceptance_criteria:
      - "Graph reads edges from simulationState.agent_graph.edges."
      - "Each agent in roster appears as a node with label."
      - "Directed links show single arrow pointing to target."
      - "Bidirectional links show arrows in both directions."
      - "Empty state shows 'Configure communication graph' when no links exist."
      - "Graph updates when flow configuration changes."
      - "Graph persists during simulation and after reset."
    dependencies:
      - "TASK-048"
    release_target: "MVP"
    priority: "P1"
    estimate: "M"
    tags: ["ui", "visualization", "graph"]

  - id: "TASK-051"
    feature_id: "FEAT-015"
    epic_id: "EPIC-005"
    title: "Format blocked and stub messages in message log"
    description: "Enhance MultiAgentMessages.tsx to visually distinguish blocked messages and stub responses. Add tick number to each message row for clarity. This improves readability and helps users understand simulation state at a glance."
    acceptance_criteria:
      - "Stub messages display '[STUB]' badge in distinct color (e.g., blue)."
      - "Blocked messages display '(BLOCKED)' badge in warning color (e.g., orange/red)."
      - "Each message row shows tick number."
      - "Blocked messages show reason below content (e.g., 'agent-1 → agent-3 not allowed')."
      - "Visual styling differentiates message types (border, background, or badge)."
    dependencies:
      - "TASK-048"
    release_target: "MVP"
    priority: "P1"
    estimate: "S"
    tags: ["ui", "messages", "formatting"]

  - id: "TASK-052"
    feature_id: "FEAT-015"
    epic_id: "EPIC-005"
    title: "Create standalone simulation screen"
    description: "Add a dedicated /simulation screen that auto-creates a session and reuses existing widgets for a focused sandbox UI. This enables manual testing without the questionnaire or planning flows."
    acceptance_criteria:
      - "Create apps/ui/src/screens/Simulation.tsx."
      - "Add /simulation route in App.tsx."
      - "Session auto-creates on load without user input."
      - "Page composes AgentInitializer, AgentAssignment, AgentFlowEditor, SimulationConfig, TickControls, MultiAgentMessages."
      - "Questionnaire/planning UI is not shown on the /simulation screen."
      - "New button creates a fresh session and resets state."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["ui", "routing", "sandbox"]

  - id: "TASK-053"
    feature_id: "FEAT-015"
    epic_id: "EPIC-005"
    title: "Move simulation UI to /simulation route"
    description: "Relocate simulation-related UI from /control to /simulation, keeping the control panel focused on session monitoring. Update routing and navigation to point to the new simulation screen."
    acceptance_criteria:
      - "Simulation UI is accessible at /simulation."
      - "Control panel no longer renders simulation widgets."
      - "Routing uses Simulation.tsx for the /simulation screen."
      - "Navigation links for simulation point to /simulation."
      - "Questionnaire/planning UI is not shown on /simulation."
    dependencies:
      - "TASK-052"
    release_target: "MVP"
    priority: "P1"
    estimate: "M"
    tags: ["ui", "routing", "navigation"]

  # FEAT-016: Real LLM Agent Responses with Guardrails
  - id: "TASK-060"
    feature_id: "FEAT-016"
    epic_id: "EPIC-006"
    title: "Add session-level LLM configuration fields"
    description: "Extend Session model in apps/api/vibeforge_api/core/session.py to include LLM mode toggle, provider selection, model name, temperature, and cost tracking fields. Update serialization and API responses. Session defaults to stub mode (use_real_llm=False) for safety."
    acceptance_criteria:
      - "Session model includes: use_real_llm (bool, default False), llm_provider (str, default 'openai'), default_model (str, default 'gpt-4o-mini'), default_temperature (float, default 0.7), simulation_cost_usd (float, default 0.0)."
      - "Session.to_dict() serializes new fields correctly."
      - "Session.from_dict() deserializes new fields correctly."
      - "GET /control/sessions/{id}/simulation/state includes new fields in response."
      - "TypeScript types in controlClient.ts updated to include new fields."
      - "Session defaults to stub mode (use_real_llm=False) for safety."
    dependencies: []
    release_target: "V1"
    priority: "P0"
    estimate: "S"
    tags: ["api", "session", "config"]

  - id: "TASK-061"
    feature_id: "FEAT-016"
    epic_id: "EPIC-006"
    title: "Add LLM cost and rate limiting guardrails to Session"
    description: "Add cost budget and rate limiting fields to Session model. Implement validation logic to prevent runaway API costs and enforce tick rate limits. This is a critical safety feature to prevent accidental high API bills from simulation bugs or runaway loops."
    acceptance_criteria:
      - "Session includes: max_cost_usd (float, default 1.0), tick_rate_limit_ms (int, default 1000 = 1 tick per second max), last_tick_timestamp (datetime, nullable)."
      - "Before each tick, validate: current cost < max_cost_usd."
      - "Before each tick when use_real_llm=True, validate: time since last_tick >= tick_rate_limit_ms."
      - "If cost budget exceeded, return HTTP 429 with message 'Cost budget exceeded: ${current} / ${max}'."
      - "If rate limit exceeded, return HTTP 429 with message 'Rate limit: wait {remaining}ms'."
      - "POST /control/sessions/{id}/simulation/configure accepts max_cost_usd and tick_rate_limit_ms."
      - "Unit tests cover both guardrails."
    dependencies:
      - "TASK-060"
    release_target: "V1"
    priority: "P0"
    estimate: "M"
    tags: ["api", "guardrails", "safety"]

  - id: "TASK-062"
    feature_id: "FEAT-016"
    epic_id: "EPIC-006"
    title: "Create LlmResponseGenerator service with role-based prompts"
    description: "Create orchestration/coordinator/llm_response_generator.py with LlmResponseGenerator class. Implement role-based system prompts (orchestrator, worker, reviewer, fixer, foreman) and conversation history building. This service handles all LLM interactions for agent responses."
    acceptance_criteria:
      - "LlmResponseGenerator class accepts LlmClient in constructor."
      - "Async method generate_response(agent_id, agent_role, agent_model, message_history, incoming_message) returns LlmResponse."
      - "System prompts defined for all 5 roles in orchestration/prompts.py."
      - "System prompt is prepended to conversation history."
      - "Incoming message appended as user message."
      - "LLM request uses agent's configured model and temperature."
      - "Response content extracted and returned as dict (matching stub format structure)."
      - "Error handling: if LLM call fails, log error and raise exception (caller handles fallback)."
    dependencies:
      - "TASK-060"
    release_target: "V1"
    priority: "P0"
    estimate: "M"
    tags: ["orchestration", "llm", "prompts"]

  - id: "TASK-063"
    feature_id: "FEAT-016"
    epic_id: "EPIC-006"
    title: "Add agent conversation history tracking to TickEngine"
    description: "Extend TickEngine to maintain per-agent conversation history. Persist histories to session state. Limit history depth to prevent unbounded memory growth. Each agent maintains its own conversation context across ticks."
    acceptance_criteria:
      - "TickEngine includes: agent_conversations dict[str, list[dict]] mapping agent_id to message history."
      - "When message delivered, append to recipient's history as {'role': 'user', 'content': message.content}."
      - "When response generated, append to responder's history as {'role': 'assistant', 'content': response_content}."
      - "History limited to last 20 messages per agent (configurable via session.max_history_depth, default 20)."
      - "Conversation histories persisted to session.simulation_agent_conversations."
      - "TickEngine.__init__ restores histories from session state."
      - "sync_session_state() persists histories to session."
    dependencies:
      - "TASK-060"
    release_target: "V1"
    priority: "P0"
    estimate: "M"
    tags: ["orchestration", "conversation", "memory"]

  - id: "TASK-064"
    feature_id: "FEAT-016"
    epic_id: "EPIC-006"
    title: "Wire real LLM calls into TickEngine with cost tracking"
    description: "Modify TickEngine.advance_tick() to conditionally call LlmResponseGenerator when session.use_real_llm is True. Track token usage and update session cost. Handle async LLM calls. Implement fallback to stub on LLM failure. This is the core integration point between the simulation engine and real LLM providers."
    acceptance_criteria:
      - "TickEngine.__init__ accepts optional llm_client parameter (defaults to get_llm_client())."
      - "If session.use_real_llm is True, instantiate LlmResponseGenerator with llm_client."
      - "In advance_tick(), when message expects response: if use_real_llm, call await llm_generator.generate_response() with agent conversation history; if use_real_llm=False or LLM call fails, fallback to generate_stub_response()."
      - "Track LlmResponse.usage tokens and calculate cost based on model pricing (gpt-4o-mini: $0.15/$0.60 per 1M tokens)."
      - "Update session.simulation_cost_usd after each LLM call."
      - "Emit COST_TRACKING event to EventLog with: tick, agent, tokens, cost."
      - "Convert advance_tick() to async method."
      - "Update API endpoint handlers in control.py to await engine.advance_tick()."
      - "Error handling: log LLM failures, emit error event, use stub as fallback."
    dependencies:
      - "TASK-061"
      - "TASK-062"
      - "TASK-063"
    release_target: "V1"
    priority: "P0"
    estimate: "L"
    tags: ["orchestration", "llm", "async", "cost-tracking"]

  - id: "TASK-065"
    feature_id: "FEAT-016"
    epic_id: "EPIC-006"
    title: "Add UI controls for LLM mode and cost display"
    description: "Extend SimulationConfig.tsx to include toggle for stub vs real LLM mode, model selector, cost budget input, and rate limit input. Display current cost in TickControls.tsx. Provide clear warnings about API costs to prevent accidental spend."
    acceptance_criteria:
      - "SimulationConfig shows toggle: 'Use Real LLM' (default off)."
      - "When toggle enabled, show: model dropdown (gpt-4o-mini, gpt-4o, gpt-4-turbo), temperature slider (0.0 - 1.0, default 0.7), max cost budget input (USD, default $1.00), rate limit input (ms between ticks, default 1000ms), warning message 'Real LLM calls will incur API costs'."
      - "When toggle disabled, show 'Using deterministic stub responses (no cost)'."
      - "Toggle and inputs disabled once simulation is started."
      - "TickControls displays: 'Cost: ${current_cost} / ${max_cost}'."
      - "Cost display updates after each tick (via polling or state refresh)."
      - "Cost displayed in red when approaching budget (>80%)."
    dependencies:
      - "TASK-060"
      - "TASK-061"
    release_target: "V1"
    priority: "P0"
    estimate: "M"
    tags: ["ui", "config", "cost"]

  - id: "TASK-066"
    feature_id: "FEAT-016"
    epic_id: "EPIC-006"
    title: "Add unit tests for LLM integration and guardrails"
    description: "Create comprehensive unit tests for LlmResponseGenerator, conversation history tracking, cost tracking, and rate limiting guardrails. Ensure all safety mechanisms work correctly before production use."
    acceptance_criteria:
      - "Test: LlmResponseGenerator generates response with correct system prompt for each role."
      - "Test: LlmResponseGenerator builds conversation history correctly."
      - "Test: TickEngine tracks conversation history per agent."
      - "Test: TickEngine limits history to max_history_depth."
      - "Test: TickEngine calculates cost correctly based on token usage."
      - "Test: Tick endpoint blocks when cost budget exceeded (429 response)."
      - "Test: Tick endpoint blocks when rate limit violated (429 response)."
      - "Test: LLM failure falls back to stub response."
      - "Test: use_real_llm=False always uses stubs (no LLM calls)."
      - "All tests in apps/api/tests/test_llm_integration.py."
    dependencies:
      - "TASK-064"
    release_target: "V1"
    priority: "P1"
    estimate: "M"
    tags: ["testing", "qa", "guardrails"]

  - id: "TASK-067"
    feature_id: "FEAT-016"
    epic_id: "EPIC-006"
    title: "Add integration test for end-to-end LLM simulation"
    description: "Create integration test that runs a complete simulation with real LLM calls (using test API key or mock). Verify multi-turn conversations, cost tracking, and guardrails work together correctly in a realistic scenario."
    acceptance_criteria:
      - "Integration test configures 2 agents with communication link."
      - "Sets initial prompt, starts simulation with use_real_llm=True."
      - "Advances 5 ticks, verifies LLM responses appear (not stubs)."
      - "Verifies conversation history grows for both agents."
      - "Verifies simulation_cost_usd increases after each LLM call."
      - "Test uses mock LLM client or test API key (not production)."
      - "Test in apps/api/tests/test_llm_simulation_integration.py."
    dependencies:
      - "TASK-064"
    release_target: "V1"
    priority: "P1"
    estimate: "M"
    tags: ["testing", "integration", "qa"]
