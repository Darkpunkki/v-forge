"""RepoContextLoader for task-scoped context selection (VF-151)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

DEFAULT_CONTEXT_BUDGET_BYTES = 40_000


@dataclass(frozen=True)
class RepoContextFile:
    """Represents a single file loaded into task context."""

    path: str
    content: str
    truncated: bool = False


class RepoContextLoader:
    """Select a bounded set of repo files for task context."""

    @staticmethod
    def select_files(
        repo_path: Path,
        files_to_read: Iterable[str],
        max_bytes: int | None = DEFAULT_CONTEXT_BUDGET_BYTES,
        context_notes: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        """
        Load task-scoped context files with a byte budget.

        Args:
            repo_path: Root path of the repo.
            files_to_read: Relative file paths to include.
            max_bytes: Maximum bytes to include across all files.
            context_notes: Optional context notes from the task inputs.

        Returns:
            Dictionary containing selected files and metadata.
        """
        resolved_repo = repo_path.resolve()
        selected: list[RepoContextFile] = []
        warnings: list[str] = []
        total_bytes = 0

        for rel_path in files_to_read:
            if max_bytes is not None and total_bytes >= max_bytes:
                warnings.append("Context budget reached; remaining files skipped.")
                break

            candidate = (resolved_repo / rel_path).resolve()
            if not _is_within_repo(resolved_repo, candidate):
                warnings.append(f"Skipped path outside repo: {rel_path}")
                continue

            if not candidate.exists() or not candidate.is_file():
                warnings.append(f"File not found: {rel_path}")
                continue

            content = candidate.read_text(encoding="utf-8", errors="replace")
            content_bytes = content.encode("utf-8")

            truncated = False
            if max_bytes is not None and total_bytes + len(content_bytes) > max_bytes:
                remaining = max_bytes - total_bytes
                if remaining <= 0:
                    warnings.append("Context budget reached; remaining files skipped.")
                    break
                content_bytes = content_bytes[:remaining]
                content = content_bytes.decode("utf-8", errors="replace")
                truncated = True

            selected.append(
                RepoContextFile(path=rel_path, content=content, truncated=truncated)
            )
            total_bytes += len(content_bytes)

        return {
            "files": [file.__dict__ for file in selected],
            "total_bytes": total_bytes,
            "budget_bytes": max_bytes,
            "context_notes": list(context_notes or []),
            "warnings": warnings,
        }


def _is_within_repo(repo_path: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(repo_path)
    except ValueError:
        return False
    return True
