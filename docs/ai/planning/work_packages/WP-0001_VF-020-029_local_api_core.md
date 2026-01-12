# WP-0001 — Local UI API Completion

## VF Tasks Included
- VF-020: API server skeleton (REST)
- VF-021: Endpoint: POST /sessions (startSession)
- VF-022: Endpoint: GET /sessions/{id}/question (getNextQuestion)
- VF-023: Endpoint: POST /sessions/{id}/answers (submitAnswer)
- VF-024: Endpoint: GET /sessions/{id}/plan (getPlanSummary)
- VF-025: Endpoint: POST /sessions/{id}/plan/decision (approve/reject)
- VF-026: Endpoint: GET /sessions/{id}/progress (progress/events)
- VF-029: API validation + error mapping (bad phase, invalid session, schema violations)

## Goal
Make the session API stable and phase-safe so UI can drive the flow reliably.

## Ordered Execution Steps

### 1. VF-020: Create API server skeleton
- Set up FastAPI application structure in `apps/api/vibeforge_api/`
- Define main.py with app instance and CORS configuration
- Create basic health check endpoint
- Set up router structure for session endpoints
- Files: `apps/api/vibeforge_api/main.py`, `apps/api/vibeforge_api/__init__.py`

### 2. VF-002: Define core DTOs + shared types
- Create shared types module for SessionPhase enum, error responses
- Define Pydantic models for API request/response contracts
- Files: `apps/api/vibeforge_api/models/types.py`, `apps/api/vibeforge_api/models/__init__.py`

### 3. VF-021: POST /sessions (startSession)
- Implement session creation endpoint
- Initialize session with unique ID and QUESTIONNAIRE phase
- Return sessionId in response
- Files: `apps/api/vibeforge_api/routers/sessions.py`

### 4. VF-022: GET /sessions/{id}/question (getNextQuestion)
- Implement endpoint to retrieve next question for session
- Return question structure (id, text, type, options)
- Files: `apps/api/vibeforge_api/routers/sessions.py`

### 5. VF-023: POST /sessions/{id}/answers (submitAnswer)
- Implement endpoint to accept and validate answer
- Store answer in session state
- Advance questionnaire state
- Files: `apps/api/vibeforge_api/routers/sessions.py`

### 6. VF-024: GET /sessions/{id}/plan (getPlanSummary)
- Implement endpoint to retrieve plan summary
- Return plan details when session is in PLAN_REVIEW phase
- Files: `apps/api/vibeforge_api/routers/sessions.py`

### 7. VF-025: POST /sessions/{id}/plan/decision (approve/reject)
- Implement endpoint to accept plan approval/rejection
- Update session phase based on decision
- Files: `apps/api/vibeforge_api/routers/sessions.py`

### 8. VF-026: GET /sessions/{id}/progress (progress/events)
- Implement endpoint to expose progress snapshots
- Return current phase, completed tasks, active task
- Files: `apps/api/vibeforge_api/routers/sessions.py`

### 9. VF-029: API validation + error mapping
- Implement phase validation middleware/dependency
- Create consistent error response models
- Add validation for session existence, phase transitions
- Handle schema violations with clear error messages
- Files: `apps/api/vibeforge_api/middleware/validation.py`, `apps/api/vibeforge_api/models/errors.py`

## Done Means...

### Verification Commands
1. Install dependencies: `cd apps/api && pip install -r requirements.txt`
2. Run tests: `pytest` (unit tests for all endpoints pass)
3. Start server: `uvicorn vibeforge_api.main:app --reload`
4. Smoke test:
   - Visit `/docs` - OpenAPI docs load
   - POST `/sessions` - creates session, returns sessionId
   - GET `/sessions/{id}/question` - returns first question
   - POST `/sessions/{id}/answers` - accepts answer
   - GET `/sessions/{id}/progress` - returns progress

### Task Checklist
- [x] VF-020: API server skeleton created with FastAPI
  - `apps/api/vibeforge_api/main.py`, `apps/api/vibeforge_api/__init__.py`
  - CORS configured for local dev
- [x] VF-002: Core DTOs and SessionPhase enum defined
  - `apps/api/vibeforge_api/models/types.py`, `apps/api/vibeforge_api/models/requests.py`, `apps/api/vibeforge_api/models/responses.py`
  - SessionPhase, AgentRole, GateResult, ErrorResponse models
- [x] VF-021: POST /sessions endpoint working
  - `apps/api/vibeforge_api/routers/sessions.py:20`
  - Creates session, returns sessionId
- [x] VF-022: GET /sessions/{id}/question endpoint working
  - `apps/api/vibeforge_api/routers/sessions.py:32`
  - Returns next question from questionnaire engine
- [x] VF-023: POST /sessions/{id}/answers endpoint working
  - `apps/api/vibeforge_api/routers/sessions.py:57`
  - Validates and stores answers, advances questionnaire
- [x] VF-024: GET /sessions/{id}/plan endpoint working
  - `apps/api/vibeforge_api/routers/sessions.py:103`
  - Returns plan summary (mock data for MVP)
- [x] VF-025: POST /sessions/{id}/plan/decision endpoint working
  - `apps/api/vibeforge_api/routers/sessions.py:127`
  - Approves/rejects plan, transitions phase
- [x] VF-026: GET /sessions/{id}/progress endpoint working
  - `apps/api/vibeforge_api/routers/sessions.py:155`
  - Returns progress with tasks and logs
- [x] VF-029: Validation and error handling implemented
  - Phase validation in all endpoints
  - Session existence checks
  - Answer validation against question schema
- [x] All endpoints return consistent error formats
  - HTTPException with status codes and detail messages
- [x] Phase validation prevents illegal transitions
  - Each endpoint checks current phase
- [x] OpenAPI docs accessible at /docs
  - FastAPI auto-generates OpenAPI docs

## Implementation Notes
- Use in-memory storage for MVP (dict-based session store)
- Focus on API contracts and phase safety, not full business logic yet
- Keep endpoints thin; business logic will move to coordinator later
- Error responses must include: code, message, detail (optional)
