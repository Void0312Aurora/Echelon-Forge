from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Sequence


_HERE = Path(__file__).resolve().parent
_LOCK_PATH = _HERE / "upstream.lock.json"
_PATCH_PATH = _HERE / "patches" / "0001-cmo-continuous-bundle-export-v1.patch"


class ArnisBootstrapError(RuntimeError):
    pass


def _load_lock() -> dict[str, Any]:
    try:
        value = json.loads(_LOCK_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ArnisBootstrapError(f"failed to read {_LOCK_PATH}: {exc}") from exc
    if not isinstance(value, dict):
        raise ArnisBootstrapError("Arnis upstream lock must be a JSON object")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=cwd,
        env=env,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _default_source_dir(lock: dict[str, Any]) -> Path:
    upstream = lock["upstream"]
    suffix = (
        f"v{upstream['version']}-{upstream['commit'][:12]}-{lock['install_id'].split('-', 1)[-1]}"
    )
    return Path.home() / ".cache" / "cmo" / "third_party" / "arnis" / suffix


def _default_build_dir(lock: dict[str, Any]) -> Path:
    return Path.home() / ".cache" / "cmo" / "build" / "arnis" / str(lock["install_id"])


def _default_install_dir(lock: dict[str, Any]) -> Path:
    return Path.home() / ".local" / "opt" / "arnis-cmo" / str(lock["install_id"])


def _verify_patch(lock: dict[str, Any]) -> None:
    expected = str(lock["patch"]["sha256"])
    if not _PATCH_PATH.is_file():
        raise ArnisBootstrapError(f"missing Arnis patch: {_PATCH_PATH}")
    actual = _sha256(_PATCH_PATH)
    if actual != expected:
        raise ArnisBootstrapError(
            f"Arnis patch checksum mismatch: expected {expected}, got {actual}"
        )


def _ensure_checkout(lock: dict[str, Any], source_dir: Path) -> None:
    upstream = lock["upstream"]
    if not source_dir.exists():
        source_dir.parent.mkdir(parents=True, exist_ok=True)
        _run(
            (
                "git",
                "clone",
                # Filter-free checkout: on-disk bytes must equal blob bytes
                # so the raw-byte verification can compare them directly.
                "-c",
                "core.autocrlf=false",
                "-c",
                "core.filemode=false",
                "--filter=blob:none",
                "--no-checkout",
                str(upstream["repository"]),
                str(source_dir),
            )
        )
        _run(("git", "checkout", "--detach", str(upstream["commit"])), cwd=source_dir)
    if not (source_dir / ".git").is_dir():
        raise ArnisBootstrapError(f"source path is not a git checkout: {source_dir}")
    revision = _run(("git", "rev-parse", "HEAD"), cwd=source_dir).stdout.strip()
    if revision != upstream["commit"]:
        raise ArnisBootstrapError(
            f"Arnis checkout revision mismatch: expected {upstream['commit']}, got {revision}"
        )


def _git_tree_id(source_dir: Path, index_file: Path, *setup: tuple[str, ...]) -> str:
    """Run git commands against an isolated index and return `write-tree`."""
    env = dict(os.environ)
    env["GIT_INDEX_FILE"] = str(index_file)
    for command in setup:
        _run(("git", *command), cwd=source_dir, env=env)
    return _run(("git", "write-tree"), cwd=source_dir, env=env).stdout.strip()


def _expected_patched_tree_id(source_dir: Path, pinned_commit: str) -> str:
    """Tree id of exactly pinned-commit + pinned-patch, built in isolation."""
    with tempfile.TemporaryDirectory(prefix="arnis-verify-") as tmp:
        index_file = Path(tmp) / "expected-index"
        return _git_tree_id(
            source_dir,
            index_file,
            ("read-tree", pinned_commit),
            ("apply", "--cached", str(_PATCH_PATH)),
        )


def _git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _expected_blobs(source_dir: Path, tree_id: str) -> dict[str, str]:
    """path -> blob sha map for a tree, read straight from the object db."""
    listing = _run(("git", "ls-tree", "-r", "-z", tree_id), cwd=source_dir).stdout
    blobs: dict[str, str] = {}
    for record in listing.split("\0"):
        if not record:
            continue
        meta, _tab, path = record.partition("\t")
        parts = meta.split()
        if len(parts) < 3:
            raise ArnisBootstrapError(f"unparseable ls-tree record: {record!r}")
        blobs[path] = parts[2]
    return blobs


def _actual_raw_blobs(source_dir: Path) -> dict[str, str]:
    """path -> blob sha map hashed from raw on-disk bytes.

    Deliberately avoids `git add`/`git hash-object` on the worktree: those
    honor repository-local clean filters and .git/info/attributes, which are
    attacker-writable in a cached checkout -- a poisoned filter could hash
    "expected" bytes while cargo reads modified files, or execute code during
    verification. Hashing raw bytes with hashlib has no such hooks.
    """
    blobs: dict[str, str] = {}
    for path in sorted(source_dir.rglob("*")):
        if path.is_dir():
            continue
        relative = path.relative_to(source_dir).as_posix()
        if relative == ".git" or relative.startswith(".git/"):
            continue
        blobs[relative] = _git_blob_sha1(path.read_bytes())
    return blobs


def _verify_worktree_matches_tree(
    source_dir: Path, expected_tree: str, *, context: str
) -> None:
    """Fail closed unless on-disk bytes exactly match the expected tree.

    Compares raw file bytes (what cargo will actually read) against the blob
    ids of the expected tree. This covers tracked edits, untracked additions
    (ignored or not), deletions, and content smuggled behind clean filters.
    Requires a filter-free checkout (core.autocrlf=false); a legacy checkout
    that was smudged on disk fails closed and should be re-cloned.
    """
    expected = _expected_blobs(source_dir, expected_tree)
    actual = _actual_raw_blobs(source_dir)
    if expected == actual:
        return
    deviations: list[str] = []
    for path in sorted(set(expected) | set(actual)):
        want = expected.get(path)
        got = actual.get(path)
        if want == got:
            continue
        if want is None:
            deviations.append(f"added      {path}")
        elif got is None:
            deviations.append(f"missing    {path}")
        else:
            deviations.append(f"modified   {path}")
    raise ArnisBootstrapError(
        f"Arnis checkout does not match {context}; refusing to build. "
        "Deviations:\n" + "\n".join(deviations[:40])
    )


def _ensure_patch_applied(source_dir: Path, lock: dict[str, Any]) -> None:
    """Ensure the working tree is exactly pinned-commit + pinned-patch.

    A cached checkout could carry extra tracked edits or untracked files
    (e.g. a .cargo/config.toml build hook) that cargo would execute, after
    which the install metadata would falsely record a pinned build. The
    working tree is therefore compared against the expected tree derived in
    an isolated index; any deviation fails closed.
    """
    pinned_commit = str(lock["upstream"]["commit"])
    expected_patched = _expected_patched_tree_id(source_dir, pinned_commit)
    actual = _actual_raw_blobs(source_dir)
    if actual == _expected_blobs(source_dir, expected_patched):
        return
    pinned_tree = _run(
        ("git", "rev-parse", f"{pinned_commit}^{{tree}}"), cwd=source_dir
    ).stdout.strip()
    if actual != _expected_blobs(source_dir, pinned_tree):
        # Neither pristine nor exactly-patched: refuse to touch it.
        _verify_worktree_matches_tree(
            source_dir, pinned_tree, context="the pinned commit (before patching)"
        )
    _run(("git", "apply", str(_PATCH_PATH)), cwd=source_dir)
    _verify_worktree_matches_tree(
        source_dir, expected_patched, context="pinned commit + pinned patch"
    )


def _install_binary(
    lock: dict[str, Any],
    *,
    source_dir: Path,
    build_dir: Path,
    install_dir: Path,
) -> Path:
    cargo = shutil.which("cargo")
    if cargo is None:
        user_cargo = Path.home() / ".cargo" / "bin" / "cargo"
        if user_cargo.is_file():
            cargo = str(user_cargo)
    if cargo is None:
        raise ArnisBootstrapError(
            "cargo is required; install the stable Rust toolchain before preparing Arnis"
        )
    build_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["CARGO_TARGET_DIR"] = str(build_dir)
    command = [cargo, "build"] + list(lock["build"]["cargo_arguments"])
    completed = _run(command, cwd=source_dir, env=env, check=False)
    if completed.returncode != 0:
        raise ArnisBootstrapError(f"Arnis build failed:\n{completed.stdout}\n{completed.stderr}")
    built_binary = build_dir / "release" / "arnis"
    if not built_binary.is_file():
        raise ArnisBootstrapError(f"built Arnis binary is missing: {built_binary}")
    install_dir.mkdir(parents=True, exist_ok=True)
    installed_binary = install_dir / "arnis-cmo"
    shutil.copy2(built_binary, installed_binary)
    installed_binary.chmod(installed_binary.stat().st_mode | 0o111)
    metadata = {
        "install_id": lock["install_id"],
        "patch_sha256": lock["patch"]["sha256"],
        "source_revision": lock["upstream"]["commit"],
    }
    (install_dir / "installation.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return installed_binary


def _is_managed_install_binary(target: Path, managed_root: Path) -> bool:
    try:
        resolved = target.resolve(strict=True)
        root = managed_root.resolve(strict=True)
    except OSError:
        return False
    if resolved.name != "arnis-cmo" or resolved.parent.parent != root:
        return False
    metadata_path = resolved.parent / "installation.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(metadata, dict):
        return False
    patch_sha256 = metadata.get("patch_sha256")
    source_revision = metadata.get("source_revision")
    return (
        metadata.get("install_id") == resolved.parent.name
        and isinstance(patch_sha256, str)
        and len(patch_sha256) == 64
        and all(char in "0123456789abcdef" for char in patch_sha256)
        and isinstance(source_revision, str)
        and len(source_revision) == 40
        and all(char in "0123456789abcdef" for char in source_revision)
    )


def _ensure_command_link(installed_binary: Path, command_link: Path) -> None:
    command_link.parent.mkdir(parents=True, exist_ok=True)
    if command_link.is_symlink():
        if command_link.resolve() == installed_binary.resolve():
            return
        current_target = command_link.resolve(strict=False)
        managed_root = installed_binary.parent.parent
        if _is_managed_install_binary(current_target, managed_root):
            command_link.unlink()
            command_link.symlink_to(installed_binary)
            return
        raise ArnisBootstrapError(f"refusing to replace unrelated symlink: {command_link}")
    if command_link.exists():
        raise ArnisBootstrapError(f"refusing to replace existing path: {command_link}")
    command_link.symlink_to(installed_binary)


def prepare_arnis(
    *,
    source_dir: Path | None = None,
    build_dir: Path | None = None,
    install_dir: Path | None = None,
    command_link: Path | None = None,
) -> dict[str, str]:
    lock = _load_lock()
    _verify_patch(lock)
    source = (source_dir or _default_source_dir(lock)).expanduser().resolve()
    build = (build_dir or _default_build_dir(lock)).expanduser().resolve()
    install = (install_dir or _default_install_dir(lock)).expanduser().resolve()
    link = (command_link or (Path.home() / ".local" / "bin" / "arnis-cmo")).expanduser()
    _ensure_checkout(lock, source)
    _ensure_patch_applied(source, lock)
    binary = _install_binary(
        lock,
        source_dir=source,
        build_dir=build,
        install_dir=install,
    )
    _ensure_command_link(binary, link)
    return {
        "binary": str(binary),
        "command_link": str(link),
        "install_id": str(lock["install_id"]),
        "source_dir": str(source),
    }


__all__ = ["ArnisBootstrapError", "prepare_arnis"]
