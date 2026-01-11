"""Session state machine: formal phase transitions with entry actions and exit criteria.

VF-160: Encode allowed phase transitions as a formal table
VF-161: Define entry actions per phase
VF-162: Define exit criteria per phase
"""

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, Any

from apps.api.vibeforge_api.models.types import SessionPhase


class TransitionError(Exception):
    """Raised when an invalid phase transition is attempted."""

    def __init__(self, from_phase: SessionPhase, to_phase: SessionPhase, reason: str):
        self.from_phase = from_phase
        self.to_phase = to_phase
        self.reason = reason
        super().__init__(f"Cannot transition from {from_phase.value} to {to_phase.value}: {reason}")


class ExitCriteriaNotMet(Exception):
    """Raised when exit criteria for current phase are not satisfied."""

    def __init__(self, phase: SessionPhase, criteria: str):
        self.phase = phase
        self.criteria = criteria
        super().__init__(f"Exit criteria not met for {phase.value}: {criteria}")


# =============================================================================
# VF-160: Formal phase transition table
# =============================================================================

# Allowed transitions: from_phase -> set of valid to_phases
ALLOWED_TRANSITIONS: dict[SessionPhase, set[SessionPhase]] = {
    SessionPhase.QUESTIONNAIRE: {
        SessionPhase.BUILD_SPEC,  # Questionnaire complete -> generate spec
        SessionPhase.FAILED,       # Error during questionnaire
    },
    SessionPhase.BUILD_SPEC: {
        SessionPhase.IDEA,         # Spec generated -> generate concept
        SessionPhase.FAILED,       # Error during spec generation
    },
    SessionPhase.IDEA: {
        SessionPhase.PLAN_REVIEW,  # Concept generated -> generate plan
        SessionPhase.FAILED,       # Error during concept generation
    },
    SessionPhase.PLAN_REVIEW: {
        SessionPhase.EXECUTION,    # Plan approved -> start execution
        SessionPhase.IDEA,         # Plan rejected -> regenerate concept
        SessionPhase.FAILED,       # Error during planning
    },
    SessionPhase.EXECUTION: {
        SessionPhase.CLARIFICATION,  # Need user input
        SessionPhase.VERIFICATION,   # All tasks done -> verify
        SessionPhase.COMPLETE,       # Direct completion (no verification needed)
        SessionPhase.FAILED,         # Unrecoverable execution error
    },
    SessionPhase.CLARIFICATION: {
        SessionPhase.EXECUTION,    # Resume execution after clarification
        SessionPhase.FAILED,       # Abort after clarification
    },
    SessionPhase.VERIFICATION: {
        SessionPhase.COMPLETE,     # Verification passed
        SessionPhase.EXECUTION,    # Verification failed -> retry (fix loop)
        SessionPhase.FAILED,       # Unrecoverable verification failure
    },
    SessionPhase.COMPLETE: set(),  # Terminal state - no outgoing transitions
    SessionPhase.FAILED: set(),    # Terminal state - no outgoing transitions
}


def is_valid_transition(from_phase: SessionPhase, to_phase: SessionPhase) -> bool:
    """Check if a phase transition is allowed.

    Args:
        from_phase: Current phase
        to_phase: Target phase

    Returns:
        True if transition is allowed, False otherwise
    """
    allowed = ALLOWED_TRANSITIONS.get(from_phase, set())
    return to_phase in allowed


def validate_transition(from_phase: SessionPhase, to_phase: SessionPhase) -> None:
    """Validate a phase transition, raising an error if invalid.

    Args:
        from_phase: Current phase
        to_phase: Target phase

    Raises:
        TransitionError: If the transition is not allowed
    """
    if not is_valid_transition(from_phase, to_phase):
        allowed = ALLOWED_TRANSITIONS.get(from_phase, set())
        allowed_str = ", ".join(p.value for p in allowed) if allowed else "none"
        raise TransitionError(
            from_phase,
            to_phase,
            f"Allowed transitions from {from_phase.value}: {allowed_str}"
        )


def get_allowed_transitions(from_phase: SessionPhase) -> set[SessionPhase]:
    """Get the set of phases that can be transitioned to from the given phase.

    Args:
        from_phase: Current phase

    Returns:
        Set of valid target phases
    """
    return ALLOWED_TRANSITIONS.get(from_phase, set()).copy()


def is_terminal_phase(phase: SessionPhase) -> bool:
    """Check if a phase is terminal (no outgoing transitions).

    Args:
        phase: Phase to check

    Returns:
        True if terminal, False otherwise
    """
    return phase in {SessionPhase.COMPLETE, SessionPhase.FAILED}


# =============================================================================
# VF-161: Entry actions per phase
# =============================================================================

@dataclass
class EntryAction:
    """Defines what happens when entering a phase."""

    phase: SessionPhase
    description: str
    # The actual action is implemented in SessionCoordinator methods
    # This dataclass documents the contract

    def __str__(self) -> str:
        return f"{self.phase.value}: {self.description}"


# Entry action registry - documents what should happen on entering each phase
ENTRY_ACTIONS: dict[SessionPhase, EntryAction] = {
    SessionPhase.QUESTIONNAIRE: EntryAction(
        phase=SessionPhase.QUESTIONNAIRE,
        description="Initialize questionnaire state, set current_question_index to 0"
    ),
    SessionPhase.BUILD_SPEC: EntryAction(
        phase=SessionPhase.BUILD_SPEC,
        description="Generate IntentProfile from answers, create BuildSpec from profile"
    ),
    SessionPhase.IDEA: EntryAction(
        phase=SessionPhase.IDEA,
        description="Generate ConceptDoc from BuildSpec using orchestrator"
    ),
    SessionPhase.PLAN_REVIEW: EntryAction(
        phase=SessionPhase.PLAN_REVIEW,
        description="Generate TaskGraph from concept, run gate pipeline, present plan summary"
    ),
    SessionPhase.EXECUTION: EntryAction(
        phase=SessionPhase.EXECUTION,
        description="Initialize TaskMaster with TaskGraph, begin task scheduling loop"
    ),
    SessionPhase.CLARIFICATION: EntryAction(
        phase=SessionPhase.CLARIFICATION,
        description="Store clarification context, pause execution, await user response"
    ),
    SessionPhase.VERIFICATION: EntryAction(
        phase=SessionPhase.VERIFICATION,
        description="Run global verification suite (build, tests, smoke check)"
    ),
    SessionPhase.COMPLETE: EntryAction(
        phase=SessionPhase.COMPLETE,
        description="Generate RunSummary, emit completion event, finalize artifacts"
    ),
    SessionPhase.FAILED: EntryAction(
        phase=SessionPhase.FAILED,
        description="Record failure reason, emit failure event, cleanup resources"
    ),
}


def get_entry_action(phase: SessionPhase) -> Optional[EntryAction]:
    """Get the entry action for a phase.

    Args:
        phase: Target phase

    Returns:
        EntryAction if defined, None otherwise
    """
    return ENTRY_ACTIONS.get(phase)


# =============================================================================
# VF-162: Exit criteria per phase
# =============================================================================

@dataclass
class ExitCriteria:
    """Defines what must be true to exit a phase."""

    phase: SessionPhase
    description: str
    # The check function takes a session-like object and returns (is_met, reason)
    check: Callable[[Any], tuple[bool, str]]

    def __str__(self) -> str:
        return f"{self.phase.value}: {self.description}"


def _questionnaire_exit_check(session: Any) -> tuple[bool, str]:
    """Check if questionnaire can be exited."""
    # Questionnaire is complete when all required questions are answered
    # The questionnaire engine determines this via get_next_question returning None
    if not hasattr(session, 'answers') or not session.answers:
        return False, "No answers recorded"
    # We rely on the questionnaire engine's finalize() succeeding
    return True, "Answers recorded"


def _build_spec_exit_check(session: Any) -> tuple[bool, str]:
    """Check if BUILD_SPEC phase can be exited."""
    if not hasattr(session, 'intent_profile') or session.intent_profile is None:
        return False, "IntentProfile not generated"
    if not hasattr(session, 'build_spec') or session.build_spec is None:
        return False, "BuildSpec not generated"
    return True, "BuildSpec ready"


def _idea_exit_check(session: Any) -> tuple[bool, str]:
    """Check if IDEA phase can be exited."""
    if not hasattr(session, 'concept') or session.concept is None:
        return False, "ConceptDoc not generated"
    return True, "Concept ready"


def _plan_review_exit_check(session: Any) -> tuple[bool, str]:
    """Check if PLAN_REVIEW phase can be exited."""
    if not hasattr(session, 'task_graph') or session.task_graph is None:
        return False, "TaskGraph not generated"
    # Plan must be approved (transition to EXECUTION) or rejected (back to IDEA)
    return True, "TaskGraph ready"


def _execution_exit_check(session: Any) -> tuple[bool, str]:
    """Check if EXECUTION phase can be exited."""
    # Can exit to CLARIFICATION (need input), VERIFICATION (done), or FAILED
    # The coordinator determines which based on task states
    if not hasattr(session, 'task_graph') or session.task_graph is None:
        return False, "No TaskGraph to execute"
    return True, "Execution state valid"


def _clarification_exit_check(session: Any) -> tuple[bool, str]:
    """Check if CLARIFICATION phase can be exited."""
    if not hasattr(session, 'clarification_answer') or session.clarification_answer is None:
        return False, "Clarification answer not provided"
    return True, "Clarification answered"


def _verification_exit_check(session: Any) -> tuple[bool, str]:
    """Check if VERIFICATION phase can be exited."""
    # Verification results determine exit
    # This is checked by the coordinator after running verifiers
    return True, "Ready to evaluate verification results"


def _terminal_exit_check(session: Any) -> tuple[bool, str]:
    """Terminal phases cannot be exited."""
    return False, "Terminal phase - no exit allowed"


# Exit criteria registry
EXIT_CRITERIA: dict[SessionPhase, ExitCriteria] = {
    SessionPhase.QUESTIONNAIRE: ExitCriteria(
        phase=SessionPhase.QUESTIONNAIRE,
        description="All required questions answered",
        check=_questionnaire_exit_check
    ),
    SessionPhase.BUILD_SPEC: ExitCriteria(
        phase=SessionPhase.BUILD_SPEC,
        description="IntentProfile and BuildSpec generated",
        check=_build_spec_exit_check
    ),
    SessionPhase.IDEA: ExitCriteria(
        phase=SessionPhase.IDEA,
        description="ConceptDoc generated",
        check=_idea_exit_check
    ),
    SessionPhase.PLAN_REVIEW: ExitCriteria(
        phase=SessionPhase.PLAN_REVIEW,
        description="TaskGraph generated and plan decision made",
        check=_plan_review_exit_check
    ),
    SessionPhase.EXECUTION: ExitCriteria(
        phase=SessionPhase.EXECUTION,
        description="All tasks completed or clarification/failure required",
        check=_execution_exit_check
    ),
    SessionPhase.CLARIFICATION: ExitCriteria(
        phase=SessionPhase.CLARIFICATION,
        description="User provided clarification answer",
        check=_clarification_exit_check
    ),
    SessionPhase.VERIFICATION: ExitCriteria(
        phase=SessionPhase.VERIFICATION,
        description="Verification suite completed",
        check=_verification_exit_check
    ),
    SessionPhase.COMPLETE: ExitCriteria(
        phase=SessionPhase.COMPLETE,
        description="Terminal phase - no exit",
        check=_terminal_exit_check
    ),
    SessionPhase.FAILED: ExitCriteria(
        phase=SessionPhase.FAILED,
        description="Terminal phase - no exit",
        check=_terminal_exit_check
    ),
}


def get_exit_criteria(phase: SessionPhase) -> Optional[ExitCriteria]:
    """Get the exit criteria for a phase.

    Args:
        phase: Current phase

    Returns:
        ExitCriteria if defined, None otherwise
    """
    return EXIT_CRITERIA.get(phase)


def check_exit_criteria(phase: SessionPhase, session: Any) -> tuple[bool, str]:
    """Check if exit criteria for a phase are met.

    Args:
        phase: Current phase
        session: Session object to check

    Returns:
        Tuple of (is_met, reason)
    """
    criteria = EXIT_CRITERIA.get(phase)
    if criteria is None:
        return True, "No exit criteria defined"
    return criteria.check(session)


def validate_exit(phase: SessionPhase, session: Any) -> None:
    """Validate that exit criteria are met, raising an error if not.

    Args:
        phase: Current phase
        session: Session object to check

    Raises:
        ExitCriteriaNotMet: If criteria are not satisfied
    """
    is_met, reason = check_exit_criteria(phase, session)
    if not is_met:
        raise ExitCriteriaNotMet(phase, reason)


# =============================================================================
# Combined validation
# =============================================================================

def validate_phase_transition(
    session: Any,
    from_phase: SessionPhase,
    to_phase: SessionPhase,
    skip_exit_check: bool = False
) -> None:
    """Validate a complete phase transition including exit criteria and transition rules.

    Args:
        session: Session object
        from_phase: Current phase
        to_phase: Target phase
        skip_exit_check: If True, skip exit criteria validation (for error recovery)

    Raises:
        ExitCriteriaNotMet: If exit criteria for current phase are not met
        TransitionError: If the transition is not allowed
    """
    # Skip exit check for transitions to FAILED (error recovery)
    if not skip_exit_check and to_phase != SessionPhase.FAILED:
        validate_exit(from_phase, session)

    # Validate transition is allowed
    validate_transition(from_phase, to_phase)
