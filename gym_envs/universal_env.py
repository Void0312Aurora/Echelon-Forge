import os
import sys
import time

import numpy as np

# Prefer the in-repo C++ extension when present.
# This avoids stale site-packages wheels during active physics iteration.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_BUILD_DIRS = []
_ENV_BUILD_DIR = os.environ.get("CMO_BUILD_DIR", "").strip()
if _ENV_BUILD_DIR:
    _BUILD_DIRS.append(_ENV_BUILD_DIR if os.path.isabs(_ENV_BUILD_DIR) else os.path.join(_REPO_ROOT, _ENV_BUILD_DIR))
_BUILD_DIRS.extend(
    [
        os.path.join(_REPO_ROOT, "build-workshop"),
        os.path.join(_REPO_ROOT, "build-gpu"),
        os.path.join(_REPO_ROOT, "build"),
    ]
)
for _build_dir in reversed(_BUILD_DIRS):
    _build_dir = os.path.abspath(_build_dir)
    if os.path.isdir(_build_dir) and any(
        fname.startswith("ef_py") and fname.endswith(".so") for fname in os.listdir(_build_dir)
    ):
        if _build_dir in sys.path:
            sys.path.remove(_build_dir)
        sys.path.insert(0, _build_dir)

import ef_py
from gym_envs.scenario_loader import (
    ScenarioLoader,
    normalize_execution_step_runtime_mode,
    normalize_flight_shaping_backend,
)
from python.mission_obs_taxonomy import mission_observation_dim as shared_mission_observation_dim

try:
    import gymnasium as gym
    from gymnasium import spaces
except ModuleNotFoundError:  # Optional dependency for non-training workflows
    gym = None
    spaces = None


def _configure_sim_log_level() -> None:
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


_configure_sim_log_level()


def half_to_unit(x: float) -> float:
    y = (x - 0.5) * 2.0
    if y <= 0.0:
        return 0.0
    if y >= 1.0:
        return 1.0
    return y


def downsample_visual_mean(visual: np.ndarray, factor: int) -> np.ndarray:
    if factor <= 1:
        return visual.astype(np.float32, copy=False)
    h, w, c = visual.shape
    if h % factor != 0 or w % factor != 0:
        raise ValueError(f"visual shape {visual.shape} not divisible by downsample factor {factor}")
    nh, nw = h // factor, w // factor
    out = visual.reshape(nh, factor, nw, factor, c).mean(axis=(1, 3))
    return out.astype(np.float32, copy=False)


def expected_action_dim(action_mode: str) -> int:
    dims = {"full": 17, "takeoff2": 2, "takeoff4": 4}
    if str(action_mode) not in dims:
        raise ValueError(f"Unknown action_mode: {action_mode}")
    return int(dims[str(action_mode)])


def mission_observation_dim(mission_obs_mode: str) -> int:
    return int(shared_mission_observation_dim(mission_obs_mode))

def make_action_space(action_mode: str):
    if spaces is None:
        raise ModuleNotFoundError("gymnasium is required to build action spaces.")
    if action_mode == "full":
        return spaces.Box(
            low=np.array(
                [-1.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                dtype=np.float32,
            ),
            high=np.array(
                [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
                dtype=np.float32,
            ),
            dtype=np.float32,
        )
    if action_mode == "takeoff2":
        return spaces.Box(
            low=np.array([-1.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 1.0], dtype=np.float32),
            dtype=np.float32,
        )
    if action_mode == "takeoff4":
        return spaces.Box(
            low=np.array([-1.0, -1.0, -1.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
            dtype=np.float32,
        )
    raise ValueError(f"Unknown action_mode: {action_mode}")


def make_observation_space(
    *,
    action_space,
    mission_obs_mode: str,
    include_visual: bool,
    include_proprio: bool,
    arb_height: int,
    arb_width: int,
    arb_channels: int,
    obs_size: int = 42,
    max_contacts: int = 10,
    max_rwr: int = 4,
):
    if spaces is None:
        raise ModuleNotFoundError("gymnasium is required to build observation spaces.")
    mission_dim = mission_observation_dim(mission_obs_mode)
    obs_spaces = {
        "instruments": spaces.Box(low=-np.inf, high=np.inf, shape=(int(obs_size),), dtype=np.float32),
        "contacts": spaces.Box(low=-np.inf, high=np.inf, shape=(int(max_contacts), 5), dtype=np.float32),
        "rwr": spaces.Box(low=-np.inf, high=np.inf, shape=(int(max_rwr), 4), dtype=np.float32),
        "mission": spaces.Box(low=-np.inf, high=np.inf, shape=(int(mission_dim),), dtype=np.float32),
    }
    if include_proprio:
        obs_spaces["proprio"] = spaces.Box(
            low=action_space.low.astype(np.float32, copy=False),
            high=action_space.high.astype(np.float32, copy=False),
            shape=action_space.shape,
            dtype=np.float32,
        )
    if include_visual:
        obs_spaces["visual"] = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(int(arb_height), int(arb_width), int(arb_channels)),
            dtype=np.float32,
        )
    return spaces.Dict(obs_spaces)
def normalize_action(action, *, action_space, action_mode: str) -> np.ndarray:
    action = np.asarray(action, dtype=np.float32)
    if action.ndim != 1:
        action = action.reshape(-1)
    expected_dim = expected_action_dim(action_mode)
    if action.size != expected_dim:
        raise ValueError(
            f"Action shape mismatch for action_mode='{action_mode}': got {action.shape} "
            f"(size={action.size}), expected ({expected_dim},)."
        )
    try:
        action = np.clip(action, action_space.low, action_space.high)
    except Exception:
        pass
    return action.astype(np.float32, copy=False)


def build_pilot_action(action: np.ndarray, *, action_mode: str, inst_now=None):
    pilot_act = ef_py.PilotAction()
    pilot_act.active = True

    if action_mode == "full":
        pilot_act.stick_pitch = float(action[0])
        pilot_act.stick_roll = float(action[1])
        pilot_act.rudder = float(action[2])
        pilot_act.throttle = float(action[3])
        pilot_act.gear_handle = float(action[4])
        pilot_act.flaps = float(half_to_unit(float(action[5])))
        pilot_act.speedbrake = float(half_to_unit(float(action[6])))
        pilot_act.brake_left = False
        pilot_act.brake_right = False
        pilot_act.brake = float(half_to_unit(float(max(action[7], action[8]))))
        pilot_act.radar_active = bool(action[9] > 0.5)
        pilot_act.radar_scan_az = float(action[10]) * 60.0
        pilot_act.radar_scan_el = float(action[11]) * 30.0
        pilot_act.tms_up = bool(action[12] > 0.5)
        pilot_act.master_arm = bool(action[13] > 0.5)
        pilot_act.fire_weapon = bool(action[14] > 0.5)
        pilot_act.fire_gun = bool(action[15] > 0.5)
        pilot_act.weapon_select_id = int(action[16] * 7)
        pilot_act.program_chaff = False
        pilot_act.program_flare = False
        pilot_act.jettison_emergency = False
        return pilot_act

    pilot_act.stick_roll = 0.0
    pilot_act.rudder = 0.0
    pilot_act.flaps = 0.0
    pilot_act.speedbrake = 0.0
    pilot_act.brake = 0.0
    pilot_act.brake_left = False
    pilot_act.brake_right = False
    pilot_act.radar_active = False
    pilot_act.radar_scan_az = 0.0
    pilot_act.radar_scan_el = 0.0
    pilot_act.tms_up = False
    pilot_act.master_arm = False
    pilot_act.fire_weapon = False
    pilot_act.fire_gun = False
    pilot_act.weapon_select_id = 0
    pilot_act.program_chaff = False
    pilot_act.program_flare = False
    pilot_act.jettison_emergency = False

    if action_mode == "takeoff2":
        pilot_act.stick_pitch = float(action[0])
        pilot_act.throttle = float(action[1])
    elif action_mode == "takeoff4":
        pilot_act.stick_pitch = float(action[0])
        pilot_act.stick_roll = float(action[1])
        pilot_act.rudder = float(action[2])
        pilot_act.throttle = float(action[3])
    else:
        raise ValueError(f"Unknown action_mode: {action_mode}")

    alt_radar = float(getattr(inst_now, "alt_radar", 0.0)) if inst_now is not None else 0.0
    pilot_act.gear_handle = 0.0 if alt_radar > 30.0 else 1.0
    return pilot_act


def build_universal_observation(
    loader,
    inst,
    truth,
    *,
    mission_obs_mode: str,
    max_contacts: int,
    max_rwr: int,
    include_proprio: bool,
    last_action,
    action_space,
    steps: int | None = None,
    max_steps: int | None = None,
):
    if hasattr(loader, "reset_runtime_eval_cache"):
        try:
            loader.reset_runtime_eval_cache()
        except Exception:
            pass
    ils_vec = loader.get_ils_observation(float(truth.x), float(truth.y), float(inst.alt_baro))
    compiled_obs_enabled = bool(getattr(loader, "use_compiled_execution_step_runtime", True)) and hasattr(
        ef_py, "compute_execution_observation_runtime_numpy"
    )
    if compiled_obs_enabled:
        inst_vec, contacts, rwr = ef_py.compute_execution_observation_runtime_numpy(
            inst,
            truth,
            float(ils_vec[0]) if len(ils_vec) > 0 else 0.0,
            float(ils_vec[1]) if len(ils_vec) > 1 else 0.0,
            float(ils_vec[2]) if len(ils_vec) > 2 else 0.0,
            float(ils_vec[3]) if len(ils_vec) > 3 else 0.0,
            int(max_contacts),
            int(max_rwr),
        )
        inst_vec = np.asarray(inst_vec, dtype=np.float32)
        contacts = np.asarray(contacts, dtype=np.float32).reshape(int(max_contacts), 5)
        rwr = np.asarray(rwr, dtype=np.float32).reshape(int(max_rwr), 4)
    else:
        inst_vec = np.array(
            [
                inst.ias,
                inst.mach,
                inst.alt_baro,
                inst.alt_radar,
                inst.vvi,
                inst.aoa,
                inst.beta,
                inst.pitch,
                inst.roll,
                inst.heading,
                inst.g_load,
                inst.g_load_axial,
                inst.p,
                inst.q,
                inst.r,
                inst.engine_rpm,
                inst.fuel_internal + inst.fuel_external,
                inst.fuel_flow,
                inst.gear_pos,
                inst.flaps_pos,
                inst.speedbrake_pos,
                inst.cmd_heading,
                inst.cmd_alt,
                inst.cmd_speed,
                getattr(inst, "lat", 0.0),
                getattr(inst, "lon", 0.0),
                getattr(inst, "vn", 0.0),
                getattr(inst, "ve", 0.0),
                getattr(inst, "vd", 0.0),
                getattr(inst, "ground_speed", 0.0),
                getattr(inst, "ground_track", 0.0),
                getattr(inst, "wind_speed", 0.0),
                getattr(inst, "wind_dir", 0.0),
                getattr(inst, "oat", 15.0),
                float(getattr(inst, "gps_available", True)),
                getattr(inst, "position_uncertainty", 10.0),
                float(getattr(inst, "rwr_active", False)),
                float(getattr(inst, "missiles_remaining", 0)),
            ],
            dtype=np.float64,
        )

        contacts = np.zeros((int(max_contacts), 5), dtype=np.float32)
        for i, track in enumerate(getattr(truth, "contacts", [])):
            if i >= int(max_contacts):
                break
            contacts[i] = [track.range, track.azimuth, track.elevation, track.closing_speed, track.time_since_update]

        rwr = np.zeros((int(max_rwr), 4), dtype=np.float32)
        for i, warning in enumerate(getattr(truth, "rwr_warnings", [])):
            if i >= int(max_rwr):
                break
            rwr[i] = [
                warning.bearing,
                warning.signal_strength,
                1.0 if warning.is_lock else 0.0,
                1.0 if warning.is_launch else 0.0,
            ]

        inst_vec = np.concatenate([inst_vec, ils_vec.astype(np.float64, copy=False)], axis=0)
        inst_vec = np.nan_to_num(inst_vec, nan=0.0, posinf=0.0, neginf=0.0)
        inst_vec = np.clip(inst_vec, -1.0e6, 1.0e6).astype(np.float32, copy=False)
    step_eval = None
    if (
        steps is not None
        and max_steps is not None
        and hasattr(loader, "_prepare_step_evaluation")
    ):
        try:
            step_eval = loader._prepare_step_evaluation(
                truth=truth,
                inst_obj=inst,
                inst_vec=inst_vec,
                ils_vec=np.asarray(ils_vec, dtype=np.float32),
                steps=int(steps),
                max_steps=int(max_steps),
                mission_obs_mode=mission_obs_mode,
            )
        except Exception:
            step_eval = None
    if isinstance(step_eval, dict):
        frame_products = step_eval.get("frame_products")
        if frame_products is not None and bool(getattr(frame_products, "mission_observation_evaluated", False)):
            miss_vec = np.asarray(frame_products.mission_observation.values, dtype=np.float32)
        else:
            miss_vec = loader.get_mission_observation(mission_obs_mode, truth=truth, inst=inst)
    else:
        miss_vec = loader.get_mission_observation(mission_obs_mode, truth=truth, inst=inst)

    obs = {
        "instruments": inst_vec,
        "contacts": contacts,
        "rwr": rwr,
        "mission": miss_vec,
    }
    if include_proprio:
        if last_action is None:
            proprio = np.zeros((int(action_space.shape[0]),), dtype=np.float32)
        else:
            proprio = np.asarray(last_action, dtype=np.float32).reshape(-1)
        obs["proprio"] = proprio
    return obs


def build_step_info(
    loader,
    sim,
    agent_id: int,
    *,
    mission_status,
    terminated: bool,
    truncated: bool,
    inst_now=None,
    truth_now=None,
):
    info = {
        "mission_status": np.array(mission_status, dtype=np.float32),
        "terminated": float(bool(terminated)),
        "truncated": float(bool(truncated)),
    }
    try:
        tr = getattr(loader, "last_termination_reason", None)
        if isinstance(tr, str) and tr:
            info["termination_reason"] = tr
    except Exception:
        pass
    try:
        rb = getattr(loader, "last_reward_breakdown", None)
        if isinstance(rb, dict) and rb:
            info["reward_terms"] = {k: float(v) for k, v in rb.items()}
    except Exception:
        pass
    compiled_runtime_enabled = bool(
        hasattr(loader, "_compiled_step_info_enabled")
        and loader._compiled_step_info_enabled()
        and hasattr(loader, "_compute_step_info_runtime_products")
    )
    try:
        inst_now = inst_now if inst_now is not None else sim.get_instrument_state(agent_id)
        if compiled_runtime_enabled:
            truth_now = truth_now if truth_now is not None else sim.get_agent_observation(agent_id)
            products = loader._compute_step_info_runtime_products(inst_now=inst_now, truth_now=truth_now)
            info["on_runway"] = float(bool(products.on_runway))
            info["gear_collapsed"] = float(bool(products.gear_collapsed))
            info["gear_stress"] = float(products.gear_stress)
            info["on_ground"] = float(bool(products.on_ground))
            if bool(products.has_runway_frame):
                info["on_runway_geom"] = float(bool(products.on_runway_geom))
                info["runway_cross_m"] = float(products.runway_cross_m)
                info["runway_along_m"] = float(products.runway_along_m)
        else:
            info["on_runway"] = float(bool(getattr(inst_now, "on_runway", True)))
            info["gear_collapsed"] = float(bool(getattr(inst_now, "gear_collapsed", False)))
            info["gear_stress"] = float(getattr(inst_now, "gear_stress", 0.0))
            alt_agl = float(getattr(inst_now, "alt_radar", 0.0))
            cfg = loader.get_rewards_config()
            on_ground_alt_threshold = float(cfg.get("on_ground_alt_threshold", 2.5))
            airborne_alt_threshold = float(cfg.get("airborne_alt_threshold", cfg.get("liftoff_alt_threshold", 5.0)))
            on_ground = alt_agl <= on_ground_alt_threshold
            airborne = alt_agl >= airborne_alt_threshold
            preliftoff = not airborne
            info["on_ground"] = float(on_ground)
            try:
                truth_now = truth_now if truth_now is not None else sim.get_agent_observation(agent_id)
                valid_rf, along_m, cross_m, rw_len, rw_wid = loader.get_runway_local_frame(
                    float(truth_now.x), float(truth_now.y)
                )
                if valid_rf and rw_len > 1.0 and rw_wid > 1.0:
                    runway_width_margin_m = float(cfg.get("runway_width_margin_m", 2.0))
                    runway_length_margin_m = float(cfg.get("runway_length_margin_m", 0.0))
                    info["on_runway_geom"] = float(
                        bool(
                            preliftoff
                            and abs(cross_m) <= 0.5 * rw_wid + runway_width_margin_m
                            and abs(along_m) <= 0.5 * rw_len + runway_length_margin_m
                        )
                    )
                    info["runway_cross_m"] = float(cross_m)
                    info["runway_along_m"] = float(along_m)
            except Exception:
                pass
    except Exception:
        pass
    return info


def build_step_info_minimal(
    loader,
    *,
    mission_status,
    terminated: bool,
    truncated: bool,
):
    info = {
        "mission_status": np.array(mission_status, dtype=np.float32),
        "terminated": float(bool(terminated)),
        "truncated": float(bool(truncated)),
    }
    try:
        tr = getattr(loader, "last_termination_reason", None)
        if isinstance(tr, str) and tr:
            info["termination_reason"] = tr
    except Exception:
        pass
    try:
        rb = getattr(loader, "last_reward_breakdown", None)
        if isinstance(rb, dict) and rb:
            info["reward_terms"] = {k: float(v) for k, v in rb.items()}
    except Exception:
        pass
    return info


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
            collect_step_timing: bool = False,
        ):
            super().__init__()
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
                raise ValueError(
                    f"Unknown execution_step_runtime_mode: {execution_step_runtime_mode!r}"
                )
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

            # Initialize Core
            self.sim = ef_py.SimulationKernel()

            # Load DB
            db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../examples/config/database"))
            self.sim.load_database(db_path)

            self.loader = ScenarioLoader(self.sim)
            if self.execution_step_runtime_mode is not None:
                self.loader.set_execution_step_runtime_mode(self.execution_step_runtime_mode)
            if self.flight_shaping_backend is not None:
                self.loader.set_flight_shaping_backend(self.flight_shaping_backend)

            # Action Space
            # - full: Full Digital Pilot (17 dims) for end-to-end tasks
            # - takeoff2: Minimal takeoff curriculum (pitch, throttle)
            # - takeoff4: Minimal takeoff curriculum (pitch, roll, rudder, throttle)
            self.action_space = make_action_space(self.action_mode)

            # Observation Space
            self.max_contacts = 10
            self.max_rwr = 4

            # Instrument State Size: see _get_obs
            # Base instrument vector (38) + ILS channels (4)
            self.obs_size = 42

            # ARB Visual observation dimensions
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
                # Best-effort: do not crash the training loop for a bad curriculum config.
                print(f"[WARN] set_randomization_overrides failed: {e}")
                return

        def step(self, action):
            step_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            self.steps += 1

            action_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            action = normalize_action(action, action_space=self.action_space, action_mode=self.action_mode)
            self._last_action = action.astype(np.float32, copy=True)

            # 1. Apply Action (Full Digital Pilot)
            inst_now = None if self.action_mode == "full" else self.sim.get_instrument_state(self.agent_id)
            pilot_act = build_pilot_action(action, action_mode=self.action_mode, inst_now=inst_now)
            action_prepare_ms = (time.perf_counter() - action_t0) * 1000.0 if self.collect_step_timing else 0.0

            write_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            self.sim.set_pilot_action(self.agent_id, pilot_act)
            command_write_ms = (time.perf_counter() - write_t0) * 1000.0 if self.collect_step_timing else 0.0

            # 2. Step Sim
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

            # 3. Get Observation
            obs_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            obs = self._build_obs_from_state(inst_now, truth_now)
            obs_build_ms = (time.perf_counter() - obs_t0) * 1000.0 if self.collect_step_timing else 0.0

            # 4. Compute Reward & Done (Logic delegated to Loader/Config)
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
                        visual_raw = self.sim.get_visual_observation_downsampled(
                            self.agent_id, self.visual_downsample
                        )
                        visual = np.asarray(visual_raw, dtype=np.float32)
                        if visual.ndim == 1:
                            visual = visual.reshape(self.arb_height, self.arb_width, self.arb_channels)
                        self._visual_cache = visual
                    else:
                        visual_raw = self.sim.get_visual_observation(self.agent_id)
                        visual = np.asarray(visual_raw, dtype=np.float32)
                        if visual.ndim == 1:
                            visual = visual.reshape(
                                self.arb_height_native, self.arb_width_native, self.arb_channels
                            )
                        self._visual_cache = downsample_visual_mean(visual, self.visual_downsample)
                    self._visual_cache_step = int(self.steps)
                obs["visual"] = np.asarray(self._visual_cache, dtype=np.float32, copy=False)
            return obs

        def _get_obs(self):
            inst = self.sim.get_instrument_state(self.agent_id)
            raw_truth = self.sim.get_agent_observation(self.agent_id)
            return self._build_obs_from_state(inst, raw_truth)
