from __future__ import annotations

import os
import sys


def repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def build_dirs(root: str | None = None) -> list[str]:
    base = root or repo_root()
    candidates = [
        os.path.join(base, "build-gpu"),
        os.path.join(base, "build"),
    ]
    return [path for path in candidates if os.path.isdir(path)]


def build_dir(root: str | None = None) -> str:
    dirs = build_dirs(root)
    if dirs:
        return dirs[0]
    return os.path.join(root or repo_root(), "build")


def ensure_repo_imports() -> str:
    root = repo_root()
    for build in reversed(build_dirs(root)):
        if build not in sys.path:
            sys.path.insert(0, build)
    if root not in sys.path:
        sys.path.insert(0, root)
    return root


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
