"""Coordinator package: SessionCoordinator orchestrates the factory workflow."""

from orchestration.coordinator.session_coordinator import SessionCoordinator
from orchestration.coordinator.state_machine import (
    TransitionError,
    ExitCriteriaNotMet,
    ALLOWED_TRANSITIONS,
    is_valid_transition,
    validate_transition,
    get_allowed_transitions,
    is_terminal_phase,
    ENTRY_ACTIONS,
    get_entry_action,
    EXIT_CRITERIA,
    get_exit_criteria,
    check_exit_criteria,
    validate_exit,
    validate_phase_transition,
    # VF-164: Fix loop guardrails
    MAX_FIX_LOOPS,
    can_return_to_execution,
    validate_fix_loop_transition,
)

__all__ = [
    "SessionCoordinator",
    "TransitionError",
    "ExitCriteriaNotMet",
    "ALLOWED_TRANSITIONS",
    "is_valid_transition",
    "validate_transition",
    "get_allowed_transitions",
    "is_terminal_phase",
    "ENTRY_ACTIONS",
    "get_entry_action",
    "EXIT_CRITERIA",
    "get_exit_criteria",
    "check_exit_criteria",
    "validate_exit",
    "validate_phase_transition",
    # VF-164: Fix loop guardrails
    "MAX_FIX_LOOPS",
    "can_return_to_execution",
    "validate_fix_loop_transition",
]
