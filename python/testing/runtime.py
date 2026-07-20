from __future__ import annotations

import os
import sys
import shutil
from glob import glob
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


def _is_windows() -> bool:
    return os.name == "nt"


def _candidate_build_names() -> tuple[str, ...]:
    if _is_windows():
        return ("build-local-win", "build-workshop", "build-gpu", "build", "build-facade-local")
    return ("build-workshop", "build-gpu", "build", "build-facade-local")


def _ef_py_artifact_paths(path: str) -> list[str]:
    search_dirs = [path]
    if _is_windows():
        search_dirs.extend(
            os.path.join(path, config)
            for config in ("Release", "RelWithDebInfo", "Debug")
            if os.path.isdir(os.path.join(path, config))
        )

    patterns = ("ef_py*.pyd", "ef_py*.so", "ef_py")
    artifacts: list[str] = []
    for search_dir in search_dirs:
        for pattern in patterns:
            artifacts.extend(glob(os.path.join(search_dir, pattern)))
    return artifacts


def _has_ef_py_artifact(path: str) -> bool:
    return bool(_ef_py_artifact_paths(path))


def _newest_ef_py_artifact_mtime(path: str) -> float:
    mtimes: list[float] = []
    for artifact in _ef_py_artifact_paths(path):
        try:
            mtimes.append(os.path.getmtime(artifact))
        except OSError:
            continue
    return max(mtimes, default=0.0)


def build_dirs(root: str | None = None) -> list[str]:
    base = root or repo_root()
    env_build = _normalize_build_path(base, os.environ.get("CMO_BUILD_DIR", ""))
    if env_build:
        if not os.path.isdir(env_build):
            raise RuntimeError(f"CMO_BUILD_DIR does not exist: {env_build}")
        if not _has_ef_py_artifact(env_build):
            raise RuntimeError(
                "CMO_BUILD_DIR does not contain an ef_py artifact: "
                f"{env_build}"
            )
        return [env_build]

    candidates = [os.path.join(base, name) for name in _candidate_build_names()]

    existing: list[str] = []
    seen: set[str] = set()
    for path in candidates:
        normalized = os.path.abspath(path)
        if normalized in seen:
            continue
        seen.add(normalized)
        if os.path.isdir(normalized):
            existing.append(normalized)
    with_artifacts = [path for path in existing if _has_ef_py_artifact(path)]
    if with_artifacts and not _is_windows():
        with_artifacts.sort(key=_newest_ef_py_artifact_mtime, reverse=True)
    return with_artifacts


def build_dir(root: str | None = None) -> str:
    dirs = build_dirs(root)
    if dirs:
        return dirs[0]
    raise RuntimeError(
        "No local ef_py build artifact found. Configure and build ef_py, or set "
        "CMO_BUILD_DIR to a build directory containing the extension."
    )


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
    if not builds:
        raise RuntimeError(
            "No local ef_py build artifact found; refusing to fall back to an installed "
            "site-packages extension."
        )
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
