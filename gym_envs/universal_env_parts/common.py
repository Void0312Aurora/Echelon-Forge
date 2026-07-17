from __future__ import annotations

import os

from python.runtime_bootstrap import configure_repo_imports


configure_repo_imports()

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
