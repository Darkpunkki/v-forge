"""Tests for agent bridge path sandboxing."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from cli_wrapper import ClaudeInvocationError, _normalize_workdir, resolve_safe_path


def test_normalize_workdir_rejects_traversal(tmp_path: Path) -> None:
    bad_workdir = os.path.join(str(tmp_path), "..", "outside")
    with pytest.raises(ClaudeInvocationError):
        _normalize_workdir(bad_workdir)


def test_resolve_safe_path_allows_relative(tmp_path: Path) -> None:
    base = tmp_path / "workdir"
    base.mkdir()
    target = resolve_safe_path(str(base), "subdir/file.txt")
    assert str(target).startswith(str(base))


def test_resolve_safe_path_rejects_traversal(tmp_path: Path) -> None:
    base = tmp_path / "workdir"
    base.mkdir()
    with pytest.raises(ClaudeInvocationError):
        resolve_safe_path(str(base), "../secret.txt")


def test_resolve_safe_path_rejects_absolute_outside(tmp_path: Path) -> None:
    base = tmp_path / "workdir"
    outside = tmp_path / "outside"
    base.mkdir()
    outside.mkdir()
    with pytest.raises(ClaudeInvocationError):
        resolve_safe_path(str(base), str(outside / "file.txt"))


def test_resolve_safe_path_rejects_symlink_escape(tmp_path: Path) -> None:
    base = tmp_path / "workdir"
    outside = tmp_path / "outside"
    base.mkdir()
    outside.mkdir()

    link_path = base / "link"
    try:
        os.symlink(outside, link_path, target_is_directory=True)
    except OSError:
        pytest.skip("Symlink creation not permitted on this platform")

    with pytest.raises(ClaudeInvocationError):
        resolve_safe_path(str(base), str(link_path / "file.txt"))
