"""Tests for SessionStore and SessionStoreInterface."""

import pytest

from vibeforge_api.core.session import Session, SessionStore, SessionStoreInterface
from vibeforge_api.models.types import SessionPhase


class TestSessionStoreInterface:
    """Test SessionStoreInterface abstract base class."""

    def test_interface_is_abstract(self):
        """Test that SessionStoreInterface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            SessionStoreInterface()

    def test_interface_defines_required_methods(self):
        """Test that interface defines all required abstract methods."""
        required_methods = [
            "create_session",
            "get_session",
            "update_session",
            "delete_session",
            "list_sessions",
        ]

        for method in required_methods:
            assert hasattr(SessionStoreInterface, method)

    def test_session_store_implements_interface(self):
        """Test that SessionStore implements SessionStoreInterface."""
        store = SessionStore()
        assert isinstance(store, SessionStoreInterface)


class TestSessionStore:
    """Test SessionStore in-memory implementation."""

    def test_initialization(self):
        """Test SessionStore initializes empty."""
        store = SessionStore()
        assert store.list_sessions() == []

    def test_create_session(self):
        """Test VF-031: creating a new session."""
        store = SessionStore()

        session = store.create_session()

        assert session is not None
        assert session.session_id is not None
        assert session.phase == SessionPhase.QUESTIONNAIRE
        assert store.list_sessions() == [session.session_id]

    def test_create_multiple_sessions(self):
        """Test creating multiple sessions."""
        store = SessionStore()

        session1 = store.create_session()
        session2 = store.create_session()
        session3 = store.create_session()

        assert len(store.list_sessions()) == 3
        assert session1.session_id != session2.session_id
        assert session2.session_id != session3.session_id

    def test_get_session(self):
        """Test VF-031: retrieving a session by ID."""
        store = SessionStore()
        session = store.create_session()

        retrieved = store.get_session(session.session_id)

        assert retrieved is not None
        assert retrieved.session_id == session.session_id
        assert retrieved is session  # Should be same instance

    def test_get_session_not_found(self):
        """Test getting non-existent session returns None."""
        store = SessionStore()

        retrieved = store.get_session("nonexistent-id")

        assert retrieved is None

    def test_update_session(self):
        """Test VF-031: updating a session."""
        store = SessionStore()
        session = store.create_session()

        # Modify session
        session.phase = SessionPhase.BUILD_SPEC
        session.add_log("Test log")

        # Update store
        store.update_session(session)

        # Retrieve and verify
        retrieved = store.get_session(session.session_id)
        assert retrieved.phase == SessionPhase.BUILD_SPEC
        assert len(retrieved.logs) == 1

    def test_delete_session(self):
        """Test VF-031: deleting a session."""
        store = SessionStore()
        session = store.create_session()
        session_id = session.session_id

        assert store.get_session(session_id) is not None

        store.delete_session(session_id)

        assert store.get_session(session_id) is None
        assert session_id not in store.list_sessions()

    def test_delete_nonexistent_session(self):
        """Test deleting non-existent session doesn't raise error."""
        store = SessionStore()

        # Should not raise error
        store.delete_session("nonexistent-id")

    def test_list_sessions(self):
        """Test VF-031: listing all session IDs."""
        store = SessionStore()

        session1 = store.create_session()
        session2 = store.create_session()
        session3 = store.create_session()

        session_ids = store.list_sessions()

        assert len(session_ids) == 3
        assert session1.session_id in session_ids
        assert session2.session_id in session_ids
        assert session3.session_id in session_ids

    def test_list_sessions_empty(self):
        """Test listing sessions when store is empty."""
        store = SessionStore()

        assert store.list_sessions() == []

    def test_list_sessions_after_deletion(self):
        """Test list updates after deleting a session."""
        store = SessionStore()

        session1 = store.create_session()
        session2 = store.create_session()

        store.delete_session(session1.session_id)

        session_ids = store.list_sessions()
        assert len(session_ids) == 1
        assert session2.session_id in session_ids
        assert session1.session_id not in session_ids

    def test_session_isolation(self):
        """Test that sessions are isolated from each other."""
        store = SessionStore()

        session1 = store.create_session()
        session2 = store.create_session()

        session1.add_log("Log for session 1")
        session2.add_log("Log for session 2")

        assert len(session1.logs) == 1
        assert len(session2.logs) == 1
        assert "session 1" in session1.logs[0]
        assert "session 2" in session2.logs[0]

    def test_session_persistence_across_operations(self):
        """Test that session state persists across store operations."""
        store = SessionStore()

        # Create and modify session
        session = store.create_session()
        session_id = session.session_id
        session.add_answer("q1", "answer1")
        session.add_log("test log")
        session.add_error("task-1", "test error")
        store.update_session(session)

        # Retrieve and verify all state
        retrieved = store.get_session(session_id)
        assert retrieved.answers["q1"] == "answer1"
        assert len(retrieved.logs) == 1
        assert len(retrieved.error_history) == 1
        assert retrieved.error_history[0]["task_id"] == "task-1"

    def test_update_creates_if_not_exists(self):
        """Test that update_session works even for new sessions."""
        store = SessionStore()

        # Create session without using create_session
        session = Session(session_id="custom-123")
        session.add_log("Custom session")

        # Update should work
        store.update_session(session)

        # Should be retrievable
        retrieved = store.get_session("custom-123")
        assert retrieved is not None
        assert retrieved.session_id == "custom-123"

    def test_global_instance_available(self):
        """Test that global session_store instance is available."""
        from vibeforge_api.core.session import session_store

        assert session_store is not None
        assert isinstance(session_store, SessionStore)
        assert isinstance(session_store, SessionStoreInterface)

    def test_multiple_store_instances_independent(self):
        """Test that multiple SessionStore instances are independent."""
        store1 = SessionStore()
        store2 = SessionStore()

        session1 = store1.create_session()
        session2 = store2.create_session()

        # Sessions should not be visible across stores
        assert store1.get_session(session2.session_id) is None
        assert store2.get_session(session1.session_id) is None
        assert len(store1.list_sessions()) == 1
        assert len(store2.list_sessions()) == 1
