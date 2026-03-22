from __future__ import annotations

import os
import sys


def repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def build_dir(root: str | None = None) -> str:
    return os.path.join(root or repo_root(), "build")


def ensure_repo_imports() -> str:
    root = repo_root()
    build = build_dir(root)
    if os.path.isdir(build) and build not in sys.path:
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
