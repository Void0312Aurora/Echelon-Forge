"""Pinned-build integrity: the Arnis bootstrap must reject dirty checkouts.

A cached source checkout could carry extra tracked edits or untracked files
(e.g. a `.cargo/config.toml` build hook) that `cargo build` would execute,
after which the install metadata would falsely record a pinned build. The
bootstrap fails closed on any deviation from pinned-commit(+patch).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tools.environment.arnis.bootstrap import (
    ArnisBootstrapError,
    _PATCH_PATH,
    _patch_file_paths,
    _verify_clean_worktree,
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ("git", *args),
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture()
def pinned_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "arnis-src"
    repo.mkdir()
    _git(repo, "init", "--quiet")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "src").mkdir()
    (repo / "src" / "main.rs").write_text("fn main() {}\n", encoding="utf-8")
    (repo / "Cargo.toml").write_text("[package]\nname = \"arnis\"\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "--quiet", "-m", "pinned")
    return repo


def test_clean_unpatched_checkout_passes(pinned_repo: Path) -> None:
    _verify_clean_worktree(pinned_repo, patch_applied=False)


def test_tracked_modification_rejected_before_patching(pinned_repo: Path) -> None:
    (pinned_repo / "src" / "main.rs").write_text("fn main() { evil(); }\n", encoding="utf-8")
    with pytest.raises(ArnisBootstrapError, match="unexpected modifications"):
        _verify_clean_worktree(pinned_repo, patch_applied=False)


def test_untracked_cargo_config_rejected(pinned_repo: Path) -> None:
    cargo_dir = pinned_repo / ".cargo"
    cargo_dir.mkdir()
    (cargo_dir / "config.toml").write_text("[build]\nrustc-wrapper = \"evil\"\n", encoding="utf-8")
    with pytest.raises(ArnisBootstrapError, match="untracked files"):
        _verify_clean_worktree(pinned_repo, patch_applied=False)


def test_untracked_files_rejected_even_when_patched(pinned_repo: Path) -> None:
    (pinned_repo / "extra.rs").write_text("// stray\n", encoding="utf-8")
    with pytest.raises(ArnisBootstrapError, match="untracked files"):
        _verify_clean_worktree(pinned_repo, patch_applied=True)


def test_tracked_modification_outside_patch_rejected_when_patched(pinned_repo: Path) -> None:
    # A tracked edit to a file the pinned patch does not touch must fail even
    # if git-apply --reverse --check happens to succeed for the patch itself.
    (pinned_repo / "Cargo.toml").write_text(
        "[package]\nname = \"arnis\"\n[build]\nscript = \"evil.rs\"\n", encoding="utf-8"
    )
    with pytest.raises(ArnisBootstrapError):
        _verify_clean_worktree(pinned_repo, patch_applied=True)


def test_patch_file_paths_parse_pinned_patch() -> None:
    assert _PATCH_PATH.is_file()
    paths = _patch_file_paths()
    assert len(paths) > 0
    assert all(isinstance(p, str) and p for p in paths)
