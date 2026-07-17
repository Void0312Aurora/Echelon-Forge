from __future__ import annotations

import os
import sys

# Prefer the in-repo C++ extension when present.
# This avoids stale site-packages wheels during active physics iteration.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
_ENV_BUILD_DIR = os.environ.get("CMO_BUILD_DIR", "").strip()


def _has_ef_py_artifact(path: str) -> bool:
    try:
        names = os.listdir(path)
    except OSError:
        return False
    return any(
        name == "ef_py"
        or (name.startswith("ef_py") and name.endswith((".so", ".pyd")))
        for name in names
    )


if _ENV_BUILD_DIR:
    _EXPLICIT_BUILD_DIR = (
        _ENV_BUILD_DIR
        if os.path.isabs(_ENV_BUILD_DIR)
        else os.path.join(_REPO_ROOT, _ENV_BUILD_DIR)
    )
    _EXPLICIT_BUILD_DIR = os.path.abspath(_EXPLICIT_BUILD_DIR)
    if not os.path.isdir(_EXPLICIT_BUILD_DIR):
        raise RuntimeError(f"CMO_BUILD_DIR does not exist: {_EXPLICIT_BUILD_DIR}")
    if not _has_ef_py_artifact(_EXPLICIT_BUILD_DIR):
        raise RuntimeError(
            "CMO_BUILD_DIR does not contain an ef_py artifact: "
            f"{_EXPLICIT_BUILD_DIR}"
        )
    _BUILD_DIRS = [_EXPLICIT_BUILD_DIR]
else:
    _BUILD_DIRS = [
        os.path.join(_REPO_ROOT, "build-workshop"),
        os.path.join(_REPO_ROOT, "build-gpu"),
        os.path.join(_REPO_ROOT, "build"),
    ]

for _build_dir in reversed(_BUILD_DIRS):
    _build_dir = os.path.abspath(_build_dir)
    if os.path.isdir(_build_dir) and _has_ef_py_artifact(_build_dir):
        if _build_dir in sys.path:
            sys.path.remove(_build_dir)
        sys.path.insert(0, _build_dir)

import ef_py

try:
    import gymnasium as gym
    from gymnasium import spaces
except ModuleNotFoundError:  # Optional dependency for non-training workflows
    gym = None
    spaces = None


def configure_sim_log_level() -> None:
    """
    Keep RL workloads from spending wall-clock time on per-reset info logging.

    The physics kernel exposes a global spdlog level through `ef_py.set_log_level`.
    Training creates many environments and frequent episode resets, especially for
    leader-layer curricula. Defaulting to `warn` preserves real diagnostics while
    avoiding a large stream of hot-path `info` messages.
    """
    level = str(os.environ.get("CMO_SIM_LOG_LEVEL", "warn")).strip().lower() or "warn"
    try:
        ef_py.set_log_level(level)
    except Exception:
        pass


configure_sim_log_level()


__all__ = ["configure_sim_log_level", "ef_py", "gym", "spaces"]
