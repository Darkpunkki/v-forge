"""Run bundle export utilities for observability."""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class RunBundleManifest:
    """Summary metadata for an exported run bundle."""

    session_id: str
    created_at: str
    repo_files: int
    artifact_files: int
    includes_events: bool
    includes_run_summary: bool
    files: list[str]


def export_run_bundle(session_id: str, workspace_root: Path) -> Path:
    """Export a portable run bundle archive for a session.

    Args:
        session_id: Session identifier to export.
        workspace_root: Root path containing session workspaces.

    Returns:
        Path to the created zip archive.

    Raises:
        ValueError: If the session workspace does not exist.
    """
    workspace_path = Path(workspace_root) / session_id
    if not workspace_path.exists():
        raise ValueError(f"Workspace not found for session {session_id}")

    repo_path = workspace_path / "repo"
    artifacts_path = workspace_path / "artifacts"
    events_path = workspace_path / "events.jsonl"

    bundles_path = workspace_path / "bundles"
    bundles_path.mkdir(exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    bundle_path = bundles_path / f"run_bundle_{session_id}_{timestamp}.zip"

    repo_files = list(_iter_files(repo_path))
    artifact_files = list(_iter_files(artifacts_path))
    includes_events = events_path.exists()
    includes_run_summary = (artifacts_path / "run_summary.json").exists()

    file_manifest: list[str] = []

    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        file_manifest.extend(_add_directory(bundle, repo_path, "repo"))
        file_manifest.extend(_add_directory(bundle, artifacts_path, "artifacts"))

        if includes_events:
            bundle.write(events_path, "events.jsonl")
            file_manifest.append("events.jsonl")

        manifest = RunBundleManifest(
            session_id=session_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            repo_files=len(repo_files),
            artifact_files=len(artifact_files),
            includes_events=includes_events,
            includes_run_summary=includes_run_summary,
            files=sorted(file_manifest),
        )

        bundle.writestr("bundle_summary.json", json.dumps(manifest.__dict__, indent=2))

    return bundle_path


def _iter_files(base_path: Path) -> Iterable[Path]:
    if not base_path.exists():
        return []
    return (path for path in base_path.rglob("*") if path.is_file())


def _add_directory(bundle: zipfile.ZipFile, base_path: Path, prefix: str) -> list[str]:
    if not base_path.exists():
        return []
    added_files: list[str] = []
    for file_path in _iter_files(base_path):
        arcname = f"{prefix}/{file_path.relative_to(base_path)}"
        bundle.write(file_path, arcname)
        added_files.append(arcname)
    return added_files
