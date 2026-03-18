import glob
import os
import sys

import numpy as np

# Prefer the in-repo C++ extension (built via CMake into `./build`) when present.
# This avoids stale site-packages wheels during active physics iteration.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_BUILD_DIR = os.path.join(_REPO_ROOT, "build")
if os.path.isdir(_BUILD_DIR) and glob.glob(os.path.join(_BUILD_DIR, "ef_py*.so")):
    sys.path.insert(0, _BUILD_DIR)

import ef_py
from gym_envs.scenario_loader import ScenarioLoader

try:
    import gymnasium as gym
    from gymnasium import spaces
except ModuleNotFoundError:  # Optional dependency for non-training workflows
    gym = None
    spaces = None


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
            self._last_inst = None
            self._last_truth = None
            self._last_action = None
            self._visual_cache = None
            self._visual_cache_step = -1

            # Initialize Core
            self.sim = ef_py.SimulationKernel()

            # Load DB
            db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../examples/config/database"))
            self.sim.load_database(db_path)

            self.loader = ScenarioLoader(self.sim)

            # Action Space
            # - full: Full Digital Pilot (17 dims) for end-to-end tasks
            # - takeoff2: Minimal takeoff curriculum (pitch, throttle)
            # - takeoff4: Minimal takeoff curriculum (pitch, roll, rudder, throttle)
            if self.action_mode == "full":
                # 17 dimensions to cover all act.md operations
                # Layout:
                # [0] stick_pitch    [-1, 1]
                # [1] stick_roll     [-1, 1]
                # [2] rudder         [-1, 1]
                # [3] throttle       [0, 1]
                # [4] gear           [0, 1]
                # [5] flaps          [0, 1]
                # [6] speedbrake     [0, 1]
                # [7] brake_left     [0, 1] (treat as continuous, threshold at 0.5)
                # [8] brake_right    [0, 1]
                # [9] radar_active   [0, 1]
                # [10] radar_az      [-1, 1] (normalized)
                # [11] radar_el      [-1, 1] (normalized)
                # [12] tms_up        [0, 1]
                # [13] master_arm    [0, 1]
                # [14] fire_weapon   [0, 1]
                # [15] fire_gun      [0, 1]
                # [16] weapon_select [0, 1] (normalized, map to int 0-7)
                self.action_space = spaces.Box(
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
            elif self.action_mode == "takeoff2":
                self.action_space = spaces.Box(
                    low=np.array([-1.0, 0.0], dtype=np.float32),
                    high=np.array([1.0, 1.0], dtype=np.float32),
                    dtype=np.float32,
                )
            elif self.action_mode == "takeoff4":
                self.action_space = spaces.Box(
                    low=np.array([-1.0, -1.0, -1.0, 0.0], dtype=np.float32),
                    high=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
                    dtype=np.float32,
                )
            else:
                raise ValueError(f"Unknown action_mode: {self.action_mode}")

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
            if self.mission_obs_mode == "basic":
                mission_dim = 4
            elif self.mission_obs_mode == "nav_v1":
                mission_dim = 11
            elif self.mission_obs_mode == "nav_v2":
                mission_dim = 14
            else:
                raise ValueError(f"Unknown mission_obs_mode: {self.mission_obs_mode}")

            obs_spaces = {
                "instruments": spaces.Box(low=-np.inf, high=np.inf, shape=(self.obs_size,), dtype=np.float32),
                "contacts": spaces.Box(low=-np.inf, high=np.inf, shape=(self.max_contacts, 5), dtype=np.float32),
                "rwr": spaces.Box(low=-np.inf, high=np.inf, shape=(self.max_rwr, 4), dtype=np.float32),
                "mission": spaces.Box(low=-np.inf, high=np.inf, shape=(mission_dim,), dtype=np.float32),
            }
            if self.include_proprio:
                obs_spaces["proprio"] = spaces.Box(
                    low=self.action_space.low.astype(np.float32, copy=False),
                    high=self.action_space.high.astype(np.float32, copy=False),
                    shape=self.action_space.shape,
                    dtype=np.float32,
                )
            if self.include_visual:
                obs_spaces["visual"] = spaces.Box(
                    low=-np.inf,
                    high=np.inf,
                    shape=(self.arb_height, self.arb_width, self.arb_channels),
                    dtype=np.float32,
                )
            self.observation_space = spaces.Dict(obs_spaces)

            self.agent_id = None
            self.steps = 0
            self.max_steps = 1000

        def reset(self, seed=None, options=None):
            super().reset(seed=seed)
            self.agent_id = self.loader.load_scenario(self.scenario_path, seed=seed)
            self.max_steps = self.loader.get_max_steps()

            if self.agent_id is None:
                raise ValueError("Scenario must define at least one entity with 'is_agent': true")

            self.steps = 0
            self._last_action = None
            self._visual_cache = None
            self._visual_cache_step = -1
            return self._get_obs(), {}

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
            self.steps += 1

            action = np.asarray(action, dtype=np.float32)
            if action.ndim != 1:
                action = action.reshape(-1)

            expected_dim = {"full": 17, "takeoff2": 2, "takeoff4": 4}.get(self.action_mode)
            if expected_dim is None:
                raise ValueError(f"Unknown action_mode: {self.action_mode}")
            if action.size != expected_dim:
                raise ValueError(
                    f"Action shape mismatch for action_mode='{self.action_mode}': got {action.shape} "
                    f"(size={action.size}), expected ({expected_dim},)."
                )
            # Be robust to policies that output slightly out-of-bounds actions (SB3 may or may not clip depending
            # on distribution settings). Real actuators saturate at their limits.
            try:
                action = np.clip(action, self.action_space.low, self.action_space.high)
            except Exception:
                pass
            self._last_action = action.astype(np.float32, copy=True)

            # 1. Apply Action (Full Digital Pilot)
            pilot_act = ef_py.PilotAction()
            pilot_act.active = True

            if self.action_mode == "full":
                # Primary Controls
                pilot_act.stick_pitch = float(action[0])
                pilot_act.stick_roll = float(action[1])
                pilot_act.rudder = float(action[2])
                pilot_act.throttle = float(action[3])

                # Secondary Controls
                # Important: many continuous-control policies initialize actions near the midpoint
                # of each dimension. For [0, 1] controls, that midpoint is 0.5, which would otherwise
                # mean "half brakes / half speedbrake / half flaps" and can completely prevent ground roll.
                pilot_act.gear_handle = float(action[4])
                pilot_act.flaps = float(half_to_unit(float(action[5])))
                pilot_act.speedbrake = float(half_to_unit(float(action[6])))

                # Brakes: use analog braking via `brake` only.
                # NOTE: `brake_left/brake_right` are *binary* flags in the physics engine and force full braking
                # when asserted. Mapping continuous RL actions to those flags makes it too easy to get stuck
                # (tiny noise -> full braking). Keep them false and let `brake` handle intensity.
                pilot_act.brake_left = False
                pilot_act.brake_right = False
                pilot_act.brake = float(half_to_unit(float(max(action[7], action[8]))))

                # Sensors
                pilot_act.radar_active = bool(action[9] > 0.5)
                pilot_act.radar_scan_az = float(action[10]) * 60.0  # Map to degrees
                pilot_act.radar_scan_el = float(action[11]) * 30.0  # Map to degrees
                pilot_act.tms_up = bool(action[12] > 0.5)

                # Weapons
                pilot_act.master_arm = bool(action[13] > 0.5)
                pilot_act.fire_weapon = bool(action[14] > 0.5)
                pilot_act.fire_gun = bool(action[15] > 0.5)
                pilot_act.weapon_select_id = int(action[16] * 7)  # Map to 0-7

                # Countermeasures (not in action space yet, default off)
                pilot_act.program_chaff = False
                pilot_act.program_flare = False
                pilot_act.jettison_emergency = False
            else:
                # Curriculum-friendly takeoff control: keep non-essential switches in safe defaults.
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

                if self.action_mode == "takeoff2":
                    pilot_act.stick_pitch = float(action[0])
                    pilot_act.throttle = float(action[1])
                elif self.action_mode == "takeoff4":
                    pilot_act.stick_pitch = float(action[0])
                    pilot_act.stick_roll = float(action[1])
                    pilot_act.rudder = float(action[2])
                    pilot_act.throttle = float(action[3])
                else:  # pragma: no cover
                    raise ValueError(f"Unknown action_mode: {self.action_mode}")

                # Auto gear retraction after liftoff for takeoff curricula.
                # Use radar altitude (AGL), not baro/MSL, so high-elevation airfields do not retract on the ground.
                inst_now = self.sim.get_instrument_state(self.agent_id)
                pilot_act.gear_handle = 0.0 if float(inst_now.alt_radar) > 30.0 else 1.0

            self.sim.set_pilot_action(self.agent_id, pilot_act)

            # 2. Step Sim
            self.sim.step()
            self.loader.update_behaviors(self.steps * self.sim.get_time_step())

            # 3. Get Observation
            obs = self._get_obs()

            # 4. Compute Reward & Done (Logic delegated to Loader/Config)
            reward, terminated, truncated, mission_status = self.loader.compute_full_step(
                obs, self.sim, self.steps, self.max_steps
            )
            # Keep obs["mission"] as the mission command ([cmd, hdg, alt, spd]) every step.
            # Return mission progress/status via info for logging/debugging.
            info = {
                "mission_status": np.array(mission_status, dtype=np.float32),
                "terminated": float(bool(terminated)),
                "truncated": float(bool(truncated)),
            }
            try:
                tr = getattr(self.loader, "last_termination_reason", None)
                if isinstance(tr, str) and tr:
                    info["termination_reason"] = tr
            except Exception:
                pass
            try:
                rb = getattr(self.loader, "last_reward_breakdown", None)
                if isinstance(rb, dict) and rb:
                    info["reward_terms"] = {k: float(v) for k, v in rb.items()}
            except Exception:
                pass
            try:
                inst_now = self._last_inst if self._last_inst is not None else self.sim.get_instrument_state(self.agent_id)
                info["on_runway"] = float(bool(getattr(inst_now, "on_runway", True)))
                info["gear_collapsed"] = float(bool(getattr(inst_now, "gear_collapsed", False)))
                info["gear_stress"] = float(getattr(inst_now, "gear_stress", 0.0))
                alt_agl = float(getattr(inst_now, "alt_radar", 0.0))
                cfg = self.loader.get_rewards_config()
                on_ground_alt_threshold = float(cfg.get("on_ground_alt_threshold", 2.5))
                airborne_alt_threshold = float(cfg.get("airborne_alt_threshold", cfg.get("liftoff_alt_threshold", 5.0)))
                on_ground = alt_agl <= on_ground_alt_threshold
                airborne = alt_agl >= airborne_alt_threshold
                preliftoff = not airborne
                info["on_ground"] = float(on_ground)
                try:
                    truth_now = self._last_truth if self._last_truth is not None else self.sim.get_agent_observation(self.agent_id)
                    valid_rf, along_m, cross_m, rw_len, rw_wid = self.loader.get_runway_local_frame(
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

            return obs, reward, terminated, truncated, info

        def _get_obs(self):
            # 1. Instruments
            inst = self.sim.get_instrument_state(self.agent_id)
            self._last_inst = inst

            inst_vec = np.array(
                [
                    # 1. Flight Dynamics (14)
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
                    # 2. Propulsion (3)
                    inst.engine_rpm,
                    inst.fuel_internal + inst.fuel_external,
                    inst.fuel_flow,
                    # 3. Configuration (3)
                    inst.gear_pos,
                    inst.flaps_pos,
                    inst.speedbrake_pos,
                    # 4. Navigation Commands (3)
                    inst.cmd_heading,
                    inst.cmd_alt,
                    inst.cmd_speed,
                    # 5. EGI / Navigation (9) - What pilot sees on HSD/TSD
                    getattr(inst, 'lat', 0.0),
                    getattr(inst, 'lon', 0.0),
                    getattr(inst, 'vn', 0.0),
                    getattr(inst, 've', 0.0),
                    getattr(inst, 'vd', 0.0),
                    getattr(inst, 'ground_speed', 0.0),
                    getattr(inst, 'ground_track', 0.0),
                    getattr(inst, 'wind_speed', 0.0),
                    getattr(inst, 'wind_dir', 0.0),
                    # 6. Environment (1)
                    getattr(inst, 'oat', 15.0),  # Outside Air Temperature
                    # 7. GPS/INS Status (2)
                    float(getattr(inst, 'gps_available', True)),
                    getattr(inst, 'position_uncertainty', 10.0),
                    # 8. Tactical (2)
                    float(getattr(inst, 'rwr_active', False)),
                    float(getattr(inst, 'missiles_remaining', 0)),
                    # Total: 15 + 3 + 3 + 3 + 9 + 1 + 2 + 2 = 38
                ],
                dtype=np.float64,
            )

            # 2. Contacts (Via Truth for now, simulating Sensor Fusion)
            raw_truth = self.sim.get_agent_observation(self.agent_id)
            self._last_truth = raw_truth

            contacts = np.zeros((self.max_contacts, 5), dtype=np.float32)
            for i, t in enumerate(raw_truth.contacts):
                if i >= self.max_contacts:
                    break
                contacts[i] = [t.range, t.azimuth, t.elevation, t.closing_speed, t.time_since_update]

            rwr = np.zeros((self.max_rwr, 4), dtype=np.float32)
            for i, w in enumerate(raw_truth.rwr_warnings):
                if i >= self.max_rwr:
                    break
                rwr[i] = [
                    w.bearing,
                    w.signal_strength,
                    1.0 if w.is_lock else 0.0,
                    1.0 if w.is_launch else 0.0,
                ]

            # 3. Mission Command (From Loader)
            miss_vec = self.loader.get_mission_observation(self.mission_obs_mode)

            # 4. ILS (derived from scenario geometry; enables runway alignment without exposing runway heading directly)
            ils_vec = self.loader.get_ils_observation(float(raw_truth.x), float(raw_truth.y), float(inst.alt_baro))

            # Append ILS to the instrument vector to keep policy/model code simple.
            inst_vec = np.concatenate([inst_vec, ils_vec.astype(np.float64, copy=False)], axis=0)
            inst_vec = np.nan_to_num(inst_vec, nan=0.0, posinf=0.0, neginf=0.0)
            inst_vec = np.clip(inst_vec, -1.0e6, 1.0e6).astype(np.float32, copy=False)

            obs = {
                "instruments": inst_vec,
                "contacts": contacts,
                "rwr": rwr,
                "mission": miss_vec,
            }
            if self.include_proprio:
                if self._last_action is None:
                    proprio = np.zeros((int(self.action_space.shape[0]),), dtype=np.float32)
                else:
                    proprio = np.asarray(self._last_action, dtype=np.float32).reshape(-1)
                obs["proprio"] = proprio
            if self.include_visual:
                need_refresh = (
                    self._visual_cache is None
                    or self.visual_update_interval <= 1
                    or self.steps <= 0
                    or (self.steps - self._visual_cache_step) >= self.visual_update_interval
                )
                if need_refresh:
                    visual_flat = self.sim.get_visual_observation(self.agent_id)
                    visual = np.asarray(visual_flat, dtype=np.float32).reshape(
                        self.arb_height_native, self.arb_width_native, self.arb_channels
                    )
                    self._visual_cache = downsample_visual_mean(visual, self.visual_downsample)
                    self._visual_cache_step = int(self.steps)
                obs["visual"] = np.asarray(self._visual_cache, dtype=np.float32, copy=False)
            return obs
