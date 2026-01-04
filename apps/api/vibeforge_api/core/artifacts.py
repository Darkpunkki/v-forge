"""Artifact storage for session data and metadata."""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class PatchMetadata:
    """Metadata for a patch application."""

    task_id: str
    timestamp: str
    diff_content: str
    apply_outcome: str  # "success", "failed", "conflict"
    affected_files: list[str]
    lines_added: int
    lines_removed: int
    error_message: Optional[str] = None


class ArtifactStore:
    """Stores and retrieves session artifacts."""

    def __init__(self, artifacts_root: Path):
        """Initialize artifact store.

        Args:
            artifacts_root: Root directory for artifacts (workspace artifacts/ path)
        """
        self.artifacts_root = Path(artifacts_root)
        self.artifacts_root.mkdir(parents=True, exist_ok=True)

    def save_patch_metadata(self, metadata: PatchMetadata) -> Path:
        """Save patch metadata to artifacts directory.

        Args:
            metadata: PatchMetadata to save

        Returns:
            Path to saved metadata file
        """
        # Create patches subdirectory
        patches_dir = self.artifacts_root / "patches"
        patches_dir.mkdir(exist_ok=True)

        # Generate filename: patch_{task_id}_{timestamp}.json
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"patch_{metadata.task_id}_{timestamp}.json"
        file_path = patches_dir / filename

        # Save as JSON
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(asdict(metadata), f, indent=2)

        return file_path

    def get_patch_metadata(self, task_id: str) -> Optional[PatchMetadata]:
        """Retrieve patch metadata for a task.

        Args:
            task_id: Task identifier

        Returns:
            PatchMetadata if found, None otherwise
        """
        patches_dir = self.artifacts_root / "patches"
        if not patches_dir.exists():
            return None

        # Find files matching task_id
        pattern = f"patch_{task_id}_*.json"
        matching_files = list(patches_dir.glob(pattern))

        if not matching_files:
            return None

        # Get the most recent one
        latest_file = max(matching_files, key=lambda p: p.stat().st_mtime)

        # Load and return
        with open(latest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return PatchMetadata(**data)

    def list_patch_metadata(self) -> list[PatchMetadata]:
        """List all patch metadata.

        Returns:
            List of PatchMetadata, sorted by timestamp (newest first)
        """
        patches_dir = self.artifacts_root / "patches"
        if not patches_dir.exists():
            return []

        metadata_list = []
        for file_path in patches_dir.glob("patch_*.json"):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                metadata_list.append(PatchMetadata(**data))

        # Sort by timestamp (newest first)
        metadata_list.sort(key=lambda m: m.timestamp, reverse=True)
        return metadata_list

    def save_artifact(self, name: str, content: Any, subdir: Optional[str] = None):
        """Save a generic artifact.

        Args:
            name: Artifact name (will be used as filename)
            content: Content to save (dict/list will be JSON, str will be text)
            subdir: Optional subdirectory within artifacts
        """
        target_dir = self.artifacts_root
        if subdir:
            target_dir = target_dir / subdir
            target_dir.mkdir(exist_ok=True)

        file_path = target_dir / name

        if isinstance(content, (dict, list)):
            # Save as JSON
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2)
        else:
            # Save as text
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(str(content))

    def get_artifact(self, name: str, subdir: Optional[str] = None) -> Optional[str]:
        """Retrieve a generic artifact.

        Args:
            name: Artifact name
            subdir: Optional subdirectory within artifacts

        Returns:
            Content as string if found, None otherwise
        """
        target_dir = self.artifacts_root
        if subdir:
            target_dir = target_dir / subdir

        file_path = target_dir / name

        if not file_path.exists():
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()


class SessionArtifactStore:
    """Global artifact store that works with session IDs."""

    def __init__(self):
        """Initialize session artifact store."""
        pass

    def _get_artifacts_path(self, session_id: str) -> Path:
        """Get artifacts path for a session using workspace manager."""
        from vibeforge_api.core.workspace import workspace_manager

        return workspace_manager.get_artifacts_path(session_id)

    def save_artifact(
        self, session_id: str, name: str, content: Any, subdir: Optional[str] = None
    ):
        """Save an artifact for a session.

        Args:
            session_id: Session identifier
            name: Artifact name (will be used as filename)
            content: Content to save (dict/list will be JSON, str will be text)
            subdir: Optional subdirectory within artifacts
        """
        artifacts_root = self._get_artifacts_path(session_id)
        store = ArtifactStore(artifacts_root)
        store.save_artifact(name, content, subdir)

    def get_artifact(
        self, session_id: str, name: str, subdir: Optional[str] = None
    ) -> Optional[str]:
        """Retrieve an artifact for a session.

        Args:
            session_id: Session identifier
            name: Artifact name
            subdir: Optional subdirectory within artifacts

        Returns:
            Content as string if found, None otherwise
        """
        artifacts_root = self._get_artifacts_path(session_id)
        store = ArtifactStore(artifacts_root)
        return store.get_artifact(name, subdir)

    def save_patch_metadata(self, session_id: str, metadata: PatchMetadata) -> Path:
        """Save patch metadata for a session.

        Args:
            session_id: Session identifier
            metadata: PatchMetadata to save

        Returns:
            Path to saved metadata file
        """
        artifacts_root = self._get_artifacts_path(session_id)
        store = ArtifactStore(artifacts_root)
        return store.save_patch_metadata(metadata)

    def get_patch_metadata(
        self, session_id: str, task_id: str
    ) -> Optional[PatchMetadata]:
        """Retrieve patch metadata for a task in a session.

        Args:
            session_id: Session identifier
            task_id: Task identifier

        Returns:
            PatchMetadata if found, None otherwise
        """
        artifacts_root = self._get_artifacts_path(session_id)
        store = ArtifactStore(artifacts_root)
        return store.get_patch_metadata(task_id)

    def list_patch_metadata(self, session_id: str) -> list[PatchMetadata]:
        """List all patch metadata for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of PatchMetadata, sorted by timestamp (newest first)
        """
        artifacts_root = self._get_artifacts_path(session_id)
        store = ArtifactStore(artifacts_root)
        return store.list_patch_metadata()


# Global session artifact store instance
artifact_store = SessionArtifactStore()
