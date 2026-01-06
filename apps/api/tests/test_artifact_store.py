import time

import pytest

from vibeforge_api.core.artifacts import ArtifactStore, SessionArtifactQuery


@pytest.fixture
def artifacts_root(tmp_path):
    root = tmp_path / "workspaces" / "session-1" / "artifacts"
    root.mkdir(parents=True)
    return root


def test_list_and_exists_artifacts(artifacts_root):
    store = ArtifactStore(artifacts_root)
    store.save_artifact("build_spec.json", {"name": "demo"})
    store.save_artifact("concept.json", {"idea": "cool"})

    assert set(store.list_artifacts()) == {"build_spec", "concept"}
    assert store.artifact_exists("build_spec.json")


def test_artifact_metadata_and_delete(artifacts_root):
    store = ArtifactStore(artifacts_root)
    store.save_artifact("result.json", {"status": "ok"})

    metadata = store.get_artifact_metadata("result.json")
    assert metadata["key"] == "result"
    assert metadata["size_bytes"] > 0
    assert metadata["path"].endswith("result.json")

    assert store.delete_artifact("result.json") is True
    assert store.artifact_exists("result.json") is False


def test_session_artifact_query_lists_sessions(tmp_path):
    workspace_root = tmp_path / "workspaces"
    (workspace_root / "s1" / "artifacts").mkdir(parents=True)
    (workspace_root / "s2" / "artifacts").mkdir(parents=True)

    query = SessionArtifactQuery(workspace_root)
    assert set(query.list_sessions()) == {"s1", "s2"}


def test_session_artifact_query_returns_artifacts(tmp_path):
    workspace_root = tmp_path / "workspaces"
    artifacts_path = workspace_root / "s1" / "artifacts"
    artifacts_path.mkdir(parents=True)
    store = ArtifactStore(artifacts_path)
    store.save_artifact("build_spec.json", {"name": "demo"})
    store.save_artifact("concept.json", {"idea": "cool"})

    query = SessionArtifactQuery(workspace_root)
    artifacts = query.get_session_artifacts("s1")
    assert set(artifacts) == {"build_spec", "concept"}


def test_query_sessions_by_date_filters(tmp_path):
    workspace_root = tmp_path / "workspaces"
    session_one = workspace_root / "s1" / "artifacts"
    session_two = workspace_root / "s2" / "artifacts"
    session_one.mkdir(parents=True)
    time.sleep(0.01)
    session_two.mkdir(parents=True)

    query = SessionArtifactQuery(workspace_root)
    start = session_two.parent.stat().st_mtime - 0.001
    results = query.query_sessions_by_date(start_date=start)

    assert len(results) == 1
    assert results[0]["session_id"] == "s2"


def test_get_session_summary_counts_artifacts(tmp_path):
    workspace_root = tmp_path / "workspaces"
    artifacts_path = workspace_root / "s3" / "artifacts"
    artifacts_path.mkdir(parents=True)
    store = ArtifactStore(artifacts_path)
    store.save_artifact("artifact.json", {"value": 1})

    query = SessionArtifactQuery(workspace_root)
    summary = query.get_session_summary("s3")

    assert summary["session_id"] == "s3"
    assert summary["artifact_count"] == 1
    assert summary["artifacts"] == ["artifact"]
