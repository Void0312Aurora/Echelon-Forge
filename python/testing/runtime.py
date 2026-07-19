"""Archive-only compatibility facade for the canonical runtime bootstrap.

Maintained code must import :mod:`python.runtime_bootstrap` directly.
This module re-exports its public surface for archive callers only.
"""

from python.runtime_bootstrap import (
    build_dir,
    build_dirs,
    configure_repo_imports,
    configure_sim_log_level,
    ensure_repo_imports,
    iter_build_dirs,
    repo_root,
    resolve_repo_path,
)

__all__ = [
    "build_dir",
    "build_dirs",
    "configure_repo_imports",
    "configure_sim_log_level",
    "ensure_repo_imports",
    "iter_build_dirs",
    "repo_root",
    "resolve_repo_path",
]
