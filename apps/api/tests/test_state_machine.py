"""Tests for session state machine (VF-160, VF-161, VF-162).

These tests validate:
- VF-160: Formal phase transition table
- VF-161: Entry actions per phase
- VF-162: Exit criteria per phase
"""

import pytest
from unittest.mock import MagicMock

from apps.api.vibeforge_api.models.types import SessionPhase
from orchestration.coordinator.state_machine import (
    # VF-160: Transition validation
    ALLOWED_TRANSITIONS,
    is_valid_transition,
    validate_transition,
    get_allowed_transitions,
    is_terminal_phase,
    TransitionError,
    # VF-161: Entry actions
    ENTRY_ACTIONS,
    get_entry_action,
    # VF-162: Exit criteria
    EXIT_CRITERIA,
    get_exit_criteria,
    check_exit_criteria,
    validate_exit,
    ExitCriteriaNotMet,
    # Combined
    validate_phase_transition,
)


class TestVF160_TransitionTable:
    """Tests for VF-160: Formal phase transition table."""

    def test_allowed_transitions_covers_all_phases(self):
        """Every phase should have an entry in ALLOWED_TRANSITIONS."""
        for phase in SessionPhase:
            assert phase in ALLOWED_TRANSITIONS, f"Missing entry for {phase}"

    def test_questionnaire_allowed_transitions(self):
        """QUESTIONNAIRE can transition to BUILD_SPEC or FAILED."""
        allowed = get_allowed_transitions(SessionPhase.QUESTIONNAIRE)
        assert SessionPhase.BUILD_SPEC in allowed
        assert SessionPhase.FAILED in allowed
        assert len(allowed) == 2

    def test_build_spec_allowed_transitions(self):
        """BUILD_SPEC can transition to IDEA or FAILED."""
        allowed = get_allowed_transitions(SessionPhase.BUILD_SPEC)
        assert SessionPhase.IDEA in allowed
        assert SessionPhase.FAILED in allowed
        assert len(allowed) == 2

    def test_idea_allowed_transitions(self):
        """IDEA can transition to PLAN_REVIEW or FAILED."""
        allowed = get_allowed_transitions(SessionPhase.IDEA)
        assert SessionPhase.PLAN_REVIEW in allowed
        assert SessionPhase.FAILED in allowed
        assert len(allowed) == 2

    def test_plan_review_allowed_transitions(self):
        """PLAN_REVIEW can transition to EXECUTION, IDEA, or FAILED."""
        allowed = get_allowed_transitions(SessionPhase.PLAN_REVIEW)
        assert SessionPhase.EXECUTION in allowed
        assert SessionPhase.IDEA in allowed  # Reject plan -> regenerate
        assert SessionPhase.FAILED in allowed
        assert len(allowed) == 3

    def test_execution_allowed_transitions(self):
        """EXECUTION can transition to CLARIFICATION, VERIFICATION, COMPLETE, or FAILED."""
        allowed = get_allowed_transitions(SessionPhase.EXECUTION)
        assert SessionPhase.CLARIFICATION in allowed
        assert SessionPhase.VERIFICATION in allowed
        assert SessionPhase.COMPLETE in allowed
        assert SessionPhase.FAILED in allowed
        assert len(allowed) == 4

    def test_clarification_allowed_transitions(self):
        """CLARIFICATION can transition to EXECUTION or FAILED."""
        allowed = get_allowed_transitions(SessionPhase.CLARIFICATION)
        assert SessionPhase.EXECUTION in allowed
        assert SessionPhase.FAILED in allowed
        assert len(allowed) == 2

    def test_verification_allowed_transitions(self):
        """VERIFICATION can transition to COMPLETE, EXECUTION (fix loop), or FAILED."""
        allowed = get_allowed_transitions(SessionPhase.VERIFICATION)
        assert SessionPhase.COMPLETE in allowed
        assert SessionPhase.EXECUTION in allowed  # Fix loop
        assert SessionPhase.FAILED in allowed
        assert len(allowed) == 3

    def test_terminal_phases_have_no_transitions(self):
        """COMPLETE and FAILED are terminal phases."""
        assert get_allowed_transitions(SessionPhase.COMPLETE) == set()
        assert get_allowed_transitions(SessionPhase.FAILED) == set()

    def test_is_terminal_phase(self):
        """is_terminal_phase correctly identifies terminal phases."""
        assert is_terminal_phase(SessionPhase.COMPLETE) is True
        assert is_terminal_phase(SessionPhase.FAILED) is True
        assert is_terminal_phase(SessionPhase.QUESTIONNAIRE) is False
        assert is_terminal_phase(SessionPhase.EXECUTION) is False

    def test_is_valid_transition_valid(self):
        """is_valid_transition returns True for allowed transitions."""
        assert is_valid_transition(SessionPhase.QUESTIONNAIRE, SessionPhase.BUILD_SPEC) is True
        assert is_valid_transition(SessionPhase.BUILD_SPEC, SessionPhase.IDEA) is True
        assert is_valid_transition(SessionPhase.EXECUTION, SessionPhase.COMPLETE) is True

    def test_is_valid_transition_invalid(self):
        """is_valid_transition returns False for disallowed transitions."""
        # Can't skip phases
        assert is_valid_transition(SessionPhase.QUESTIONNAIRE, SessionPhase.EXECUTION) is False
        # Can't go backwards (except PLAN_REVIEW -> IDEA)
        assert is_valid_transition(SessionPhase.EXECUTION, SessionPhase.QUESTIONNAIRE) is False
        # Can't exit terminal
        assert is_valid_transition(SessionPhase.COMPLETE, SessionPhase.EXECUTION) is False

    def test_validate_transition_valid(self):
        """validate_transition doesn't raise for allowed transitions."""
        # Should not raise
        validate_transition(SessionPhase.QUESTIONNAIRE, SessionPhase.BUILD_SPEC)
        validate_transition(SessionPhase.PLAN_REVIEW, SessionPhase.IDEA)  # Reject plan

    def test_validate_transition_invalid_raises(self):
        """validate_transition raises TransitionError for disallowed transitions."""
        with pytest.raises(TransitionError) as exc_info:
            validate_transition(SessionPhase.QUESTIONNAIRE, SessionPhase.EXECUTION)

        assert exc_info.value.from_phase == SessionPhase.QUESTIONNAIRE
        assert exc_info.value.to_phase == SessionPhase.EXECUTION
        assert "BUILD_SPEC" in str(exc_info.value)  # Allowed transition mentioned

    def test_validate_transition_from_terminal_raises(self):
        """validate_transition raises for transitions from terminal phases."""
        with pytest.raises(TransitionError) as exc_info:
            validate_transition(SessionPhase.COMPLETE, SessionPhase.EXECUTION)

        assert "none" in str(exc_info.value).lower()  # No allowed transitions


class TestVF161_EntryActions:
    """Tests for VF-161: Entry actions per phase."""

    def test_entry_actions_defined_for_all_phases(self):
        """Every phase should have an entry action defined."""
        for phase in SessionPhase:
            action = get_entry_action(phase)
            assert action is not None, f"Missing entry action for {phase}"
            assert action.phase == phase
            assert action.description  # Non-empty description

    def test_questionnaire_entry_action(self):
        """QUESTIONNAIRE entry action initializes questionnaire state."""
        action = get_entry_action(SessionPhase.QUESTIONNAIRE)
        assert "questionnaire" in action.description.lower()
        assert "question" in action.description.lower()

    def test_build_spec_entry_action(self):
        """BUILD_SPEC entry action generates IntentProfile and BuildSpec."""
        action = get_entry_action(SessionPhase.BUILD_SPEC)
        assert "intentprofile" in action.description.lower() or "buildspec" in action.description.lower()

    def test_idea_entry_action(self):
        """IDEA entry action generates ConceptDoc."""
        action = get_entry_action(SessionPhase.IDEA)
        assert "concept" in action.description.lower()

    def test_plan_review_entry_action(self):
        """PLAN_REVIEW entry action generates TaskGraph and runs gates."""
        action = get_entry_action(SessionPhase.PLAN_REVIEW)
        assert "taskgraph" in action.description.lower() or "gate" in action.description.lower()

    def test_execution_entry_action(self):
        """EXECUTION entry action initializes TaskMaster and scheduling."""
        action = get_entry_action(SessionPhase.EXECUTION)
        assert "task" in action.description.lower()

    def test_complete_entry_action(self):
        """COMPLETE entry action generates RunSummary."""
        action = get_entry_action(SessionPhase.COMPLETE)
        assert "summary" in action.description.lower() or "final" in action.description.lower()

    def test_failed_entry_action(self):
        """FAILED entry action records failure and cleans up."""
        action = get_entry_action(SessionPhase.FAILED)
        assert "failure" in action.description.lower() or "error" in action.description.lower()


class TestVF162_ExitCriteria:
    """Tests for VF-162: Exit criteria per phase."""

    def test_exit_criteria_defined_for_all_phases(self):
        """Every phase should have exit criteria defined."""
        for phase in SessionPhase:
            criteria = get_exit_criteria(phase)
            assert criteria is not None, f"Missing exit criteria for {phase}"
            assert criteria.phase == phase
            assert criteria.description  # Non-empty description
            assert callable(criteria.check)

    def test_questionnaire_exit_criteria_no_answers(self):
        """QUESTIONNAIRE exit fails if no answers recorded."""
        session = MagicMock()
        session.answers = {}

        is_met, reason = check_exit_criteria(SessionPhase.QUESTIONNAIRE, session)
        assert is_met is False
        assert "answer" in reason.lower()

    def test_questionnaire_exit_criteria_with_answers(self):
        """QUESTIONNAIRE exit passes if answers recorded."""
        session = MagicMock()
        session.answers = {"q1": "answer1"}

        is_met, reason = check_exit_criteria(SessionPhase.QUESTIONNAIRE, session)
        assert is_met is True

    def test_build_spec_exit_criteria_no_spec(self):
        """BUILD_SPEC exit fails if no BuildSpec."""
        session = MagicMock()
        session.intent_profile = {"app_type": "web"}
        session.build_spec = None

        is_met, reason = check_exit_criteria(SessionPhase.BUILD_SPEC, session)
        assert is_met is False
        assert "buildspec" in reason.lower()

    def test_build_spec_exit_criteria_with_spec(self):
        """BUILD_SPEC exit passes if BuildSpec generated."""
        session = MagicMock()
        session.intent_profile = {"app_type": "web"}
        session.build_spec = {"stack": "vite-react"}

        is_met, reason = check_exit_criteria(SessionPhase.BUILD_SPEC, session)
        assert is_met is True

    def test_idea_exit_criteria_no_concept(self):
        """IDEA exit fails if no ConceptDoc."""
        session = MagicMock()
        session.concept = None

        is_met, reason = check_exit_criteria(SessionPhase.IDEA, session)
        assert is_met is False
        assert "concept" in reason.lower()

    def test_idea_exit_criteria_with_concept(self):
        """IDEA exit passes if ConceptDoc generated."""
        session = MagicMock()
        session.concept = {"description": "A todo app"}

        is_met, reason = check_exit_criteria(SessionPhase.IDEA, session)
        assert is_met is True

    def test_clarification_exit_criteria_no_answer(self):
        """CLARIFICATION exit fails if no answer provided."""
        session = MagicMock()
        session.clarification_answer = None

        is_met, reason = check_exit_criteria(SessionPhase.CLARIFICATION, session)
        assert is_met is False
        assert "answer" in reason.lower()

    def test_clarification_exit_criteria_with_answer(self):
        """CLARIFICATION exit passes if answer provided."""
        session = MagicMock()
        session.clarification_answer = "option_a"

        is_met, reason = check_exit_criteria(SessionPhase.CLARIFICATION, session)
        assert is_met is True

    def test_terminal_phases_cannot_exit(self):
        """Terminal phases (COMPLETE, FAILED) cannot be exited."""
        session = MagicMock()

        is_met, reason = check_exit_criteria(SessionPhase.COMPLETE, session)
        assert is_met is False
        assert "terminal" in reason.lower()

        is_met, reason = check_exit_criteria(SessionPhase.FAILED, session)
        assert is_met is False
        assert "terminal" in reason.lower()

    def test_validate_exit_raises_on_failure(self):
        """validate_exit raises ExitCriteriaNotMet when criteria not met."""
        session = MagicMock()
        session.answers = {}

        with pytest.raises(ExitCriteriaNotMet) as exc_info:
            validate_exit(SessionPhase.QUESTIONNAIRE, session)

        assert exc_info.value.phase == SessionPhase.QUESTIONNAIRE


class TestCombinedValidation:
    """Tests for combined phase transition validation."""

    def test_validate_phase_transition_valid(self):
        """Valid transition with met exit criteria passes."""
        session = MagicMock()
        session.answers = {"q1": "answer1"}

        # Should not raise
        validate_phase_transition(
            session,
            SessionPhase.QUESTIONNAIRE,
            SessionPhase.BUILD_SPEC
        )

    def test_validate_phase_transition_invalid_transition(self):
        """Invalid transition raises TransitionError."""
        session = MagicMock()
        session.answers = {"q1": "answer1"}

        with pytest.raises(TransitionError):
            validate_phase_transition(
                session,
                SessionPhase.QUESTIONNAIRE,
                SessionPhase.EXECUTION  # Can't skip to EXECUTION
            )

    def test_validate_phase_transition_exit_criteria_not_met(self):
        """Transition with unmet exit criteria raises ExitCriteriaNotMet."""
        session = MagicMock()
        session.answers = {}  # No answers

        with pytest.raises(ExitCriteriaNotMet):
            validate_phase_transition(
                session,
                SessionPhase.QUESTIONNAIRE,
                SessionPhase.BUILD_SPEC
            )

    def test_validate_phase_transition_to_failed_skips_exit_check(self):
        """Transition to FAILED always allowed (error recovery)."""
        session = MagicMock()
        session.answers = {}  # Exit criteria not met

        # Should not raise - FAILED is error recovery
        validate_phase_transition(
            session,
            SessionPhase.QUESTIONNAIRE,
            SessionPhase.FAILED,
            skip_exit_check=True
        )

    def test_validate_phase_transition_with_skip_exit_check(self):
        """skip_exit_check=True allows transition without exit criteria."""
        session = MagicMock()
        session.answers = {}  # Exit criteria not met

        # Should not raise with skip_exit_check
        validate_phase_transition(
            session,
            SessionPhase.QUESTIONNAIRE,
            SessionPhase.BUILD_SPEC,
            skip_exit_check=True
        )
