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
from uuid import uuid4

from apps.api.vibeforge_api.core.session import Session, SessionStoreInterface
from apps.api.vibeforge_api.core.workspace import WorkspaceManager
from apps.api.vibeforge_api.core.questionnaire import QuestionnaireEngine
from apps.api.vibeforge_api.core.spec_builder import SpecBuilder
from apps.api.vibeforge_api.core.artifacts import ArtifactStore
from apps.api.vibeforge_api.core.event_log import (
    Event,
    EventLog,
    EventType,
    create_phase_transition_event,
)
from apps.api.vibeforge_api.core.patch import PatchApplier
from apps.api.vibeforge_api.core.gates import GatePipeline, DiffAndCommandGate, PolicyGate, GateContext
from apps.api.vibeforge_api.core.verifiers import VerifierSuite
from apps.api.vibeforge_api.models.types import SessionPhase
from orchestration.orchestrator import Orchestrator
from orchestration.models import ConceptDoc, TaskGraph, RunSummary
from orchestration.context_loader import RepoContextLoader, DEFAULT_CONTEXT_BUDGET_BYTES
from runtime.task_master import TaskMaster
from runtime.distributor import Distributor
from models.agent_framework import AgentFramework, AgentResult
from orchestration.coordinator.state_machine import (
    validate_transition,
    validate_phase_transition,
    is_valid_transition,
    get_entry_action,
    check_exit_criteria,
    TransitionError,
    ExitCriteriaNotMet,
    # VF-164: Fix loop guardrails
    can_return_to_execution,
    validate_fix_loop_transition,
)


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

    def get_agent_config(self, session: Session, agent_id: str) -> Optional[dict]:
        """Get configuration for a specific agent (VF-194).

        Args:
            session: Session with agent configuration
            agent_id: Agent identifier

        Returns:
            Agent config dict if found, None otherwise
        """
        for agent in session.agents:
            if agent.get("agent_id") == agent_id:
                return agent
        return None

    def get_forced_model(self, session: Session, agent_id: str) -> Optional[str]:
        """Get forced model for agent if configured (VF-194).

        Args:
            session: Session with agent model mappings
            agent_id: Agent identifier

        Returns:
            Model name/ID if configured, None otherwise
        """
        return session.agent_models.get(agent_id)

    def get_agent_for_role(self, session: Session, role: str) -> Optional[str]:
        """Find agent ID assigned to the given role (VF-194).

        Args:
            session: Session with agent role mappings
            role: Role name (e.g., "worker", "reviewer")

        Returns:
            Agent ID if found, None otherwise
        """
        for agent_id, assigned_role in session.agent_roles.items():
            if assigned_role == role:
                return agent_id
        return None

    def is_workflow_configured(self, session: Session) -> bool:
        """Check if simulation workflow is configured (VF-194).

        Args:
            session: Session to check

        Returns:
            True if workflow configured (agents, roles, main_task set)
        """
        return (
            len(session.agents) > 0
            and len(session.agent_roles) > 0
            and session.main_task is not None
        )

    def _transition_phase(
        self,
        session: Session,
        new_phase: SessionPhase,
        reason: str,
        skip_exit_check: bool = False,
    ) -> None:
        """Transition session phase with validation and emit a phase transition event.

        This method enforces the state machine rules (VF-160, VF-161, VF-162):
        1. Validates that the transition is allowed
        2. Checks exit criteria for current phase (unless skip_exit_check=True)
        3. Updates session phase
        4. Emits phase transition event

        Args:
            session: Session to transition
            new_phase: Target phase
            reason: Human-readable reason for transition
            skip_exit_check: Skip exit criteria validation (for error recovery paths)

        Raises:
            TransitionError: If the transition is not allowed
            ExitCriteriaNotMet: If exit criteria for current phase are not met
        """
        old_phase = session.phase

        # VF-160: Validate transition is allowed
        # VF-162: Check exit criteria (skip for FAILED transitions - error recovery)
        if new_phase == SessionPhase.FAILED:
            # Always allow transition to FAILED (error recovery)
            validate_transition(old_phase, new_phase)
        elif not skip_exit_check:
            # Full validation: exit criteria + transition rules
            validate_phase_transition(session, old_phase, new_phase, skip_exit_check=False)
        else:
            # Skip exit check but still validate transition
            validate_transition(old_phase, new_phase)

        # Perform the transition
        session.update_phase(new_phase)

        # Emit phase transition event
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

    def get_next_question(self, session_id: str) -> Optional[dict]:
        """Get the next questionnaire question for a session.

        Args:
            session_id: ID of the session

        Returns:
            dict with next question, or None if questionnaire complete

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

        # Persist IntentProfile as artifact
        workspace_path = self.workspace_manager.workspace_root / session_id
        artifact_store = ArtifactStore(str(workspace_path / "artifacts"))
        artifact_store.save_artifact("intent_profile.json", intent_profile)
        session.add_log("IntentProfile persisted to artifacts/intent_profile.json")

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

        concept_doc = (
            ConceptDoc.from_dict(session_id, session.concept)
            if isinstance(session.concept, dict)
            else session.concept
        )

        try:
            # Call Orchestrator to generate TaskGraph
            session.add_log("Generating TaskGraph from concept...")
            task_graph: TaskGraph = await self.orchestrator.createTaskGraph(
                session.build_spec, concept_doc
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

        # Transition back to IDEA phase (skip exit check since we intentionally cleared task_graph)
        self._transition_phase(session, SessionPhase.IDEA, reason, skip_exit_check=True)
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

    def _queue_fix_loop_clarification(
        self, session: Session, task_id: str, error_message: str, failure_kind: str
    ) -> dict[str, Any]:
        """Create a clarification prompt for fix-loop decisions after failures."""
        clarification = {
            "question": (
                "Verification failed multiple times. Choose how to proceed with the fix loop."
            ),
            "options": [
                {"value": "retry_with_fixer", "label": "Retry with fixer"},
                {"value": "abort_task", "label": "Stop and review failure"},
            ],
            "context": {
                "task_id": task_id,
                "failure_kind": failure_kind,
                "error_message": error_message,
            },
            "task_id": task_id,
            "type": "fix_loop",
        }
        session.pending_clarification = clarification
        session.clarification_answer = None
        session.clarification_context = {
            "type": "fix_loop",
            "task_id": task_id,
            "failure_kind": failure_kind,
            "error_message": error_message,
        }
        session.add_log(f"Fix loop clarification required for task {task_id}")
        self._transition_phase(
            session, SessionPhase.CLARIFICATION, "Fix loop clarification required"
        )
        session.add_log("Phase transition: EXECUTION → CLARIFICATION")
        self.session_store.update_session(session)
        return {
            "status": "needs_clarification",
            "task_id": task_id,
            "clarification": clarification,
        }

    def _apply_fix_loop_response(
        self, session: Session, task_master: TaskMaster
    ) -> Optional[dict[str, Any]]:
        """Apply a fix-loop clarification answer if present."""
        if not session.clarification_answer or not session.clarification_context:
            return None

        if session.clarification_context.get("type") != "fix_loop":
            return None

        task_id = session.clarification_context.get("task_id")
        error_message = session.clarification_context.get("error_message", "")
        answer = session.clarification_answer

        session.pending_clarification = None
        session.clarification_answer = None
        session.clarification_context = None

        if answer == "retry_with_fixer" and task_id:
            task_master.forceRetry(task_id, reset_attempts=True)
            session.add_log(f"User requested fix loop retry for task {task_id}")
            self.session_store.update_session(session)
            return None

        session.add_log(
            f"Fix loop stopped for task {task_id or 'unknown'}: {answer or 'no answer'}"
        )
        self.session_store.update_session(session)
        return {
            "status": "task_failed_terminal",
            "task_id": task_id,
            "error": error_message or "Task failed after verification retries",
        }

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

        if session.phase == SessionPhase.CLARIFICATION:
            if session.pending_clarification and not session.clarification_answer:
                return {
                    "status": "needs_clarification",
                    "clarification": session.pending_clarification,
                }
            if session.clarification_answer:
                self._transition_phase(
                    session,
                    SessionPhase.EXECUTION,
                    "Clarification provided; resuming execution",
                )
                session.add_log("Phase transition: CLARIFICATION → EXECUTION")
                self.session_store.update_session(session)

        # Validate phase
        if session.phase != SessionPhase.EXECUTION:
            raise ValueError(
                f"Cannot execute task: session {session_id} is in phase {session.phase.value}, "
                f"expected {SessionPhase.EXECUTION.value}"
            )

        if session.pending_clarification and not session.clarification_answer:
            if session.phase != SessionPhase.CLARIFICATION:
                self._transition_phase(
                    session,
                    SessionPhase.CLARIFICATION,
                    "Clarification required before execution can continue",
                )
                session.add_log("Phase transition: EXECUTION → CLARIFICATION")
                self.session_store.update_session(session)
            return {
                "status": "needs_clarification",
                "clarification": session.pending_clarification,
            }

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

        fix_loop_response = self._apply_fix_loop_response(session, task_master)
        if fix_loop_response:
            return fix_loop_response

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

            # VF-194: Get forced model for workflow simulation mode
            forced_model = None
            assigned_agent_id = None
            if self.is_workflow_configured(session):
                assigned_agent_id = self.get_agent_for_role(session, agent_role.role)
                if assigned_agent_id:
                    forced_model = self.get_forced_model(session, assigned_agent_id)

            # VF-194: Build metadata with workflow configuration
            agent_invoked_metadata = {
                "agent_role": agent_role.role,
                "model_tier": agent_role.model_tier,
                "routing_reason": agent_role.reason,
                "failure_count": failure_count,
                "task_description": task.description,
            }
            # VF-194: Add workflow metadata if configured
            if self.is_workflow_configured(session):
                agent_invoked_metadata["workflow_mode"] = "simulation"
                agent_invoked_metadata["main_task"] = session.main_task
                agent_invoked_metadata["configured_agents"] = len(session.agents)
            if assigned_agent_id:
                agent_invoked_metadata["agent_id"] = assigned_agent_id
            if forced_model:
                agent_invoked_metadata["forced_model"] = forced_model

            self._emit_event(
                Event(
                    event_type=EventType.AGENT_INVOKED,
                    timestamp=datetime.now(timezone.utc),
                    session_id=session_id,
                    message=f"Agent {agent_role.role} invoked for task {task.task_id}",
                    phase=session.phase.value,
                    task_id=task.task_id,
                    metadata=agent_invoked_metadata,
                )
            )

            # Prepare execution context
            workspace_path = self.workspace_manager.workspace_root / session_id
            files_to_read = task.inputs.get("filesToRead", []) if task.inputs else []
            context_notes = task.inputs.get("contextNotes", []) if task.inputs else []
            context_budget = DEFAULT_CONTEXT_BUDGET_BYTES
            if session.build_spec:
                context_budget = session.build_spec.get(
                    "contextBudget", DEFAULT_CONTEXT_BUDGET_BYTES
                )
            repo_context = RepoContextLoader.select_files(
                workspace_path / "repo",
                files_to_read,
                max_bytes=context_budget,
                context_notes=context_notes,
            )
            context = {
                "session_id": session_id,
                "workspace_path": str(workspace_path / "repo"),
                "artifacts_path": str(workspace_path / "artifacts"),
                "build_spec": session.build_spec,
                "concept": session.concept,
                "repo_context": repo_context,
            }
            # VF-194: Add workflow configuration to context
            if forced_model:
                context["forced_model"] = forced_model
            if assigned_agent_id:
                context["agent_id"] = assigned_agent_id
            if self.is_workflow_configured(session):
                context["workflow_mode"] = "simulation"
                context["main_task"] = session.main_task

            exec_state = task_master.executions.get(task.task_id)
            if exec_state and exec_state.error_message:
                context["previous_error"] = exec_state.error_message
                context["failure_count"] = max(exec_state.attempts - 1, 0)
            if session.clarification_answer:
                context["clarification_answer"] = session.clarification_answer

            # Execute task via agent
            session.add_log(f"Calling agent to execute task...")
            agent_result: AgentResult = await self.agent_framework.runTask(
                task, agent_role.role, context
            )

            request_id = None
            if agent_result.request:
                request_metadata = agent_result.request.metadata or {}
                request_id = request_metadata.get("request_id")
                if not request_id:
                    request_id = str(uuid4())
                    request_metadata["request_id"] = request_id
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
                            "request_id": request_id,
                            "operation": request_metadata.get("operation"),
                        },
                    )
                )

            if agent_result.usage or agent_result.outputs.get("response"):
                usage = agent_result.usage
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
                            "response": agent_result.outputs.get("response"),
                            "prompt_tokens": usage.prompt_tokens if usage else None,
                            "completion_tokens": usage.completion_tokens if usage else None,
                            "total_tokens": usage.total_tokens if usage else None,
                            "request_id": request_id,
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
                if not should_retry:
                    session.clarification_answer = None
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

            if agent_result.needs_clarification:
                clarification = agent_result.clarification or {}
                question = clarification.get(
                    "question", "Additional input required to proceed."
                )
                options = clarification.get(
                    "options",
                    [
                        {"value": "proceed", "label": "Proceed"},
                        {"value": "modify", "label": "Modify request"},
                        {"value": "cancel", "label": "Cancel task"},
                    ],
                )
                session.pending_clarification = {
                    "question": question,
                    "options": options,
                    "context": clarification.get("context"),
                    "task_id": task.task_id,
                }
                session.clarification_answer = None
                session.add_log(f"Task {task.task_id} requires clarification")
                task_master.markNeedsClarification(task.task_id)
                self._transition_phase(
                    session,
                    SessionPhase.CLARIFICATION,
                    f"Clarification required for task {task.task_id}",
                )
                session.add_log("Phase transition: EXECUTION → CLARIFICATION")
                self.session_store.update_session(session)
                return {
                    "status": "needs_clarification",
                    "task_id": task.task_id,
                    "clarification": session.pending_clarification,
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
            from apps.api.vibeforge_api.models.types import GateResultStatus

            if gate_result.status == GateResultStatus.BLOCK:
                # Gates blocked
                error_msg = f"Gates blocked: {gate_result.message}"
                session.add_log(error_msg)
                session.add_error(task_id=task.task_id, error_message=error_msg)

                should_retry = task_master.markFailed(task.task_id, error_msg)
                if not should_retry:
                    session.clarification_answer = None
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
                    if not should_retry:
                        session.clarification_answer = None
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
                    if not should_retry:
                        session.clarification_answer = None
                    self.session_store.update_session(session)

                    if should_retry:
                        return {
                            "status": "task_failed_retrying",
                            "task_id": task.task_id,
                            "error": error_msg,
                            "verification": verification_results,
                        }
                    else:
                        return self._queue_fix_loop_clarification(
                            session,
                            task.task_id,
                            error_msg,
                            "verification",
                        )

                session.add_log("Verification passed")

            # Task completed successfully
            task_master.markDone(task.task_id, result=agent_result.to_dict())
            session.completed_task_ids.append(task.task_id)
            session.active_task_id = None
            session.clarification_answer = None
            session.reset_fix_loop()  # VF-164: Reset fix loop counter on success
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
        repo_path = self.workspace_manager.get_repo_path(session_id)
        files_generated: list[str] = []
        if repo_path.exists():
            for file_path in repo_path.rglob("*"):
                if file_path.is_file():
                    files_generated.append(str(file_path.relative_to(repo_path)))

        completed_tasks = [
            {"task_id": task_id, "status": "completed"}
            for task_id in session.completed_task_ids
        ]
        verification_summary = {}
        for name, result in zip(["build", "test"], verification_results):
            status = "passed" if result.success else "failed"
            verification_summary[name] = f"{status}: {result.message}"

        try:
            run_summary: RunSummary = await self.orchestrator.summarize(
                session_id=session_id,
                files_generated=sorted(files_generated),
                completed_tasks=completed_tasks,
                verification_results=verification_summary,
            )
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

    def resume_execution(
        self, session_id: str, reason: str = "Clarification resolved"
    ) -> None:
        """Resume execution after clarification."""
        session = self._get_session_or_raise(session_id)
        old_phase = session.phase
        self._transition_phase(session, SessionPhase.EXECUTION, reason)
        session.add_log(f"Phase transition: {old_phase.value} → EXECUTION")
        self.session_store.update_session(session)

    def trigger_fix_loop(self, session_id: str, reason: str) -> dict[str, Any]:
        """Trigger a fix-loop return from VERIFICATION to EXECUTION (VF-164).

        This implements bounded fix-loop transitions with guardrails to prevent
        infinite verification-execution cycles.

        Args:
            session_id: ID of the session
            reason: Reason for the fix loop (e.g., verification failure)

        Returns:
            dict: Status of fix loop trigger

        Raises:
            ValueError: If session not found or wrong phase
            TransitionError: If fix loop limit exceeded
        """
        session = self._get_session_or_raise(session_id)

        # Validate we're in a state where fix-loop makes sense
        if session.phase not in {SessionPhase.VERIFICATION, SessionPhase.EXECUTION}:
            raise ValueError(
                f"Cannot trigger fix loop: session {session_id} is in phase {session.phase.value}, "
                f"expected VERIFICATION or EXECUTION"
            )

        # Check fix-loop guardrails (VF-164)
        can_loop, loop_reason = can_return_to_execution(session)

        if not can_loop:
            # Fix loop limit exceeded - fail the session
            session.add_log(f"Fix loop limit exceeded: {loop_reason}")
            return self.fail_session(
                session_id,
                f"Fix loop limit exceeded after {session.fix_loop_count} attempts: {reason}",
                task_id="fix_loop",
            )

        # Increment fix loop counter
        session.increment_fix_loop()
        session.add_log(f"Fix loop triggered ({session.fix_loop_count}/{session.max_fix_loops}): {reason}")

        # Emit fix loop event
        self._emit_event(
            Event(
                event_type=EventType.INFO,
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
                message=f"Fix loop triggered: {reason}",
                phase=session.phase.value,
                metadata={
                    "fix_loop_count": session.fix_loop_count,
                    "max_fix_loops": session.max_fix_loops,
                    "reason": reason,
                },
            )
        )

        # Transition back to EXECUTION if we were in VERIFICATION
        old_phase = session.phase
        if old_phase == SessionPhase.VERIFICATION:
            self._transition_phase(session, SessionPhase.EXECUTION, f"Fix loop: {reason}")
            session.add_log(f"Phase transition: VERIFICATION → EXECUTION (fix loop)")

        self.session_store.update_session(session)

        return {
            "status": "fix_loop_triggered",
            "fix_loop_count": session.fix_loop_count,
            "max_fix_loops": session.max_fix_loops,
            "reason": reason,
        }

    def fail_session(self, session_id: str, reason: str, task_id: str = "session") -> dict[str, Any]:
        """Transition a session to FAILED with a reason (VF-163).

        Creates a failure artifact with error details and recovery options.

        Args:
            session_id: ID of the session
            reason: Reason for failure
            task_id: ID of the task that caused failure (default: "session")

        Returns:
            dict: Failure details with recovery options
        """
        session = self._get_session_or_raise(session_id)
        old_phase = session.phase

        # Record the error
        session.add_error(task_id=task_id, error_message=reason)
        session.failure_reason = reason
        session.active_task_id = None
        session.pending_clarification = None

        # Create failure artifact (VF-163)
        failure_artifact = {
            "session_id": session_id,
            "failure_reason": reason,
            "failure_task_id": task_id,
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "phase_at_failure": old_phase.value,
            "error_history": session.error_history,
            "completed_tasks": session.completed_task_ids,
            "failed_tasks": session.failed_task_ids,
            "fix_loop_count": session.fix_loop_count,
        }
        session.failure_artifact = failure_artifact

        # Persist failure artifact
        try:
            workspace_path = self.workspace_manager.workspace_root / session_id
            artifact_store = ArtifactStore(str(workspace_path / "artifacts"))
            artifact_store.save_artifact("failure_report.json", failure_artifact)
            session.add_log("Failure artifact persisted to artifacts/failure_report.json")
        except Exception as e:
            session.add_log(f"Failed to persist failure artifact: {str(e)}")

        # Emit failure event
        self._emit_event(
            Event(
                event_type=EventType.SESSION_FAILED,
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
                message=f"Session failed: {reason}",
                phase=old_phase.value,
                task_id=task_id,
                metadata={
                    "failure_reason": reason,
                    "error_count": len(session.error_history),
                },
            )
        )

        # Transition to FAILED
        self._transition_phase(session, SessionPhase.FAILED, reason)
        session.add_log(f"Phase transition: {old_phase.value} → FAILED")

        self.session_store.update_session(session)

        # Return failure details with recovery options (VF-163)
        return {
            "status": "failed",
            "reason": reason,
            "task_id": task_id,
            "failure_artifact": failure_artifact,
            "recovery_options": session.get_recovery_options(),
            "artifacts_location": str(self.workspace_manager.workspace_root / session_id / "artifacts"),
        }

    def abort_session(self, session_id: str, reason: str = "User aborted") -> dict[str, Any]:
        """Abort session and preserve artifacts (VF-165).

        Safely stops execution, cleans up resources, and transitions to terminal state.
        Can be called from any non-terminal phase.

        Args:
            session_id: ID of the session
            reason: Reason for abort (for logging)

        Returns:
            dict: Confirmation with preserved artifacts location and recovery options

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

        old_phase = session.phase

        # Mark session as aborted (VF-165)
        session.is_aborted = True
        session.abort_reason = reason

        # Stop running task if any
        if session.active_task_id:
            session.add_log(f"Aborting active task: {session.active_task_id}")
            if session_id in self._task_masters:
                task_master = self._task_masters[session_id]
                try:
                    task_master.markFailed(
                        session.active_task_id, f"Aborted by user: {reason}"
                    )
                except Exception as e:
                    session.add_log(f"Warning: failed to mark task as failed: {str(e)}")
            session.active_task_id = None

        # Clear any pending clarification
        session.pending_clarification = None
        session.clarification_answer = None
        session.clarification_context = None

        # Log abort
        session.add_log(f"Session aborted: {reason}")
        session.add_error(task_id="session", error_message=f"Aborted: {reason}")

        # Create abort artifact (similar to failure artifact but marked as abort)
        abort_artifact = {
            "session_id": session_id,
            "abort_reason": reason,
            "aborted_at": datetime.now(timezone.utc).isoformat(),
            "phase_at_abort": old_phase.value,
            "completed_tasks": session.completed_task_ids,
            "failed_tasks": session.failed_task_ids,
            "active_task_at_abort": session.active_task_id,
            "is_user_initiated": True,
        }
        session.failure_artifact = abort_artifact
        session.failure_reason = f"Aborted: {reason}"

        # Persist abort artifact
        workspace_path = self.workspace_manager.workspace_root / session_id
        try:
            artifact_store = ArtifactStore(str(workspace_path / "artifacts"))
            artifact_store.save_artifact("abort_report.json", abort_artifact)
            session.add_log("Abort artifact persisted to artifacts/abort_report.json")
        except Exception as e:
            session.add_log(f"Warning: failed to persist abort artifact: {str(e)}")

        # Emit abort event
        self._emit_event(
            Event(
                event_type=EventType.SESSION_ABORTED,
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
                message=f"Session aborted: {reason}",
                phase=old_phase.value,
                metadata={
                    "abort_reason": reason,
                    "phase_at_abort": old_phase.value,
                    "completed_task_count": len(session.completed_task_ids),
                },
            )
        )

        # Transition to FAILED (using FAILED to indicate aborted state)
        self._transition_phase(session, SessionPhase.FAILED, f"Aborted: {reason}")
        session.add_log(f"Phase transition: {old_phase.value} → FAILED (aborted)")

        # Update session
        self.session_store.update_session(session)

        return {
            "status": "aborted",
            "message": f"Session aborted: {reason}",
            "abort_artifact": abort_artifact,
            "recovery_options": session.get_recovery_options(),
            "artifacts_preserved": str(workspace_path / "artifacts"),
            "workspace_preserved": str(workspace_path / "repo"),
        }

    # =========================================================================
    # VF-167: Session persistence and resume
    # =========================================================================

    def save_session_state(self, session_id: str) -> dict[str, Any]:
        """Save session state to artifacts for later resume (VF-167).

        Persists the full session state to a JSON artifact, enabling resume
        after API restart.

        Args:
            session_id: ID of the session

        Returns:
            dict: Status with artifact path

        Raises:
            ValueError: If session not found
        """
        session = self._get_session_or_raise(session_id)

        # Serialize session state
        session_state = session.to_dict()

        # Persist to artifacts
        workspace_path = self.workspace_manager.workspace_root / session_id
        try:
            artifact_store = ArtifactStore(str(workspace_path / "artifacts"))
            artifact_store.save_artifact("session_state.json", session_state)
            session.add_log("Session state saved to artifacts/session_state.json")
            self.session_store.update_session(session)
        except Exception as e:
            raise ValueError(f"Failed to save session state: {str(e)}")

        return {
            "status": "saved",
            "session_id": session_id,
            "artifact_path": str(workspace_path / "artifacts" / "session_state.json"),
            "phase": session.phase.value,
        }

    def resume_session(self, session_id: str) -> dict[str, Any]:
        """Resume a session from stored artifacts (VF-167).

        Loads session state from artifacts and restores it to the session store.
        Supports resuming from specific phases with limitations.

        Supported resume phases:
        - QUESTIONNAIRE: Resume answering questions
        - BUILD_SPEC: Resume spec generation
        - IDEA: Resume concept generation
        - PLAN_REVIEW: Resume plan review (approve/reject)
        - EXECUTION: Resume task execution (limited - active task may be lost)
        - CLARIFICATION: Resume waiting for clarification answer

        Unsupported resume phases (terminal):
        - COMPLETE: Session already finished
        - FAILED: Session already failed

        Args:
            session_id: ID of the session to resume

        Returns:
            dict: Status with session info and any warnings

        Raises:
            ValueError: If session state not found or resume not supported
        """
        import json

        workspace_path = self.workspace_manager.workspace_root / session_id
        state_path = workspace_path / "artifacts" / "session_state.json"

        if not state_path.exists():
            raise ValueError(
                f"No saved session state found for {session_id}. "
                f"Expected: {state_path}"
            )

        # Load session state
        try:
            with open(state_path, "r") as f:
                session_state = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid session state file: {str(e)}")

        # Restore session from state
        session = Session.from_dict(session_state)

        # Check for terminal phases
        terminal_phases = {SessionPhase.COMPLETE, SessionPhase.FAILED}
        if session.phase in terminal_phases:
            return {
                "status": "not_resumable",
                "session_id": session_id,
                "phase": session.phase.value,
                "reason": f"Session is in terminal phase {session.phase.value}",
                "recovery_options": session.get_recovery_options(),
            }

        # Build warnings for resume limitations
        warnings = []

        # Check for active task in EXECUTION phase
        if session.phase == SessionPhase.EXECUTION and session.active_task_id:
            warnings.append(
                f"Active task '{session.active_task_id}' may need to be re-executed. "
                f"Task state was not persisted."
            )
            # Clear active task - it will need to be re-scheduled
            session.active_task_id = None

        # Add resume log entry
        session.add_log(f"Session resumed from artifacts at phase {session.phase.value}")

        # Store the restored session
        self.session_store.update_session(session)

        # Emit resume event
        self._emit_event(
            Event(
                event_type=EventType.INFO,
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
                message=f"Session resumed from artifacts",
                phase=session.phase.value,
                metadata={
                    "resumed_from_phase": session.phase.value,
                    "completed_tasks": len(session.completed_task_ids),
                    "failed_tasks": len(session.failed_task_ids),
                    "warnings": warnings,
                },
            )
        )

        return {
            "status": "resumed",
            "session_id": session_id,
            "phase": session.phase.value,
            "completed_tasks": len(session.completed_task_ids),
            "failed_tasks": len(session.failed_task_ids),
            "warnings": warnings if warnings else None,
            "next_action": self._get_resume_next_action(session),
        }

    def _get_resume_next_action(self, session: Session) -> str:
        """Get the recommended next action after resuming a session.

        Args:
            session: The resumed session

        Returns:
            str: Description of recommended next action
        """
        phase_actions = {
            SessionPhase.QUESTIONNAIRE: "Call get_next_question() to continue questionnaire",
            SessionPhase.BUILD_SPEC: "Call generate_build_spec() to generate spec",
            SessionPhase.IDEA: "Call generate_concept() to generate concept",
            SessionPhase.PLAN_REVIEW: "Call approve_plan() or reject_plan() to continue",
            SessionPhase.EXECUTION: "Call execute_next_task() to continue execution",
            SessionPhase.CLARIFICATION: "Call submit_clarification_answer() with user response",
            SessionPhase.VERIFICATION: "Call finalize_session() to complete verification",
        }
        return phase_actions.get(session.phase, "Session in unknown state")

    def list_resumable_sessions(self) -> list[dict[str, Any]]:
        """List all sessions that have saved state and can be resumed (VF-167).

        Scans the workspace for session_state.json artifacts.

        Returns:
            list: List of resumable session info dicts
        """
        import json

        resumable = []
        workspace_root = self.workspace_manager.workspace_root

        if not workspace_root.exists():
            return resumable

        for session_dir in workspace_root.iterdir():
            if not session_dir.is_dir():
                continue

            state_path = session_dir / "artifacts" / "session_state.json"
            if not state_path.exists():
                continue

            try:
                with open(state_path, "r") as f:
                    state = json.load(f)

                session_id = state.get("session_id", session_dir.name)
                phase = state.get("phase", "UNKNOWN")
                is_terminal = phase in {"COMPLETE", "FAILED"}

                resumable.append({
                    "session_id": session_id,
                    "phase": phase,
                    "is_terminal": is_terminal,
                    "is_resumable": not is_terminal,
                    "updated_at": state.get("updated_at"),
                    "completed_tasks": len(state.get("completed_task_ids", [])),
                    "failed_tasks": len(state.get("failed_task_ids", [])),
                })
            except (json.JSONDecodeError, KeyError):
                # Skip invalid state files
                continue

        return resumable

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
