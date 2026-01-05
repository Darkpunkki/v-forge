"""
Test repository layout to ensure monorepo structure is maintained.

This test validates that all required top-level directories exist
and prevents accidental deletion or restructuring.
"""
import os
from pathlib import Path


def get_repo_root():
    """Get the repository root directory (3 levels up from this file)."""
    return Path(__file__).parent.parent.parent.parent


def test_required_directories_exist():
    """Verify all required top-level directories exist."""
    repo_root = get_repo_root()

    required_dirs = [
        "apps",
        "core",
        "orchestration",
        "models",
        "runtime",
        "storage",
        "configs",
        "schemas",
        "docs",
    ]

    for dir_name in required_dirs:
        dir_path = repo_root / dir_name
        assert dir_path.exists(), f"Required directory missing: {dir_name}"
        assert dir_path.is_dir(), f"Path exists but is not a directory: {dir_name}"


def test_apps_subdirectories_exist():
    """Verify apps/ subdirectories exist."""
    repo_root = get_repo_root()
    apps_dir = repo_root / "apps"

    required_subdirs = ["api", "ui"]

    for subdir_name in required_subdirs:
        subdir_path = apps_dir / subdir_name
        assert subdir_path.exists(), f"Required apps subdirectory missing: {subdir_name}"


def test_core_subdirectories_exist():
    """Verify core/ subdirectories exist."""
    repo_root = get_repo_root()
    core_dir = repo_root / "core"

    required_subdirs = ["gates", "verifiers", "spec"]

    for subdir_name in required_subdirs:
        subdir_path = core_dir / subdir_name
        assert subdir_path.exists(), f"Required core subdirectory missing: {subdir_name}"


def test_orchestration_subdirectories_exist():
    """Verify orchestration/ subdirectories exist."""
    repo_root = get_repo_root()
    orch_dir = repo_root / "orchestration"

    required_subdirs = ["coordinator", "phases", "routing"]

    for subdir_name in required_subdirs:
        subdir_path = orch_dir / subdir_name
        assert subdir_path.exists(), f"Required orchestration subdirectory missing: {subdir_name}"


def test_models_subdirectories_exist():
    """Verify models/ subdirectories exist."""
    repo_root = get_repo_root()
    models_dir = repo_root / "models"

    required_subdirs = ["base", "claude", "openai"]

    for subdir_name in required_subdirs:
        subdir_path = models_dir / subdir_name
        assert subdir_path.exists(), f"Required models subdirectory missing: {subdir_name}"


def test_runtime_subdirectories_exist():
    """Verify runtime/ subdirectories exist."""
    repo_root = get_repo_root()
    runtime_dir = repo_root / "runtime"

    required_subdirs = ["workspace", "commands", "sandbox"]

    for subdir_name in required_subdirs:
        subdir_path = runtime_dir / subdir_name
        assert subdir_path.exists(), f"Required runtime subdirectory missing: {subdir_name}"


def test_storage_subdirectories_exist():
    """Verify storage/ subdirectories exist."""
    repo_root = get_repo_root()
    storage_dir = repo_root / "storage"

    required_subdirs = ["sessions", "artifacts", "events"]

    for subdir_name in required_subdirs:
        subdir_path = storage_dir / subdir_name
        assert subdir_path.exists(), f"Required storage subdirectory missing: {subdir_name}"


def test_readme_files_exist():
    """Verify README.md files exist in major directories."""
    repo_root = get_repo_root()

    required_readmes = [
        "core/README.md",
        "orchestration/README.md",
        "models/README.md",
        "runtime/README.md",
        "storage/README.md",
    ]

    for readme_path in required_readmes:
        full_path = repo_root / readme_path
        assert full_path.exists(), f"Required README missing: {readme_path}"
        assert full_path.is_file(), f"Path exists but is not a file: {readme_path}"
