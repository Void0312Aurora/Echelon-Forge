"""Maintained execution-runtime construction for world-model commands."""

from __future__ import annotations

from python.rl.runtime.single_world_batch_runtime import (
    build_single_world_batch_execution_runtime,
)


def build_world_model_execution_env(
    *,
    scenario_path: str,
    include_visual: bool,
    include_proprio: bool,
    action_mode: str,
):
    """Build the single-world Gym facade backed by the maintained WorldBatch runtime."""

    return build_single_world_batch_execution_runtime(
        scenario_path=str(scenario_path),
        env_settings={
            "include_visual": bool(include_visual),
            "include_proprio": bool(include_proprio),
            "action_mode": str(action_mode),
        },
        worker_threads=1,
    )


__all__ = ["build_world_model_execution_env"]
