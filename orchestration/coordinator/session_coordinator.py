"""SessionCoordinator: Orchestrates the factory workflow across all session phases.

This is the brain of the VibeForge factory. It coordinates:
- Session initialization and workspace setup
- Questionnaire flow and IntentProfile generation
- BuildSpec creation
- Concept and TaskGraph generation
- Task execution loop
- Verification and completion

VF-032, VF-033, VF-034 (WP-0018)
VF-035, VF-036 (WP-0019)
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from vibeforge_api.core.session import Session, SessionStoreInterface
from vibeforge_api.core.workspace import WorkspaceManager
from vibeforge_api.core.questionnaire import QuestionnaireEngine
from vibeforge_api.core.spec_builder import SpecBuilder
from vibeforge_api.core.artifacts import ArtifactStore
from vibeforge_api.core.event_log import (
    Event,
    EventLog,
    EventType,
    create_phase_transition_event,
)
from vibeforge_api.core.patch import PatchApplier
from vibeforge_api.core.gates import GatePipeline, DiffAndCommandGate, PolicyGate, GateContext
from vibeforge_api.core.verifiers import VerifierSuite
from vibeforge_api.models.types import SessionPhase
from vibeforge_api.models.responses import QuestionResponse
from orchestration.orchestrator import Orchestrator
from orchestration.models import ConceptDoc, TaskGraph, RunSummary
from runtime.task_master import TaskMaster
from runtime.distributor import Distributor
from models.agent_framework import AgentFramework, AgentResult


class SessionCoordinator:
    """Orchestrates the factory workflow across all session phases.

    This is the "brain" of VibeForge - it knows the phase sequence and delegates
    to specialized components for each stage.
    """

    def __init__(
        self,
        session_store: SessionStoreInterface,
        workspace_manager: WorkspaceManager,
        questionnaire_engine: QuestionnaireEngine,
        spec_builder: SpecBuilder,
        orchestrator: Orchestrator,
        agent_framework: Optional[AgentFramework] = None,
        distributor: Optional[Distributor] = None,
        event_log: Optional[EventLog] = None,
    ):
        """Initialize SessionCoordinator with dependencies.

        Args:
            session_store: Session persistence layer
            workspace_manager: Workspace initialization
            questionnaire_engine: Questionnaire flow driver
            spec_builder: BuildSpec generator
            orchestrator: High-level concept/plan generator
            agent_framework: Agent execution framework (optional, for VF-037)
            distributor: Task-to-role distributor (optional, for VF-037)
        """
        self.session_store = session_store
        self.workspace_manager = workspace_manager
        self.questionnaire_engine = questionnaire_engine
        self.spec_builder = spec_builder
        self.orchestrator = orchestrator
        self.agent_framework = agent_framework
        self.distributor = distributor or Distributor()
        self.event_log = event_log or EventLog(
            getattr(self.workspace_manager, "workspace_root", Path("./workspaces"))
        )

        # Task execution state (per session)
        self._task_masters: dict[str, TaskMaster] = {}

    def _emit_event(self, event: Event) -> None:
        """Persist an event to the event log, ignoring failures."""

        try:
            self.event_log.append(event)
        except Exception:
            # Observability should not break execution; errors are logged via session logs.
            pass

    def _transition_phase(self, session: Session, new_phase: SessionPhase, reason: str) -> None:
        """Transition session phase and emit a phase transition event."""

        old_phase = session.phase
        session.update_phase(new_phase)
        self._emit_event(
            create_phase_transition_event(
                session.session_id, old_phase.value, new_phase.value, reason
            )
        )

    # =========================================================================
    # VF-032: startSession() + phase initialization
    # =========================================================================

    def start_session(self) -> str:
        """Start a new session and initialize workspace.

        This is the entry point for all VibeForge runs. It:
        1. Creates a new session in storage
        2. Initializes workspace (repo/ and artifacts/ directories)
        3. Sets phase to QUESTIONNAIRE
        4. Returns session_id for subsequent API calls

        Returns:
            str: The session_id for the newly created session

        Raises:
            RuntimeError: If workspace initialization fails
        """
        # Create new session (defaults to QUESTIONNAIRE phase)
        session = self.session_store.create_session()
        session_id = session.session_id

        try:
            # Initialize workspace for this session
            workspace_path = self.workspace_manager.init_repo(session_id)

            # Log workspace initialization
            session.add_log(f"Workspace initialized at {workspace_path}")
            self._emit_event(
                Event(
                    event_type=EventType.WORKSPACE_INITIALIZED,
                    timestamp=datetime.now(timezone.utc),
                    session_id=session_id,
                    message=f"Workspace initialized at {workspace_path}",
                    phase=session.phase.value,
                )
            )

            # Update session in storage
            self.session_store.update_session(session)

            return session_id

        except Exception as e:
            # Record error and re-raise
            session.add_error(
                task_id="init",
                error_message=f"Workspace initialization failed: {str(e)}",
            )
            self.session_store.update_session(session)
            raise RuntimeError(f"Failed to initialize session workspace: {str(e)}") from e

    # =========================================================================
    # VF-033: questionnaire step loop (nextQuestion/applyAnswer/finalize)
    # =========================================================================

    def get_next_question(self, session_id: str) -> Optional[QuestionResponse]:
        """Get the next questionnaire question for a session.

        Args:
            session_id: ID of the session

        Returns:
            QuestionResponse with next question, or None if questionnaire complete

        Raises:
            ValueError: If session not found or not in QUESTIONNAIRE phase
        """
        session = self._get_session_or_raise(session_id)

        # Validate phase
        if session.phase != SessionPhase.QUESTIONNAIRE:
            raise ValueError(
                f"Cannot get question: session {session_id} is in phase {session.phase.value}, "
                f"expected {SessionPhase.QUESTIONNAIRE.value}"
            )

        # Delegate to questionnaire engine
        question = self.questionnaire_engine.get_next_question(session.current_question_index)

        return question

    def submit_answer(self, session_id: str, question_id: str, answer: Any) -> None:
        """Submit an answer to the current question.

        Args:
            session_id: ID of the session
            question_id: ID of the question being answered
            answer: The answer value

        Raises:
            ValueError: If session not found, wrong phase, or invalid answer
        """
        session = self._get_session_or_raise(session_id)

        # Validate phase
        if session.phase != SessionPhase.QUESTIONNAIRE:
            raise ValueError(
                f"Cannot submit answer: session {session_id} is in phase {session.phase.value}, "
                f"expected {SessionPhase.QUESTIONNAIRE.value}"
            )

        # Validate answer via questionnaire engine
        question = self.questionnaire_engine.get_next_question(session.current_question_index)
        if not question:
            raise ValueError(f"No question available at index {session.current_question_index}")

        if question.question_id != question_id:
            raise ValueError(
                f"Question ID mismatch: expected {question.question_id}, got {question_id}"
            )

        # Validate answer format
        if not self.questionnaire_engine.validate_answer(question_id, answer):
            raise ValueError(f"Invalid answer for question {question_id}: {answer}")

        # Store answer
        session.add_answer(question_id, answer)
        session.current_question_index += 1
        session.add_log(f"Answer submitted for {question_id}: {answer}")

        # Update session
        self.session_store.update_session(session)

    def finalize_questionnaire(self, session_id: str) -> dict[str, Any]:
        """Finalize questionnaire and generate IntentProfile.

        Args:
            session_id: ID of the session

        Returns:
            dict: The generated IntentProfile

        Raises:
            ValueError: If session not found, wrong phase, or questionnaire incomplete
        """
        session = self._get_session_or_raise(session_id)

        # Validate phase
        if session.phase != SessionPhase.QUESTIONNAIRE:
            raise ValueError(
                f"Cannot finalize questionnaire: session {session_id} is in phase {session.phase.value}, "
                f"expected {SessionPhase.QUESTIONNAIRE.value}"
            )

        # Ensure all questions answered
        total_questions = len(self.questionnaire_engine.questions)
        if session.current_question_index < total_questions:
            raise ValueError(
                f"Questionnaire incomplete: answered {session.current_question_index}/{total_questions} questions"
            )

        # Generate IntentProfile
        intent_profile = self.questionnaire_engine.finalize(session_id, session.answers)

        # Store in session
        session.intent_profile = intent_profile
        session.add_log("IntentProfile generated")
        self._emit_event(
            Event(
                event_type=EventType.INTENT_PROFILE_CREATED,
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
                message="IntentProfile generated",
                phase=session.phase.value,
                metadata={"question_count": total_questions},
            )
        )

        # Transition to BUILD_SPEC phase
        self._transition_phase(
            session, SessionPhase.BUILD_SPEC, "Questionnaire finalized"
        )
        session.add_log(f"Phase transition: QUESTIONNAIRE → BUILD_SPEC")

        # Update session
        self.session_store.update_session(session)

        return intent_profile

    # =========================================================================
    # VF-034: buildSpec stage
    # =========================================================================

    def generate_build_spec(self, session_id: str) -> dict[str, Any]:
        """Generate BuildSpec from IntentProfile.

        This is a deterministic transformation: same IntentProfile always
        produces the same BuildSpec (for reproducibility and testing).

        Args:
            session_id: ID of the session

        Returns:
            dict: The generated BuildSpec

        Raises:
            ValueError: If session not found, wrong phase, or IntentProfile missing
        """
        session = self._get_session_or_raise(session_id)

        # Validate phase
        if session.phase != SessionPhase.BUILD_SPEC:
            raise ValueError(
                f"Cannot generate BuildSpec: session {session_id} is in phase {session.phase.value}, "
                f"expected {SessionPhase.BUILD_SPEC.value}"
            )

        # Ensure IntentProfile exists
        if not session.intent_profile:
            raise ValueError(f"IntentProfile missing for session {session_id}")

        # Generate BuildSpec deterministically
        build_spec = self.spec_builder.fromIntent(session.intent_profile)

        # Store in session
        session.build_spec = build_spec
        session.add_log("BuildSpec generated")
        self._emit_event(
            Event(
                event_type=EventType.BUILD_SPEC_CREATED,
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
                message="BuildSpec generated",
                phase=session.phase.value,
            )
        )

        # Persist BuildSpec as artifact
        workspace_path = self.workspace_manager.workspace_root / session_id
        artifact_store = ArtifactStore(str(workspace_path / "artifacts"))
        artifact_store.save_artifact("build_spec.json", build_spec)
        session.add_log("BuildSpec persisted to artifacts/build_spec.json")

        # Transition to IDEA phase
        self._transition_phase(session, SessionPhase.IDEA, "BuildSpec generated")
        session.add_log(f"Phase transition: BUILD_SPEC → IDEA")

        # Update session
        self.session_store.update_session(session)

        return build_spec

    # =========================================================================
    # VF-035: concept generation stage
    # =========================================================================

    async def generate_concept(self, session_id: str) -> dict[str, Any]:
        """Generate concept from BuildSpec using Orchestrator.

        This calls the LLM to generate a creative concept based on the
        constraints in BuildSpec (stack, genre, twists, scope).

        Args:
            session_id: ID of the session

        Returns:
            dict: The generated concept (ConceptDoc as dict)

        Raises:
            ValueError: If session not found, wrong phase, or BuildSpec missing
            RuntimeError: If concept generation fails
        """
        session = self._get_session_or_raise(session_id)

        # Validate phase
        if session.phase != SessionPhase.IDEA:
            raise ValueError(
                f"Cannot generate concept: session {session_id} is in phase {session.phase.value}, "
                f"expected {SessionPhase.IDEA.value}"
            )

        # Ensure BuildSpec exists
        if not session.build_spec:
            raise ValueError(f"BuildSpec missing for session {session_id}")

        try:
            # Call Orchestrator to generate concept
            session.add_log("Generating concept from BuildSpec...")
            concept_doc: ConceptDoc = await self.orchestrator.generateConcept(session.build_spec)

            # Convert ConceptDoc to dict for storage
            concept = concept_doc.to_dict()

            # Store in session
            session.concept = concept
            session.add_log("Concept generated successfully")
            self._emit_event(
                Event(
                    event_type=EventType.CONCEPT_CREATED,
                    timestamp=datetime.now(timezone.utc),
                    session_id=session_id,
                    message="Concept generated",
                    phase=session.phase.value,
                )
            )

            # Persist concept as artifact
            workspace_path = self.workspace_manager.workspace_root / session_id
            artifact_store = ArtifactStore(str(workspace_path / "artifacts"))
            artifact_store.save_artifact("concept.json", concept)
            session.add_log("Concept persisted to artifacts/concept.json")

            # Transition to PLAN_REVIEW phase
            self._transition_phase(
                session, SessionPhase.PLAN_REVIEW, "Concept generated"
            )
            session.add_log(f"Phase transition: IDEA → PLAN_REVIEW")

            # Update session
            self.session_store.update_session(session)

            return concept

        except Exception as e:
            # Record error and re-raise
            session.add_error(
                task_id="concept_generation",
                error_message=f"Concept generation failed: {str(e)}",
            )
            self.session_store.update_session(session)
            raise RuntimeError(f"Failed to generate concept: {str(e)}") from e

    # =========================================================================
    # VF-036: plan proposal + plan approval stage
    # =========================================================================

    async def generate_plan(self, session_id: str) -> dict[str, Any]:
        """Generate TaskGraph from BuildSpec and Concept using Orchestrator.

        This calls the LLM to create an execution plan (TaskGraph DAG)
        based on the concept and constraints.

        Args:
            session_id: ID of the session

        Returns:
            dict: The generated TaskGraph (as dict)

        Raises:
            ValueError: If session not found, wrong phase, or concept missing
            RuntimeError: If plan generation fails
        """
        session = self._get_session_or_raise(session_id)

        # Validate phase
        if session.phase != SessionPhase.PLAN_REVIEW:
            raise ValueError(
                f"Cannot generate plan: session {session_id} is in phase {session.phase.value}, "
                f"expected {SessionPhase.PLAN_REVIEW.value}"
            )

        # Ensure BuildSpec and Concept exist
        if not session.build_spec:
            raise ValueError(f"BuildSpec missing for session {session_id}")
        if not session.concept:
            raise ValueError(f"Concept missing for session {session_id}")

        try:
            # Call Orchestrator to generate TaskGraph
            session.add_log("Generating TaskGraph from concept...")
            task_graph: TaskGraph = await self.orchestrator.createTaskGraph(
                session.build_spec, session.concept
            )

            # Validate TaskGraph DAG
            task_graph.validate_dag()
            session.add_log("TaskGraph validated successfully")

            # Convert TaskGraph to dict for storage
            task_graph_dict = task_graph.to_dict()

            # Store in session
            session.task_graph = task_graph_dict
            session.add_log(f"TaskGraph generated: {len(task_graph.tasks)} tasks")
            self._emit_event(
                Event(
                    event_type=EventType.TASK_GRAPH_CREATED,
                    timestamp=datetime.now(timezone.utc),
                    session_id=session_id,
                    message="TaskGraph generated",
                    phase=session.phase.value,
                    metadata={"task_count": len(task_graph.tasks)},
                )
            )

            # Persist TaskGraph as artifact
            workspace_path = self.workspace_manager.workspace_root / session_id
            artifact_store = ArtifactStore(str(workspace_path / "artifacts"))
            artifact_store.save_artifact("task_graph.json", task_graph_dict)
            session.add_log("TaskGraph persisted to artifacts/task_graph.json")

            # Remain in PLAN_REVIEW phase (waiting for user approval)
            session.add_log("Awaiting plan approval from user...")

            # Update session
            self.session_store.update_session(session)

            return task_graph_dict

        except Exception as e:
            # Record error and re-raise
            session.add_error(
                task_id="plan_generation",
                error_message=f"Plan generation failed: {str(e)}",
            )
            self.session_store.update_session(session)
            raise RuntimeError(f"Failed to generate plan: {str(e)}") from e

    def get_plan_summary(self, session_id: str) -> dict[str, Any]:
        """Get a user-friendly summary of the generated plan.

        Formats TaskGraph into a simple structure for UI display.

        Args:
            session_id: ID of the session

        Returns:
            dict: Plan summary with task_count, task_list, etc.

        Raises:
            ValueError: If session not found, wrong phase, or plan missing
        """
        session = self._get_session_or_raise(session_id)

        # Validate phase
        if session.phase != SessionPhase.PLAN_REVIEW:
            raise ValueError(
                f"Cannot get plan summary: session {session_id} is in phase {session.phase.value}, "
                f"expected {SessionPhase.PLAN_REVIEW.value}"
            )

        # Ensure TaskGraph exists
        if not session.task_graph:
            raise ValueError(f"TaskGraph missing for session {session_id}")

        # Create TaskGraph object from dict for easier access
        task_graph = TaskGraph.from_dict(session_id, session.task_graph)

        # Extract summary information
        summary = {
            "task_count": len(task_graph.tasks),
            "task_list": [
                {"task_id": t.task_id, "description": t.description, "role": t.role}
                for t in task_graph.tasks
            ],
            "verification_steps": list(set(t.verification.get("type", "manual") for t in task_graph.tasks)),
            "estimated_scope": {
                "max_files": session.build_spec.get("scopeBudget", {}).get("maxTotalFiles", "unknown"),
                "max_screens": session.build_spec.get("scopeBudget", {}).get("maxScreens", "unknown"),
            },
            "constraints": {
                "stack": session.build_spec.get("stack", {}).get("preset", "unknown"),
                "platform": session.build_spec.get("target", {}).get("platform", "unknown"),
            },
        }

        return summary

    def approve_plan(self, session_id: str) -> dict[str, str]:
        """Approve the plan and transition to EXECUTION phase.

        Args:
            session_id: ID of the session

        Returns:
            dict: Confirmation message

        Raises:
            ValueError: If session not found, wrong phase, or plan missing
        """
        session = self._get_session_or_raise(session_id)

        # Validate phase
        if session.phase != SessionPhase.PLAN_REVIEW:
            raise ValueError(
                f"Cannot approve plan: session {session_id} is in phase {session.phase.value}, "
                f"expected {SessionPhase.PLAN_REVIEW.value}"
            )

        # Ensure TaskGraph exists
        if not session.task_graph:
            raise ValueError(f"TaskGraph missing for session {session_id}")

        # Transition to EXECUTION phase
        self._transition_phase(session, SessionPhase.EXECUTION, "Plan approved")
        session.add_log("Plan approved by user")
        session.add_log(f"Phase transition: PLAN_REVIEW → EXECUTION")
        self._emit_event(
            Event(
                event_type=EventType.PLAN_APPROVED,
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
                message="Plan approved by user",
                phase=session.phase.value,
            )
        )

        # Update session
        self.session_store.update_session(session)

        return {"status": "approved", "message": "Plan approved, ready for execution"}

    def reject_plan(self, session_id: str, reason: str = "User rejected plan") -> dict[str, str]:
        """Reject the plan and transition back to IDEA phase for regeneration.

        Args:
            session_id: ID of the session
            reason: Reason for rejection (for logging)

        Returns:
            dict: Confirmation message

        Raises:
            ValueError: If session not found or wrong phase
        """
        session = self._get_session_or_raise(session_id)

        # Validate phase
        if session.phase != SessionPhase.PLAN_REVIEW:
            raise ValueError(
                f"Cannot reject plan: session {session_id} is in phase {session.phase.value}, "
                f"expected {SessionPhase.PLAN_REVIEW.value}"
            )

        # Clear TaskGraph to force regeneration
        session.task_graph = None

        # Transition back to IDEA phase
        self._transition_phase(session, SessionPhase.IDEA, reason)
        session.add_log(f"Plan rejected by user: {reason}")
        session.add_log(f"Phase transition: PLAN_REVIEW → IDEA (for regeneration)")
        self._emit_event(
            Event(
                event_type=EventType.PLAN_REJECTED,
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
                message=f"Plan rejected: {reason}",
                phase=session.phase.value,
            )
        )

        # Update session
        self.session_store.update_session(session)

        return {"status": "rejected", "message": "Plan rejected, returning to concept stage"}

    # =========================================================================
    # VF-037: executeNextTask() loop
    # =========================================================================

    async def execute_next_task(self, session_id: str) -> dict[str, Any]:
        """Execute the next ready task from the TaskGraph.

        This orchestrates the full execution loop:
        1. Schedule next ready task (TaskMaster)
        2. Route to agent role (Distributor)
        3. Execute via agent (AgentFramework)
        4. Gate the result (PolicyGate, DiffAndCommandGate)
        5. Apply diff (PatchApplier)
        6. Verify (VerifierSuite)
        7. Mark done/failed (TaskMaster)

        Args:
            session_id: ID of the session

        Returns:
            dict: Execution result with status and details

        Raises:
            ValueError: If session not found, wrong phase, or agent framework missing
            RuntimeError: If task execution fails unrecoverably
        """
        session = self._get_session_or_raise(session_id)

        # Validate phase
        if session.phase != SessionPhase.EXECUTION:
            raise ValueError(
                f"Cannot execute task: session {session_id} is in phase {session.phase.value}, "
                f"expected {SessionPhase.EXECUTION.value}"
            )

        # Ensure agent framework is configured
        if not self.agent_framework:
            raise ValueError("AgentFramework not configured for task execution")

        # Get or create TaskMaster for this session
        if session_id not in self._task_masters:
            # First execution - enqueue TaskGraph
            if not session.task_graph:
                raise ValueError(f"TaskGraph missing for session {session_id}")

            task_graph = TaskGraph.from_dict(session_id, session.task_graph)
            task_master = TaskMaster(max_retries=2)
            task_master.enqueue(task_graph)
            self._task_masters[session_id] = task_master
            session.add_log("TaskGraph enqueued for execution")
            self._emit_event(
                Event(
                    event_type=EventType.INFO,
                    timestamp=datetime.now(timezone.utc),
                    session_id=session_id,
                    message="TaskGraph enqueued for execution",
                    phase=session.phase.value,
                )
            )

        task_master = self._task_masters[session_id]

        # Schedule next ready task
        task = task_master.scheduleNext()

        if not task:
            # No ready tasks - check if execution complete
            status = task_master.get_status()
            if status["completed"] == status["total_tasks"]:
                session.add_log("All tasks complete - ready for finalization")
                return {
                    "status": "all_tasks_complete",
                    "message": "All tasks complete, call finalize_session()",
                }
            else:
                # Tasks blocked by failures
                return {
                    "status": "blocked",
                    "message": "No ready tasks - execution blocked by failures",
                    "task_status": status,
                }

        session.add_log(f"Executing task: {task.task_id} ({task.description})")
        session.active_task_id = task.task_id

        try:
            # Get failure count for escalation
            exec_state = task_master.executions[task.task_id]
            failure_count = exec_state.attempts - 1  # attempts includes current run

            # Route task to agent role
            agent_role = self.distributor.route(task, failure_count)
            session.add_log(
                f"Task routed to {agent_role.role} ({agent_role.model_tier}): {agent_role.reason}"
            )

            self._emit_event(
                Event(
                    event_type=EventType.MODEL_ROUTED,
                    timestamp=datetime.now(timezone.utc),
                    session_id=session_id,
                    message=f"Task routed to {agent_role.role} ({agent_role.model_tier})",
                    phase=session.phase.value,
                    task_id=task.task_id,
                    metadata={
                        "agent_role": agent_role.role,
                        "model_tier": agent_role.model_tier,
                        "routing_reason": agent_role.reason,
                        "failure_count": failure_count,
                        "task_description": task.description,
                    },
                )
            )

            self._emit_event(
                Event(
                    event_type=EventType.TASK_STARTED,
                    timestamp=datetime.now(timezone.utc),
                    session_id=session_id,
                    message=f"Executing task {task.task_id}",
                    phase=session.phase.value,
                    task_id=task.task_id,
                    metadata={
                        "description": task.description,
                        "agent_role": agent_role.role,
                        "model_tier": agent_role.model_tier,
                    },
                )
            )

            self._emit_event(
                Event(
                    event_type=EventType.AGENT_INVOKED,
                    timestamp=datetime.now(timezone.utc),
                    session_id=session_id,
                    message=f"Agent {agent_role.role} invoked for task {task.task_id}",
                    phase=session.phase.value,
                    task_id=task.task_id,
                    metadata={
                        "agent_role": agent_role.role,
                        "model_tier": agent_role.model_tier,
                        "routing_reason": agent_role.reason,
                        "failure_count": failure_count,
                        "task_description": task.description,
                    },
                )
            )

            # Prepare execution context
            workspace_path = self.workspace_manager.workspace_root / session_id
            context = {
                "session_id": session_id,
                "workspace_path": str(workspace_path / "repo"),
                "artifacts_path": str(workspace_path / "artifacts"),
                "build_spec": session.build_spec,
                "concept": session.concept,
            }

            # Execute task via agent
            session.add_log(f"Calling agent to execute task...")
            agent_result: AgentResult = await self.agent_framework.runTask(
                task, agent_role.role, context
            )

            if agent_result.request:
                system_message = ""
                user_prompt = ""
                for message in agent_result.request.messages:
                    if message.role == "system" and not system_message:
                        system_message = message.content
                    elif message.role == "user" and not user_prompt:
                        user_prompt = message.content

                self._emit_event(
                    Event(
                        event_type=EventType.LLM_REQUEST_SENT,
                        timestamp=datetime.now(timezone.utc),
                        session_id=session_id,
                        message=f"LLM request sent for task {task.task_id}",
                        phase=session.phase.value,
                        task_id=task.task_id,
                        metadata={
                            "agent_role": agent_role.role,
                            "model": agent_result.request.model,
                            "prompt": user_prompt,
                            "system_message": system_message,
                            "max_tokens": agent_result.request.max_tokens,
                            "temperature": agent_result.request.temperature,
                        },
                    )
                )

            if agent_result.usage:
                self._emit_event(
                    Event(
                        event_type=EventType.LLM_RESPONSE_RECEIVED,
                        timestamp=datetime.now(timezone.utc),
                        session_id=session_id,
                        message=f"LLM response received for task {task.task_id}",
                        phase=session.phase.value,
                        task_id=task.task_id,
                        metadata={
                            "agent_role": agent_role.role,
                            "model": agent_result.outputs.get("model"),
                            "prompt_tokens": agent_result.usage.prompt_tokens,
                            "completion_tokens": agent_result.usage.completion_tokens,
                            "total_tokens": agent_result.usage.total_tokens,
                        },
                    )
                )

            if not agent_result.success:
                # Agent failed to produce result
                error_msg = agent_result.error_message or "Agent execution failed"
                session.add_log(f"Agent execution failed: {error_msg}")
                session.add_error(task_id=task.task_id, error_message=error_msg)
                self._emit_event(
                    Event(
                        event_type=EventType.TASK_FAILED,
                        timestamp=datetime.now(timezone.utc),
                        session_id=session_id,
                        message=error_msg,
                        phase=session.phase.value,
                        task_id=task.task_id,
                        metadata={"agent_role": agent_role.role},
                    )
                )

                self._emit_event(
                    Event(
                        event_type=EventType.AGENT_COMPLETED,
                        timestamp=datetime.now(timezone.utc),
                        session_id=session_id,
                        message=f"Agent {agent_role.role} failed task {task.task_id}",
                        phase=session.phase.value,
                        task_id=task.task_id,
                        metadata={
                            "agent_role": agent_role.role,
                            "model_tier": agent_role.model_tier,
                            "success": False,
                        },
                    )
                )

                # Mark failed (retry or terminal failure)
                should_retry = task_master.markFailed(task.task_id, error_msg)
                self.session_store.update_session(session)

                if should_retry:
                    return {
                        "status": "task_failed_retrying",
                        "task_id": task.task_id,
                        "error": error_msg,
                        "attempts": exec_state.attempts,
                    }
                else:
                    return {
                        "status": "task_failed_terminal",
                        "task_id": task.task_id,
                        "error": error_msg,
                    }

            # Agent succeeded - validate and apply outputs
            session.add_log(f"Agent produced result: {len(agent_result.outputs)} outputs")

            # Gate the agent result
            gate_context = GateContext(
                build_spec=session.build_spec,
                proposed_diff=agent_result.outputs.get("diff", ""),
                proposed_commands=agent_result.outputs.get("commands", []),
                task_data=task.constraints,
            )

            # Create gate pipeline
            gates = GatePipeline([PolicyGate(), DiffAndCommandGate()])

            gate_result, gate_results = gates.evaluate_with_results(gate_context)

            for gate, result in gate_results:
                self._emit_event(
                    Event(
                        event_type=EventType.GATE_EVALUATED,
                        timestamp=datetime.now(timezone.utc),
                        session_id=session_id,
                        message=result.message,
                        phase=session.phase.value,
                        task_id=task.task_id,
                        metadata={
                            "gate_name": gate.__class__.__name__,
                            "status": result.status.value,
                            "details": result.details or {},
                        },
                    )
                )

            # Import enum for comparison
            from vibeforge_api.models.types import GateResultStatus

            if gate_result.status == GateResultStatus.BLOCK:
                # Gates blocked
                error_msg = f"Gates blocked: {gate_result.message}"
                session.add_log(error_msg)
                session.add_error(task_id=task.task_id, error_message=error_msg)

                should_retry = task_master.markFailed(task.task_id, error_msg)
                self.session_store.update_session(session)

                if should_retry:
                    return {
                        "status": "task_failed_retrying",
                        "task_id": task.task_id,
                        "error": error_msg,
                        "gate_message": gate_result.message,
                    }
                else:
                    return {
                        "status": "task_failed_terminal",
                        "task_id": task.task_id,
                        "error": error_msg,
                    }

            # Apply diff if present
            if "diff" in agent_result.outputs and agent_result.outputs["diff"]:
                session.add_log("Applying diff to workspace...")
                patch_applier = PatchApplier(str(workspace_path / "repo"))

                try:
                    patch_applier.apply_patch(agent_result.outputs["diff"])
                    session.add_log("Diff applied successfully")
                except Exception as e:
                    error_msg = f"Patch apply failed: {str(e)}"
                    session.add_log(error_msg)
                    session.add_error(task_id=task.task_id, error_message=error_msg)

                    should_retry = task_master.markFailed(task.task_id, error_msg)
                    self.session_store.update_session(session)

                    if should_retry:
                        return {
                            "status": "task_failed_retrying",
                            "task_id": task.task_id,
                            "error": error_msg,
                        }
                    else:
                        return {
                            "status": "task_failed_terminal",
                            "task_id": task.task_id,
                            "error": error_msg,
                        }

            # Run task verification
            if task.verification and task.verification.get("type") != "manual":
                verification_type = task.verification.get("type", "unknown")
                session.add_log(f"Running verification: {verification_type}")

                verifier_suite = VerifierSuite()

                # Run task-specific verification (convert type to list of verifier names)
                verifier_names = [verification_type] if verification_type != "unknown" else []
                verification_results = verifier_suite.run_task_verification(
                    verifier_names, workspace_path, session.build_spec
                )

                # Check if all verifications passed
                all_passed = all(result.success for result in verification_results)

                if not all_passed:
                    failed_messages = [
                        result.message for result in verification_results if not result.success
                    ]
                    error_msg = f"Verification failed: {'; '.join(failed_messages)}"
                    session.add_log(error_msg)
                    session.add_error(task_id=task.task_id, error_message=error_msg)

                    should_retry = task_master.markFailed(task.task_id, error_msg)
                    self.session_store.update_session(session)

                    if should_retry:
                        return {
                            "status": "task_failed_retrying",
                            "task_id": task.task_id,
                            "error": error_msg,
                            "verification": verification_result,
                        }
                    else:
                        return {
                            "status": "task_failed_terminal",
                            "task_id": task.task_id,
                            "error": error_msg,
                        }

                session.add_log("Verification passed")

            # Task completed successfully
            task_master.markDone(task.task_id, result=agent_result.to_dict())
            session.completed_task_ids.append(task.task_id)
            session.active_task_id = None
            session.add_log(f"Task {task.task_id} completed successfully")
            self._emit_event(
                Event(
                    event_type=EventType.AGENT_COMPLETED,
                    timestamp=datetime.now(timezone.utc),
                    session_id=session_id,
                    message=f"Agent {agent_role.role} completed task {task.task_id}",
                    phase=session.phase.value,
                    task_id=task.task_id,
                    metadata={
                        "agent_role": agent_role.role,
                        "model_tier": agent_role.model_tier,
                        "success": True,
                        "model": agent_result.outputs.get("model"),
                    },
                )
            )
            self._emit_event(
                Event(
                    event_type=EventType.TASK_COMPLETED,
                    timestamp=datetime.now(timezone.utc),
                    session_id=session_id,
                    message=f"Task {task.task_id} completed successfully",
                    phase=session.phase.value,
                    task_id=task.task_id,
                    metadata={"agent_role": agent_role.role},
                )
            )

            # Persist agent result as artifact
            artifact_store = ArtifactStore(str(workspace_path / "artifacts"))
            artifact_store.save_artifact(f"task_{task.task_id}_result.json", agent_result.to_dict())

            self.session_store.update_session(session)

            return {
                "status": "task_complete",
                "task_id": task.task_id,
                "outputs": agent_result.outputs,
            }

        except Exception as e:
            # Unhandled error
            error_msg = f"Unexpected error executing task {task.task_id}: {str(e)}"
            session.add_log(error_msg)
            session.add_error(task_id=task.task_id, error_message=error_msg)

            task_master.markFailed(task.task_id, error_msg)
            self.session_store.update_session(session)

            raise RuntimeError(error_msg) from e

    # =========================================================================
    # VF-038: finalize() global verification + summary
    # =========================================================================

    async def finalize_session(self, session_id: str) -> dict[str, Any]:
        """Finalize session with global verification and summary generation.

        Runs global verification suite (build + test) and requests final
        summary from Orchestrator. Transitions to COMPLETE on success.

        Args:
            session_id: ID of the session

        Returns:
            dict: RunSummary with status, summary, files, run_instructions

        Raises:
            ValueError: If session not found, wrong phase, or tasks incomplete
            RuntimeError: If global verification fails
        """
        session = self._get_session_or_raise(session_id)

        # Validate phase
        if session.phase != SessionPhase.EXECUTION:
            raise ValueError(
                f"Cannot finalize: session {session_id} is in phase {session.phase.value}, "
                f"expected {SessionPhase.EXECUTION.value}"
            )

        # Check TaskMaster status
        if session_id not in self._task_masters:
            raise ValueError("No TaskMaster found - execution not started")

        task_master = self._task_masters[session_id]
        status = task_master.get_status()

        if status["completed"] != status["total_tasks"]:
            raise ValueError(
                f"Cannot finalize: tasks incomplete ({status['completed']}/{status['total_tasks']} done)"
            )

        session.add_log("Starting global verification...")

        # Run global verification
        workspace_path = self.workspace_manager.workspace_root / session_id
        verifier_suite = VerifierSuite()

        verification_results = verifier_suite.run_global_verification(workspace_path, session.build_spec)

        # Check if verification passed (verification_results is list[VerificationResult])
        all_passed = all(result.success for result in verification_results)

        if not all_passed:
            # Global verification failed
            failed_steps = [
                result.message for result in verification_results if not result.success
            ]
            error_msg = f"Global verification failed: {'; '.join(failed_steps)}"
            session.add_log(error_msg)
            session.add_error(task_id="global_verification", error_message=error_msg)
            self.session_store.update_session(session)

            raise RuntimeError(
                f"Global verification failed: {failed_steps}. "
                f"Results: {verification_results}"
            )

        session.add_log("Global verification passed")

        # Request summary from Orchestrator
        session.add_log("Generating final summary from Orchestrator...")

        # Prepare artifacts for summary (convert VerificationResult objects to dicts)
        from dataclasses import asdict

        verification_results_dict = [asdict(result) for result in verification_results]

        artifact_store = ArtifactStore(str(workspace_path / "artifacts"))
        artifacts = {
            "build_spec": session.build_spec,
            "concept": session.concept,
            "task_graph": session.task_graph,
            "verification_results": verification_results_dict,
            "completed_tasks": session.completed_task_ids,
        }

        try:
            run_summary: RunSummary = await self.orchestrator.summarize(artifacts)
            summary_dict = run_summary.to_dict()

            # Persist RunSummary
            artifact_store.save_artifact("run_summary.json", summary_dict)
            session.add_log("RunSummary generated and persisted")

            # Transition to COMPLETE
            self._transition_phase(session, SessionPhase.COMPLETE, "Execution complete")
            session.add_log("Phase transition: EXECUTION → COMPLETE")

            self.session_store.update_session(session)

            return summary_dict

        except Exception as e:
            # Orchestrator summary failed - generate fallback
            session.add_log(f"Orchestrator summarize failed: {str(e)}, using fallback")

            fallback_summary = {
                "status": "complete",
                "summary": f"Session completed with {len(session.completed_task_ids)} tasks",
                "files_generated": [],
                "verification_results": verification_results_dict,
                "how_to_run": ["See build_spec.json for stack-specific run commands"],
                "limitations": ["Orchestrator summary generation failed"],
            }

            artifact_store.save_artifact("run_summary.json", fallback_summary)

            # Transition to COMPLETE anyway
            self._transition_phase(session, SessionPhase.COMPLETE, "Execution complete")
            session.add_log("Phase transition: EXECUTION → COMPLETE (with fallback summary)")

            self.session_store.update_session(session)

            return fallback_summary

    # =========================================================================
    # VF-039: abort/reset session flows
    # =========================================================================

    def abort_session(self, session_id: str, reason: str = "User aborted") -> dict[str, str]:
        """Abort session and preserve artifacts.

        Safely stops execution and transitions to terminal state.
        Can be called from any non-terminal phase.

        Args:
            session_id: ID of the session
            reason: Reason for abort (for logging)

        Returns:
            dict: Confirmation with preserved artifacts location

        Raises:
            ValueError: If session not found or already in terminal state
        """
        session = self._get_session_or_raise(session_id)

        # Check if already in terminal state
        terminal_states = {SessionPhase.COMPLETE, SessionPhase.FAILED}
        if session.phase in terminal_states:
            raise ValueError(
                f"Cannot abort: session {session_id} already in terminal state {session.phase.value}"
            )

        # Stop running task if any
        if session.active_task_id:
            session.add_log(f"Aborting active task: {session.active_task_id}")
            if session_id in self._task_masters:
                task_master = self._task_masters[session_id]
                task_master.markFailed(
                    session.active_task_id, f"Aborted by user: {reason}"
                )
            session.active_task_id = None

        # Log abort
        session.add_log(f"Session aborted: {reason}")
        session.add_error(task_id="session", error_message=f"Aborted: {reason}")

        # Preserve current phase for reference
        # Transition to FAILED (using FAILED to indicate aborted state)
        old_phase = session.phase
        self._transition_phase(session, SessionPhase.FAILED, reason)
        session.add_log(f"Phase transition: {old_phase.value} → FAILED (aborted)")

        # Update session
        self.session_store.update_session(session)

        workspace_path = self.workspace_manager.workspace_root / session_id

        return {
            "status": "aborted",
            "message": f"Session aborted: {reason}",
            "artifacts_preserved": str(workspace_path / "artifacts"),
            "workspace_preserved": str(workspace_path / "repo"),
        }

    # =========================================================================
    # Helper methods
    # =========================================================================

    def _get_session_or_raise(self, session_id: str) -> Session:
        """Retrieve session or raise ValueError if not found.

        Args:
            session_id: ID of the session

        Returns:
            Session: The session object

        Raises:
            ValueError: If session not found
        """
        session = self.session_store.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        return session
