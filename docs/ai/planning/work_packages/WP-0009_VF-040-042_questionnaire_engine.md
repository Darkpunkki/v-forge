# WP-0009 — Questionnaire engine foundations

## VF Tasks Included
- VF-040: Define QuestionBank (audience/platform/domains/vibe/constraints/budgets)
- VF-041: Implement QuestionnaireEngine.nextQuestion() (adaptive branching)
- VF-042: Implement QuestionnaireEngine.applyAnswer() + validation

## Goal
Deliver a deterministic, structured questionnaire engine that serves curated questions, validates answers, and tracks session state without free-text inputs.

## Ordered Execution Steps

### 1. Define structured QuestionBank
- Create a curated set of questions with allowed options covering audience, platform, domain, vibe, constraints, budgets, and scope.
- Encode questions as data (JSON/YAML or Python constants) with ids, prompt text, option values/labels, and branching rules.
- Add schema/validation to prevent malformed entries and keep options fully structured.

### 2. Implement questionnaire state + branching
- Extend `QuestionnaireEngine` to compute the next question based on prior answers and optional branching logic.
- Ensure ordering is deterministic and avoids repeats; provide a terminal state when complete.
- Add helper to surface progress metadata (questions asked/remaining) for UI.

### 3. Implement answer application + validation
- Add strict validation of incoming answers against allowed option ids (reject free text or unknown choices).
- Persist answers into session state and ensure they influence subsequent branching decisions.
- Record any clarification prompts or dependencies needed for later phases (e.g., stack hints, constraints).

### 4. Wire into API and artifacts
- Update session/questionnaire API endpoints to use new QuestionBank and branching behavior.
- Persist questionnaire state and answers via ArtifactStore for replayability.
- Add telemetry hooks or logs for served questions/answers to aid debugging.

## Done Means...

### Verification Commands
1. `cd apps/api && pytest tests/test_questionnaire_engine.py -v`
2. `cd apps/api && pytest tests/test_sessions.py -k questionnaire -v`
3. `cd apps/api && pytest tests/test_e2e_demo.py::test_e2e_questionnaire_to_result -v` (regression)
4. Manual: call questionnaire endpoints to confirm structured questions and validation errors for invalid answers
