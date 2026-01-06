# WP-0018 — SessionCoordinator initialization and questionnaire phases

## VF Tasks Included
- [x] VF-032 — SessionCoordinator: startSession() + phase initialization
  - **Files:** `orchestration/coordinator/session_coordinator.py` (start_session method)
  - **Tests:** `apps/api/tests/test_session_coordinator.py::TestSessionCoordinatorStartSession` (3 tests)
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorStartSession -v` (3 passed)
- [x] VF-033 — SessionCoordinator: questionnaire step loop (nextQuestion/applyAnswer/finalize)
  - **Files:** `orchestration/coordinator/session_coordinator.py` (get_next_question, submit_answer, finalize_questionnaire methods)
  - **Tests:** `apps/api/tests/test_session_coordinator.py::TestSessionCoordinatorQuestionnaire` (8 tests)
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorQuestionnaire -v` (8 passed)
- [x] VF-034 — SessionCoordinator: buildSpec stage
  - **Files:** `orchestration/coordinator/session_coordinator.py` (generate_build_spec method)
  - **Tests:** `apps/api/tests/test_session_coordinator.py::TestSessionCoordinatorBuildSpec` (5 tests)
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorBuildSpec -v` (5 passed)

## Goal
Enable SessionCoordinator to initialize sessions, drive questionnaire flow, and generate BuildSpec deterministically from user answers.

## Dependencies
- ✅ WP-0013 (Session model + SessionStore)
- ✅ WP-0009 (QuestionnaireEngine)
- ✅ WP-0010 (SpecBuilder)
- ✅ WP-0002 (WorkspaceManager)

## Execution Steps

### 1. VF-032: SessionCoordinator.startSession() + phase initialization
**Intent:** Orchestrate workspace/artifact initialization and set the session to QUESTIONNAIRE phase.

**Implementation:**
- Create `orchestration/coordinator/session_coordinator.py`
- Implement `SessionCoordinator` class with dependencies:
  - SessionStore (storage)
  - WorkspaceManager (workspace initialization)
  - QuestionnaireEngine (questionnaire flow)
  - SpecBuilder (BuildSpec generation)
- Implement `startSession()` method:
  - Create new Session via SessionStore
  - Initialize workspace for session (repo/ and artifacts/ directories)
  - Transition session to QUESTIONNAIRE phase
  - Return session_id

**Done means:**
- SessionCoordinator class exists with proper dependency injection
- startSession() creates session, initializes workspace, sets QUESTIONNAIRE phase
- Unit tests verify workspace creation and phase transition

### 2. VF-033: SessionCoordinator questionnaire step loop
**Intent:** Drive questionnaire progression and finalize IntentProfile when complete.

**Implementation:**
- Implement `getNextQuestion(session_id)` method:
  - Retrieve session from SessionStore
  - Validate session is in QUESTIONNAIRE phase
  - Delegate to QuestionnaireEngine.get_next_question()
  - Return question or None if complete
- Implement `submitAnswer(session_id, answer)` method:
  - Retrieve session
  - Validate session is in QUESTIONNAIRE phase
  - Validate answer via QuestionnaireEngine
  - Add answer to session.answers
  - Update session via SessionStore
- Implement `finalizeQuestionnaire(session_id)` method:
  - Retrieve session
  - Generate IntentProfile via QuestionnaireEngine.finalize()
  - Store IntentProfile in session
  - Transition session to SPEC_BUILD phase
  - Return IntentProfile

**Done means:**
- getNextQuestion() serves questions sequentially
- submitAnswer() validates and stores answers
- finalizeQuestionnaire() generates IntentProfile and transitions to SPEC_BUILD
- Unit tests verify flow and phase transitions

### 3. VF-034: SessionCoordinator buildSpec stage
**Intent:** Convert IntentProfile to BuildSpec (deterministic), including idea seed + policy guardrails.

**Implementation:**
- Implement `generateBuildSpec(session_id)` method:
  - Retrieve session
  - Validate session is in SPEC_BUILD phase
  - Get IntentProfile from session
  - Call SpecBuilder.from_intent(IntentProfile) to generate BuildSpec
  - Store BuildSpec in session
  - Persist BuildSpec as artifact via ArtifactStore
  - Transition session to IDEA phase
  - Return BuildSpec

**Done means:**
- generateBuildSpec() converts IntentProfile → BuildSpec deterministically
- BuildSpec persisted as artifact
- Session transitions to IDEA phase
- Unit tests verify BuildSpec generation and persistence

## Verification Commands
```bash
# Unit tests for SessionCoordinator
cd apps/api && pytest tests/test_session_coordinator.py -v

# Full test suite
cd apps/api && pytest -v
```

## Done Means
- [x] SessionCoordinator class exists in `orchestration/coordinator/session_coordinator.py`
- [x] startSession() initializes sessions and workspaces correctly
- [x] getNextQuestion(), submitAnswer(), finalizeQuestionnaire() drive questionnaire flow
- [x] generateBuildSpec() converts IntentProfile → BuildSpec deterministically
- [x] All phase transitions work correctly (SESSION_START → QUESTIONNAIRE → SPEC_BUILD → IDEA)
- [x] Unit tests cover all methods and phase transitions
- [x] All tests pass (397+ expected)

## Notes
- SessionCoordinator is the orchestration layer that ties together all components
- Phase transitions must be strict and validated
- Each phase has clear entry/exit criteria
- Errors should be captured and stored in session.error_history
