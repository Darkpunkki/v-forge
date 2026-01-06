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

from typing import Any, Optional

from vibeforge_api.core.session import Session, SessionStoreInterface
from vibeforge_api.core.workspace import WorkspaceManager
from vibeforge_api.core.questionnaire import QuestionnaireEngine
from vibeforge_api.core.spec_builder import SpecBuilder
from vibeforge_api.core.artifacts import ArtifactStore
from vibeforge_api.models.types import SessionPhase
from vibeforge_api.models.responses import QuestionResponse
from orchestration.orchestrator import Orchestrator
from orchestration.models import ConceptDoc, TaskGraph


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
    ):
        """Initialize SessionCoordinator with dependencies.

        Args:
            session_store: Session persistence layer
            workspace_manager: Workspace initialization
            questionnaire_engine: Questionnaire flow driver
            spec_builder: BuildSpec generator
            orchestrator: High-level concept/plan generator
        """
        self.session_store = session_store
        self.workspace_manager = workspace_manager
        self.questionnaire_engine = questionnaire_engine
        self.spec_builder = spec_builder
        self.orchestrator = orchestrator

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

        # Transition to BUILD_SPEC phase
        session.update_phase(SessionPhase.BUILD_SPEC)
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

        # Persist BuildSpec as artifact
        workspace_path = self.workspace_manager.workspace_root / session_id
        artifact_store = ArtifactStore(str(workspace_path / "artifacts"))
        artifact_store.save_artifact("build_spec.json", build_spec)
        session.add_log("BuildSpec persisted to artifacts/build_spec.json")

        # Transition to IDEA phase
        session.update_phase(SessionPhase.IDEA)
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

            # Persist concept as artifact
            workspace_path = self.workspace_manager.workspace_root / session_id
            artifact_store = ArtifactStore(str(workspace_path / "artifacts"))
            artifact_store.save_artifact("concept.json", concept)
            session.add_log("Concept persisted to artifacts/concept.json")

            # Transition to PLAN_REVIEW phase
            session.update_phase(SessionPhase.PLAN_REVIEW)
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
        session.update_phase(SessionPhase.EXECUTION)
        session.add_log("Plan approved by user")
        session.add_log(f"Phase transition: PLAN_REVIEW → EXECUTION")

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
        session.update_phase(SessionPhase.IDEA)
        session.add_log(f"Plan rejected by user: {reason}")
        session.add_log(f"Phase transition: PLAN_REVIEW → IDEA (for regeneration)")

        # Update session
        self.session_store.update_session(session)

        return {"status": "rejected", "message": "Plan rejected, returning to concept stage"}

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
