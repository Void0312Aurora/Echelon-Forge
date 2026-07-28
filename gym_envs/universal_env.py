from __future__ import annotations

from gym_envs.universal_env_parts.common import configure_sim_log_level, gym, spaces
from gym_envs.universal_env_parts import (
    add_air_combat_event_action_info,
    apply_air_combat_event_action_gate,
    build_pilot_action,
    build_step_info,
    build_step_info_minimal,
    build_universal_observation,
    downsample_visual_mean,
    air_combat_hybrid_effective_action,
    expected_action_dim,
    finalize_air_combat_event_action_info,
    half_to_unit,
    make_action_space,
    make_observation_space,
    make_temporal_history_buffer,
    mission_observation_dim,
    naval_action_family_for_mode,
    naval_policy_instruments,
    naval_station_action_command,
    normalize_action,
    append_temporal_history,
    apply_naval_station_action,
    attach_temporal_history,
    bind_naval_station_eval_reference,
    reset_air_combat_event_action_state,
    reset_temporal_history,
    reset_naval_station_action_state,
    is_air_combat_hybrid_action_mode,
    is_naval_station_action_mode,
    temporal_history_enabled,
    validate_naval_action_mode_for_loader,
)

_configure_sim_log_level = configure_sim_log_level


def _raw_universal_env_removed_message():
    return (
        "UniversalEnv's raw ef_py.SimulationKernel constructor path has been removed; "
        "use WorldBatchVecEnv/RuntimeFacadeAdapter instead."
    )


if gym is None:

    class UniversalEnv:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            raise ModuleNotFoundError(
                "UniversalEnv requires the optional dependency 'gymnasium'. "
                "Install it (e.g. `pip install gymnasium`) to run RL training."
            )

else:

    class UniversalEnv(gym.Env):
        """Fail-fast compatibility name for the removed raw-kernel environment."""

        metadata = {"render_modes": ["human"], "render_fps": 60}

        def __init__(
            self,
            scenario_path,
            render_mode=None,
            include_visual: bool = False,
            include_proprio: bool = False,
            action_mode: str = "full",
            mission_obs_mode: str = "basic",
            visual_downsample: int = 1,
            visual_update_interval: int = 1,
            temporal_history_len: int = 1,
            execution_step_runtime_mode: str | None = None,
            step_info_mode: str = "full",
            flight_shaping_backend: str | None = None,
            collect_step_timing: bool = False,
        ):
            super().__init__()
            raise RuntimeError(_raw_universal_env_removed_message())


__all__ = [
    "UniversalEnv",
    "_configure_sim_log_level",
    "add_air_combat_event_action_info",
    "air_combat_hybrid_effective_action",
    "apply_air_combat_event_action_gate",
    "build_pilot_action",
    "build_step_info",
    "build_step_info_minimal",
    "build_universal_observation",
    "downsample_visual_mean",
    "expected_action_dim",
    "finalize_air_combat_event_action_info",
    "half_to_unit",
    "is_air_combat_hybrid_action_mode",
    "make_action_space",
    "make_observation_space",
    "mission_observation_dim",
    "naval_action_family_for_mode",
    "naval_policy_instruments",
    "naval_station_action_command",
    "normalize_action",
    "reset_air_combat_event_action_state",
    "spaces",
    "validate_naval_action_mode_for_loader",
]
