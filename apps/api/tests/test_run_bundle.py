"""Tests for run bundle export utilities."""

import json
import zipfile

from vibeforge_api.core.run_bundle import export_run_bundle
from vibeforge_api.core.workspace import WorkspaceManager


def test_export_run_bundle_includes_expected_files(tmp_path):
    """Ensure run bundles include repo, artifacts, and summary metadata."""
    workspace_manager = WorkspaceManager(str(tmp_path / "workspaces"))
    session_id = "session-1"
    workspace_path = workspace_manager.init_repo(session_id)

    (workspace_path / "repo" / "main.py").write_text("print('hello')")
    (workspace_path / "artifacts" / "run_summary.json").write_text("{}")
    (workspace_path / "artifacts" / "extra.json").write_text("{\"key\": \"value\"}")
    (workspace_path / "events.jsonl").write_text("{\"event\": \"test\"}\n")

    bundle_path = export_run_bundle(session_id, workspace_manager.workspace_root)

    assert bundle_path.exists()

    with zipfile.ZipFile(bundle_path) as bundle:
        names = set(bundle.namelist())
        assert "repo/README.md" in names
        assert "repo/main.py" in names
        assert "artifacts/run_summary.json" in names
        assert "artifacts/extra.json" in names
        assert "events.jsonl" in names
        assert "bundle_summary.json" in names

        summary = json.loads(bundle.read("bundle_summary.json"))
        assert summary["session_id"] == session_id
        assert summary["includes_run_summary"] is True
