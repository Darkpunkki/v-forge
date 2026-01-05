# WP-0011 — Clarification endpoint

## VF Tasks Included
- VF-027: Endpoint: POST /sessions/{id}/clarifications (submitClarificationChoice)

## Goal
Complete the Local UI API by adding the clarification endpoint. This endpoint accepts user choices for clarification questions raised by gates or agents and feeds them back into the coordinator/agent loop.

## Dependencies
- WP-0001 ✓ (API foundation with sessions router)
- WP-0007d ✓ (UI clarification screen already implemented)
- WP-0004 ✓ (Gates pipeline that generates clarification questions)

## Execution Plan

### 1. Review existing clarification infrastructure
- Check if gates.py has clarification question generation (GateAdapter.generate_clarification_question)
- Review UI types/API client for clarification contract (ClarificationResponse, ClarificationAnswerRequest)
- Check sessions.py for any existing clarification logic

### 2. Implement GET /sessions/{id}/clarification endpoint
- Return pending clarification question if session is in CLARIFICATION_NEEDED phase
- Return 404 or error if no clarification is pending
- Match the ClarificationResponse type from UI (question, context, options)

### 3. Implement POST /sessions/{id}/clarification endpoint (VF-027)
- Accept user's answer choice
- Validate the answer is one of the valid options
- Feed the answer back into the coordinator/agent loop
- Transition session to appropriate next phase
- Return next phase and status

### 4. Add request/response models
- ClarificationAnswerRequest (answer field)
- ClarificationResponse (question, context, options)
- Update models/__init__.py exports if needed

### 5. Write tests
- test_get_clarification_when_pending
- test_get_clarification_wrong_phase
- test_submit_clarification_valid_answer
- test_submit_clarification_invalid_answer
- test_clarification_phase_transition

### 6. Verify integration
- Run all API tests
- Manually test clarification flow if possible

## Done Means
- [x] VF-027: POST /sessions/{id}/clarification endpoint implemented
  - **Files changed:**
    - `apps/api/vibeforge_api/models/requests.py` (added ClarificationAnswerRequest)
    - `apps/api/vibeforge_api/models/responses.py` (added ClarificationResponse, ClarificationOption)
    - `apps/api/vibeforge_api/models/__init__.py` (exported new models)
    - `apps/api/vibeforge_api/routers/sessions.py` (added GET and POST /clarification endpoints)
    - `apps/api/vibeforge_api/core/session.py` (added pending_clarification and clarification_answer fields)
    - `apps/api/tests/test_sessions.py` (added 7 clarification tests)
  - **Endpoints implemented:**
    - GET `/sessions/{id}/clarification` - Returns pending clarification question
    - POST `/sessions/{id}/clarification` - Accepts user's clarification answer (VF-027)
  - **Tests:** 7 new tests, all passing
  - **Verification:** `cd apps/api && pytest tests/test_sessions.py -k clarification -v` (7 passed)
  - **Full test suite:** `cd apps/api && pytest -v` (162 passed, was 155)

## Verification Commands
```bash
cd apps/api && pytest tests/test_sessions.py -k clarification -v
cd apps/api && pytest -v
```

## Notes
- The UI already has the clarification screen (WP-0007d) with getClarification/submitClarification client functions
- Gates already have GateAdapter.generate_clarification_question for warnings
- This WP bridges the gap between gate warnings and UI interaction
