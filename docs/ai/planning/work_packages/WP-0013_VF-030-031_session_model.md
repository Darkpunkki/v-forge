# WP-0013 — Session model + store

## VF Tasks Included
- VF-030: Implement Session model + phases enum
- VF-031: Implement SessionStore (in-memory) + persistence seam interface

## Goal
Define the Session domain model with phases enum and implement in-memory SessionStore with a persistence interface for future disk/DB storage.

## Dependencies
- WP-0002 ✓ (workspace/artifacts available)

## Current State Analysis

The Session model and SessionStore already exist in `apps/api/vibeforge_api/core/session.py`:

**Existing Session model features:**
- ✓ Session ID (UUID)
- ✓ Phase tracking (SessionPhase enum from models.types)
- ✓ Timestamps (created_at, updated_at)
- ✓ Questionnaire state (current_question_index, answers)
- ✓ Artifact pointers (intent_profile, build_spec, concept, task_graph)
- ✓ Execution state (completed_task_ids, failed_task_ids, active_task_id, logs)
- ✓ Clarification state (pending_clarification, clarification_answer)
- ✓ Methods: update_phase(), add_answer(), add_log()

**Existing SessionStore features:**
- ✓ In-memory storage (_sessions dict)
- ✓ CRUD operations (create_session, get_session, update_session, delete_session)
- ✓ Global instance (session_store)

**Gaps identified:**
1. **Error history details** - Currently only tracks failed_task_ids, but VF-030 requires "error history" with error messages/details
2. **Persistence interface** - VF-031 requires an abstract interface for future disk/DB persistence

## Execution Plan

### 1. Enhance Session model with error history (VF-030)
- Add error_history list to track error details (not just IDs)
- Each error entry should include: timestamp, task_id, error_message, phase
- Add add_error() method to Session class

### 2. Define persistence seam interface (VF-031)
- Create SessionStoreInterface abstract base class
- Define methods: create_session, get_session, update_session, delete_session, list_sessions
- Make SessionStore implement this interface
- Add docstrings explaining the persistence seam

### 3. Write comprehensive tests
- test_session_model.py: Test Session class
  - Phase transitions
  - Artifact tracking
  - Error history
  - Timestamp updates
- test_session_store.py: Test SessionStore
  - CRUD operations
  - Session not found scenarios
  - Multiple sessions
  - Interface compliance

## Done Means
- [x] VF-030: Session model enhanced with error history
  - **Files:** `apps/api/vibeforge_api/core/session.py` (added error_history list, add_error() method)
  - **Features:** Error entries include timestamp, task_id, error_message, phase
  - **Tests:** `apps/api/tests/test_session_model.py` (15 tests covering all Session features)
  - **Verification:** All session model tests passing

- [x] VF-031: SessionStore with persistence interface
  - **Files:** `apps/api/vibeforge_api/core/session.py` (SessionStoreInterface abstract class, SessionStore implementation)
  - **Interface:** SessionStoreInterface defines CRUD + list_sessions methods
  - **Implementation:** SessionStore implements all interface methods with in-memory storage
  - **Tests:** `apps/api/tests/test_session_store.py` (19 tests covering interface and implementation)
  - **Verification:** All store tests passing, interface compliance validated

## Verification Commands
```bash
cd apps/api && pytest tests/test_session_model.py -v
cd apps/api && pytest tests/test_session_store.py -v
cd apps/api && pytest -v
```

## Notes
- Session model and SessionStore already have MVP implementation
- This WP adds error history details and persistence interface
- Maintains backward compatibility with existing code
- Tests validate both existing and new functionality
