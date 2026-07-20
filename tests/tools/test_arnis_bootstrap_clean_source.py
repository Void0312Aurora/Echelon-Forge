"""Pinned-build integrity: the working tree must be exactly commit + patch.

A cached source checkout could carry extra tracked edits or untracked files
(e.g. a `.cargo/config.toml` build hook) that `cargo build` would execute,
after which the install metadata would falsely record a pinned build. The
bootstrap compares the working tree against the expected tree (pinned commit
plus pinned patch, materialized in an isolated git index) and fails closed
on any deviation -- including edits inside files the patch touches, which
hunk-context checks cannot see, and including the patch's own new files,
which a plain `git status` reports as untracked.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

import tools.environment.arnis.bootstrap as bootstrap
from tools.environment.arnis.bootstrap import ArnisBootstrapError, _ensure_patch_applied


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ("git", *args),
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


@pytest.fixture()
def pinned_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, dict]:
    """A pinned commit plus a synthetic patch that edits AND adds files."""
    repo = tmp_path / "arnis-src"
    repo.mkdir()
    _git(repo, "init", "--quiet")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "src").mkdir()
    (repo / "src" / "main.rs").write_text(
        "fn main() {\n    one();\n    two();\n    three();\n}\n", encoding="utf-8"
    )
    (repo / "Cargo.toml").write_text('[package]\nname = "arnis"\n', encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "--quiet", "-m", "pinned")
    commit = _git(repo, "rev-parse", "HEAD")

    # Author the patch with git itself so the format (incl. new-file hunks)
    # is exactly what `git apply` expects; then restore the pinned state.
    (repo / "src" / "main.rs").write_text(
        "fn main() {\n    one();\n    two_patched();\n    three();\n}\n", encoding="utf-8"
    )
    (repo / "src" / "cmo_export.rs").write_text("pub fn export() {}\n", encoding="utf-8")
    _git(repo, "add", "-A")
    patch_text = _git(repo, "diff", "--cached", "--binary")
    _git(repo, "reset", "--hard", commit, "--quiet")
    _git(repo, "clean", "-fd", "--quiet")

    patch_path = tmp_path / "pinned.patch"
    # newline="\n": Windows would otherwise translate to CRLF and corrupt
    # the patch relative to the LF content in the repository.
    with patch_path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(patch_text + "\n")
    monkeypatch.setattr(bootstrap, "_PATCH_PATH", patch_path)

    lock = {"upstream": {"commit": commit}}
    return repo, lock


def test_first_run_applies_patch_with_new_files(pinned_repo: tuple[Path, dict]) -> None:
    # Regression: the patch adds src/cmo_export.rs, which plain `git apply`
    # leaves untracked. A fresh checkout's first bootstrap must succeed.
    repo, lock = pinned_repo
    _ensure_patch_applied(repo, lock)
    assert (repo / "src" / "cmo_export.rs").is_file()
    assert "two_patched" in (repo / "src" / "main.rs").read_text(encoding="utf-8")


def test_second_run_is_idempotent(pinned_repo: tuple[Path, dict]) -> None:
    repo, lock = pinned_repo
    _ensure_patch_applied(repo, lock)
    _ensure_patch_applied(repo, lock)  # already-patched branch must pass


def test_injection_inside_patched_file_rejected(pinned_repo: tuple[Path, dict]) -> None:
    # Regression: an extra edit in a file the patch touches, outside the
    # patch hunks, slips past `git apply --reverse --check` + path allowlists.
    # The tree comparison must reject it.
    repo, lock = pinned_repo
    _ensure_patch_applied(repo, lock)
    main_rs = repo / "src" / "main.rs"
    main_rs.write_text(
        main_rs.read_text(encoding="utf-8") + "fn injected_build_hook() {}\n", encoding="utf-8"
    )
    with pytest.raises(ArnisBootstrapError, match="refusing to build"):
        _ensure_patch_applied(repo, lock)


def test_untracked_cargo_config_rejected(pinned_repo: tuple[Path, dict]) -> None:
    repo, lock = pinned_repo
    _ensure_patch_applied(repo, lock)
    cargo_dir = repo / ".cargo"
    cargo_dir.mkdir()
    (cargo_dir / "config.toml").write_text('[build]\nrustc-wrapper = "evil"\n', encoding="utf-8")
    with pytest.raises(ArnisBootstrapError, match="refusing to build"):
        _ensure_patch_applied(repo, lock)


def test_gitignore_hidden_cargo_config_rejected(pinned_repo: tuple[Path, dict]) -> None:
    # Exclude rules are attacker-writable in a cached checkout: hiding the
    # injected file via .git/info/exclude must not bypass the tree check.
    repo, lock = pinned_repo
    _ensure_patch_applied(repo, lock)
    exclude = repo / ".git" / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    exclude.write_text(".cargo/\n", encoding="utf-8")
    cargo_dir = repo / ".cargo"
    cargo_dir.mkdir()
    (cargo_dir / "config.toml").write_text('[build]\nrustc-wrapper = "evil"\n', encoding="utf-8")
    with pytest.raises(ArnisBootstrapError, match="refusing to build"):
        _ensure_patch_applied(repo, lock)


def test_dirty_unpatched_checkout_rejected(pinned_repo: tuple[Path, dict]) -> None:
    repo, lock = pinned_repo
    (repo / "Cargo.toml").write_text(
        '[package]\nname = "arnis"\n[build]\nscript = "evil.rs"\n', encoding="utf-8"
    )
    with pytest.raises(ArnisBootstrapError, match="refusing to build"):
        _ensure_patch_applied(repo, lock)


def test_deleted_patched_file_rejected(pinned_repo: tuple[Path, dict]) -> None:
    repo, lock = pinned_repo
    _ensure_patch_applied(repo, lock)
    (repo / "src" / "cmo_export.rs").unlink()
    with pytest.raises(ArnisBootstrapError, match="refusing to build"):
        _ensure_patch_applied(repo, lock)


def test_real_pinned_patch_is_parseable() -> None:
    # The real patch must stay machine-appliable (it adds new files, which is
    # exactly why the verification works on tree identity, not `git status`).
    from tools.environment.arnis.bootstrap import _PATCH_PATH

    assert _PATCH_PATH.is_file()
    result = subprocess.run(
        ("git", "apply", "--stat", str(_PATCH_PATH)),
        capture_output=True,
        text=True,
        check=True,
    )
    assert "cmo_export.rs" in result.stdout
