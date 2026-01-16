"""TickEngine: Discrete tick-based simulation progression (VF-202, VF-203).

The TickEngine manages the tick lifecycle for simulation mode:
- advance_tick(): Perform one atomic unit of work
- validate_message(): Graph-gated messaging validation
- send_message(): Send message with graph validation

One tick represents one atomic unit of simulation progress:
- Process pending messages from the queue
- Execute ready agent work items
- Emit new messages to queue
- Return events produced during the tick
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import logging
from typing import Optional

from apps.api.vibeforge_api.core.event_log import Event, EventLog, EventType
from apps.api.vibeforge_api.core.llm_provider import get_llm_client
from apps.api.vibeforge_api.core.session import Session
from models.base.llm_client import LlmClient, LlmUsage
from orchestration.coordinator.llm_response_generator import LlmResponseGenerator
from orchestration.models import AgentFlowGraph

MODEL_PRICING_USD_PER_M_TOKEN = {
    "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
}

logger = logging.getLogger(__name__)


class MessageValidationStatus(str, Enum):
    """Status of message validation against agent graph."""

    ALLOWED = "allowed"
    BLOCKED = "blocked"


@dataclass
class MessageValidation:
    """Result of validating a message against the agent graph."""

    is_allowed: bool
    status: MessageValidationStatus
    reason: str
    from_agent: str
    to_agent: str


@dataclass
class Message:
    """A message in the simulation message queue."""

    message_id: str
    from_agent: str
    to_agent: str
    content: dict
    tick_created: int
    tick_delivered: Optional[int] = None
    is_delivered: bool = False
    is_blocked: bool = False
    blocked_reason: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize message to a dict for session persistence."""
        return {
            "message_id": self.message_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "content": self.content,
            "tick_created": self.tick_created,
            "tick_delivered": self.tick_delivered,
            "is_delivered": self.is_delivered,
            "is_blocked": self.is_blocked,
            "blocked_reason": self.blocked_reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """Restore message from session storage."""
        return cls(
            message_id=data.get("message_id", ""),
            from_agent=data.get("from_agent", ""),
            to_agent=data.get("to_agent", ""),
            content=data.get("content", {}),
            tick_created=data.get("tick_created", 0),
            tick_delivered=data.get("tick_delivered"),
            is_delivered=data.get("is_delivered", False),
            is_blocked=data.get("is_blocked", False),
            blocked_reason=data.get("blocked_reason"),
        )


@dataclass
class TickResult:
    """Result of advancing one tick."""

    tick_index: int
    events_in_tick: int
    messages_in_tick: int
    messages_blocked: int
    events: list[Event] = field(default_factory=list)
    messages_sent: list[Message] = field(default_factory=list)
    messages_delivered: list[Message] = field(default_factory=list)


class TickEngine:
    """Engine for discrete tick-based simulation progression (VF-202).

    Manages the tick lifecycle for simulation mode. Each tick represents
    one atomic unit of progress in the simulation.

    Attributes:
        session: The session being simulated
        agent_graph: The agent communication graph for message validation
        message_queue: Queue of pending messages to process
        event_log: Optional EventLog for persisting emitted events
        tick_events: Events produced during the current tick
    """

    def __init__(
        self,
        session: Session,
        agent_graph: Optional[AgentFlowGraph] = None,
        event_log: Optional[EventLog] = None,
        llm_client: Optional[LlmClient] = None,
    ):
        """Initialize the tick engine.

        Args:
            session: Session to simulate
            agent_graph: Agent communication graph (loaded from session if None)
        """
        self.session = session
        self._message_counter = getattr(session, "simulation_message_counter", 0)
        self.event_log = event_log
        self.llm_client = llm_client or get_llm_client()
        self.llm_generator: Optional[LlmResponseGenerator] = None

        # Load agent graph from session if not provided
        if agent_graph is not None:
            self.agent_graph = agent_graph
        elif session.agent_graph:
            # Reconstruct from session dict
            self.agent_graph = AgentFlowGraph(**session.agent_graph)
        else:
            self.agent_graph = AgentFlowGraph(edges=[])

        # Message queue (persisted across ticks)
        queue_state = getattr(session, "simulation_message_queue", None)
        if queue_state:
            self.message_queue = [Message.from_dict(item) for item in queue_state]
        else:
            self.message_queue = []

        # Conversation history per agent (persisted across ticks)
        self.agent_conversations = getattr(
            session, "simulation_agent_conversations", {}
        ) or {}

        # Events for current tick only (reset each tick)
        self._tick_events: list[Event] = []

    def _generate_message_id(self) -> str:
        """Generate a unique message ID."""
        self._message_counter += 1
        return f"msg-{self.session.tick_index}-{self._message_counter}"

    def _emit_event(self, event: Event) -> None:
        """Emit an event for the current tick."""
        self._tick_events.append(event)
        if self.event_log is not None:
            try:
                self.event_log.append(event)
            except OSError as exc:
                logger.warning(
                    "Failed to append event log for session %s: %s",
                    event.session_id,
                    exc,
                )

    def sync_session_state(self) -> None:
        """Persist message queue state into the session."""
        self.session.simulation_message_queue = [
            message.to_dict() for message in self.message_queue
        ]
        self.session.simulation_message_counter = self._message_counter
        self.session.simulation_agent_conversations = self.agent_conversations
        self.session.simulation_expected_responses = getattr(
            self.session, "simulation_expected_responses", []
        )
        self.session.simulation_final_answer = getattr(
            self.session, "simulation_final_answer", None
        )

    def _append_history(self, agent_id: str, role: str, content: dict) -> None:
        if not agent_id:
            return
        history = self.agent_conversations.setdefault(agent_id, [])
        history.append({"role": role, "content": content})
        max_depth = getattr(self.session, "max_history_depth", 20) or 20
        if max_depth > 0 and len(history) > max_depth:
            del history[:-max_depth]

    def _get_llm_generator(self) -> LlmResponseGenerator:
        if self.llm_generator is None:
            self.llm_generator = LlmResponseGenerator(self.llm_client)
        self.llm_generator.default_temperature = self.session.default_temperature
        self.llm_generator.default_model = self.session.default_model
        return self.llm_generator

    def _calculate_llm_cost(self, model: str, usage: Optional[LlmUsage]) -> float:
        if not usage:
            return 0.0
        rates = MODEL_PRICING_USD_PER_M_TOKEN.get(model)
        if not rates:
            return 0.0
        prompt_cost = (usage.prompt_tokens or 0) / 1_000_000 * rates["prompt"]
        completion_cost = (usage.completion_tokens or 0) / 1_000_000 * rates["completion"]
        return prompt_cost + completion_cost

    def _emit_cost_event(
        self,
        agent_id: str,
        model: str,
        usage: Optional[LlmUsage],
        cost_usd: float,
        tick_index: int,
    ) -> None:
        usage = usage or LlmUsage()
        self._emit_event(
            Event(
                event_type=EventType.COST_TRACKING,
                timestamp=datetime.now(timezone.utc),
                session_id=self.session.session_id,
                message=f"Cost tracked: ${cost_usd:.6f}",
                phase=self.session.phase.value,
                metadata={
                    "tick_index": tick_index,
                    "agent_id": agent_id,
                    "model": model,
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                    "cost_usd": cost_usd,
                    "total_cost_usd": self.session.simulation_cost_usd,
                },
            )
        )

    def _get_agent_ids(self) -> list[str]:
        """Get list of configured agent IDs from session."""
        return [agent.get("agent_id", "") for agent in self.session.agents]

    def _get_delegate_targets(self, orchestrator_id: str) -> list[str]:
        targets = []
        for agent_id in self._get_agent_ids():
            if not agent_id or agent_id == orchestrator_id:
                continue
            if self.session.agent_roles.get(agent_id) == "orchestrator":
                continue
            targets.append(agent_id)
        return targets

    def _should_delegate(self, message: Message) -> bool:
        if message.from_agent != "user":
            return False
        if not self._is_orchestrator(message.to_agent):
            return False
        if not self._message_expects_response(message):
            return False
        expected = getattr(self.session, "simulation_expected_responses", [])
        if expected:
            return False
        return bool(self._get_delegate_targets(message.to_agent))

    def _queue_delegation_messages(self, orchestrator_id: str, prompt_text: str) -> None:
        targets = self._get_delegate_targets(orchestrator_id)
        if not targets:
            return
        self.session.simulation_expected_responses = list(targets)
        self.session.simulation_final_answer = None
        main_task = self.session.main_task or prompt_text
        for target in targets:
            self.send_message(
                from_agent=orchestrator_id,
                to_agent=target,
                content={
                    "text": (
                        "Analyze the task and respond with reasoning + conclusion.\n\n"
                        f"Task: {main_task}"
                    ),
                    "expect_response": True,
                    "delegation": True,
                },
            )

    async def _finalize_delegation(
        self,
        orchestrator_id: str,
        tick_index: int,
    ) -> None:
        response_payload = None
        if self.session.use_real_llm:
            generator = self._get_llm_generator()
            agent_model = self.session.agent_models.get(
                orchestrator_id, self.session.default_model
            )
            agent_role = self.session.agent_roles.get(orchestrator_id)
            try:
                response = await generator.generate_response(
                    agent_id=orchestrator_id,
                    agent_role=agent_role,
                    agent_model=agent_model,
                    message_history=self.agent_conversations.get(orchestrator_id, []),
                    incoming_message=(
                        "Provide a final answer to the user based on the discussion."
                    ),
                )
                response_payload = (
                    response.metadata.get("content") if response.metadata else None
                )
                if not isinstance(response_payload, dict):
                    response_payload = {
                        "text": response.content,
                        "is_stub": False,
                        "expect_response": False,
                    }
                cost_usd = self._calculate_llm_cost(response.model, response.usage)
                if cost_usd > 0:
                    self.session.simulation_cost_usd += cost_usd
                    self._emit_cost_event(
                        agent_id=orchestrator_id,
                        model=response.model,
                        usage=response.usage,
                        cost_usd=cost_usd,
                        tick_index=tick_index,
                    )
            except Exception as exc:
                self._emit_event(
                    Event(
                        event_type=EventType.LLM_FAILURE,
                        timestamp=datetime.now(timezone.utc),
                        session_id=self.session.session_id,
                        message="LLM response generation failed",
                        phase=self.session.phase.value,
                        metadata={
                            "tick_index": tick_index,
                            "agent_id": orchestrator_id,
                            "error": str(exc),
                        },
                    )
                )
                response_payload = None

        if response_payload is None:
            prompt = self.session.main_task or self.session.initial_prompt or ""
            response_payload = {
                "text": (
                    "[STUB] Final answer placeholder."
                    + (f" Task: {prompt}" if prompt else "")
                ),
                "is_stub": True,
                "expect_response": False,
            }

        response_payload["final_answer"] = True
        self._append_history(orchestrator_id, "assistant", response_payload)

        success, final_message = self.send_message(
            from_agent=orchestrator_id,
            to_agent="user",
            content=response_payload,
            bypass_validation=True,
        )
        if success and final_message:
            final_message.is_delivered = True
            final_message.tick_delivered = tick_index

        self.session.simulation_final_answer = response_payload.get("text")
        self.session.simulation_expected_responses = []
        self.session.tick_status = "completed"

    def _message_expects_response(self, message: Message) -> bool:
        """Check if a message should trigger an automated response."""
        if not isinstance(message.content, dict):
            return False
        return bool(
            message.content.get("expect_response")
            or message.content.get("expects_response")
        )

    def _is_orchestrator(self, agent_id: str) -> bool:
        """Check if agent is the orchestrator (can broadcast)."""
        role = self.session.agent_roles.get(agent_id)
        return role == "orchestrator"

    def generate_stub_response(
        self,
        responding_agent: str,
        source_agent: str,
        message_content: dict,
        tick_index: int,
    ) -> dict:
        """Generate a deterministic stub response payload."""
        content_json = json.dumps(
            message_content,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        content_hash = hashlib.sha256(content_json.encode("utf-8")).hexdigest()
        stub_hash = content_hash[:10]
        text = (
            f"[STUB] {responding_agent} -> {source_agent} "
            f"@ tick {tick_index} ({stub_hash})"
        )
        return {
            "text": text,
            "is_stub": True,
            "stub_hash": stub_hash,
            "expect_response": False,
        }

    # =========================================================================
    # VF-203: Graph-gated messaging
    # =========================================================================

    def validate_message(
        self, from_agent: str, to_agent: str
    ) -> MessageValidation:
        """Validate if a message is allowed based on agent_graph (VF-203).

        A message A→B is allowed if:
        1. Edge A→B exists in agent_graph, OR
        2. from_agent is orchestrator (can broadcast), OR
        3. Message is to self (A→A)

        Args:
            from_agent: Source agent ID
            to_agent: Target agent ID

        Returns:
            MessageValidation with is_allowed, reason, status
        """
        agent_ids = self._get_agent_ids()

        # Validate agents exist
        if from_agent not in agent_ids:
            return MessageValidation(
                is_allowed=False,
                status=MessageValidationStatus.BLOCKED,
                reason=f"Source agent '{from_agent}' not configured",
                from_agent=from_agent,
                to_agent=to_agent,
            )

        if to_agent not in agent_ids:
            return MessageValidation(
                is_allowed=False,
                status=MessageValidationStatus.BLOCKED,
                reason=f"Target agent '{to_agent}' not configured",
                from_agent=from_agent,
                to_agent=to_agent,
            )

        # Self-message is always allowed
        if from_agent == to_agent:
            return MessageValidation(
                is_allowed=True,
                status=MessageValidationStatus.ALLOWED,
                reason="Self-message always allowed",
                from_agent=from_agent,
                to_agent=to_agent,
            )

        # Orchestrator can broadcast to any agent
        if self._is_orchestrator(from_agent):
            return MessageValidation(
                is_allowed=True,
                status=MessageValidationStatus.ALLOWED,
                reason="Orchestrator can broadcast to any agent",
                from_agent=from_agent,
                to_agent=to_agent,
            )

        # Check if edge exists in graph
        edge_exists = any(
            (
                edge.from_agent == from_agent
                and edge.to_agent == to_agent
            )
            or (
                edge.bidirectional
                and edge.from_agent == to_agent
                and edge.to_agent == from_agent
            )
            for edge in self.agent_graph.edges
        )

        if edge_exists:
            return MessageValidation(
                is_allowed=True,
                status=MessageValidationStatus.ALLOWED,
                reason=f"Edge {from_agent}→{to_agent} exists in agent graph",
                from_agent=from_agent,
                to_agent=to_agent,
            )

        # No edge found - message blocked
        return MessageValidation(
            is_allowed=False,
            status=MessageValidationStatus.BLOCKED,
            reason=f"{from_agent} {chr(0x03B7)}' {to_agent} not allowed",
            from_agent=from_agent,
            to_agent=to_agent,
        )

    def send_message(
        self,
        from_agent: str,
        to_agent: str,
        content: dict,
        bypass_validation: bool = False,
    ) -> tuple[bool, Optional[Message]]:
        """Send a message with graph validation (VF-203).

        If the message is blocked by the graph, emits a MESSAGE_BLOCKED_BY_GRAPH
        event so the UI can display why nothing happened.

        Args:
            from_agent: Source agent ID
            to_agent: Target agent ID
            content: Message content
            bypass_validation: Skip graph validation (for system messages)

        Returns:
            Tuple of (success, message_or_none)
        """
        # Validate message against graph
        if not bypass_validation:
            validation = self.validate_message(from_agent, to_agent)

            if not validation.is_allowed:
                # Emit blocked event
                self._emit_event(
                    Event(
                        event_type=EventType.MESSAGE_BLOCKED_BY_GRAPH,
                        timestamp=datetime.now(timezone.utc),
                        session_id=self.session.session_id,
                        message=f"Message blocked: {validation.reason}",
                        phase=self.session.phase.value,
                        metadata={
                            "from_agent": from_agent,
                            "to_agent": to_agent,
                            "reason": validation.reason,
                            "tick_index": self.session.tick_index,
                        },
                    )
                )
                return False, None

        # Create and queue message
        message = Message(
            message_id=self._generate_message_id(),
            from_agent=from_agent,
            to_agent=to_agent,
            content=content,
            tick_created=self.session.tick_index,
        )
        self.message_queue.append(message)

        metadata = {
            "message_id": message.message_id,
            "from_agent": from_agent,
            "to_agent": to_agent,
            "tick_index": self.session.tick_index,
            "content": content if not isinstance(content, dict) else dict(content),
        }
        if isinstance(content, dict) and content.get("is_stub"):
            metadata["is_stub"] = True

        # Emit sent event
        self._emit_event(
            Event(
                event_type=EventType.MESSAGE_SENT,
                timestamp=datetime.now(timezone.utc),
                session_id=self.session.session_id,
                message=f"Message sent: {from_agent}→{to_agent}",
                phase=self.session.phase.value,
                metadata=metadata,
            )
        )

        return True, message

    # =========================================================================
    # VF-202: Tick advancement
    # =========================================================================

    def get_pending_messages(self, agent_id: str) -> list[Message]:
        """Get pending messages for an agent."""
        return [
            msg for msg in self.message_queue
            if msg.to_agent == agent_id and not msg.is_delivered and not msg.is_blocked
        ]

    def deliver_message(self, message: Message) -> None:
        """Mark a message as delivered."""
        message.is_delivered = True
        message.tick_delivered = self.session.tick_index

    async def advance_tick(self) -> TickResult:
        """Advance simulation by one tick (VF-202).

        One tick performs:
        1. Increment tick counter
        2. Deliver pending messages to target agents
        3. (Future: Execute agent work items)
        4. Emit TICK_ADVANCED event

        Returns:
            TickResult with events and messages processed
        """
        # Reset tick events
        self._tick_events = []

        # Increment tick
        old_tick = self.session.tick_index
        self.session.tick_index += 1
        new_tick = self.session.tick_index

        # Process a single pending message in FIFO order
        messages_delivered = []
        agents_acted: set[str] = set()
        for message in self.message_queue:
            if message.is_delivered or message.is_blocked:
                continue
            if message.from_agent in agents_acted:
                continue
            self.deliver_message(message)
            messages_delivered.append(message)
            agents_acted.add(message.from_agent)
            self._append_history(message.to_agent, "user", message.content)
            if self._should_delegate(message):
                prompt_text = ""
                if isinstance(message.content, dict):
                    prompt_text = str(message.content.get("text", ""))
                elif isinstance(message.content, str):
                    prompt_text = message.content
                self._queue_delegation_messages(message.to_agent, prompt_text)
            elif self._message_expects_response(message):
                response_payload = None
                if self.session.use_real_llm:
                    generator = self._get_llm_generator()
                    agent_model = self.session.agent_models.get(
                        message.to_agent, self.session.default_model
                    )
                    agent_role = self.session.agent_roles.get(message.to_agent)
                    try:
                        response = await generator.generate_response(
                            agent_id=message.to_agent,
                            agent_role=agent_role,
                            agent_model=agent_model,
                            message_history=self.agent_conversations.get(
                                message.to_agent, []
                            ),
                            incoming_message=message.content,
                        )
                        response_payload = (
                            response.metadata.get("content") if response.metadata else None
                        )
                        if not isinstance(response_payload, dict):
                            response_payload = {
                                "text": response.content,
                                "is_stub": False,
                                "expect_response": False,
                            }
                        cost_usd = self._calculate_llm_cost(
                            response.model, response.usage
                        )
                        if cost_usd > 0:
                            self.session.simulation_cost_usd += cost_usd
                            self._emit_cost_event(
                                agent_id=message.to_agent,
                                model=response.model,
                                usage=response.usage,
                                cost_usd=cost_usd,
                                tick_index=new_tick,
                            )
                    except Exception as exc:
                        self._emit_event(
                            Event(
                                event_type=EventType.LLM_FAILURE,
                                timestamp=datetime.now(timezone.utc),
                                session_id=self.session.session_id,
                                message="LLM response generation failed",
                                phase=self.session.phase.value,
                                metadata={
                                    "tick_index": new_tick,
                                    "agent_id": message.to_agent,
                                    "error": str(exc),
                                },
                            )
                        )
                        response_payload = None

                if response_payload is None:
                    response_payload = self.generate_stub_response(
                        responding_agent=message.to_agent,
                        source_agent=message.from_agent,
                        message_content=message.content,
                        tick_index=new_tick,
                    )

                response_payload["in_response_to"] = message.message_id
                self._append_history(message.to_agent, "assistant", response_payload)
                self.send_message(
                    message.to_agent,
                    message.from_agent,
                    response_payload,
                    bypass_validation=True,
                )

            expected = getattr(self.session, "simulation_expected_responses", [])
            if (
                expected
                and self._is_orchestrator(message.to_agent)
                and message.from_agent in expected
            ):
                self.session.simulation_expected_responses = [
                    agent_id for agent_id in expected
                    if agent_id != message.from_agent
                ]
                if not self.session.simulation_expected_responses:
                    await self._finalize_delegation(message.to_agent, new_tick)
            break

        # Count messages sent this tick
        messages_sent = [
            msg for msg in self.message_queue
            if msg.tick_created == new_tick
        ]

        # Count blocked messages
        messages_blocked = len([
            e for e in self._tick_events
            if e.event_type == EventType.MESSAGE_BLOCKED_BY_GRAPH
        ])

        # Emit tick advanced event
        self._emit_event(
            Event(
                event_type=EventType.TICK_ADVANCED,
                timestamp=datetime.now(timezone.utc),
                session_id=self.session.session_id,
                message=f"Tick advanced: {old_tick} → {new_tick}",
                phase=self.session.phase.value,
                metadata={
                    "old_tick": old_tick,
                    "new_tick": new_tick,
                    "old_tick_index": old_tick,
                    "new_tick_index": new_tick,
                    "messages_delivered": len(messages_delivered),
                    "messages_blocked": messages_blocked,
                    "messages_sent": len(messages_sent),
                },
            )
        )

        return TickResult(
            tick_index=new_tick,
            events_in_tick=len(self._tick_events),
            messages_in_tick=len(messages_sent),
            messages_blocked=messages_blocked,
            events=list(self._tick_events),
            messages_sent=messages_sent,
            messages_delivered=messages_delivered,
        )

    def get_tick_events(self) -> list[Event]:
        """Get events produced during the current/last tick."""
        return list(self._tick_events)

    def get_tick_state(self) -> dict:
        """Get current tick state summary."""
        return {
            "tick_index": self.session.tick_index,
            "tick_status": self.session.tick_status,
            "pending_messages": len([
                m for m in self.message_queue
                if not m.is_delivered and not m.is_blocked
            ]),
            "delivered_messages": len([
                m for m in self.message_queue if m.is_delivered
            ]),
            "blocked_messages": len([
                m for m in self.message_queue if m.is_blocked
            ]),
            "total_messages": len(self.message_queue),
        }

    def clear_delivered_messages(self) -> int:
        """Clear delivered messages from queue. Returns count cleared."""
        original_count = len(self.message_queue)
        self.message_queue = [
            m for m in self.message_queue if not m.is_delivered
        ]
        return original_count - len(self.message_queue)
