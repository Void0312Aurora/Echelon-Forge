from __future__ import annotations

import os
import time

import numpy as np

from gym_envs.universal_env_parts.common import configure_sim_log_level, ef_py, gym, spaces
from gym_envs.scenario_loader import (
    ScenarioLoader,
    normalize_execution_step_runtime_mode,
    normalize_flight_shaping_backend,
)
from gym_envs.universal_env_parts import (
    build_pilot_action,
    build_step_info,
    build_step_info_minimal,
    build_universal_observation,
    downsample_visual_mean,
    expected_action_dim,
    half_to_unit,
    make_action_space,
    make_observation_space,
    mission_observation_dim,
    normalize_action,
)

_configure_sim_log_level = configure_sim_log_level

_RUNTIME_COMPAT_TRUE = {"1", "true", "on", "yes", "compat", "compatibility", "diagnostics", "debug"}
_RUNTIME_COMPAT_FALSE = {"", "0", "false", "off", "no", "none", "mainline", "compiled"}


def _normalize_runtime_compatibility_enabled(value):
    if isinstance(value, bool):
        return bool(value)
    if value is None:
        return False
    normalized = str(value).strip().lower()
    if normalized in _RUNTIME_COMPAT_TRUE:
        return True
    if normalized in _RUNTIME_COMPAT_FALSE:
        return False
    return bool(value)


def _raw_universal_env_compatibility_required_message():
    return (
        "UniversalEnv's raw ef_py.SimulationKernel path is a quarantined compatibility "
        "escape hatch; use WorldBatchVecEnv/RuntimeFacadeAdapter for production setup or "
        "pass runtime_compatibility_enabled=True to opt in explicitly."
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
        """
        Universal Environment for Flight Simulation.

        Action Space (17 dimensions total):
        - [0-3] Primary Controls: stick_pitch, stick_roll, rudder, throttle (continuous)
        - [4-6] Secondary Controls: gear, flaps, speedbrake (continuous 0-1)
        - [7-8] Brakes: brake_left, brake_right (binary 0/1)
        - [9-12] Sensors: radar_active (binary), radar_az, radar_el, tms_up (binary)
        - [13-16] Weapons: master_arm (binary), fire_weapon (binary), fire_gun (binary), weapon_select (discrete)

        Observation Space: Dict with instruments, contacts, rwr, mission
        """

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
            execution_step_runtime_mode: str | None = None,
            step_info_mode: str = "full",
            flight_shaping_backend: str | None = None,
            runtime_compatibility_enabled: bool = False,
            collect_step_timing: bool = False,
        ):
            super().__init__()
            self.runtime_compatibility_enabled = _normalize_runtime_compatibility_enabled(
                runtime_compatibility_enabled
            )
            if not self.runtime_compatibility_enabled:
                raise RuntimeError(_raw_universal_env_compatibility_required_message())
            self.render_mode = render_mode
            self.scenario_path = scenario_path
            self.include_visual = bool(include_visual)
            self.include_proprio = bool(include_proprio)
            self.action_mode = str(action_mode)
            self.mission_obs_mode = str(mission_obs_mode).strip().lower()
            self.visual_downsample = max(1, int(visual_downsample))
            self.visual_update_interval = max(1, int(visual_update_interval))
            self.execution_step_runtime_mode = (
                normalize_execution_step_runtime_mode(execution_step_runtime_mode)
                if execution_step_runtime_mode is not None
                else None
            )
            self.flight_shaping_backend = (
                normalize_flight_shaping_backend(flight_shaping_backend)
                if flight_shaping_backend is not None
                else None
            )
            self.step_info_mode = str(step_info_mode).strip().lower()
            if self.execution_step_runtime_mode not in (None, "compiled", "legacy"):
                raise ValueError(f"Unknown execution_step_runtime_mode: {execution_step_runtime_mode!r}")
            if self.flight_shaping_backend not in (None, "auto", "compiled", "legacy", "gpu_host"):
                raise ValueError(f"Unknown flight_shaping_backend: {flight_shaping_backend!r}")
            if self.step_info_mode not in ("full", "terminal", "off"):
                raise ValueError(f"Unknown step_info_mode: {step_info_mode!r}")
            self.collect_step_timing = bool(collect_step_timing)
            self._last_inst = None
            self._last_truth = None
            self._last_action = None
            self._visual_cache = None
            self._visual_cache_step = -1
            self.last_reset_timing: dict[str, float] = {}
            self.last_step_timing: dict[str, float] = {}

            self.sim = ef_py.SimulationKernel()

            db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../examples/config/database"))
            self.sim.load_database(db_path)

            self.loader = ScenarioLoader(self.sim)
            if self.execution_step_runtime_mode is not None:
                self.loader.set_execution_step_runtime_mode(self.execution_step_runtime_mode)
            if self.flight_shaping_backend is not None:
                self.loader.set_flight_shaping_backend(self.flight_shaping_backend)

            self.action_space = make_action_space(self.action_mode)

            self.max_contacts = 10
            self.max_rwr = 4
            self.obs_size = 42

            self.arb_height_native = 48
            self.arb_width_native = 96
            self.arb_channels = 10
            if self.arb_height_native % self.visual_downsample != 0 or self.arb_width_native % self.visual_downsample != 0:
                raise ValueError(
                    f"visual_downsample={self.visual_downsample} must divide "
                    f"{self.arb_height_native}x{self.arb_width_native}"
                )
            self.arb_height = self.arb_height_native // self.visual_downsample
            self.arb_width = self.arb_width_native // self.visual_downsample
            self.observation_space = make_observation_space(
                action_space=self.action_space,
                mission_obs_mode=self.mission_obs_mode,
                include_visual=self.include_visual,
                include_proprio=self.include_proprio,
                arb_height=self.arb_height,
                arb_width=self.arb_width,
                arb_channels=self.arb_channels,
                obs_size=self.obs_size,
                max_contacts=self.max_contacts,
                max_rwr=self.max_rwr,
            )

            self.agent_id = None
            self.steps = 0
            self.max_steps = 1000

        def reset(self, seed=None, options=None):
            reset_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            super().reset(seed=seed)
            load_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            self.agent_id = self.loader.load_scenario(self.scenario_path, seed=seed)
            self.max_steps = self.loader.get_max_steps()
            load_ms = (time.perf_counter() - load_t0) * 1000.0 if self.collect_step_timing else 0.0

            if self.agent_id is None:
                raise ValueError("Scenario must define at least one entity with 'is_agent': true")

            self.steps = 0
            self._last_action = None
            self._visual_cache = None
            self._visual_cache_step = -1
            obs_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            obs = self._get_obs()
            obs_ms = (time.perf_counter() - obs_t0) * 1000.0 if self.collect_step_timing else 0.0
            if self.collect_step_timing:
                self.last_reset_timing = {
                    "scenario_load_ms": float(load_ms),
                    "initial_obs_build_ms": float(obs_ms),
                    "total_ms": float((time.perf_counter() - reset_t0) * 1000.0),
                }
                return obs, {"timing": dict(self.last_reset_timing)}
            self.last_reset_timing = {}
            return obs, {}

        def set_randomization_overrides(self, overrides: dict | None) -> None:
            """
            Called by training callbacks (e.g. curriculum) to override scenario randomization ranges.

            Note: overrides are applied on the *next* reset/load_scenario().
            """
            try:
                self.loader.set_randomization_overrides(overrides)
            except Exception as e:
                print(f"[WARN] set_randomization_overrides failed: {e}")
                return

        def step(self, action):
            step_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            self.steps += 1

            action_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            action = normalize_action(action, action_space=self.action_space, action_mode=self.action_mode)
            self._last_action = action.astype(np.float32, copy=True)

            inst_now = None if self.action_mode == "full" else self.sim.get_instrument_state(self.agent_id)
            pilot_act = build_pilot_action(action, action_mode=self.action_mode, inst_now=inst_now)
            action_prepare_ms = (time.perf_counter() - action_t0) * 1000.0 if self.collect_step_timing else 0.0

            write_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            self.sim.set_pilot_action(self.agent_id, pilot_act)
            command_write_ms = (time.perf_counter() - write_t0) * 1000.0 if self.collect_step_timing else 0.0

            kernel_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            self.sim.step()
            kernel_step_ms = (time.perf_counter() - kernel_t0) * 1000.0 if self.collect_step_timing else 0.0

            state_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            truth_now = self.sim.get_agent_observation(self.agent_id)
            inst_now = self.sim.get_instrument_state(self.agent_id)
            state_read_ms = (time.perf_counter() - state_t0) * 1000.0 if self.collect_step_timing else 0.0
            self._last_truth = truth_now
            self._last_inst = inst_now

            behavior_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            self.loader.update_behaviors(
                self.steps * self.sim.get_time_step(),
                truth=truth_now,
                inst=inst_now,
            )
            behavior_update_ms = (time.perf_counter() - behavior_t0) * 1000.0 if self.collect_step_timing else 0.0

            obs_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            obs = self._build_obs_from_state(inst_now, truth_now)
            obs_build_ms = (time.perf_counter() - obs_t0) * 1000.0 if self.collect_step_timing else 0.0

            reward_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            reward, terminated, truncated, mission_status = self.loader.compute_full_step(
                obs,
                self.sim,
                self.steps,
                self.max_steps,
                truth=self._last_truth,
                inst_state=self._last_inst,
            )
            reward_compute_ms = (time.perf_counter() - reward_t0) * 1000.0 if self.collect_step_timing else 0.0
            info_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            if self.step_info_mode == "off":
                info = build_step_info_minimal(
                    self.loader,
                    mission_status=mission_status,
                    terminated=terminated,
                    truncated=truncated,
                )
            elif self.step_info_mode == "terminal" and not bool(terminated or truncated):
                info = build_step_info_minimal(
                    self.loader,
                    mission_status=mission_status,
                    terminated=terminated,
                    truncated=truncated,
                )
            else:
                info = build_step_info(
                    self.loader,
                    self.sim,
                    int(self.agent_id),
                    mission_status=mission_status,
                    terminated=terminated,
                    truncated=truncated,
                    inst_now=self._last_inst,
                    truth_now=self._last_truth,
                )
            if self.collect_step_timing:
                info_build_ms = (time.perf_counter() - info_t0) * 1000.0
                self.last_step_timing = {
                    "action_prepare_ms": float(action_prepare_ms),
                    "command_write_ms": float(command_write_ms),
                    "kernel_step_ms": float(kernel_step_ms),
                    "state_read_ms": float(state_read_ms),
                    "behavior_update_ms": float(behavior_update_ms),
                    "obs_build_ms": float(obs_build_ms),
                    "reward_compute_ms": float(reward_compute_ms),
                    "info_build_ms": float(info_build_ms),
                    "total_ms": float((time.perf_counter() - step_t0) * 1000.0),
                }
                info["timing"] = dict(self.last_step_timing)
            else:
                self.last_step_timing = {}

            return obs, reward, terminated, truncated, info

        def _build_obs_from_state(self, inst, raw_truth):
            self._last_inst = inst
            self._last_truth = raw_truth
            obs = build_universal_observation(
                self.loader,
                inst,
                raw_truth,
                mission_obs_mode=self.mission_obs_mode,
                max_contacts=self.max_contacts,
                max_rwr=self.max_rwr,
                include_proprio=self.include_proprio,
                last_action=self._last_action,
                action_space=self.action_space,
                steps=int(self.steps),
                max_steps=int(self.max_steps),
            )
            if self.include_visual:
                need_refresh = (
                    self._visual_cache is None
                    or self.visual_update_interval <= 1
                    or self.steps <= 0
                    or (self.steps - self._visual_cache_step) >= self.visual_update_interval
                )
                if need_refresh:
                    if self.visual_downsample > 1 and hasattr(self.sim, "get_visual_observation_downsampled"):
                        visual_raw = self.sim.get_visual_observation_downsampled(self.agent_id, self.visual_downsample)
                        visual = np.asarray(visual_raw, dtype=np.float32)
                        if visual.ndim == 1:
                            visual = visual.reshape(self.arb_height, self.arb_width, self.arb_channels)
                        self._visual_cache = visual
                    else:
                        visual_raw = self.sim.get_visual_observation(self.agent_id)
                        visual = np.asarray(visual_raw, dtype=np.float32)
                        if visual.ndim == 1:
                            visual = visual.reshape(self.arb_height_native, self.arb_width_native, self.arb_channels)
                        self._visual_cache = downsample_visual_mean(visual, self.visual_downsample)
                    self._visual_cache_step = int(self.steps)
                obs["visual"] = np.asarray(self._visual_cache, dtype=np.float32, copy=False)
            return obs

        def _get_obs(self):
            inst = self.sim.get_instrument_state(self.agent_id)
            raw_truth = self.sim.get_agent_observation(self.agent_id)
            return self._build_obs_from_state(inst, raw_truth)


__all__ = [
    "UniversalEnv",
    "_configure_sim_log_level",
    "build_pilot_action",
    "build_step_info",
    "build_step_info_minimal",
    "build_universal_observation",
    "downsample_visual_mean",
    "expected_action_dim",
    "half_to_unit",
    "make_action_space",
    "make_observation_space",
    "mission_observation_dim",
    "normalize_action",
    "spaces",
]
