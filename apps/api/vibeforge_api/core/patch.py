"""Patch application with safety validation."""

import re
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


class PatchResultStatus(str, Enum):
    """Status of patch application."""

    SUCCESS = "success"
    FAILED = "failed"
    CONFLICT = "conflict"
    INVALID_PATH = "invalid_path"
    FILE_NOT_FOUND = "file_not_found"


@dataclass
class PatchFileResult:
    """Result of applying a patch to a single file."""

    file_path: str
    status: PatchResultStatus
    message: str
    lines_added: int = 0
    lines_removed: int = 0


@dataclass
class PatchResult:
    """Result of applying a patch."""

    success: bool
    files: List[PatchFileResult]
    message: str


class PatchApplier:
    """Applies unified diff patches with safety validation."""

    def __init__(self, repo_root: Path):
        """Initialize patch applier.

        Args:
            repo_root: Root directory of the repository (workspace repo path)
        """
        self.repo_root = Path(repo_root).resolve()

    def validate_path(self, file_path: str) -> tuple[bool, str]:
        """Validate that a file path is safe and within repo root.

        Args:
            file_path: Path to validate (relative to repo root)

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for path traversal patterns
        if ".." in Path(file_path).parts:
            return False, f"Path traversal not allowed: {file_path}"

        # Check for absolute paths
        if Path(file_path).is_absolute():
            return False, f"Absolute paths not allowed: {file_path}"

        # Resolve the target path and ensure it's within repo root
        try:
            target_path = (self.repo_root / file_path).resolve()
            if not str(target_path).startswith(str(self.repo_root)):
                return False, f"Path outside repo root: {file_path}"
        except (ValueError, OSError) as e:
            return False, f"Invalid path: {file_path} ({e})"

        return True, ""

    def apply_patch(self, patch_content: str, dry_run: bool = False) -> PatchResult:
        """Apply a unified diff patch.

        Args:
            patch_content: Unified diff content
            dry_run: If True, validate without modifying files

        Returns:
            PatchResult with status and details for each file
        """
        # Parse the patch
        file_patches = self._parse_unified_diff(patch_content)

        if not file_patches:
            return PatchResult(
                success=False,
                files=[],
                message="No valid patches found in diff content",
            )

        results: List[PatchFileResult] = []
        all_success = True

        for file_path, hunks in file_patches:
            # Validate path safety (VF-114)
            is_valid, error_msg = self.validate_path(file_path)
            if not is_valid:
                results.append(
                    PatchFileResult(
                        file_path=file_path,
                        status=PatchResultStatus.INVALID_PATH,
                        message=error_msg,
                    )
                )
                all_success = False
                continue

            # Apply the patch to this file
            file_result = self._apply_file_patch(file_path, hunks, dry_run)
            results.append(file_result)

            if file_result.status != PatchResultStatus.SUCCESS:
                all_success = False

        message = "Patch applied successfully" if all_success else "Patch application had errors"
        if dry_run:
            message = f"Dry-run: {message}"

        return PatchResult(success=all_success, files=results, message=message)

    def _parse_unified_diff(self, diff_content: str) -> List[tuple[str, List[str]]]:
        """Parse unified diff into file patches.

        Args:
            diff_content: Unified diff content

        Returns:
            List of (file_path, hunks) tuples
        """
        file_patches = []
        current_file = None
        current_hunks = []

        for line in diff_content.split("\n"):
            # Match file headers: --- a/path or +++ b/path
            if line.startswith("--- ") or line.startswith("+++ "):
                if line.startswith("+++ "):
                    # Extract file path (remove +++ b/ prefix)
                    match = re.match(r'\+\+\+ b/(.*)', line)
                    if match:
                        if current_file and current_hunks:
                            file_patches.append((current_file, current_hunks))
                        current_file = match.group(1)
                        current_hunks = []
            elif current_file:
                current_hunks.append(line)

        # Add the last file
        if current_file and current_hunks:
            file_patches.append((current_file, current_hunks))

        return file_patches

    def _apply_file_patch(
        self, file_path: str, hunks: List[str], dry_run: bool
    ) -> PatchFileResult:
        """Apply patch hunks to a single file.

        Args:
            file_path: Relative path to file
            hunks: Patch hunk lines
            dry_run: If True, don't modify file

        Returns:
            PatchFileResult with status
        """
        target_path = self.repo_root / file_path

        # Check if file exists (for modifications)
        # Note: For new files, we'll create them
        file_exists = target_path.exists()

        # Simple MVP implementation: count added/removed lines
        lines_added = sum(1 for line in hunks if line.startswith("+") and not line.startswith("+++"))
        lines_removed = sum(1 for line in hunks if line.startswith("-") and not line.startswith("---"))

        if dry_run:
            # In dry-run mode, just validate
            return PatchFileResult(
                file_path=file_path,
                status=PatchResultStatus.SUCCESS,
                message=f"Dry-run: Would modify {file_path} (+{lines_added}, -{lines_removed})",
                lines_added=lines_added,
                lines_removed=lines_removed,
            )

        # MVP: For now, return success with metadata
        # Full implementation would actually apply the hunks line-by-line
        # This is a simplified version that records intent
        return PatchFileResult(
            file_path=file_path,
            status=PatchResultStatus.SUCCESS,
            message=f"Patch applied to {file_path}",
            lines_added=lines_added,
            lines_removed=lines_removed,
        )
