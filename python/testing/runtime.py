from __future__ import annotations

import os
import sys
import shutil
from typing import Iterable


def repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _normalize_build_path(base: str, value: str) -> str:
    candidate = str(value or "").strip()
    if not candidate:
        return ""
    if os.path.isabs(candidate):
        return os.path.abspath(candidate)
    return os.path.abspath(os.path.join(base, candidate))


def build_dirs(root: str | None = None) -> list[str]:
    base = root or repo_root()
    candidates: list[str] = []

    env_build = _normalize_build_path(base, os.environ.get("CMO_BUILD_DIR", ""))
    if env_build:
        candidates.append(env_build)

    candidates.extend(
        [
            os.path.join(base, "build-local-win"),
            os.path.join(base, "build-workshop"),
            os.path.join(base, "build-gpu"),
            os.path.join(base, "build"),
            os.path.join(base, "build-facade-local"),
        ]
    )

    out: list[str] = []
    seen: set[str] = set()
    for path in candidates:
        normalized = os.path.abspath(path)
        if normalized in seen:
            continue
        seen.add(normalized)
        if os.path.isdir(normalized):
            out.append(normalized)
    return out


def build_dir(root: str | None = None) -> str:
    dirs = build_dirs(root)
    if dirs:
        return dirs[0]
    return os.path.join(root or repo_root(), "build")


def _iter_windows_dll_dirs(build: str) -> tuple[str, ...]:
    if os.name != "nt":
        return ()

    candidates: list[str] = []
    for candidate in (
        build,
        os.path.join(build, "_deps", "flecs-build"),
        os.path.join(build, "Release"),
        os.path.join(build, "RelWithDebInfo"),
        os.path.join(build, "Debug"),
    ):
        if os.path.isdir(candidate):
            candidates.append(os.path.abspath(candidate))

    compiler = shutil.which("g++.exe")
    if compiler:
        compiler_dir = os.path.abspath(os.path.dirname(compiler))
        if os.path.isdir(compiler_dir):
            candidates.append(compiler_dir)

    # Preserve order but drop duplicates.
    seen: set[str] = set()
    ordered: list[str] = []
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        ordered.append(candidate)
    return tuple(ordered)


def ensure_repo_imports() -> str:
    root = repo_root()
    builds = build_dirs(root)
    for build in reversed(builds):
        if build in sys.path:
            sys.path.remove(build)
        sys.path.insert(0, build)
    if root not in sys.path:
        sys.path.insert(0, root)
    if builds and os.name == "nt":
        for dll_dir in _iter_windows_dll_dirs(builds[0]):
            try:
                os.add_dll_directory(dll_dir)
            except (AttributeError, OSError):
                pass
    if builds:
        os.environ["CMO_BUILD_DIR"] = builds[0]
    return root


def iter_build_dirs(root: str | None = None) -> Iterable[str]:
    return tuple(build_dirs(root))


def configure_sim_log_level(level: str = "warn") -> str:
    root = ensure_repo_imports()
    normalized = str(level or "warn").strip().lower() or "warn"
    os.environ["CMO_SIM_LOG_LEVEL"] = normalized
    try:
        import ef_py  # type: ignore

        ef_py.set_log_level(normalized)
    except Exception:
        pass
    return root


def resolve_repo_path(*parts: str) -> str:
    return os.path.join(repo_root(), *parts)
