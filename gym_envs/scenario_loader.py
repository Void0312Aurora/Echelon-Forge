import json
import os
import math
import copy
import ef_py
import numpy as np
from python.rl.leader_tasking import RuleBasedLeaderPhaseManager, build_kernel_mission_command
from python.rl.mission_defs import COMMAND_CODE_LANDING, is_landing_command_code


def _coerce_nonnegative_int(value, default: int = 0) -> int:
    try:
        out = int(value)
    except Exception:
        return int(default)
    return out if out >= 0 else int(default)


def _canonical_recovery_approach_name(value, *, landing_mode: str = "") -> str:
    default_by_mode = {
        "ils": "ILS",
        "ils_final": "ILS",
        "visual": "Visual",
        "overhead": "Overhead",
        "tacan": "TACAN",
    }
    default_name = default_by_mode.get(str(landing_mode or "").strip().lower(), "StraightIn")
    if value is None:
        return default_name
    try:
        if hasattr(value, "name"):
            value = value.name
    except Exception:
        pass
    if isinstance(value, str):
        key = str(value).strip().lower()
        mapping = {
            "": default_name,
            "none": "None",
            "straightin": "StraightIn",
            "straight_in": "StraightIn",
            "ils": "ILS",
            "ils_final": "ILS",
            "visual": "Visual",
            "overhead": "Overhead",
            "tacan": "TACAN",
        }
        return mapping.get(key, default_name)
    mapping_by_int = {
        0: "None",
        1: "StraightIn",
        2: "ILS",
        3: "Visual",
        4: "Overhead",
        5: "TACAN",
    }
    return mapping_by_int.get(_coerce_nonnegative_int(value, 0), default_name)


class ScenarioLoader:
    def __init__(self, sim_kernel):
        self.sim = sim_kernel
        self.scenario_data = {}
        self.entities = {} # map name -> entity_id
        self.agent_id = None
        self.steps = 0
        self.captured_time = 0.0
        self.max_contacts = 10
        self.max_rwr = 4

        # Waypoint mission state (command_code == 3).
        # Waypoints are part of the mission command (realistic: FMS/EGI steerpoints).
        self.waypoints: list[dict] = []
        self.waypoint_idx: int = 0
        self._waypoint_prev_dist_m: float | None = None
        self.waypoint_total_route_length_m: float = 0.0
        
        # Property Map for generic access
        self.prop_map = {
            "altitude": 2, "z": 2,
            "speed": 9, "velocity": 9,
            "health": 10, "hp": 10,
            "missiles": 11, "ammo": 11,
            "pitch": 7, "roll": 8, "heading": 6,
            "x": 0, "y": 1,
            "vx": 3, "vy": 4, "vz": 5
        }
        self.ils_beacons = []
        self.world_yaw_deg = 0.0
        self.world_yaw_origin_x = 0.0
        self.world_yaw_origin_y = 0.0
        self.rotate_mission_heading_with_world = False
        self.randomization_overrides = {}
        self.last_reward_breakdown = {}
        self.last_termination_reason = "idle"
        self._approach_prev_dme_m = None
        self._approach_prev_loc_abs = None
        self._approach_prev_gs_abs = None
        self.post_waypoint_transition: dict | None = None
        self.mission_phase_name: str = "idle"
        self.task_order = None
        self.leader_intent = None
        self.pilot_report = None
        self._leader_phase_manager = RuleBasedLeaderPhaseManager()

    def _task_order_spec(self) -> dict:
        task_cfg = self.scenario_data.get("task_order", None)
        return task_cfg if isinstance(task_cfg, dict) else {}

    def _normalize_mission_command_dict(self, cmd: dict | None) -> dict:
        if not isinstance(cmd, dict):
            return {
                "command_code": 0,
                "target_heading": 0.0,
                "target_altitude": 0.0,
                "target_speed": 0.0,
                "route_ref_id": 0,
                "recovery_base_id": 0,
                "recovery_runway_id": 0,
                "recovery_approach_type": "None",
            }

        task_cfg = self._task_order_spec()
        cmd["command_code"] = int(cmd.get("command_code", 0))
        cmd["target_heading"] = float(cmd.get("target_heading", 0.0))
        cmd["target_altitude"] = float(cmd.get("target_altitude", 0.0))
        cmd["target_speed"] = float(cmd.get("target_speed", 0.0))
        cmd["route_ref_id"] = _coerce_nonnegative_int(cmd.get("route_ref_id", 0), 0)

        recovery_base_id = _coerce_nonnegative_int(
            cmd.get("recovery_base_id", task_cfg.get("recovery_base_id", 0)),
            0,
        )
        recovery_runway_id = _coerce_nonnegative_int(
            cmd.get("recovery_runway_id", task_cfg.get("recovery_runway_id", 0)),
            0,
        )
        landing_mode = str(cmd.get("landing_mode", "")).strip().lower()
        is_terminal_cmd = bool(
            int(cmd.get("command_code", 0)) == COMMAND_CODE_LANDING
            or landing_mode
            or recovery_base_id > 0
            or recovery_runway_id > 0
        )
        recovery_approach_raw = cmd.get(
            "recovery_approach_type",
            task_cfg.get("recovery_approach_type", None),
        )
        if recovery_approach_raw is None and is_terminal_cmd:
            recovery_approach_raw = "StraightIn"
        cmd["recovery_base_id"] = int(recovery_base_id)
        cmd["recovery_runway_id"] = int(recovery_runway_id)
        cmd["recovery_approach_type"] = _canonical_recovery_approach_name(
            recovery_approach_raw,
            landing_mode=landing_mode,
        )

        post = cmd.get("post_waypoint_transition", None)
        if isinstance(post, dict):
            cmd["post_waypoint_transition"] = self._normalize_mission_command_dict(copy.deepcopy(post))
        return cmd

    def _sample_uniform(self, value, default: float) -> float:
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            try:
                return float(self.rng.uniform(float(value[0]), float(value[1])))
            except Exception:
                return float(default)
        try:
            return float(value)
        except Exception:
            return float(default)

    def _sample_int(self, value, default: int) -> int:
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            try:
                lo = int(math.floor(float(value[0])))
                hi = int(math.floor(float(value[1])))
                if hi < lo:
                    lo, hi = hi, lo
                return int(self.rng.randint(lo, hi + 1))
            except Exception:
                return int(default)
        try:
            return int(value)
        except Exception:
            return int(default)

    def _sample_entity_spawn(self, ent_cfg: dict) -> tuple[list[float], list[float], float, float, float]:
        pos = list(ent_cfg.get("pos", [0.0, 0.0, 0.0]))
        vel = list(ent_cfg.get("vel", [0.0, 0.0, 0.0]))
        heading = float(ent_cfg.get("heading", 0.0))
        pitch = float(ent_cfg.get("pitch", 0.0))
        roll = float(ent_cfg.get("roll", 0.0))

        rand_cfg = ent_cfg.get("randomization", None)
        if not isinstance(rand_cfg, dict):
            return pos, vel, heading, pitch, roll

        heading += self._sample_uniform(rand_cfg.get("heading_offset_deg_range", [0.0, 0.0]), 0.0)
        pitch += self._sample_uniform(rand_cfg.get("pitch_offset_deg_range", [0.0, 0.0]), 0.0)
        roll += self._sample_uniform(rand_cfg.get("roll_offset_deg_range", [0.0, 0.0]), 0.0)

        h_rad = math.radians(float(heading))
        fwd_x = math.sin(h_rad)
        fwd_y = math.cos(h_rad)
        right_x = math.cos(h_rad)
        right_y = -math.sin(h_rad)

        along_off = self._sample_uniform(rand_cfg.get("along_body_m_range", [0.0, 0.0]), 0.0)
        cross_off = self._sample_uniform(rand_cfg.get("cross_body_m_range", [0.0, 0.0]), 0.0)
        alt_off = self._sample_uniform(rand_cfg.get("altitude_offset_m_range", [0.0, 0.0]), 0.0)

        try:
            pos[0] = float(pos[0]) + along_off * fwd_x + cross_off * right_x
            pos[1] = float(pos[1]) + along_off * fwd_y + cross_off * right_y
            pos[2] = float(pos[2]) + alt_off
        except Exception:
            pass

        try:
            base_horiz_speed = math.sqrt(float(vel[0]) * float(vel[0]) + float(vel[1]) * float(vel[1]))
        except Exception:
            base_horiz_speed = 0.0
        speed_scale = self._sample_uniform(rand_cfg.get("speed_scale_range", [1.0, 1.0]), 1.0)
        speed_off = self._sample_uniform(rand_cfg.get("speed_offset_mps_range", [0.0, 0.0]), 0.0)
        horiz_speed = max(0.0, float(base_horiz_speed) * float(speed_scale) + float(speed_off))
        sink_rate = self._sample_uniform(rand_cfg.get("sink_rate_mps_range", [float(vel[2]) if len(vel) > 2 else 0.0, float(vel[2]) if len(vel) > 2 else 0.0]), float(vel[2]) if len(vel) > 2 else 0.0)

        if len(vel) < 3:
            vel = [0.0, 0.0, 0.0]
        vel[0] = float(horiz_speed * fwd_x)
        vel[1] = float(horiz_speed * fwd_y)
        vel[2] = float(sink_rate)

        return pos, vel, float(heading), float(pitch), float(roll)

    def _rotate_waypoints_inplace(self, waypoints: list[dict]) -> None:
        if abs(float(self.world_yaw_deg)) <= 1.0e-6:
            return
        for wp in waypoints:
            if not isinstance(wp, dict):
                if isinstance(wp, list) and len(wp) >= 2:
                    px, py = self._rotate_xy_clockwise(
                        wp[0],
                        wp[1],
                        self.world_yaw_origin_x,
                        self.world_yaw_origin_y,
                        self.world_yaw_deg,
                    )
                    wp[0] = px
                    wp[1] = py
                continue
            if "pos" in wp and isinstance(wp.get("pos"), list) and len(wp["pos"]) >= 2:
                px, py = self._rotate_xy_clockwise(
                    wp["pos"][0],
                    wp["pos"][1],
                    self.world_yaw_origin_x,
                    self.world_yaw_origin_y,
                    self.world_yaw_deg,
                )
                wp["pos"][0] = px
                wp["pos"][1] = py
            elif "x" in wp and "y" in wp:
                px, py = self._rotate_xy_clockwise(
                    wp.get("x", 0.0),
                    wp.get("y", 0.0),
                    self.world_yaw_origin_x,
                    self.world_yaw_origin_y,
                    self.world_yaw_deg,
                )
                wp["x"] = px
                wp["y"] = py

    def _generate_route_waypoints(self, cfg: dict) -> list[dict]:
        def _range_lo(value, default: float) -> float:
            if isinstance(value, (list, tuple)) and len(value) >= 1:
                try:
                    if len(value) >= 2:
                        return float(min(value[0], value[1]))
                    return float(value[0])
                except Exception:
                    return float(default)
            try:
                return float(value)
            except Exception:
                return float(default)

        entities = self.scenario_data.get("entities", [])
        spawn = None
        for ent in entities:
            if isinstance(ent, dict) and bool(ent.get("is_agent", False)):
                spawn = ent
                break
        if spawn is None and isinstance(entities, list) and entities:
            spawn = entities[0] if isinstance(entities[0], dict) else None

        spawn_pos = spawn.get("pos", [0.0, 0.0, 0.0]) if isinstance(spawn, dict) else [0.0, 0.0, 0.0]
        try:
            x = float(spawn_pos[0])
            y = float(spawn_pos[1])
            spawn_alt = float(spawn_pos[2])
        except Exception:
            x = 0.0
            y = 0.0
            spawn_alt = float(self.mission_cmd.get("target_altitude", 1200.0))

        try:
            base_heading = float(self.mission_cmd.get("target_heading", spawn.get("heading", 90.0) if isinstance(spawn, dict) else 90.0))
        except Exception:
            base_heading = 90.0
        initial_abs = cfg.get("initial_course_deg_range", None)
        if initial_abs is not None:
            course_deg = self._sample_uniform(initial_abs, base_heading) % 360.0
        else:
            delta = self._sample_uniform(cfg.get("first_leg_heading_delta_deg_range", [0.0, 0.0]), 0.0)
            course_deg = (base_heading + float(delta)) % 360.0

        count = max(2, self._sample_int(cfg.get("waypoint_count_range", [3, 5]), 4))
        leg_default = float(cfg.get("leg_length_m", 16000.0))
        leg_range = cfg.get("leg_length_m_range", [leg_default, leg_default])
        first_leg_range = cfg.get("first_leg_length_m_range", leg_range)
        subsequent_leg_range = cfg.get("subsequent_leg_length_m_range", leg_range)
        min_leg_m = max(
            2000.0,
            float(
                cfg.get(
                    "min_leg_length_m",
                    min(
                        float(first_leg_range[0] if isinstance(first_leg_range, (list, tuple)) and len(first_leg_range) >= 1 else leg_default),
                        float(subsequent_leg_range[0] if isinstance(subsequent_leg_range, (list, tuple)) and len(subsequent_leg_range) >= 1 else leg_default),
                    ),
                )
            ),
        )
        radius_range = cfg.get("waypoint_radius_m_range", [900.0, 1400.0])
        speed_range = cfg.get("speed_mps_range", [float(self.mission_cmd.get("target_speed", 210.0)), float(self.mission_cmd.get("target_speed", 210.0))])
        altitude_range = cfg.get("altitude_m_range", [float(self.mission_cmd.get("target_altitude", spawn_alt)), float(self.mission_cmd.get("target_altitude", spawn_alt))])
        altitude_step_range = cfg.get("altitude_step_m_range", [0.0, 0.0])
        turn_range = cfg.get("turn_angle_deg_range", [-60.0, 60.0])
        min_turn_abs = max(0.0, float(cfg.get("min_turn_abs_deg", 10.0)))
        max_turn_abs = abs(float(cfg.get("max_turn_abs_deg", 120.0)))
        turn_feasibility_enabled = bool(cfg.get("turn_feasibility_enabled", False))
        turn_leg_usage_fraction_limit = float(cfg.get("turn_leg_usage_fraction_limit", 0.30))
        turn_leg_usage_fraction_limit = float(np.clip(turn_leg_usage_fraction_limit, 0.05, 0.49))
        turn_clearance_m = max(
            0.0,
            float(
                cfg.get(
                    "turn_clearance_m",
                    max(
                        800.0,
                        float(self.mission_cmd.get("waypoint_radius_m", 1000.0)),
                    ),
                )
            ),
        )
        env_cfg = self.scenario_data.get("environment", {}) if isinstance(self.scenario_data.get("environment", {}), dict) else {}
        time_step_s = float(env_cfg.get("time_step", 0.05))
        max_steps = int(env_cfg.get("max_steps", self.get_max_steps()))
        route_budget_fraction = float(cfg.get("route_budget_fraction", 0.80))
        route_budget_fraction = float(np.clip(route_budget_fraction, 0.25, 1.00))
        route_budget_margin_fraction = float(cfg.get("route_budget_margin_fraction", 0.0))
        route_budget_margin_fraction = float(np.clip(route_budget_margin_fraction, 0.0, 0.50))
        target_speed_mps = max(80.0, float(self.mission_cmd.get("target_speed", 210.0)))
        turn_speed_ref_mps = max(
            80.0,
            float(
                cfg.get(
                    "turn_feasibility_speed_mps",
                    max(target_speed_mps, _range_lo(speed_range, target_speed_mps)),
                )
            ),
        )
        bank_limit_deg = float(self.mission_cmd.get("lnav_bank_limit_deg", 30.0))
        max_route_distance_m = max(min_leg_m * float(count), target_speed_mps * time_step_s * float(max_steps) * route_budget_fraction)
        if route_budget_margin_fraction > 0.0:
            max_route_distance_m = max(min_leg_m * float(count), max_route_distance_m * (1.0 - route_budget_margin_fraction))
        max_count = max(2, int(max_route_distance_m // min_leg_m))
        count = min(count, max_count)

        try:
            alt_lo = float(min(altitude_range[0], altitude_range[1]))
            alt_hi = float(max(altitude_range[0], altitude_range[1]))
        except Exception:
            alt_lo = alt_hi = float(self.mission_cmd.get("target_altitude", spawn_alt))
        altitude = float(np.clip(self._sample_uniform(altitude_range, float(self.mission_cmd.get("target_altitude", spawn_alt))), alt_lo, alt_hi))
        default_mode = self._normalize_waypoint_mode(self.mission_cmd.get("waypoint_mode", "flyby"))
        waypoint_mode_cycle = cfg.get("waypoint_mode_cycle", None)
        if not isinstance(waypoint_mode_cycle, (list, tuple)):
            waypoint_mode_cycle = []
        waypoint_mode_cycle = [self._normalize_waypoint_mode(x) for x in waypoint_mode_cycle if str(x).strip()]
        final_waypoint_mode = self._normalize_waypoint_mode(cfg.get("final_waypoint_mode", "flyover"))

        waypoints: list[dict] = []
        remaining_route_budget_m = float(max_route_distance_m)
        for idx in range(count):
            legs_left = max(1, count - idx)
            leg_sample_cfg = first_leg_range if idx == 0 else subsequent_leg_range
            leg_sample_m = max(min_leg_m, float(self._sample_uniform(leg_sample_cfg, leg_default)))
            min_remaining_after_this_m = min_leg_m * float(max(0, legs_left - 1))
            leg_cap_m = max(min_leg_m, remaining_route_budget_m - min_remaining_after_this_m)
            leg_m = min(leg_sample_m, leg_cap_m)
            remaining_route_budget_m = max(0.0, remaining_route_budget_m - leg_m)
            h_rad = math.radians(course_deg)
            x += leg_m * math.sin(h_rad)
            y += leg_m * math.cos(h_rad)
            if idx > 0:
                altitude += float(self._sample_uniform(altitude_step_range, 0.0))
                altitude = float(np.clip(altitude, alt_lo, alt_hi))
            radius_m = max(300.0, float(self._sample_uniform(radius_range, 1000.0)))
            speed_mps = max(80.0, float(self._sample_uniform(speed_range, float(self.mission_cmd.get("target_speed", 210.0)))))
            if idx >= count - 1:
                waypoint_mode = final_waypoint_mode
            elif waypoint_mode_cycle:
                waypoint_mode = waypoint_mode_cycle[idx % len(waypoint_mode_cycle)]
            else:
                waypoint_mode = default_mode
            waypoints.append(
                {
                    "x": float(x),
                    "y": float(y),
                    "z": float(altitude),
                    "altitude_m": float(altitude),
                    "speed_mps": float(speed_mps),
                    "radius_m": float(radius_m),
                    "waypoint_mode": str(waypoint_mode),
                }
            )
            if idx >= count - 1:
                continue

            next_leg_floor_m = min_leg_m
            if idx < (count - 1):
                lower_bound_m = max(min_leg_m, _range_lo(subsequent_leg_range, leg_default))
                legs_remaining_after_next = max(0, count - idx - 2)
                min_remaining_after_next_m = min_leg_m * float(legs_remaining_after_next)
                next_leg_cap_m = max(min_leg_m, remaining_route_budget_m - min_remaining_after_next_m)
                next_leg_floor_m = max(min_leg_m, min(lower_bound_m, next_leg_cap_m))

            turn_deg = float(self._sample_uniform(turn_range, 0.0))
            turn_range_abs_max = max(abs(float(turn_range[0])), abs(float(turn_range[1])))
            if abs(turn_deg) < min_turn_abs and turn_range_abs_max >= min_turn_abs:
                sign = 1.0 if turn_deg >= 0.0 else -1.0
                if abs(turn_deg) < 1.0e-6:
                    sign = 1.0 if float(self.rng.rand()) >= 0.5 else -1.0
                turn_deg = sign * min_turn_abs
            feasible_turn_abs_deg = float(max_turn_abs)
            if turn_feasibility_enabled:
                lead_budget_m = min(float(leg_m), float(next_leg_floor_m)) * turn_leg_usage_fraction_limit - max(turn_clearance_m, radius_m)
                if lead_budget_m <= 0.0:
                    feasible_turn_abs_deg = 0.0
                else:
                    feasible_turn_abs_deg = min(
                        float(max_turn_abs),
                        2.0 * math.degrees(math.atan2(float(lead_budget_m), self._turn_radius_m(turn_speed_ref_mps, bank_limit_deg))),
                    )
                    feasible_turn_abs_deg = max(0.0, float(feasible_turn_abs_deg))

            if feasible_turn_abs_deg < min_turn_abs and turn_range_abs_max >= min_turn_abs:
                turn_deg = float(np.clip(turn_deg, -feasible_turn_abs_deg, feasible_turn_abs_deg))
            else:
                turn_deg = float(np.clip(turn_deg, -min(max_turn_abs, feasible_turn_abs_deg), min(max_turn_abs, feasible_turn_abs_deg)))
            course_deg = (course_deg + turn_deg) % 360.0
        return waypoints

    def _turn_radius_m(self, speed_mps: float, bank_limit_deg: float) -> float:
        bank_rad = math.radians(float(np.clip(bank_limit_deg, 1.0, 80.0)))
        tanb = math.tan(bank_rad)
        if abs(tanb) <= 1.0e-6:
            return float("inf")
        v = max(30.0, float(speed_mps))
        return (v * v) / (9.80665 * abs(tanb))

    def set_randomization_overrides(self, overrides: dict | None) -> None:
        """
        Override `environment.randomization` fields from the scenario JSON at load time.

        Intended for curriculum learning: gradually increase randomization ranges (wind/yaw)
        without editing the scenario file on disk.
        """
        if overrides is None:
            self.randomization_overrides = {}
            return
        if not isinstance(overrides, dict):
            raise TypeError(f"randomization overrides must be a dict or None, got {type(overrides)}")
        self.randomization_overrides = dict(overrides)
        
    def load_scenario(self, json_path, seed=42):
        if seed is None:
            seed = np.random.randint(0, 2**32 - 1)
        seed = int(seed) & 0xFFFFFFFF
        self.rng = np.random.RandomState(seed)
        with open(json_path, 'r') as f:
            self.scenario_data = json.load(f)
            
        # Handle Options/Imports (Generic Prefabs)
        if "imports" in self.scenario_data:
            self._process_imports(self.scenario_data["imports"])
            
        # Parse Mission Command
        self.mission_cmd = self.scenario_data.get("mission_command", {
            "command_code": 0, "target_heading": 0.0, "target_altitude": 0.0, "target_speed": 0.0
        })
            
        # 1. Setup Environment
        if "environment" in self.scenario_data:
            env_cfg = self.scenario_data["environment"]
            env_rand = env_cfg.get("randomization", {}) if isinstance(env_cfg.get("randomization", {}), dict) else {}
            if isinstance(self.randomization_overrides, dict) and self.randomization_overrides:
                env_rand = dict(env_rand)
                env_rand.update(self.randomization_overrides)
            self.rotate_mission_heading_with_world = bool(env_rand.get("rotate_mission_heading_with_world", False))

            # World yaw randomization (rotates the entire scenario geometry around an origin).
            # This prevents agents from exploiting fixed runway/terrain headings.
            self.world_yaw_deg = 0.0
            self.world_yaw_origin_x = 0.0
            self.world_yaw_origin_y = 0.0
            if "world_yaw_range" in env_rand:
                r = env_rand["world_yaw_range"]
                yaw_deg = float(self.rng.uniform(r[0], r[1]))
                origin = env_rand.get("world_yaw_origin", [0.0, 0.0])
                try:
                    ox = float(origin[0])
                    oy = float(origin[1])
                except Exception:
                    ox, oy = 0.0, 0.0
                self._apply_world_yaw(yaw_deg, ox, oy)
                self.world_yaw_deg = yaw_deg
                self.world_yaw_origin_x = ox
                self.world_yaw_origin_y = oy

            if "time_step" in env_cfg:
                self.sim.set_time_step(env_cfg["time_step"])

            # Terrain profile must be applied explicitly on every load because the environment
            # model persists across episode resets inside the shared SimulationKernel.
            terrain_type = str(env_cfg.get("terrain_type", "legacy")).strip() or "legacy"
            if hasattr(self.sim, "set_terrain_type"):
                try:
                    self.sim.set_terrain_type(terrain_type)
                except Exception:
                    pass

            # Wind / Atmosphere configuration (optional)
            # Uses NAV convention for direction "from": 0=North, CW positive.
            wind_cfg = env_cfg.get("wind", {}) if isinstance(env_cfg.get("wind", {}), dict) else {}

            wind_speed = float(wind_cfg.get("speed_mps", 10.0))
            wind_dir_from = float(wind_cfg.get("dir_from_deg", 270.0))
            wind_shear = float(wind_cfg.get("shear_mps_per_km", 4.0))

            def _primary_runway_heading_deg() -> float | None:
                zones = env_cfg.get("zones", [])
                if not isinstance(zones, list):
                    return None
                best = None
                best_pri = -1
                for z in zones:
                    if not isinstance(z, dict):
                        continue
                    name = str(z.get("name", "")).lower()
                    surface = str(z.get("surface", ""))
                    ils_cfg = z.get("ils", {})
                    if not isinstance(ils_cfg, dict):
                        ils_cfg = {}
                    ils_enabled = bool(ils_cfg.get("enabled", False))
                    is_runway = "runway" in name
                    # Priority: ILS-enabled runway > named runway > other paved zones.
                    pri = 0
                    if ils_enabled and is_runway:
                        pri = 3
                    elif ils_enabled:
                        pri = 2
                    elif is_runway and surface in ("Concrete", "Asphalt"):
                        pri = 1
                    if pri <= best_pri:
                        continue
                    try:
                        hdg = float(z.get("heading", 0.0)) % 360.0
                    except Exception:
                        continue
                    best = hdg
                    best_pri = pri
                return best

            # Optional: runway-relative wind sampling (realistic for takeoff/landing scenarios).
            # Specify headwind/crosswind components instead of global direction:
            #   wind_headwind_range:   [min, max] m/s  (positive = headwind, negative = tailwind)
            #   wind_crosswind_range:  [min, max] m/s  (positive = wind-from runway right)
            #   wind_tailwind_max_mps: float         (optional clamp for negative headwind)
            used_runway_relative_wind = False
            if "wind_headwind_range" in env_rand or "wind_crosswind_range" in env_rand:
                r_h = env_rand.get("wind_headwind_range", [0.0, 0.0])
                r_c = env_rand.get("wind_crosswind_range", [0.0, 0.0])
                try:
                    headwind = float(self.rng.uniform(float(r_h[0]), float(r_h[1])))
                except Exception:
                    headwind = 0.0
                try:
                    crosswind = float(self.rng.uniform(float(r_c[0]), float(r_c[1])))
                except Exception:
                    crosswind = 0.0

                tw_max = env_rand.get("wind_tailwind_max_mps", env_rand.get("wind_tailwind_max", None))
                if tw_max is not None:
                    try:
                        tw_max_f = abs(float(tw_max))
                        headwind = max(headwind, -tw_max_f)
                    except Exception:
                        pass

                rw_hdg = _primary_runway_heading_deg()
                if rw_hdg is not None:
                    h_rad = math.radians(float(rw_hdg))
                    fwd_x = math.sin(h_rad)
                    fwd_y = math.cos(h_rad)
                    right_x = math.cos(h_rad)
                    right_y = -math.sin(h_rad)
                    wx = headwind * fwd_x + crosswind * right_x
                    wy = headwind * fwd_y + crosswind * right_y
                    wind_speed = float(math.sqrt(wx * wx + wy * wy))
                    wind_dir_from = float((math.degrees(math.atan2(wx, wy)) + 360.0) % 360.0)
                    used_runway_relative_wind = True

            if not used_runway_relative_wind:
                if "wind_speed_range" in env_rand:
                    r = env_rand["wind_speed_range"]
                    wind_speed = float(self.rng.uniform(r[0], r[1]))
                if "wind_dir_from_range" in env_rand:
                    r = env_rand["wind_dir_from_range"]
                    wind_dir_from = float(self.rng.uniform(r[0], r[1]))
            if "wind_shear_range" in env_rand:
                r = env_rand["wind_shear_range"]
                wind_shear = float(self.rng.uniform(r[0], r[1]))

            # Interpret wind_speed_range as the wind speed at a *reference altitude* when shear is enabled.
            #
            # The environment model applies shear as: v(z) = base_speed + shear * (z_km).
            # If we directly sample base_speed from wind_speed_range and also apply positive shear,
            # the resulting wind at typical start altitudes (e.g., 1000m) can exceed the configured
            # range by a large margin (speed + shear*1km). That makes scenario randomization harder to
            # reason about and often less realistic.
            #
            # To keep scenario configs intuitive and realism-first, we treat wind_speed_range as the
            # intended wind magnitude at a reference altitude (default: agent spawn altitude) and
            # convert it to the base_speed passed into the environment model.
            if abs(float(wind_shear)) > 1.0e-9:
                wind_ref_alt_m = env_rand.get("wind_ref_alt_m", None)
                if wind_ref_alt_m is None:
                    try:
                        # Prefer agent spawn altitude as reference.
                        for ent in self.scenario_data.get("entities", []):
                            if isinstance(ent, dict) and bool(ent.get("is_agent", False)):
                                pos = ent.get("pos", None)
                                if isinstance(pos, list) and len(pos) >= 3:
                                    wind_ref_alt_m = float(pos[2])
                                    break
                    except Exception:
                        wind_ref_alt_m = None
                if wind_ref_alt_m is None:
                    try:
                        ents = self.scenario_data.get("entities", [])
                        if isinstance(ents, list) and ents:
                            pos = ents[0].get("pos", None) if isinstance(ents[0], dict) else None
                            if isinstance(pos, list) and len(pos) >= 3:
                                wind_ref_alt_m = float(pos[2])
                    except Exception:
                        wind_ref_alt_m = None
                if wind_ref_alt_m is None:
                    wind_ref_alt_m = 0.0
                alt_km_ref = max(0.0, float(wind_ref_alt_m)) / 1000.0
                try:
                    base_speed = float(wind_speed) - float(wind_shear) * alt_km_ref
                except Exception:
                    base_speed = float(wind_speed)
                wind_speed = max(0.0, base_speed)

            if hasattr(self.sim, "set_wind"):
                try:
                    self.sim.set_wind(wind_speed, wind_dir_from, wind_shear)
                except Exception:
                    pass
            
            # Zones (Runways/Terrains)
            if hasattr(self.sim, 'clear_zones'):
                self.sim.clear_zones()
                
                # Zone Type Map (String -> Int)
                surf_map = {
                    "Concrete": 0, "Asphalt": 1, 
                    "HardPacked": 2, "SoftDirt": 3, 
                    "Water": 4, "Obstacle": 5
                }
                
                for z in env_cfg.get("zones", []):
                    sx = surf_map.get(z.get("surface", "SoftDirt"), 3)
                    if os.environ.get("CMO_DEBUG_ZONES"):
                        print(f"[DEBUG] Adding zone: {z.get('name', 'Zone')} at ({z.get('x')}, {z.get('y')}) heading={z.get('heading')}")
                    self.sim.add_zone(
                        z.get("name", "Zone"),
                        float(z.get("x", 0.0)),
                        float(z.get("y", 0.0)),
                        float(z.get("width", 1000.0)),
                        float(z.get("length", 1000.0)),
                        float(z.get("heading", 0.0)),
                        int(sx)
                    )
        
        # 2. Spawn Entities
        self.entities = {}
        agents = []
        self.sim.reset(seed)  # Deterministic Physics Reset
        
        for ent_cfg in self.scenario_data.get("entities", []):
            side_map = {
                "Blue": ef_py.Side.Blue,
                "Red": ef_py.Side.Red,
                "Neutral": ef_py.Side.Neutral
            }
            side = side_map.get(ent_cfg["side"], ef_py.Side.Neutral)

            p, v, heading, pitch, roll = self._sample_entity_spawn(ent_cfg)

            eid = self.sim.spawn_unit(
                side,
                ent_cfg["type"],
                float(p[0]), float(p[1]), float(p[2]),
                heading, pitch, roll,
                float(v[0]), float(v[1]), float(v[2])
            )
            
            self.entities[ent_cfg["name"]] = eid
            
            if ent_cfg.get("is_agent", False):
                agents.append(eid)
        
        self.agent_id = agents[0] if agents else None
        self.steps = 0
        self.captured_time = 0.0
        
        # Reset State Tracking for Rewards
        self.prev_alt = 0.0
        self.prev_speed = 0.0
        self.gear_bonus_awarded = False
        self.liftoff_awarded = False
        self.off_runway_steps = 0
        self.last_reward_breakdown = {}
        self.last_termination_reason = "running"
        self._approach_prev_dme_m = None
        self._approach_prev_loc_abs = None
        self._approach_prev_gs_abs = None
        self.post_waypoint_transition = None
        self.mission_phase_name = "primary"
        
        # Randomize Mission if ranges provided
        self._randomize_mission()
        self._randomize_task_order()
        self.mission_cmd = self._normalize_mission_command_dict(self.mission_cmd)

        post_transition_cfg = self.mission_cmd.get("post_waypoint_transition", None)
        if isinstance(post_transition_cfg, dict) and post_transition_cfg:
            self.post_waypoint_transition = copy.deepcopy(post_transition_cfg)

        # Optional: rotate mission target heading together with world-yaw randomization.
        # Default is to keep mission headings in global coordinates (more realistic for command inputs).
        if self.rotate_mission_heading_with_world and self.world_yaw_deg != 0.0:
            try:
                self.mission_cmd["target_heading"] = float(self.mission_cmd.get("target_heading", 0.0)) + float(self.world_yaw_deg)
            except Exception:
                pass
            self.mission_cmd["target_heading"] = float(self.mission_cmd.get("target_heading", 0.0)) % 360.0

        # Parse mission waypoints (if any). This must run after world-yaw has been applied.
        self._parse_waypoints()

        # Mirror mission command into the simulation kernel (so cmd_* instrument fields and
        # any mission-aware systems stay consistent with the Python-side mission randomization).
        self._sync_kernel_mission_command()
        self._reset_command_chain()
        
        # Initialize prev state if agent exists
        if self.agent_id is not None:
             truth = self.sim.get_agent_observation(self.agent_id)
             self.prev_alt = truth.z
             # Waypoint LNAV: leg origin for the first leg is the spawn position.
             self._waypoint_leg_origin_x = float(getattr(truth, "x", 0.0))
             self._waypoint_leg_origin_y = float(getattr(truth, "y", 0.0))
             # Use IAS for speed shaping/objectives (robust under randomized wind).
             # Ground speed is still used for stationary detection.
             try:
                 inst0 = self.sim.get_instrument_state(self.agent_id)
                 self.prev_speed = float(inst0.ias)
             except Exception:
                 self.prev_speed = truth.speed

        # If this is a waypoint mission, initialize the commanded heading/targets immediately so the
        # very first observation matches the active waypoint.
        try:
            self.update_behaviors(0.0)
        except Exception:
            pass

        # Cache ILS beacons (purely derived from scenario geometry; no direct runway heading is exposed).
        self.ils_beacons = self._extract_ils_beacons()
             
        return self.agent_id

    def _extract_ils_beacons(self):
        beacons = []
        zones = self.scenario_data.get("environment", {}).get("zones", [])
        if not isinstance(zones, list):
            return beacons

        for zone in zones:
            if not isinstance(zone, dict):
                continue
            name = str(zone.get("name", ""))
            surface = str(zone.get("surface", ""))
            ils_cfg = zone.get("ils", {})
            if not isinstance(ils_cfg, dict):
                ils_cfg = {}

            enabled = bool(ils_cfg.get("enabled", False))
            if not enabled:
                # Sensible default: paved runway/taxiway zones can provide an ILS beacon if named as runway.
                if ("runway" in name.lower()) and surface in ("Concrete", "Asphalt"):
                    enabled = True
                else:
                    continue

            try:
                cx = float(zone.get("x", 0.0))
                cy = float(zone.get("y", 0.0))
                width = float(zone.get("width", 0.0))
                length = float(zone.get("length", 0.0))
                heading = float(zone.get("heading", 0.0)) % 360.0
            except Exception:
                continue

            if length <= 1.0:
                continue
            if width <= 1.0:
                # Default runway width fallback (meters)
                width = float(ils_cfg.get("width_m", 60.0))

            glide_slope_deg = float(ils_cfg.get("glide_slope_deg", 3.0))
            loc_max_deg = float(ils_cfg.get("loc_max_deg", 2.5))
            gs_max_deg = float(ils_cfg.get("gs_max_deg", 0.7))
            range_m = float(ils_cfg.get("range_m", 25000.0))
            elev_m = float(ils_cfg.get("elev_m", 0.0))

            # NAV heading (0=N, CW): forward unit vector (x=East, y=North).
            h_rad = math.radians(heading)
            fwd_x = math.sin(h_rad)
            fwd_y = math.cos(h_rad)

            thr_x = cx - fwd_x * (length * 0.5)
            thr_y = cy - fwd_y * (length * 0.5)

            beacons.append(
                {
                    "name": name,
                    "cx": cx,
                    "cy": cy,
                    "thr_x": thr_x,
                    "thr_y": thr_y,
                    "heading": heading,
                    "length": length,
                    "width": width,
                    "elev_m": elev_m,
                    "glide_slope_deg": glide_slope_deg,
                    "loc_max_deg": max(0.1, loc_max_deg),
                    "gs_max_deg": max(0.1, gs_max_deg),
                    "range_m": max(100.0, range_m),
                }
            )

        return beacons

    def _nearest_ils_beacon(self, x_m: float, y_m: float):
        if not self.ils_beacons:
            return None
        best = None
        best_d2 = float("inf")
        for b in self.ils_beacons:
            dx = x_m - float(b.get("cx", 0.0))
            dy = y_m - float(b.get("cy", 0.0))
            d2 = dx * dx + dy * dy
            if d2 < best_d2:
                best_d2 = d2
                best = b
        return best

    def get_runway_local_frame(self, x_m: float, y_m: float):
        """
        Returns a geometry-only runway frame derived from the nearest ILS beacon.

        Output:
          valid: bool
          along_m: float  (positive along runway forward axis, relative to runway center)
          cross_m: float  (positive to the runway right)
          length_m: float
          width_m: float
        """
        b = self._nearest_ils_beacon(x_m, y_m)
        if b is None:
            return False, 0.0, 0.0, 0.0, 0.0
        h_rad = math.radians(float(b.get("heading", 0.0)))
        fwd_x = math.sin(h_rad)
        fwd_y = math.cos(h_rad)
        right_x = math.cos(h_rad)
        right_y = -math.sin(h_rad)

        dx = x_m - float(b.get("cx", 0.0))
        dy = y_m - float(b.get("cy", 0.0))
        along = dx * fwd_x + dy * fwd_y
        cross = dx * right_x + dy * right_y
        length = float(b.get("length", 0.0))
        width = float(b.get("width", 0.0))
        if not (length > 1.0 and width > 1.0):
            return False, float(along), float(cross), float(length), float(width)
        return True, float(along), float(cross), float(length), float(width)

    def get_ils_observation(self, x_m: float, y_m: float, alt_m: float):
        """
        Returns a small navigation observation vector:
        [ils_valid, loc_dev, gs_dev, dme_m]

        - loc_dev, gs_dev are normalized to [-1, 1] using the configured max deflections.
        - dme_m is slant-range distance to the threshold reference point.
        - For landing tasks, glideslope is referenced to a threshold-crossing-height
          point above the runway threshold rather than the threshold pavement itself.
        """
        if not self.ils_beacons:
            return np.zeros((4,), dtype=np.float32)

        best = None
        best_d2 = float("inf")
        for b in self.ils_beacons:
            dx = x_m - b["cx"]
            dy = y_m - b["cy"]
            d2 = dx * dx + dy * dy
            if d2 < best_d2:
                best_d2 = d2
                best = b

        if best is None:
            return np.zeros((4,), dtype=np.float32)

        h_rad = math.radians(float(best["heading"]))
        fwd_x = math.sin(h_rad)
        fwd_y = math.cos(h_rad)
        right_x = math.cos(h_rad)
        right_y = -math.sin(h_rad)

        # Localizer geometry: use a fixed reference point at the far end of the runway
        # (opposite the threshold) to avoid a singularity near the runway center.
        #
        # This yields a stable, pilot-like "centerline deviation angle" throughout the takeoff roll.
        cx = float(best["cx"])
        cy = float(best["cy"])
        length = float(best.get("length", 0.0))
        loc_x = cx + fwd_x * (0.5 * length)
        loc_y = cy + fwd_y * (0.5 * length)

        dx = x_m - loc_x
        dy = y_m - loc_y
        # Positive "along" means the aircraft is in front of the localizer antenna; clamp for safety.
        along = -(dx * fwd_x + dy * fwd_y)
        cross = dx * right_x + dy * right_y

        along_abs = max(abs(along), 1.0)
        loc_angle_deg = math.degrees(math.atan2(cross, along_abs))
        loc_dev = float(np.clip(loc_angle_deg / float(best["loc_max_deg"]), -1.0, 1.0))

        thr_dx = x_m - float(best["thr_x"])
        thr_dy = y_m - float(best["thr_y"])
        # Positive approach distance means the aircraft is still on final, inbound to the threshold.
        approach_dist_m = -(thr_dx * fwd_x + thr_dy * fwd_y)
        dme = float(math.sqrt(thr_dx * thr_dx + thr_dy * thr_dy + (alt_m - float(best["elev_m"])) ** 2))

        glide_slope_deg = float(best["glide_slope_deg"])
        gs_max_deg = float(best["gs_max_deg"])
        try:
            threshold_crossing_height_m = max(
                0.0,
                float(getattr(self, "mission_cmd", {}).get("threshold_crossing_height_m", 0.0)),
            )
        except Exception:
            threshold_crossing_height_m = 0.0
        gs_ref_alt_m = float(best["elev_m"]) + threshold_crossing_height_m

        if approach_dist_m <= 1.0:
            gs_dev = 0.0
        else:
            gs_angle_deg = math.degrees(math.atan2(alt_m - gs_ref_alt_m, approach_dist_m))
            gs_dev = float(np.clip((gs_angle_deg - glide_slope_deg) / gs_max_deg, -1.0, 1.0))

        valid = 1.0 if dme <= float(best["range_m"]) else 0.0

        return np.array([valid, loc_dev, gs_dev, dme], dtype=np.float32)

    def _randomize_mission(self):
        """Randomize mission parameters if ranges are specified in config."""
        # Use seeded RNG (self.rng) instead of global
        base_cmd = self.scenario_data.get("mission_command", {})
        
        # Check for randomization config
        rand_cfg = base_cmd.get("randomization", {})
        
        # 1. Heading
        if "heading_range" in rand_cfg:
            r = rand_cfg["heading_range"]
            self.mission_cmd["target_heading"] = self.rng.uniform(r[0], r[1])
        
        # 2. Altitude
        if "altitude_range" in rand_cfg:
            r = rand_cfg["altitude_range"]
            self.mission_cmd["target_altitude"] = self.rng.uniform(r[0], r[1])
            
        # 3. Speed
        if "speed_range" in rand_cfg:
            r = rand_cfg["speed_range"]
            self.mission_cmd["target_speed"] = self.rng.uniform(r[0], r[1])

        # 4. Waypoint topology / route generation
        route_generated = False
        route_gen = rand_cfg.get("route_generator", None)
        if isinstance(route_gen, dict) and bool(route_gen.get("enabled", True)):
            generated = self._generate_route_waypoints(route_gen)
            if generated:
                if self.rotate_mission_heading_with_world and abs(float(self.world_yaw_deg)) > 1.0e-6:
                    self._rotate_waypoints_inplace(generated)
                self.mission_cmd["waypoints"] = generated
                self.mission_cmd["_waypoint_template_idx"] = -1
                self.mission_cmd["_route_generator_used"] = True
                route_generated = True

        # 5. Waypoint topology / route template selection
        wp_templates = rand_cfg.get("waypoint_templates", None)
        if not route_generated and isinstance(wp_templates, list) and wp_templates:
            try:
                idx = int(self.rng.randint(0, len(wp_templates)))
            except Exception:
                idx = 0
            chosen = wp_templates[idx]
            if isinstance(chosen, list) and chosen:
                waypoints = copy.deepcopy(chosen)
                self._rotate_waypoints_inplace(waypoints)
                self.mission_cmd["waypoints"] = waypoints
                self.mission_cmd["_waypoint_template_idx"] = int(idx)
        
        # Ensure values are floats
        self.mission_cmd = self._normalize_mission_command_dict(self.mission_cmd)

    def _randomize_task_order(self):
        """Randomize top-level C2 task parameters when ranges are specified in scenario.task_order."""
        task_cfg = self.scenario_data.get("task_order", None)
        if not isinstance(task_cfg, dict):
            return

        rand_cfg = task_cfg.get("randomization", None)
        if not isinstance(rand_cfg, dict) or not rand_cfg:
            return

        def _sample_uniform(name: str):
            raw = rand_cfg.get(name, None)
            if not isinstance(raw, (list, tuple)) or len(raw) < 2:
                return None
            try:
                return float(self.rng.uniform(float(raw[0]), float(raw[1])))
            except Exception:
                return None

        def _sample_int(name: str):
            raw = rand_cfg.get(name, None)
            if not isinstance(raw, (list, tuple)) or len(raw) < 2:
                return None
            try:
                lo = int(raw[0])
                hi = int(raw[1])
            except Exception:
                return None
            if hi < lo:
                lo, hi = hi, lo
            try:
                return int(self.rng.randint(lo, hi + 1))
            except Exception:
                return None

        def _f(value, default: float = 0.0) -> float:
            try:
                return float(value)
            except Exception:
                return float(default)

        base_target_alt = _f(task_cfg.get("target_altitude_m", task_cfg.get("anchor_z_m", 0.0)), 0.0)
        base_alt_lo = _f(task_cfg.get("altitude_block_min_m", max(0.0, base_target_alt - 500.0)), max(0.0, base_target_alt - 500.0))
        base_alt_hi = _f(task_cfg.get("altitude_block_max_m", base_target_alt + 500.0), base_target_alt + 500.0)
        base_target_speed = _f(task_cfg.get("target_speed_mps", 0.0), 0.0)
        base_spd_lo = _f(task_cfg.get("speed_min_mps", max(0.0, base_target_speed - 40.0)), max(0.0, base_target_speed - 40.0))
        base_spd_hi = _f(task_cfg.get("speed_max_mps", base_target_speed + 40.0), base_target_speed + 40.0)

        alt_target = _sample_uniform("target_altitude_range_m")
        if alt_target is not None:
            task_cfg["target_altitude_m"] = float(alt_target)
        speed_target = _sample_uniform("target_speed_range_mps")
        if speed_target is not None:
            task_cfg["target_speed_mps"] = float(speed_target)

        for rand_key, field_name in (
            ("anchor_x_range_m", "anchor_x_m"),
            ("anchor_y_range_m", "anchor_y_m"),
            ("anchor_z_range_m", "anchor_z_m"),
            ("station_radius_range_m", "station_radius_m"),
            ("station_leg_length_range_m", "station_leg_length_m"),
            ("station_heading_range_deg", "station_heading_deg"),
            ("on_station_time_range_s", "on_station_time_s"),
            ("fuel_bingo_override_range_kg", "fuel_bingo_override_kg"),
        ):
            sampled = _sample_uniform(rand_key)
            if sampled is not None:
                task_cfg[field_name] = float(sampled)

        priority = _sample_int("priority_range")
        if priority is not None:
            task_cfg["priority"] = int(priority)

        task_id = _sample_int("task_id_range")
        if task_id is not None:
            task_cfg["task_id"] = int(task_id)

        station_choices = rand_cfg.get("station_type_choices", None)
        if isinstance(station_choices, list):
            station_choices = [str(x) for x in station_choices if str(x).strip()]
            if station_choices:
                try:
                    idx = int(self.rng.randint(0, len(station_choices)))
                except Exception:
                    idx = 0
                task_cfg["station_type"] = str(station_choices[idx])

        target_alt = _f(task_cfg.get("target_altitude_m", base_target_alt), base_target_alt)
        alt_halfspan = _sample_uniform("altitude_block_halfspan_range_m")
        if alt_halfspan is not None:
            alt_halfspan = max(0.0, float(alt_halfspan))
            task_cfg["altitude_block_min_m"] = max(0.0, target_alt - alt_halfspan)
            task_cfg["altitude_block_max_m"] = max(float(task_cfg["altitude_block_min_m"]), target_alt + alt_halfspan)
        else:
            lo_offset = max(0.0, base_target_alt - base_alt_lo)
            hi_offset = max(0.0, base_alt_hi - base_target_alt)
            task_cfg["altitude_block_min_m"] = max(0.0, target_alt - lo_offset)
            task_cfg["altitude_block_max_m"] = max(float(task_cfg["altitude_block_min_m"]), target_alt + hi_offset)

        target_speed = _f(task_cfg.get("target_speed_mps", base_target_speed), base_target_speed)
        speed_halfspan = _sample_uniform("speed_block_halfspan_range_mps")
        if speed_halfspan is not None:
            speed_halfspan = max(0.0, float(speed_halfspan))
            task_cfg["speed_min_mps"] = max(0.0, target_speed - speed_halfspan)
            task_cfg["speed_max_mps"] = max(float(task_cfg["speed_min_mps"]), target_speed + speed_halfspan)
        else:
            lo_offset = max(0.0, base_target_speed - base_spd_lo)
            hi_offset = max(0.0, base_spd_hi - base_target_speed)
            task_cfg["speed_min_mps"] = max(0.0, target_speed - lo_offset)
            task_cfg["speed_max_mps"] = max(float(task_cfg["speed_min_mps"]), target_speed + hi_offset)

        task_cfg["target_altitude_m"] = float(task_cfg.get("target_altitude_m", target_alt))
        task_cfg["target_speed_mps"] = float(task_cfg.get("target_speed_mps", target_speed))
        task_cfg["anchor_z_m"] = float(task_cfg.get("anchor_z_m", task_cfg["target_altitude_m"]))
        task_cfg["station_heading_deg"] = float(task_cfg.get("station_heading_deg", 0.0)) % 360.0

    @staticmethod
    def _rotate_xy_clockwise(x, y, origin_x, origin_y, yaw_deg):
        """Rotate (x,y) around (origin_x, origin_y) by yaw_deg clockwise (NAV convention)."""
        rad = -math.radians(float(yaw_deg))
        c = math.cos(rad)
        s = math.sin(rad)
        dx = float(x) - float(origin_x)
        dy = float(y) - float(origin_y)
        rx = float(origin_x) + c * dx - s * dy
        ry = float(origin_y) + s * dx + c * dy
        return rx, ry

    def _apply_world_yaw(self, yaw_deg, origin_x=0.0, origin_y=0.0):
        """Apply a deterministic world-yaw rotation to zones and entities."""
        # Zones
        env = self.scenario_data.get("environment", {})
        zones = env.get("zones", [])
        if isinstance(zones, list):
            for z in zones:
                if not isinstance(z, dict):
                    continue
                if "x" in z and "y" in z:
                    zx, zy = self._rotate_xy_clockwise(z.get("x", 0.0), z.get("y", 0.0), origin_x, origin_y, yaw_deg)
                    z["x"] = zx
                    z["y"] = zy
                if "heading" in z:
                    try:
                        z["heading"] = (float(z.get("heading", 0.0)) + float(yaw_deg)) % 360.0
                    except Exception:
                        pass

        # Entities
        ents = self.scenario_data.get("entities", [])
        if isinstance(ents, list):
            for ent in ents:
                if not isinstance(ent, dict):
                    continue
                pos = ent.get("pos", None)
                vel = ent.get("vel", None)
                if isinstance(pos, list) and len(pos) >= 2:
                    px, py = self._rotate_xy_clockwise(pos[0], pos[1], origin_x, origin_y, yaw_deg)
                    pos[0] = px
                    pos[1] = py
                if isinstance(vel, list) and len(vel) >= 2:
                    vx, vy = self._rotate_xy_clockwise(vel[0], vel[1], 0.0, 0.0, yaw_deg)
                    vel[0] = vx
                    vel[1] = vy
                if "heading" in ent:
                    try:
                        ent["heading"] = (float(ent.get("heading", 0.0)) + float(yaw_deg)) % 360.0
                    except Exception:
                        pass

        # Mission waypoints (if present): rotate together with the world so the mission remains consistent
        # under world-yaw randomization.
        mc = self.scenario_data.get("mission_command", None)
        if isinstance(mc, dict):
            wps = mc.get("waypoints", None)
            if isinstance(wps, list):
                for wp in wps:
                    if isinstance(wp, dict):
                        if "pos" in wp and isinstance(wp.get("pos"), list) and len(wp["pos"]) >= 2:
                            px, py = self._rotate_xy_clockwise(wp["pos"][0], wp["pos"][1], origin_x, origin_y, yaw_deg)
                            wp["pos"][0] = px
                            wp["pos"][1] = py
                        elif "x" in wp and "y" in wp:
                            px, py = self._rotate_xy_clockwise(wp.get("x", 0.0), wp.get("y", 0.0), origin_x, origin_y, yaw_deg)
                            wp["x"] = px
                            wp["y"] = py
                    elif isinstance(wp, list) and len(wp) >= 2:
                        px, py = self._rotate_xy_clockwise(wp[0], wp[1], origin_x, origin_y, yaw_deg)
                        wp[0] = px
                        wp[1] = py

        # Task-order geometry should rotate with the rest of the world so CAP anchors/station
        # headings remain consistent under world-yaw randomization.
        task = self.scenario_data.get("task_order", None)
        if isinstance(task, dict):
            if "anchor_x_m" in task and "anchor_y_m" in task:
                try:
                    px, py = self._rotate_xy_clockwise(
                        float(task.get("anchor_x_m", 0.0)),
                        float(task.get("anchor_y_m", 0.0)),
                        origin_x,
                        origin_y,
                        yaw_deg,
                    )
                    task["anchor_x_m"] = px
                    task["anchor_y_m"] = py
                except Exception:
                    pass
            if "station_heading_deg" in task:
                try:
                    task["station_heading_deg"] = (float(task.get("station_heading_deg", 0.0)) + float(yaw_deg)) % 360.0
                except Exception:
                    pass

    def _parse_waypoints(self) -> None:
        """
        Parse mission waypoints from scenario_data into a normalized internal list.

        Supported waypoint formats:
          - {"x":..., "y":..., "z":...}
          - {"pos":[x,y,z]}
          - [x, y, z]
        Optional per-waypoint overrides:
          - radius_m / arrival_radius_m
          - altitude_m / altitude / target_altitude / z
          - speed_mps / speed / target_speed
        """
        self.waypoints = []
        self.waypoint_idx = 0
        self._waypoint_prev_dist_m = None
        self.waypoint_total_route_length_m = 0.0

        mc = self.scenario_data.get("mission_command", None)
        if not isinstance(mc, dict):
            return
        wps = mc.get("waypoints", None)
        if not isinstance(wps, list) or not wps:
            return

        def _f(x, default: float | None = None) -> float | None:
            if x is None:
                return default
            try:
                return float(x)
            except Exception:
                return default

        default_alt = _f(mc.get("target_altitude", 0.0), 0.0) or 0.0
        default_spd = _f(mc.get("target_speed", 0.0), 0.0) or 0.0
        default_rad = _f(mc.get("waypoint_radius_m", mc.get("arrival_radius_m", 500.0)), 500.0) or 500.0
        default_mode = self._normalize_waypoint_mode(mc.get("waypoint_mode", "flyby"))

        for wp in wps:
            x = y = z = None
            rad = None
            alt = None
            spd = None
            mode = default_mode
            if isinstance(wp, dict):
                if "pos" in wp and isinstance(wp.get("pos"), list) and len(wp["pos"]) >= 2:
                    x = _f(wp["pos"][0], 0.0)
                    y = _f(wp["pos"][1], 0.0)
                    if len(wp["pos"]) >= 3:
                        z = _f(wp["pos"][2], default_alt)
                else:
                    x = _f(wp.get("x", None), 0.0)
                    y = _f(wp.get("y", None), 0.0)
                    z = _f(
                        wp.get("z", wp.get("altitude_m", wp.get("altitude", wp.get("target_altitude", None)))),
                        default_alt,
                    )
                rad = _f(wp.get("radius_m", wp.get("arrival_radius_m", None)), default_rad)
                alt = _f(wp.get("altitude_m", wp.get("altitude", wp.get("target_altitude", None))), z if z is not None else default_alt)
                spd = _f(wp.get("speed_mps", wp.get("speed", wp.get("target_speed", None))), default_spd)
                mode = self._normalize_waypoint_mode(
                    wp.get("waypoint_mode", wp.get("mode", wp.get("pass_mode", default_mode)))
                )
            elif isinstance(wp, list) and len(wp) >= 2:
                x = _f(wp[0], 0.0)
                y = _f(wp[1], 0.0)
                z = _f(wp[2], default_alt) if len(wp) >= 3 else default_alt
                rad = default_rad
                alt = z
                spd = default_spd

            if x is None or y is None:
                continue

            self.waypoints.append(
                {
                    "x": float(x),
                    "y": float(y),
                    "z": float(z if z is not None else default_alt),
                    "radius_m": float(rad if rad is not None else default_rad),
                    "altitude_m": float(alt if alt is not None else (z if z is not None else default_alt)),
                    "speed_mps": float(spd if spd is not None else default_spd),
                    "waypoint_mode": str(mode),
                }
            )
        if self.waypoints:
            px = float(getattr(self, "_waypoint_leg_origin_x", 0.0))
            py = float(getattr(self, "_waypoint_leg_origin_y", 0.0))
            total = 0.0
            for wp in self.waypoints:
                wx = float(wp.get("x", 0.0))
                wy = float(wp.get("y", 0.0))
                total += float(math.hypot(wx - px, wy - py))
                px = wx
                py = wy
            self.waypoint_total_route_length_m = float(total)

    def _normalize_waypoint_mode(self, mode_value) -> str:
        mode = str(mode_value if mode_value is not None else "flyby").strip().lower()
        if mode in ("fly-over", "fly_over", "overfly"):
            return "flyover"
        if mode in ("flyby", "flyover"):
            return mode
        return "flyby"

    def _cfg_value_for_waypoint_mode(self, cfg: dict, key: str, mode_value, default=None):
        mode = self._normalize_waypoint_mode(mode_value)
        mode_key = f"{key}_{mode}"
        if isinstance(cfg, dict) and mode_key in cfg:
            return cfg.get(mode_key)
        if isinstance(cfg, dict) and key in cfg:
            return cfg.get(key)
        return default

    def _active_waypoint_mode(self, idx: int | None = None) -> str:
        if not self.waypoints:
            return self._normalize_waypoint_mode(self.mission_cmd.get("waypoint_mode", "flyby"))
        if idx is None:
            idx = int(getattr(self, "waypoint_idx", 0))
        idx = int(np.clip(int(idx), 0, max(0, len(self.waypoints) - 1)))
        wp = self.waypoints[idx]
        return self._normalize_waypoint_mode(wp.get("waypoint_mode", self.mission_cmd.get("waypoint_mode", "flyby")))

    def _active_waypoint_arrival_products(self):
        try:
            cmd_code = int(self.mission_cmd.get("command_code", 0))
        except Exception:
            cmd_code = 0
        if cmd_code != 3 or not self.waypoints or self.agent_id is None:
            return None

        idx = int(np.clip(int(getattr(self, "waypoint_idx", 0)), 0, max(0, len(self.waypoints) - 1)))
        n = int(len(self.waypoints))
        wp = self.waypoints[idx]
        mode = self._normalize_waypoint_mode(wp.get("waypoint_mode", self.mission_cmd.get("waypoint_mode", "flyby")))

        try:
            truth = self.sim.get_agent_observation(self.agent_id)
        except Exception:
            return None
        try:
            inst = self.sim.get_instrument_state(self.agent_id)
        except Exception:
            inst = None

        ex = float(wp.get("x", 0.0))
        ey = float(wp.get("y", 0.0))
        own_x = float(getattr(truth, "x", 0.0))
        own_y = float(getattr(truth, "y", 0.0))
        dist_m = float(math.hypot(ex - own_x, ey - own_y))
        rad = max(1.0, float(wp.get("radius_m", self.mission_cmd.get("waypoint_radius_m", 500.0))))

        out = {
            "active_idx": int(idx),
            "count": int(n),
            "waypoint_mode": str(mode),
            "arrival_radius_m": float(rad),
            "sequence_gate_m": float(rad),
            "turn_lead_m": 0.0,
            "distance_to_waypoint_m": float(dist_m),
        }

        if mode != "flyby" or idx >= (n - 1):
            return out

        if idx <= 0:
            sx = float(getattr(self, "_waypoint_leg_origin_x", own_x))
            sy = float(getattr(self, "_waypoint_leg_origin_y", own_y))
        else:
            prev = self.waypoints[idx - 1]
            sx = float(prev.get("x", 0.0))
            sy = float(prev.get("y", 0.0))

        lx = ex - sx
        ly = ey - sy
        leg_len = float(math.hypot(lx, ly))
        if leg_len <= 1.0e-6:
            return out

        ux = lx / leg_len
        uy = ly / leg_len
        px = own_x - sx
        py = own_y - sy
        along = float(px * ux + py * uy)
        xtk = float(px * uy - py * ux)
        dtg = max(0.0, float(leg_len - along))

        next_wp = self.waypoints[idx + 1]
        nx = float(next_wp.get("x", 0.0)) - ex
        ny = float(next_wp.get("y", 0.0)) - ey
        if (nx * nx + ny * ny) <= 1.0e-9:
            return out

        cur_trk = float(self._bearing_to_deg(lx, ly))
        next_trk = float(self._bearing_to_deg(nx, ny))
        delta = abs(float((next_trk - cur_trk + 180.0) % 360.0 - 180.0))
        bank_lim = float(np.clip(float(self.mission_cmd.get("lnav_bank_limit_deg", 30.0)), 5.0, 70.0))
        tanb = math.tan(math.radians(bank_lim))
        lead = 0.0
        if abs(tanb) > 1.0e-6:
            speed_mps = float(getattr(truth, "speed", 0.0))
            if inst is not None:
                try:
                    ias = float(getattr(inst, "ias", speed_mps))
                    if math.isfinite(ias) and ias > 1.0:
                        speed_mps = ias
                except Exception:
                    pass
            v = max(30.0, float(speed_mps))
            r_turn = (v * v) / (9.80665 * abs(tanb))
            lead = max(0.0, float(r_turn * math.tan(math.radians(delta) * 0.5)))

        seq_gate_scale = float(self.mission_cmd.get("lnav_sequence_gate_scale", 0.35))
        seq_gate_min = float(self.mission_cmd.get("lnav_sequence_gate_min_m", rad))
        seq_gate_max = float(self.mission_cmd.get("lnav_sequence_gate_max_m", max(2.5 * rad, rad + 1500.0)))
        seq_gate_m = max(seq_gate_min, min(seq_gate_max, rad + seq_gate_scale * max(0.0, lead)))

        out["sequence_gate_m"] = float(seq_gate_m)
        out["turn_lead_m"] = float(lead)
        out["cross_track_m"] = float(xtk)
        out["distance_to_turn_m"] = float(dtg)
        return out

    def get_waypoint_visualization_products(self):
        if not self.waypoints:
            return None
        active = self._active_waypoint_arrival_products()
        active_idx = int(active["active_idx"]) if isinstance(active, dict) and "active_idx" in active else int(
            np.clip(int(getattr(self, "waypoint_idx", 0)), 0, max(0, len(self.waypoints) - 1))
        )
        markers = []
        for i, wp in enumerate(self.waypoints):
            mode = self._normalize_waypoint_mode(wp.get("waypoint_mode", self.mission_cmd.get("waypoint_mode", "flyby")))
            entry = {
                "name": f"WP_{i+1}",
                "x": float(wp.get("x", 0.0)),
                "y": float(wp.get("y", 0.0)),
                "z": float(wp.get("z", self.mission_cmd.get("target_altitude", 0.0))),
                "waypoint_mode": str(mode),
                "arrival_radius_m": float(wp.get("radius_m", self.mission_cmd.get("waypoint_radius_m", 500.0))),
                "is_active": bool(i == active_idx),
            }
            if i == active_idx and isinstance(active, dict):
                entry["sequence_gate_m"] = float(active.get("sequence_gate_m", entry["arrival_radius_m"]))
                entry["turn_lead_m"] = float(active.get("turn_lead_m", 0.0))
                entry["distance_to_waypoint_m"] = float(active.get("distance_to_waypoint_m", 0.0))
            markers.append(entry)
        return {
            "markers": markers,
            "active_idx": int(active_idx),
            "active": active,
        }

    @staticmethod
    def _bearing_to_deg(dx: float, dy: float) -> float:
        # Heading convention: 0=North, +CW. Vector mapping used in viz: x=sin(hdg), y=cos(hdg).
        return float((math.degrees(math.atan2(float(dx), float(dy))) + 360.0) % 360.0)

    @staticmethod
    def _wrap_angle_deg(angle_deg: float) -> float:
        return float((float(angle_deg) + 180.0) % 360.0 - 180.0)

    def _command_tracking_error_deg(self, inst, truth_heading_deg: float) -> float:
        """
        Returns the absolute command-tracking error in degrees.

        - Default tasks track aircraft heading.
        - Waypoint/LNAV tasks (`command_code == 3`) track *ground track* because
          `mission_cmd["target_heading"]` is used as a track bug in update_behaviors().
        """
        try:
            tgt = float(self.mission_cmd.get("target_heading", 0.0))
        except Exception:
            tgt = 0.0

        try:
            cmd_code = int(self.mission_cmd.get("command_code", 0))
        except Exception:
            cmd_code = 0

        ref = float(truth_heading_deg)
        if cmd_code == 3:
            try:
                ground_track = float(inst[30])
                if math.isfinite(ground_track):
                    ref = ground_track
            except Exception:
                pass
        return abs(self._wrap_angle_deg(tgt - ref))

    @staticmethod
    def _ground_track_from_inst(inst, fallback_heading_deg: float) -> float:
        ref = float(fallback_heading_deg)
        try:
            ground_track = float(inst[30])
            if math.isfinite(ground_track):
                ref = ground_track
        except Exception:
            pass
        return ref

    def _turn_lead_distance_m(self, turn_angle_deg: float, speed_mps: float, bank_limit_deg: float) -> float:
        turn_abs_deg = abs(float(turn_angle_deg))
        if turn_abs_deg <= 1.0e-6:
            return 0.0
        bank_lim = float(np.clip(bank_limit_deg, 5.0, 70.0))
        tanb = math.tan(math.radians(bank_lim))
        if abs(tanb) <= 1.0e-6:
            return 0.0
        v = max(30.0, float(speed_mps))
        r_turn = (v * v) / (9.80665 * abs(tanb))
        turn_half_rad = 0.5 * min(math.pi - 1.0e-3, math.radians(turn_abs_deg))
        return max(0.0, float(r_turn * math.tan(turn_half_rad)))

    def _active_waypoint_turn_relief_activation(self, cfg: dict, truth=None, inst=None) -> float:
        mode = self._active_waypoint_mode()
        max_relief = float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_max", mode, 0.0))
        heading_relief = float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_turn_heading_relief_max", mode, max_relief))
        if max(max_relief, heading_relief) <= 1.0e-6:
            return 0.0
        if not self.waypoints or self.agent_id is None:
            return 0.0
        try:
            cmd_code = int(self.mission_cmd.get("command_code", 0))
        except Exception:
            cmd_code = 0
        if cmd_code != 3:
            return 0.0

        idx = int(getattr(self, "waypoint_idx", 0))
        n = int(len(self.waypoints))
        if idx < 0 or idx >= n:
            return 0.0

        if truth is None:
            try:
                truth = self.sim.get_agent_observation(self.agent_id)
            except Exception:
                return 0.0
        if inst is None:
            try:
                inst = self.sim.get_instrument_state(self.agent_id)
            except Exception:
                inst = None

        if idx <= 0:
            sx = float(getattr(self, "_waypoint_leg_origin_x", getattr(truth, "x", 0.0)))
            sy = float(getattr(self, "_waypoint_leg_origin_y", getattr(truth, "y", 0.0)))
        else:
            prev = self.waypoints[idx - 1]
            sx = float(prev.get("x", 0.0))
            sy = float(prev.get("y", 0.0))
        wp = self.waypoints[idx]
        ex = float(wp.get("x", 0.0))
        ey = float(wp.get("y", 0.0))
        lx = ex - sx
        ly = ey - sy
        leg_len = float(math.hypot(lx, ly))
        if leg_len <= 1.0e-6:
            return 0.0

        own_x = float(getattr(truth, "x", 0.0))
        own_y = float(getattr(truth, "y", 0.0))
        ux = lx / leg_len
        uy = ly / leg_len
        px = own_x - sx
        py = own_y - sy
        along = float(px * ux + py * uy)
        dtg = max(0.0, float(leg_len - along))

        speed_mps = float(getattr(truth, "speed", 0.0))
        if inst is not None:
            try:
                ias = float(getattr(inst, "ias", speed_mps))
                if math.isfinite(ias) and ias > 1.0:
                    speed_mps = ias
            except Exception:
                pass
        speed_mps = max(80.0, float(speed_mps))
        bank_limit_deg = float(self.mission_cmd.get("lnav_bank_limit_deg", 30.0))

        base_window_m = max(1.0, float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_window_m", mode, 3000.0)))
        min_turn_deg = max(0.0, float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_min_turn_deg", mode, 15.0)))
        angle_ref_deg = max(
            min_turn_deg + 1.0,
            float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_angle_ref_deg", mode, 90.0)),
        )
        power = float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_power", mode, 1.0))
        if power < 1.0:
            power = 1.0
        if power > 8.0:
            power = 8.0

        def _turn_strength(turn_abs_deg: float, distance_from_turn_m: float) -> float:
            if turn_abs_deg <= min_turn_deg:
                return 0.0
            angle_x = (turn_abs_deg - min_turn_deg) / max(1.0e-6, angle_ref_deg - min_turn_deg)
            angle_x = float(np.clip(angle_x, 0.0, 1.0))
            prox_x = 1.0 - float(distance_from_turn_m) / base_window_m
            prox_x = float(np.clip(prox_x, 0.0, 1.0))
            return float((angle_x**power) * prox_x)

        relief = 0.0

        if idx < n - 1:
            next_wp = self.waypoints[idx + 1]
            next_dx = float(next_wp.get("x", 0.0)) - ex
            next_dy = float(next_wp.get("y", 0.0)) - ey
            if (next_dx * next_dx + next_dy * next_dy) > 1.0e-9:
                cur_trk = float(self._bearing_to_deg(lx, ly))
                next_trk = float(self._bearing_to_deg(next_dx, next_dy))
                next_turn_abs = abs(float(self._wrap_angle_deg(next_trk - cur_trk)))
                lead_m = self._turn_lead_distance_m(next_turn_abs, speed_mps, bank_limit_deg)
                dist_to_turn_start_m = max(0.0, float(dtg - lead_m))
                relief = max(relief, _turn_strength(next_turn_abs, dist_to_turn_start_m))

        if idx > 0:
            if idx == 1:
                psx = float(getattr(self, "_waypoint_leg_origin_x", sx))
                psy = float(getattr(self, "_waypoint_leg_origin_y", sy))
            else:
                prevprev = self.waypoints[idx - 2]
                psx = float(prevprev.get("x", 0.0))
                psy = float(prevprev.get("y", 0.0))
            prev_lx = sx - psx
            prev_ly = sy - psy
            if (prev_lx * prev_lx + prev_ly * prev_ly) > 1.0e-9:
                prev_trk = float(self._bearing_to_deg(prev_lx, prev_ly))
                cur_trk = float(self._bearing_to_deg(lx, ly))
                prev_turn_abs = abs(float(self._wrap_angle_deg(cur_trk - prev_trk)))
                relief = max(relief, _turn_strength(prev_turn_abs, max(0.0, along)))

        return float(np.clip(relief, 0.0, 1.0))

    def _compute_waypoint_guidance_state(self, truth=None, inst=None):
        try:
            cmd_code = int(self.mission_cmd.get("command_code", 0))
        except Exception:
            cmd_code = 0
        if cmd_code != 3 or not self.waypoints or self.agent_id is None:
            return None

        idx = int(np.clip(int(getattr(self, "waypoint_idx", 0)), 0, max(0, len(self.waypoints) - 1)))
        n = int(len(self.waypoints))
        wp = self.waypoints[idx]
        waypoint_mode = self._normalize_waypoint_mode(wp.get("waypoint_mode", self.mission_cmd.get("waypoint_mode", "flyby")))

        if truth is None:
            try:
                truth = self.sim.get_agent_observation(self.agent_id)
            except Exception:
                return None
        if inst is None:
            try:
                inst = self.sim.get_instrument_state(self.agent_id)
            except Exception:
                inst = None

        own_x = float(getattr(truth, "x", 0.0))
        own_y = float(getattr(truth, "y", 0.0))
        if idx <= 0:
            sx = float(getattr(self, "_waypoint_leg_origin_x", own_x))
            sy = float(getattr(self, "_waypoint_leg_origin_y", own_y))
        else:
            prev = self.waypoints[idx - 1]
            sx = float(prev.get("x", 0.0))
            sy = float(prev.get("y", 0.0))

        ex = float(wp.get("x", 0.0))
        ey = float(wp.get("y", 0.0))
        lx = ex - sx
        ly = ey - sy
        leg_len = float(math.hypot(lx, ly))

        dx = ex - own_x
        dy = ey - own_y
        dist_m = float(math.hypot(dx, dy))
        direct_to_track_deg = float(self._bearing_to_deg(dx, dy))

        desired_track_deg = direct_to_track_deg
        xtk_m = 0.0
        along_m = 0.0
        dtg_m = dist_m
        if leg_len > 1.0e-6:
            desired_track_deg = float(self._bearing_to_deg(lx, ly))
            ux = lx / leg_len
            uy = ly / leg_len
            rx = uy
            ry = -ux
            px = own_x - sx
            py = own_y - sy
            xtk_m = float(px * rx + py * ry)
            along_m = float(px * ux + py * uy)
            dtg_m = max(0.0, float(leg_len - along_m))

        lookahead_m = float(self.mission_cmd.get("lnav_lookahead_m", 1500.0))
        spd = float(getattr(inst, "ias", 0.0)) if inst is not None else 0.0
        if math.isfinite(spd) and spd > 1.0:
            lookahead_m = max(500.0, min(5000.0, float(spd) * 8.0))
        lookahead_m = max(200.0, float(lookahead_m))

        max_int = float(self.mission_cmd.get("lnav_max_intercept_deg", 25.0))
        capture_max_int = float(self.mission_cmd.get("lnav_capture_max_intercept_deg", max(max_int, 45.0)))
        capture_max_int = max(max_int, capture_max_int)
        waypoint_radius_m = max(1.0, float(wp.get("radius_m", self.mission_cmd.get("waypoint_radius_m", 1000.0))))
        capture_xtrack_m = float(
            self.mission_cmd.get(
                "lnav_capture_xtrack_m",
                max(2.0 * waypoint_radius_m, min(8000.0, 0.35 * max(1.0, leg_len))),
            )
        )
        capture_xtrack_m = max(waypoint_radius_m, capture_xtrack_m)
        capture_course_err_deg = float(self.mission_cmd.get("lnav_capture_course_error_deg", 45.0))
        direct_to_final_fix = bool(self.mission_cmd.get("lnav_direct_to_final_fix", True))
        flyover_capture_window_m = float(
            self.mission_cmd.get(
                "lnav_flyover_capture_window_m",
                max(2.0 * waypoint_radius_m, min(5000.0, 0.30 * max(1.0, leg_len))),
            )
        )
        flyover_capture_window_m = max(waypoint_radius_m, flyover_capture_window_m)
        before_leg = along_m < -0.25 * lookahead_m
        far_off_course = abs(xtk_m) > capture_xtrack_m
        large_to_from_angle = abs(self._wrap_angle_deg(direct_to_track_deg - desired_track_deg)) > capture_course_err_deg
        final_leg = idx >= (n - 1)
        passed_fix = along_m >= leg_len
        near_flyover_terminal = (
            waypoint_mode == "flyover"
            and (
                dist_m <= flyover_capture_window_m
                or along_m >= max(0.0, leg_len - flyover_capture_window_m)
            )
        )
        # Fly-by legs normally follow leg-track guidance with turn anticipation. But if we have already passed
        # the fix without sequencing, continuing to track the leg extension can send the aircraft farther away
        # from the missed waypoint instead of recovering back to it. Fall back to direct-to-fix recovery in that
        # case so the bridge task can rejoin the route and continue toward the landing transition.
        missed_flyby_recovery = bool(waypoint_mode == "flyby" and passed_fix)
        use_direct_to = bool(
            (final_leg and direct_to_final_fix)
            or before_leg
            or (far_off_course and large_to_from_angle)
            or near_flyover_terminal
            or (waypoint_mode == "flyover" and passed_fix)
            or missed_flyby_recovery
        )
        direct_to_fix_guidance = bool(
            use_direct_to and ((final_leg and direct_to_final_fix) or waypoint_mode == "flyover" or missed_flyby_recovery)
        )

        cmd_track_deg = desired_track_deg
        if use_direct_to:
            if direct_to_fix_guidance:
                cmd_track_deg = direct_to_track_deg
            else:
                capture_delta_deg = float(self._wrap_angle_deg(direct_to_track_deg - desired_track_deg))
                capture_delta_deg = float(np.clip(capture_delta_deg, -capture_max_int, capture_max_int))
                cmd_track_deg = float((desired_track_deg + capture_delta_deg + 360.0) % 360.0)
        else:
            intercept_rad = math.atan2(-xtk_m, lookahead_m)
            intercept_deg = float(math.degrees(intercept_rad))
            if max_int > 0.0:
                intercept_deg = float(np.clip(intercept_deg, -max_int, max_int))
            cmd_track_deg = float((desired_track_deg + intercept_deg + 360.0) % 360.0)

        reward_desired_track_deg = float(direct_to_track_deg if direct_to_fix_guidance else desired_track_deg)
        reward_xtk_m = float(0.0 if direct_to_fix_guidance else xtk_m)
        reward_dtg_m = float(dist_m if direct_to_fix_guidance else dtg_m)

        return {
            "idx": int(idx),
            "count": int(n),
            "wp": wp,
            "waypoint_mode": str(waypoint_mode),
            "sx": float(sx),
            "sy": float(sy),
            "lx": float(lx),
            "ly": float(ly),
            "dist_m": float(dist_m),
            "direct_to_track_deg": float(direct_to_track_deg),
            "desired_track_deg": float(desired_track_deg),
            "reward_desired_track_deg": float(reward_desired_track_deg),
            "xtk_m": float(xtk_m),
            "reward_xtk_m": float(reward_xtk_m),
            "along_m": float(along_m),
            "dtg_m": float(dtg_m),
            "reward_dtg_m": float(reward_dtg_m),
            "leg_len_m": float(leg_len),
            "ex": float(ex),
            "ey": float(ey),
            "waypoint_radius_m": float(waypoint_radius_m),
            "cmd_track_deg": float(cmd_track_deg),
            "use_direct_to": bool(use_direct_to),
            "direct_to_fix_guidance": bool(direct_to_fix_guidance),
        }

    def _process_imports(self, imports):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(base_dir, ".."))
        
        for imp in imports:
            path = imp.get("file")
            if not path: continue
            
            full_path = os.path.join(project_root, path)
            if not os.path.exists(full_path):
                print(f"Warning: Import file not found: {full_path}")
                continue
                
            with open(full_path, 'r') as f:
                prefab = json.load(f)
                
            # Merge Zones
            if "zones" in prefab:
                # Ensure environment dict exists
                if "environment" not in self.scenario_data:
                    self.scenario_data["environment"] = {}
                current_zones = self.scenario_data["environment"].get("zones", [])
                current_zones.extend(prefab["zones"])
                self.scenario_data["environment"]["zones"] = current_zones
                if os.environ.get("CMO_DEBUG_ZONES"):
                    print(f"[DEBUG] Merged {len(prefab['zones'])} zones from prefab")
                
            # Merge Entities
            if "entities" in prefab:
                current_ents = self.scenario_data.get("entities", [])
                current_ents.extend(prefab["entities"])
                self.scenario_data["entities"] = current_ents

    def get_max_steps(self):
        meta = self.scenario_data.get("meta", {})
        if "max_steps" in meta:
            return int(meta["max_steps"])
        env = self.scenario_data.get("environment", {})
        if "max_steps" in env:
            return int(env["max_steps"])
        return 2000

    def get_rewards_config(self):
        return self.scenario_data.get("rewards", {})

    def get_objectives(self):
        return self.scenario_data.get("objectives", [])

    def _sync_kernel_mission_command(self) -> None:
        if self.agent_id is None:
            return
        if not hasattr(self.sim, "set_mission_command") or not hasattr(ef_py, "MissionCommand"):
            return
        try:
            cmd = build_kernel_mission_command(self)
            self.sim.set_mission_command(self.agent_id, cmd)
        except Exception:
            pass

    def _sync_kernel_command_chain(self) -> None:
        if self.agent_id is None:
            return
        try:
            self._leader_phase_manager.sync_to_kernel(self)
        except Exception:
            pass

    def _reset_command_chain(self) -> None:
        if self.agent_id is None:
            return
        try:
            sim_time_s = float(self.steps) * float(self.sim.get_time_step())
        except Exception:
            sim_time_s = 0.0
        self._leader_phase_manager.reset(self, sim_time_s=sim_time_s)
        self._sync_kernel_command_chain()

    def _update_command_chain(self, sim_time: float) -> None:
        if self.agent_id is None:
            return
        self._leader_phase_manager.update(self, sim_time_s=float(sim_time))
        self._sync_kernel_mission_command()
        self._sync_kernel_command_chain()

    def _activate_post_waypoint_transition(self) -> dict | None:
        if not isinstance(self.post_waypoint_transition, dict) or not self.post_waypoint_transition:
            return None

        next_cmd = copy.deepcopy(self.post_waypoint_transition)
        if not isinstance(next_cmd, dict):
            return None

        target_heading = float(next_cmd.get("target_heading", self.mission_cmd.get("target_heading", 0.0)))
        if self.rotate_mission_heading_with_world and abs(float(self.world_yaw_deg)) > 1.0e-6:
            target_heading = (target_heading + float(self.world_yaw_deg)) % 360.0

        self.mission_cmd = {
            "command_code": int(next_cmd.get("command_code", 4)),
            "target_heading": float(target_heading),
            "target_altitude": float(next_cmd.get("target_altitude", self.mission_cmd.get("target_altitude", 0.0))),
            "target_speed": float(next_cmd.get("target_speed", self.mission_cmd.get("target_speed", 0.0))),
        }

        for key, value in next_cmd.items():
            if key in ("command_code", "target_heading", "target_altitude", "target_speed", "transition_reward"):
                continue
            self.mission_cmd[key] = value

        self.mission_cmd = self._normalize_mission_command_dict(self.mission_cmd)

        self.post_waypoint_transition = None
        self.mission_phase_name = str(next_cmd.get("phase_name", next_cmd.get("landing_mode", "post_waypoint"))).strip() or "post_waypoint"
        self.waypoints = []
        self.waypoint_idx = 0
        self._waypoint_prev_dist_m = None
        self.waypoint_total_route_length_m = 0.0
        self._approach_prev_dme_m = None
        self._approach_prev_loc_abs = None
        self._approach_prev_gs_abs = None
        self._sync_kernel_mission_command()
        return next_cmd

    def get_entity_id(self, name):
        return self.entities.get(name)
        
    def get_mission_observation(self, mode: str = "basic"):
        """
        Mission/command observation for the pilot policy.

        Modes:
          - basic: [command_code, target_heading, target_altitude, target_speed]
          - nav_v1: basic + waypoint-nav avionics style cues
                    [active_wp_idx, total_wps, dist_to_wp_m, cross_track_m,
                     along_track_remaining_m, direct_bearing_deg, desired_leg_track_deg]
          - nav_v2: basic + realistic EGI/HSD style route products
                    [selected_steerpoint, steerpoint_mode_code, steerpoint_range_m,
                     steerpoint_bearing_rel_deg, steerpoint_alt_delta_m, cdi_norm,
                     track_angle_error_deg, leg_distance_remaining_m, next_turn_deg,
                     distance_to_turn_m]
                    where steerpoint_mode_code is 0.0 for fly-by and 1.0 for fly-over.
        """
        base = np.array(
            [
                float(self.mission_cmd["command_code"]),
                float(self.mission_cmd["target_heading"]),
                float(self.mission_cmd["target_altitude"]),
                float(self.mission_cmd["target_speed"]),
            ],
            dtype=np.float32,
        )
        mode_norm = str(mode).strip().lower()
        if mode_norm in ("", "basic"):
            return base
        if mode_norm not in ("nav_v1", "nav_v2"):
            raise ValueError(f"Unknown mission observation mode: {mode}")

        products = self._get_waypoint_nav_products()
        if products is None:
            return np.concatenate([base, np.zeros((7 if mode_norm == "nav_v1" else 10,), dtype=np.float32)], axis=0)

        if mode_norm == "nav_v1":
            nav = np.array(
                [
                    float(products["active_wp_idx"]),
                    float(products["total_wps"]),
                    float(products["dist_m"]),
                    float(products["xtk_m"]),
                    float(products["dtg_m"]),
                    float(products["direct_bearing_deg"]),
                    float(products["desired_leg_track_deg"]),
                ],
                dtype=np.float32,
            )
            return np.concatenate([base, nav], axis=0)

        nav2 = np.array(
            [
                float(products["selected_steerpoint"]),
                float(products["steerpoint_mode_code"]),
                float(products["dist_m"]),
                float(products["bearing_rel_deg"]),
                float(products["altitude_delta_m"]),
                float(products["cdi_norm"]),
                float(products["track_angle_error_deg"]),
                float(products["dtg_m"]),
                float(products["next_turn_deg"]),
                float(products["distance_to_turn_m"]),
            ],
            dtype=np.float32,
        )
        return np.concatenate([base, nav2], axis=0)

    def _get_waypoint_nav_products(self):
        try:
            truth = self.sim.get_agent_observation(self.agent_id)
        except Exception:
            return None
        try:
            inst = self.sim.get_instrument_state(self.agent_id)
        except Exception:
            inst = None
        gstate = self._compute_waypoint_guidance_state(truth=truth, inst=inst)
        if gstate is None:
            return None

        idx = int(gstate["idx"])
        n = int(gstate["count"])
        wp = gstate["wp"]
        waypoint_mode = str(gstate["waypoint_mode"])

        own_z = float(getattr(truth, "z", 0.0))
        own_heading_deg = float(getattr(truth, "heading", 0.0))
        ground_track_deg = own_heading_deg
        true_airspeed_mps = float(getattr(truth, "speed", 0.0))
        if inst is not None:
            try:
                hdg = float(getattr(inst, "heading", own_heading_deg))
                if math.isfinite(hdg):
                    own_heading_deg = hdg
            except Exception:
                pass
            try:
                trk = float(getattr(inst, "ground_track", own_heading_deg))
                if math.isfinite(trk):
                    ground_track_deg = trk
            except Exception:
                pass
            try:
                ias = float(getattr(inst, "ias", true_airspeed_mps))
                if math.isfinite(ias) and ias > 1.0:
                    true_airspeed_mps = ias
            except Exception:
                pass
        if abs(self._wrap_angle_deg(ground_track_deg - own_heading_deg)) > 85.0 and true_airspeed_mps > 80.0:
            ground_track_deg = own_heading_deg

        dist_m = float(gstate["dist_m"])
        direct_bearing_deg = float(gstate["direct_to_track_deg"])
        bearing_rel_deg = float(self._wrap_angle_deg(direct_bearing_deg - own_heading_deg))
        altitude_delta_m = float(wp.get("altitude_m", wp.get("z", 0.0)) - own_z)

        desired_leg_track_deg = float(gstate["reward_desired_track_deg"])
        xtk_m = float(gstate["reward_xtk_m"])
        dtg_m = float(gstate["reward_dtg_m"])

        cdi_full_scale_m = 1500.0
        try:
            cdi_full_scale_m = float(
                self.mission_cmd.get(
                    "nav_course_dev_full_scale_m",
                    self.mission_cmd.get("course_dev_full_scale_m", max(1000.0, float(self.mission_cmd.get("waypoint_radius_m", 1000.0)))),
                )
            )
        except Exception:
            cdi_full_scale_m = 1500.0
        cdi_norm = float(np.clip(xtk_m / max(1.0, cdi_full_scale_m), -1.0, 1.0))
        track_angle_error_deg = float(self._wrap_angle_deg(desired_leg_track_deg - ground_track_deg))

        next_turn_deg = 0.0
        distance_to_turn_m = float(dtg_m)
        if bool(gstate.get("direct_to_fix_guidance", False)):
            next_turn_deg = 0.0
            distance_to_turn_m = float(dist_m)
        elif idx < n - 1:
            nxt = self.waypoints[idx + 1]
            ex = float(gstate["ex"])
            ey = float(gstate["ey"])
            next_leg_track_deg = float(self._bearing_to_deg(float(nxt.get("x", 0.0)) - ex, float(nxt.get("y", 0.0)) - ey))
            next_turn_deg = float(self._wrap_angle_deg(next_leg_track_deg - desired_leg_track_deg))
            bank_limit_deg = float(self.mission_cmd.get("lnav_bank_limit_deg", 30.0))
            bank_rad = math.radians(max(1.0, min(80.0, bank_limit_deg)))
            turn_rad = abs(math.radians(next_turn_deg))
            lead_turn_m = 0.0
            if turn_rad > 1.0e-6 and bank_rad > 1.0e-6:
                g = 9.80665
                turn_radius = (max(80.0, true_airspeed_mps) ** 2) / max(1.0e-6, g * math.tan(bank_rad))
                lead_turn_m = float(turn_radius * math.tan(0.5 * min(math.pi - 1.0e-3, turn_rad)))
            distance_to_turn_m = max(0.0, float(dtg_m - lead_turn_m))

        return {
            "active_wp_idx": float(idx),
            "total_wps": float(n),
            "selected_steerpoint": float(idx + 1),
            "steerpoint_mode_code": 1.0 if waypoint_mode == "flyover" else 0.0,
            "dist_m": float(dist_m),
            "xtk_m": float(xtk_m),
            "dtg_m": float(dtg_m),
            "direct_bearing_deg": float(direct_bearing_deg),
            "desired_leg_track_deg": float(desired_leg_track_deg),
            "bearing_rel_deg": float(bearing_rel_deg),
            "altitude_delta_m": float(altitude_delta_m),
            "cdi_norm": float(cdi_norm),
            "track_angle_error_deg": float(track_angle_error_deg),
            "next_turn_deg": float(next_turn_deg),
            "distance_to_turn_m": float(distance_to_turn_m),
        }

    def update_behaviors(self, sim_time):
        # Waypoint navigation: update commanded lateral steering for the active waypoint leg.
        #
        # Realism-first: in real aircraft, the EGI/FMS provides LNAV-style guidance:
        #   - a desired track (DTK) for the active leg (prev_wp -> next_wp)
        #   - an intercept/capture command when off-track (XTK)
        #
        # We model this by commanding a *ground-referenced* track bug (stored in mission_cmd["target_heading"])
        # that includes a small intercept angle based on cross-track error. This uses only mission data
        # (the flight plan waypoints) and own-ship navigation state, without exposing privileged world geometry
        # to the agent beyond what real avionics would present.
        if self.agent_id is None:
            return
        try:
            cmd_code = int(self.mission_cmd.get("command_code", 0))
        except Exception:
            cmd_code = 0
        if self.waypoints and cmd_code == 3:
            idx = int(getattr(self, "waypoint_idx", 0))
            if idx < 0:
                idx = 0
            if idx < len(self.waypoints):
                try:
                    truth = self.sim.get_agent_observation(self.agent_id)
                except Exception:
                    truth = None
                try:
                    inst = self.sim.get_instrument_state(self.agent_id)
                except Exception:
                    inst = None
                if truth is not None:
                    gstate = self._compute_waypoint_guidance_state(truth=truth, inst=inst)
                    if gstate is not None:
                        wp = gstate["wp"]
                        self.mission_cmd["target_heading"] = float(gstate["cmd_track_deg"])

                        # Optional per-waypoint cruise constraints.
                        try:
                            self.mission_cmd["target_altitude"] = float(wp.get("altitude_m", self.mission_cmd.get("target_altitude", 0.0)))
                        except Exception:
                            pass
                        try:
                            self.mission_cmd["target_speed"] = float(wp.get("speed_mps", self.mission_cmd.get("target_speed", 0.0)))
                        except Exception:
                            pass

                        # Keep simulation kernel mission command in sync so InstrumentState.cmd_* matches.
                        self._sync_kernel_mission_command()

        self._update_command_chain(sim_time)

    def compute_full_step(self, obs, sim, steps, max_steps):
        rules = self.scenario_data.get("objectives", [])
        cfg = self.scenario_data.get("rewards", {})
        term_reason = "running"
        
        # Get Truth State for Scoring
        truth = sim.get_agent_observation(self.agent_id)
        
        # Extract Physical Props from Instruments for Safety Checks.
        # Obs layout:
        # [ias(0), mach, alt_baro(2), alt_radar(3), vvi(4), aoa(5), beta(6),
        #  pitch(7), roll(8), heading(9), g_load(10), ..., gear(18), ...,
        #  vn(26), ve(27), vd(28), ground_speed(29), ground_track(30), ...]
        inst = obs["instruments"]
        curr_aoa = inst[5]
        curr_roll = inst[8]
        curr_g = inst[10]
        curr_gear = inst[18]
        curr_ias = float(inst[0])
        if len(inst) > 29:
            curr_ground_speed = float(inst[29])
        else:
            curr_ground_speed = math.hypot(float(getattr(truth, "vx", 0.0)), float(getattr(truth, "vy", 0.0)))
        curr_alt_agl = float(inst[3]) if len(inst) > 3 else float(getattr(truth, "z", 0.0))

        def _finite(x) -> bool:
            try:
                return math.isfinite(float(x))
            except Exception:
                return False

        # Hard guard: if physics produces NaN/Inf, terminate immediately to avoid poisoning training.
        truncated = (steps >= max_steps)
        if not all(
            _finite(v)
            for v in (
                getattr(truth, "x", 0.0),
                getattr(truth, "y", 0.0),
                getattr(truth, "z", 0.0),
                getattr(truth, "vx", 0.0),
                getattr(truth, "vy", 0.0),
                getattr(truth, "vz", 0.0),
                getattr(truth, "speed", 0.0),
                getattr(truth, "pitch", 0.0),
                getattr(truth, "roll", 0.0),
                getattr(truth, "heading", 0.0),
                getattr(truth, "health", 100.0),
                curr_ias,
                float(inst[2]),  # alt_baro
                float(inst[3]),  # alt_radar
                curr_aoa,
                curr_roll,
                curr_g,
            )
        ):
            status = [0.0] * 4
            status[3] = -1.0
            crash_pen = float(cfg.get("crash_penalty", -1000.0))
            self.last_reward_breakdown = {
                "crash_penalty": crash_pen,
                "nan_guard": 1.0,
                "total": crash_pen,
                "untracked": 0.0,
            }
            self.last_termination_reason = "nan_guard"
            return crash_pen, True, truncated, status

        # Use InstrumentState directly for gear damage / surface checks.
        # Note: stall/attitude envelope checks should not apply while the aircraft is still on the ground,
        # where AoA can be undefined/noisy at very low speeds.
        try:
            inst_obj = sim.get_instrument_state(self.agent_id)
        except Exception:
            inst_obj = None

        if inst_obj is not None:
            gear_collapsed = bool(getattr(inst_obj, "gear_collapsed", False))
            # Note: `InstrumentState.on_runway` is a surface-type flag ("on paved surface"),
            # not a geometry-accurate runway membership test. Use it for safety/termination.
            on_paved = bool(getattr(inst_obj, "on_runway", True))
            gear_stress = float(getattr(inst_obj, "gear_stress", 0.0))
        else:
            gear_collapsed = False
            on_paved = True
            gear_stress = 0.0
        alt_agl = float(inst[3])  # radar altitude (AGL)
        on_ground_alt_threshold = float(cfg.get("on_ground_alt_threshold", 2.5))
        airborne_alt_threshold = float(cfg.get("airborne_alt_threshold", cfg.get("liftoff_alt_threshold", 5.0)))
        on_ground = alt_agl <= on_ground_alt_threshold
        airborne = alt_agl >= airborne_alt_threshold
        # "Pre-liftoff" phase used for takeoff runway safety/termination: includes ground roll + rotation until the
        # aircraft clearly departs the runway environment.
        preliftoff = not airborne
        try:
            cmd_code = int(self.mission_cmd.get("command_code", 0))
        except Exception:
            cmd_code = 0
        landing_mode = str(self.mission_cmd.get("landing_mode", "")).strip().lower()
        is_landing_task = bool(is_landing_command_code(cmd_code) or landing_mode)
        # For landing, runway-membership/off-runway logic should activate only once the aircraft is actually in
        # the touchdown / rollout phase. Reusing takeoff's `preliftoff` gate here wrongly terminates short-final
        # approaches a few meters above the runway threshold before touchdown can even occur.
        runway_surface_phase = bool(on_ground) if is_landing_task else bool(preliftoff)

        # Geometry-based runway membership (best-effort).
        # Prefer runway geometry over the surface-type flag so apron/taxiway do not count as "on runway".
        on_runway_geom = None
        runway_along_m = None
        runway_cross_m = None
        runway_from_threshold_m = None
        runway_len_m = None
        runway_wid_m = None
        try:
            valid_rf, along_m, cross_m, rw_len, rw_wid = self.get_runway_local_frame(float(truth.x), float(truth.y))
            if valid_rf and rw_len > 1.0 and rw_wid > 1.0:
                runway_along_m = float(along_m)
                runway_cross_m = float(cross_m)
                runway_len_m = float(rw_len)
                runway_wid_m = float(rw_wid)
                runway_from_threshold_m = float(along_m + 0.5 * rw_len)
                runway_width_margin_m = float(cfg.get("runway_width_margin_m", 2.0))
                runway_length_margin_m = float(cfg.get("runway_length_margin_m", 0.0))
                on_runway_geom = bool(
                    (abs(cross_m) <= 0.5 * rw_wid + runway_width_margin_m)
                    and (abs(along_m) <= 0.5 * rw_len + runway_length_margin_m)
                )
        except Exception:
            on_runway_geom = None

        # Task-level runway membership:
        # - Use geometry-based runway containment during the relevant runway-surface phase when available
        #   (distinguishes runway vs apron/taxiway)
        # - Fall back to the surface-type flag (paved vs off-pavement) when geometry cannot be computed.
        # - Always report false outside the relevant runway-surface phase.
        on_runway_task = bool(on_paved) if runway_surface_phase else False
        if on_runway_geom is not None:
            on_runway_task = bool(on_runway_geom) if runway_surface_phase else False

        # Track consecutive off-runway steps during the active runway-surface phase. This allows a short grace
        # window for recovery while still preventing runway/apron exploits.
        if runway_surface_phase and (not on_runway_task):
            self.off_runway_steps = int(getattr(self, "off_runway_steps", 0)) + 1
        else:
            self.off_runway_steps = 0
        
        reward = 0.0
        terminated = False
        status = [0.0]*4
        rb = {}

        def _add_reward_term(name: str, value: float):
            nonlocal reward
            v = float(value)
            reward += v
            rb[name] = float(rb.get(name, 0.0) + v)
        
        # 1. Base Survival & Crash
        if truth.health <= 0:
            _add_reward_term("crash_penalty", cfg.get("crash_penalty", -1000.0))
            terminated = True
            status[3] = -1.0
            term_reason = "crash_health"
        else:
            _add_reward_term("survival", cfg.get("survival", 0.01))
            
        # 2. Progress Shaping (Reward for increasing Alt/Speed towards target)
        # Only apply if not crashed
        if not terminated:
            waypoint_turn_relief_activation = 0.0
            if self.waypoints:
                waypoint_turn_relief_activation = self._active_waypoint_turn_relief_activation(cfg, truth=truth, inst=inst)

            # Altitude Progress
            tgt_alt = cfg.get("altitude_progress_target", None)
            if tgt_alt is None:
                tgt_alt = self.mission_cmd.get("target_altitude", 0.0)
            try:
                tgt_alt = float(tgt_alt)
            except Exception:
                tgt_alt = 0.0
            d_alt = truth.z - self.prev_alt
            if (tgt_alt <= 0.0 or truth.z < tgt_alt) and d_alt > 0:
                # Reward climbing only until reaching the configured target altitude.
                _add_reward_term("altitude_progress", d_alt * cfg.get("altitude_progress_weight", 0.0))
            elif truth.z < 10.0 and d_alt < -1.0: # Penalize rapid descent near ground
                 _add_reward_term("low_alt_descent_penalty", d_alt * 0.1)
                 
            # Speed Progress (Until target speed)
            tgt_spd = cfg.get("speed_progress_target", None)
            if tgt_spd is None:
                tgt_spd = self.mission_cmd.get("target_speed", 180.0)
            try:
                tgt_spd = float(tgt_spd)
            except Exception:
                tgt_spd = 0.0
            # NOTE: use IAS (inst[0]) for progress shaping, not truth ground speed.
            d_spd = curr_ias - self.prev_speed
            if (tgt_spd <= 0.0 or curr_ias < tgt_spd) and d_spd > 0:
                _add_reward_term("speed_progress", d_spd * cfg.get("speed_progress_weight", 0.0))
            elif d_spd < 0:
                _add_reward_term("speed_regress", d_spd * cfg.get("speed_progress_weight_negative", 0.0))

            # Stationary penalty (discourage policies that never initiate takeoff roll)
            stationary_penalty = cfg.get("stationary_penalty", 0.0)
            if stationary_penalty != 0.0:
                grace_steps = int(cfg.get("stationary_grace_steps", 20))
                speed_thr = float(cfg.get("stationary_speed_threshold", 5.0))
                alt_thr = float(cfg.get("stationary_alt_threshold", 5.0))
                if steps > grace_steps and truth.speed < speed_thr and truth.z < alt_thr:
                    _add_reward_term("stationary_penalty", float(stationary_penalty))

            # Takeoff shaping: reward first liftoff (wheels-off) event.
            liftoff_bonus = float(cfg.get("liftoff_bonus", 0.0))
            if liftoff_bonus != 0.0 and not self.liftoff_awarded:
                liftoff_speed_thr = float(cfg.get("liftoff_speed_threshold", 80.0))
                liftoff_alt_thr = float(cfg.get("liftoff_alt_threshold", 5.0))
                if float(inst[0]) >= liftoff_speed_thr and float(inst[3]) >= liftoff_alt_thr:
                    _add_reward_term("liftoff_bonus", liftoff_bonus)
                    self.liftoff_awarded = True

            # Takeoff shaping: encourage rotation on the runway once above Vr.
            rotation_weight = float(cfg.get("rotation_reward_weight", 0.0))
            if rotation_weight != 0.0:
                rot_spd_thr = float(cfg.get("rotation_speed_threshold", 80.0))
                rot_alt_thr = float(cfg.get("rotation_alt_threshold", 5.0))
                rot_pitch_cap = float(cfg.get("rotation_pitch_cap", 15.0))
                if float(inst[0]) >= rot_spd_thr and float(inst[3]) <= rot_alt_thr:
                    # Encourage initiating rotation by rewarding positive pitch attitude and penalizing nose-down.
                    pitch_deg = float(inst[7])
                    pitch_term = float(np.clip(pitch_deg, -rot_pitch_cap, rot_pitch_cap))
                    _add_reward_term("rotation_reward", pitch_term * rotation_weight)
                    # Discourage over-rotation on the runway (can cause loss of directional control / tail strike).
                    over_w = float(cfg.get("rotation_overpitch_penalty_weight", 0.0))
                    if over_w != 0.0 and pitch_deg > rot_pitch_cap:
                        _add_reward_term("rotation_overpitch_penalty", (pitch_deg - rot_pitch_cap) * over_w)
            
            # Gear Bonus (One-time)
            # If above 50m and gear is up (<0.1), and haven't awarded yet
            if curr_alt_agl > 50.0 and curr_gear < 0.1 and not self.gear_bonus_awarded:
                _add_reward_term("gear_up_bonus", cfg.get("gear_up_bonus", 0.0))
                self.gear_bonus_awarded = True
                
            # 3. Safety Constraints (Penalties)
            # Stall
            aoa_valid = math.isfinite(float(curr_aoa)) and (abs(float(curr_aoa)) < 89.0) and (curr_ias > 10.0)
            stall_lim = cfg.get("stall_aoa_threshold", 15.0)
            if airborne and aoa_valid and abs(curr_aoa) > stall_lim:
                stall_term = float(cfg.get("stall_penalty", -1.0) * (abs(curr_aoa) - stall_lim))
                stall_clip = float(cfg.get("stall_penalty_clip", 0.0))
                if stall_clip > 0.0 and stall_term < -stall_clip:
                    stall_term = -stall_clip
                _add_reward_term("stall_penalty", stall_term)
                
            # Overload
            g_lim = cfg.get("overload_g_threshold", 6.0)
            overload_min_alt_agl_m = float(cfg.get("overload_min_alt_agl_m", 5.0))
            if airborne and curr_alt_agl > overload_min_alt_agl_m and abs(curr_g) > g_lim:
                g_term = float(cfg.get("overload_penalty", -1.0) * (abs(curr_g) - g_lim))
                g_clip = float(cfg.get("overload_penalty_clip", 0.0))
                if g_clip > 0.0 and g_term < -g_clip:
                    g_term = -g_clip
                _add_reward_term("overload_penalty", g_term)

            # 4. Early Termination (Fail Fast)
            # Prevent "Stall Hell" where agent accumulates -2000 points over 2000 steps.
            # If flight envelope is excessively violated, kill episode.
            
            # Condition A: Deep Stall / Spin (AoA > 50 deg)
            if airborne and aoa_valid and abs(curr_aoa) > 50.0:
                _add_reward_term("failfast_penalty", float(cfg.get("failfast_penalty", -50.0)))
                terminated = True
                status[3] = -1.0 # Fail code
                term_reason = "failfast_deep_stall"
            
            # Condition B: Inverted Flight at low alt (Roll > 135 deg while < 100m)
            elif airborne and truth.z < 100.0 and abs(curr_roll) > 135.0:
                _add_reward_term("failfast_penalty", float(cfg.get("failfast_penalty", -50.0)))
                terminated = True
                status[3] = -1.0
                term_reason = "failfast_inverted_low_alt"
                 
            # Condition C: Extreme Pitch (Cobra) > 85 deg
            elif airborne and abs(truth.pitch) > 85.0:
                _add_reward_term("failfast_penalty", float(cfg.get("failfast_penalty", -50.0)))
                terminated = True
                status[3] = -1.0
                term_reason = "failfast_extreme_pitch"
            
            # Condition D: Gear Collapse (off-runway at high speed)
            # Do NOT index into obs["instruments"] for gear fields: the instrument vector is for
            # training observations and its layout changes over time (e.g. when adding EGI fields).
            # Use InstrumentState directly for gear damage/off-runway logic.
            if gear_collapsed:
                _add_reward_term("gear_collapse_penalty", cfg.get("gear_collapse_penalty", -500.0))
                terminated = True
                status[3] = -1.0
                term_reason = "gear_collapse"
            elif runway_surface_phase and (not on_runway_task):
                # Off-runway penalty (per step) during the active runway-surface phase.
                # - Takeoff: ground roll / rotation before liftoff.
                # - Landing: only after touchdown / rollout begins.
                # Prefer geometry runway membership when available so apron/taxiway do not count as "on runway".
                _add_reward_term("off_runway_penalty", cfg.get("off_runway_penalty", -1.0))
                # Also penalize proportional to gear stress accumulation
                if gear_stress > 0.1:
                    _add_reward_term("gear_stress_penalty", gear_stress * cfg.get("gear_stress_penalty", -10.0))
                # Fail-fast: leaving the runway at high speed is almost always unrecoverable for takeoff training.
                # Terminating early reduces huge negative tails (rollover) that destabilize value learning.
                off_runway_term_speed = float(cfg.get("off_runway_terminate_speed", 0.0))
                if off_runway_term_speed > 0.0 and float(truth.speed) >= off_runway_term_speed:
                    # Grace period (seconds) to avoid terminating on a single-step boundary crossing.
                    # Defaults to 0.0 for legacy behavior.
                    grace_s = float(cfg.get("off_runway_terminate_grace_s", 0.0))
                    dt = float(getattr(sim, "get_time_step", lambda: 0.05)())
                    dt = dt if dt > 1.0e-6 else 0.05
                    grace_steps = int(max(0.0, grace_s) / dt)
                    if int(getattr(self, "off_runway_steps", 0)) > grace_steps:
                        _add_reward_term("off_runway_terminate_penalty", float(cfg.get("off_runway_terminate_penalty", -200.0)))
                        terminated = True
                        status[3] = -1.0
                        term_reason = "off_runway_terminate"
                
            # Roll Stability (Penalize extreme bank angles at low altitude)
            if truth.z < 100.0:
                _add_reward_term("roll_stability", abs(curr_roll) * cfg.get("roll_stability_weight", 0.0))
                
            # 4. Command Adherence (Error Penalty)
            # Only if strictly requested (usually better to let Objectives handle final success)
            if cfg.get("heading_error_weight", 0.0) != 0.0:
                 diff = self._command_tracking_error_deg(inst, truth.heading)
                 turn_heading_relief_max = float(cfg.get("waypoint_turn_heading_relief_max", cfg.get("waypoint_turn_relief_max", 0.0)))
                 turn_heading_relief_max = float(np.clip(turn_heading_relief_max, 0.0, 0.95))
                 heading_penalty_scale = 1.0 - turn_heading_relief_max * waypoint_turn_relief_activation
                 _add_reward_term("heading_error_penalty", diff * cfg.get("heading_error_weight") * heading_penalty_scale)
                 hold_db = float(cfg.get("heading_hold_deadband_deg", 0.0))
                 hold_bonus = float(cfg.get("heading_hold_bonus", 0.0))
                 if hold_bonus != 0.0 and diff <= max(0.0, hold_db):
                     _add_reward_term("heading_hold_bonus", hold_bonus)

            # Altitude/speed command tracking (airborne-only; realism-safe: targets are already in obs["mission"]).
            # These were present in scenario configs but previously not implemented, which can lead to weak
            # steady-state signals (e.g., the agent learns to "survive" but not to stabilize near the commanded
            # flight condition).
            if airborne:
                # Altitude error penalty (baro altitude vs mission target altitude)
                w_alt_err = float(cfg.get("altitude_error_weight", 0.0))
                if w_alt_err != 0.0:
                    alt_baro = float(inst[2])
                    min_alt = float(cfg.get("altitude_error_min_alt", 0.0))
                    if alt_baro >= min_alt:
                        tgt_alt = cfg.get("altitude_error_target", None)
                        if tgt_alt is None:
                            tgt_alt = self.mission_cmd.get("target_altitude", alt_baro)
                        try:
                            tgt_alt = float(tgt_alt)
                        except Exception:
                            tgt_alt = alt_baro
                        deadband = float(cfg.get("altitude_error_deadband_m", cfg.get("altitude_error_band_m", 0.0)))
                        norm = float(cfg.get("altitude_error_norm_m", 100.0))
                        if norm <= 1.0e-6:
                            norm = 100.0
                        p = float(cfg.get("altitude_error_power", 1.0))
                        if p < 1.0:
                            p = 1.0
                        if p > 8.0:
                            p = 8.0
                        err = abs(alt_baro - float(tgt_alt)) - max(0.0, deadband)
                        if err > 0.0:
                            x = err / norm
                            clip = float(cfg.get("altitude_error_clip", 0.0))
                            if clip > 0.0:
                                x = min(x, clip)
                            _add_reward_term("altitude_error_penalty", w_alt_err * (x**p))
                        else:
                            hold_bonus = float(cfg.get("altitude_hold_bonus", 0.0))
                            if hold_bonus != 0.0:
                                _add_reward_term("altitude_hold_bonus", hold_bonus)

                # Speed error penalty (IAS vs mission target speed)
                w_spd_err = float(cfg.get("speed_error_weight", 0.0))
                if w_spd_err != 0.0:
                    min_ias = float(cfg.get("speed_error_min_ias", 0.0))
                    if float(curr_ias) >= min_ias:
                        tgt_spd = cfg.get("speed_error_target", None)
                        if tgt_spd is None:
                            tgt_spd = self.mission_cmd.get("target_speed", float(curr_ias))
                        try:
                            tgt_spd = float(tgt_spd)
                        except Exception:
                            tgt_spd = float(curr_ias)
                        deadband = float(cfg.get("speed_error_deadband", cfg.get("speed_error_band", 0.0)))
                        norm = float(cfg.get("speed_error_norm", 30.0))
                        if norm <= 1.0e-6:
                            norm = 30.0
                        p = float(cfg.get("speed_error_power", 1.0))
                        if p < 1.0:
                            p = 1.0
                        if p > 8.0:
                            p = 8.0
                        err = abs(float(curr_ias) - float(tgt_spd)) - max(0.0, deadband)
                        if err > 0.0:
                            x = err / norm
                            clip = float(cfg.get("speed_error_clip", 0.0))
                            if clip > 0.0:
                                x = min(x, clip)
                            _add_reward_term("speed_error_penalty", w_spd_err * (x**p))
                        else:
                            hold_bonus = float(cfg.get("speed_hold_bonus", 0.0))
                            if hold_bonus != 0.0:
                                _add_reward_term("speed_hold_bonus", hold_bonus)

                # Stability penalties (airborne-only). These encourage smooth, realistic flight by penalizing
                # large attitudes/rates and uncoordinated slip, without adding any privileged observations.
                w_roll = float(cfg.get("roll_abs_weight", 0.0))
                if w_roll != 0.0:
                    roll = float(inst[8])
                    dead = float(cfg.get("roll_abs_deadband_deg", 0.0))
                    norm = float(cfg.get("roll_abs_norm_deg", 30.0))
                    if norm <= 1.0e-6:
                        norm = 30.0
                    p = float(cfg.get("roll_abs_power", 1.0))
                    if p < 1.0:
                        p = 1.0
                    if p > 8.0:
                        p = 8.0
                    err = abs(roll) - max(0.0, dead)
                    if err > 0.0:
                        _add_reward_term("roll_abs_penalty", w_roll * ((err / norm) ** p))

                w_pitch = float(cfg.get("pitch_abs_weight", 0.0))
                if w_pitch != 0.0:
                    pitch = float(inst[7])
                    dead = float(cfg.get("pitch_abs_deadband_deg", 0.0))
                    norm = float(cfg.get("pitch_abs_norm_deg", 20.0))
                    if norm <= 1.0e-6:
                        norm = 20.0
                    p = float(cfg.get("pitch_abs_power", 1.0))
                    if p < 1.0:
                        p = 1.0
                    if p > 8.0:
                        p = 8.0
                    err = abs(pitch) - max(0.0, dead)
                    if err > 0.0:
                        _add_reward_term("pitch_abs_penalty", w_pitch * ((err / norm) ** p))

                w_r = float(cfg.get("yaw_rate_abs_weight", 0.0))
                if w_r != 0.0:
                    r_deg_s = float(inst[14]) if len(inst) > 14 else 0.0
                    dead = float(cfg.get("yaw_rate_abs_deadband_deg_s", 0.0))
                    norm = float(cfg.get("yaw_rate_abs_norm_deg_s", 10.0))
                    if norm <= 1.0e-6:
                        norm = 10.0
                    p = float(cfg.get("yaw_rate_abs_power", 1.0))
                    if p < 1.0:
                        p = 1.0
                    if p > 8.0:
                        p = 8.0
                    err = abs(r_deg_s) - max(0.0, dead)
                    if err > 0.0:
                        _add_reward_term("yaw_rate_abs_penalty", w_r * ((err / norm) ** p))

                w_beta = float(cfg.get("beta_abs_weight", 0.0))
                if w_beta != 0.0:
                    beta = float(inst[6]) if len(inst) > 6 else 0.0
                    dead = float(cfg.get("beta_abs_deadband_deg", 0.0))
                    norm = float(cfg.get("beta_abs_norm_deg", 10.0))
                    if norm <= 1.0e-6:
                        norm = 10.0
                    p = float(cfg.get("beta_abs_power", 1.0))
                    if p < 1.0:
                        p = 1.0
                    if p > 8.0:
                        p = 8.0
                    err = abs(beta) - max(0.0, dead)
                    if err > 0.0:
                        _add_reward_term("beta_abs_penalty", w_beta * ((err / norm) ** p))

                w_g = float(cfg.get("g_deviation_weight", 0.0))
                if w_g != 0.0:
                    g_load = float(inst[10])
                    dead = float(cfg.get("g_deviation_deadband", 0.0))
                    norm = float(cfg.get("g_deviation_norm", 0.5))
                    if norm <= 1.0e-6:
                        norm = 0.5
                    p = float(cfg.get("g_deviation_power", 1.0))
                    if p < 1.0:
                        p = 1.0
                    if p > 8.0:
                        p = 8.0
                    g_dev_min_alt_agl_m = float(cfg.get("g_deviation_min_alt_agl_m", 5.0))
                    err = abs(g_load - 1.0) - max(0.0, dead)
                    if airborne and curr_alt_agl > g_dev_min_alt_agl_m and err > 0.0:
                        _add_reward_term("g_deviation_penalty", w_g * ((err / norm) ** p))
            
            # 6. Raw Speed Reward (Encourage Velocity)
            _add_reward_term("speed_reward", truth.speed * cfg.get("speed_reward_weight", 0.0))

            # 7. Runway Alignment Reward (Positive reinforcement for staying aligned)
            # 1.0 if perfectly aligned, 0.0 if 90 deg off, -1.0 if opposite
            # diff is absolute error [0, 180] from lines 643-644
            #
            # Realism note:
            # - The agent does NOT observe runway geometry (heading/cross-track) directly.
            # - We allow reward shaping to reflect a real-world training objective: keep the aircraft near the runway
            #   centerline during takeoff roll. This is a continuous penalty (not a hard "on/off runway" threshold),
            #   to avoid edge-hugging policies that look unrealistic yet stay within runway bounds.
            if (
                preliftoff
                and on_runway_task
                and runway_cross_m is not None
                and runway_wid_m is not None
            ):
                half_w = 0.5 * float(runway_wid_m)
                if half_w > 1.0e-6:
                    frac = abs(float(runway_cross_m)) / half_w
                    # Allow slight overshoot; off-runway termination handles true departures.
                    if frac > 2.0:
                        frac = 2.0
                    min_ias = float(cfg.get("runway_centerline_penalty_min_ias", 0.0))
                    max_ias = float(cfg.get("runway_centerline_penalty_max_ias", 0.0))
                    scale = 1.0
                    if max_ias > min_ias + 1.0e-6:
                        scale = (float(curr_ias) - min_ias) / (max_ias - min_ias)
                        if scale < 0.0:
                            scale = 0.0
                        if scale > 1.0:
                            scale = 1.0

                    # Continuous centerline penalty (no observation leakage; geometry is teacher-only).
                    # Meter-based shaping (recommended):
                    # - direct interpretability (e.g. "5m deviation costs ~1 per step")
                    # - avoids "safe region" exploits by being strictly increasing from 0
                    w_center_m = float(cfg.get("runway_centerline_m_penalty_weight", 0.0))
                    if w_center_m != 0.0:
                        dead_m = float(cfg.get("runway_centerline_m_deadband_m", 0.0))
                        if dead_m < 0.0:
                            dead_m = 0.0
                        norm_m = float(cfg.get("runway_centerline_m_norm_m", 5.0))
                        if norm_m <= 1.0e-6:
                            norm_m = 5.0
                        p_m = float(cfg.get("runway_centerline_m_power", 2.0))
                        if p_m < 1.0:
                            p_m = 1.0
                        if p_m > 8.0:
                            p_m = 8.0
                        err_m = abs(float(runway_cross_m)) - dead_m
                        if err_m > 0.0:
                            x_m = err_m / norm_m
                            clip_m = float(cfg.get("runway_centerline_m_clip", 0.0))
                            if clip_m > 0.0:
                                x_m = min(x_m, clip_m)
                            _add_reward_term("runway_centerline_m_penalty", w_center_m * (x_m**p_m) * scale)

                    w_center = float(cfg.get("runway_centerline_penalty_weight", 0.0))
                    if w_center != 0.0:
                        safe_frac = float(cfg.get("runway_centerline_safe_frac", 0.0))
                        if safe_frac < 0.0:
                            safe_frac = 0.0
                        if safe_frac > 0.99:
                            safe_frac = 0.99
                        x = max(0.0, frac - safe_frac) / max(1.0 - safe_frac, 1.0e-6)
                        p = float(cfg.get("runway_centerline_penalty_power", 2.0))
                        if p < 1.0:
                            p = 1.0
                        if p > 8.0:
                            p = 8.0
                        _add_reward_term("runway_centerline_penalty", w_center * (x**p) * scale)

                    # Optional centerline barrier: smoothly increases without any "safe region".
                    # This makes edge-hugging strategies strictly worse, while keeping the observation
                    # space realism intact (no privileged geometry is exposed to the agent).
                    w_bar = float(cfg.get("runway_centerline_barrier_weight", 0.0))
                    if w_bar != 0.0:
                        clip_frac = float(cfg.get("runway_centerline_barrier_clip_frac", 0.995))
                        if clip_frac <= 0.0:
                            clip_frac = 0.995
                        if clip_frac >= 0.999999:
                            clip_frac = 0.999999
                        frac_c = min(max(frac, 0.0), clip_frac)
                        barrier = -math.log(max(1.0e-6, 1.0 - frac_c))
                        _add_reward_term("runway_centerline_barrier", w_bar * barrier * scale)

            # Departure centerline shaping: after liftoff, keep the aircraft near the runway extended
            # centerline until a safe initial-climb altitude. Without this, Stage 1.5 can satisfy
            # "gear up + speed + altitude" while still drifting far off the intended departure path.
            if runway_cross_m is not None:
                dep_max_alt = float(cfg.get("departure_centerline_max_alt_agl_m", 0.0))
                if airborne and dep_max_alt > 0.0 and curr_alt_agl <= dep_max_alt:
                    w_dep_m = float(cfg.get("departure_centerline_m_penalty_weight", 0.0))
                    if w_dep_m != 0.0:
                        dead_m = float(cfg.get("departure_centerline_m_deadband_m", 0.0))
                        if dead_m < 0.0:
                            dead_m = 0.0
                        norm_m = float(cfg.get("departure_centerline_m_norm_m", 20.0))
                        if norm_m <= 1.0e-6:
                            norm_m = 20.0
                        p_m = float(cfg.get("departure_centerline_m_power", 2.0))
                        if p_m < 1.0:
                            p_m = 1.0
                        if p_m > 8.0:
                            p_m = 8.0
                        err_m = abs(float(runway_cross_m)) - dead_m
                        if err_m > 0.0:
                            x_m = err_m / norm_m
                            clip_m = float(cfg.get("departure_centerline_m_clip", 0.0))
                            if clip_m > 0.0:
                                x_m = min(x_m, clip_m)
                            _add_reward_term("departure_centerline_m_penalty", w_dep_m * (x_m**p_m))
                    w_dep_center = float(cfg.get("departure_centerline_reward_weight", 0.0))
                    if w_dep_center != 0.0:
                        band_m = float(cfg.get("departure_centerline_reward_band_m", max(1.0, dead_m)))
                        if band_m <= 1.0e-6:
                            band_m = 1.0
                        center_frac = max(0.0, 1.0 - abs(float(runway_cross_m)) / band_m)
                        if center_frac > 0.0:
                            _add_reward_term("departure_centerline_reward", w_dep_center * center_frac)

                    # Departure track shaping: while below a safe climb altitude, encourage keeping
                    # the extended runway / departure track instead of allowing a large early wander.
                    ground_track_deg = self._ground_track_from_inst(inst, truth.heading)
                    tgt_hdg = float(self.mission_cmd.get("target_heading", 0.0))
                    dep_track_err = abs(self._wrap_angle_deg(tgt_hdg - ground_track_deg))

                    w_dep_trk = float(cfg.get("departure_track_error_weight", 0.0))
                    if w_dep_trk != 0.0:
                        dead_deg = float(cfg.get("departure_track_error_deadband_deg", 0.0))
                        if dead_deg < 0.0:
                            dead_deg = 0.0
                        norm_deg = float(cfg.get("departure_track_error_norm_deg", 10.0))
                        if norm_deg <= 1.0e-6:
                            norm_deg = 10.0
                        p_deg = float(cfg.get("departure_track_error_power", 2.0))
                        if p_deg < 1.0:
                            p_deg = 1.0
                        if p_deg > 8.0:
                            p_deg = 8.0
                        err_deg = dep_track_err - dead_deg
                        if err_deg > 0.0:
                            x_deg = err_deg / norm_deg
                            clip_deg = float(cfg.get("departure_track_error_clip", 0.0))
                            if clip_deg > 0.0:
                                x_deg = min(x_deg, clip_deg)
                            _add_reward_term("departure_track_error_penalty", w_dep_trk * (x_deg**p_deg))

                    w_dep_trk_reward = float(cfg.get("departure_track_reward_weight", 0.0))
                    if w_dep_trk_reward != 0.0:
                        band_deg = float(cfg.get("departure_track_reward_band_deg", 10.0))
                        if band_deg <= 1.0e-6:
                            band_deg = 10.0
                        track_frac = max(0.0, 1.0 - dep_track_err / band_deg)
                        if track_frac > 0.0:
                            _add_reward_term("departure_track_reward", w_dep_trk_reward * track_frac)

            if cfg.get("alignment_reward_weight", 0.0) != 0.0:
                w = float(cfg.get("alignment_reward_weight"))
                # On the runway, we should NOT force alignment to the mission heading (that can conflict with runway
                # direction and encourages unrealistic pivoting/braking). Instead, use the ILS localizer deviation
                # when available to reward staying on the runway centerline.
                if on_runway_task and preliftoff:
                    try:
                        ils_valid = float(inst[-4])
                        loc_dev = float(inst[-3])
                    except Exception:
                        ils_valid = 0.0
                        loc_dev = 0.0
                    if ils_valid > 0.5:
                        # loc_dev is normalized [-1,1]; reward is [0,1] when centered.
                        _add_reward_term("alignment_reward", (1.0 - min(abs(loc_dev), 1.0)) * w)
                else:
                    # Airborne: command adherence can follow mission heading, but not immediately after liftoff.
                    # Realistic departure keeps runway heading until a safe altitude.
                    min_alt_for_cmd_align = float(cfg.get("mission_alignment_min_alt", 120.0))
                    if truth.z >= min_alt_for_cmd_align:
                        diff = self._command_tracking_error_deg(inst, truth.heading)
                        align_factor = math.cos(math.radians(diff))
                        if align_factor > 0:
                            _add_reward_term("alignment_reward", align_factor * w)

            # Approach / landing shaping via instrument-style ILS products only.
            # This keeps the task realism-first: the policy sees the same localizer /
            # glideslope / DME-style cues a pilot would see, without direct runway geometry.
            try:
                ils_valid = float(inst[-4])
                ils_loc = float(inst[-3])
                ils_gs = float(inst[-2])
                ils_dme = float(inst[-1])
            except Exception:
                ils_valid = 0.0
                ils_loc = 0.0
                ils_gs = 0.0
                ils_dme = 0.0

            approach_active = bool(
                float(cfg.get("approach_localizer_weight", 0.0)) != 0.0
                or float(cfg.get("approach_glideslope_weight", 0.0)) != 0.0
                or float(cfg.get("approach_dme_progress_weight", 0.0)) != 0.0
                or float(cfg.get("approach_capture_bonus", 0.0)) != 0.0
                or float(cfg.get("landing_sink_rate_penalty_weight", 0.0)) != 0.0
            )
            if approach_active:
                if ils_valid > 0.5:
                    curr_loc_abs = abs(float(ils_loc))
                    curr_gs_abs = abs(float(ils_gs))

                    w_loc = float(cfg.get("approach_localizer_weight", 0.0))
                    if w_loc != 0.0:
                        dead = max(0.0, float(cfg.get("approach_localizer_deadband", 0.0)))
                        norm = float(cfg.get("approach_localizer_norm", 1.0))
                        if norm <= 1.0e-6:
                            norm = 1.0
                        p = float(np.clip(float(cfg.get("approach_localizer_power", 2.0)), 1.0, 8.0))
                        err = abs(float(ils_loc)) - dead
                        if err > 0.0:
                            x = err / norm
                            clip = float(cfg.get("approach_localizer_clip", 0.0))
                            if clip > 0.0:
                                x = min(x, clip)
                            _add_reward_term("approach_localizer", w_loc * (x**p))

                    w_loc_improve = float(cfg.get("approach_localizer_improve_weight", 0.0))
                    if w_loc_improve != 0.0 and self._approach_prev_loc_abs is not None:
                        loc_delta = float(self._approach_prev_loc_abs) - curr_loc_abs
                        _add_reward_term("approach_localizer_improve", loc_delta * w_loc_improve)

                    w_gs = float(cfg.get("approach_glideslope_weight", 0.0))
                    if w_gs != 0.0:
                        dead = max(0.0, float(cfg.get("approach_glideslope_deadband", 0.0)))
                        norm = float(cfg.get("approach_glideslope_norm", 1.0))
                        if norm <= 1.0e-6:
                            norm = 1.0
                        p = float(np.clip(float(cfg.get("approach_glideslope_power", 2.0)), 1.0, 8.0))
                        err = abs(float(ils_gs)) - dead
                        if err > 0.0:
                            x = err / norm
                            clip = float(cfg.get("approach_glideslope_clip", 0.0))
                            if clip > 0.0:
                                x = min(x, clip)
                            _add_reward_term("approach_glideslope", w_gs * (x**p))

                    w_gs_improve = float(cfg.get("approach_glideslope_improve_weight", 0.0))
                    if w_gs_improve != 0.0 and self._approach_prev_gs_abs is not None:
                        gs_delta = float(self._approach_prev_gs_abs) - curr_gs_abs
                        _add_reward_term("approach_glideslope_improve", gs_delta * w_gs_improve)

                    w_dme = float(cfg.get("approach_dme_progress_weight", 0.0))
                    if w_dme != 0.0 and math.isfinite(float(ils_dme)):
                        if self._approach_prev_dme_m is not None:
                            dme_delta = float(self._approach_prev_dme_m) - float(ils_dme)
                            quality = 1.0
                            loc_band = float(cfg.get("approach_dme_progress_localizer_band", 0.0))
                            if loc_band > 1.0e-6:
                                quality *= max(0.0, 1.0 - curr_loc_abs / loc_band)
                            gs_band = float(cfg.get("approach_dme_progress_glideslope_band", 0.0))
                            if gs_band > 1.0e-6:
                                quality *= max(0.0, 1.0 - curr_gs_abs / gs_band)
                            quality_power = float(np.clip(float(cfg.get("approach_dme_progress_quality_power", 1.0)), 0.5, 4.0))
                            quality = float(np.clip(quality, 0.0, 1.0)) ** quality_power
                            _add_reward_term("approach_dme_progress", dme_delta * w_dme * quality)
                        self._approach_prev_dme_m = float(ils_dme)

                    capture_bonus = float(cfg.get("approach_capture_bonus", 0.0))
                    if capture_bonus != 0.0:
                        loc_band = max(0.0, float(cfg.get("approach_capture_localizer_band", 0.20)))
                        gs_band = max(0.0, float(cfg.get("approach_capture_glideslope_band", 0.20)))
                        if abs(float(ils_loc)) <= loc_band and abs(float(ils_gs)) <= gs_band:
                            _add_reward_term("approach_capture_bonus", capture_bonus)

                    self._approach_prev_loc_abs = float(curr_loc_abs)
                    self._approach_prev_gs_abs = float(curr_gs_abs)
                else:
                    self._approach_prev_dme_m = None
                    self._approach_prev_loc_abs = None
                    self._approach_prev_gs_abs = None

                sink_w = float(cfg.get("landing_sink_rate_penalty_weight", 0.0))
                flare_agl_m = max(0.0, float(cfg.get("landing_flare_agl_m", 20.0)))
                if sink_w != 0.0 and curr_alt_agl <= flare_agl_m:
                    sink_rate = abs(float(inst[4])) if len(inst) > 4 else 0.0
                    dead = max(0.0, float(cfg.get("landing_sink_rate_deadband_mps", 0.0)))
                    norm = float(cfg.get("landing_sink_rate_norm_mps", 2.0))
                    if norm <= 1.0e-6:
                        norm = 2.0
                    p = float(np.clip(float(cfg.get("landing_sink_rate_power", 2.0)), 1.0, 8.0))
                    err = sink_rate - dead
                    if err > 0.0:
                        x = err / norm
                        clip = float(cfg.get("landing_sink_rate_clip", 0.0))
                        if clip > 0.0:
                            x = min(x, clip)
                        _add_reward_term("landing_sink_rate_penalty", sink_w * (x**p))

        # Update Prev State
        self.prev_alt = truth.z
        self.prev_speed = curr_ias

        # 4.x Waypoint Navigation (Cruise): reach a sequence of mission waypoints.
        # Note: This is a mission-level task (reach waypoints), not "fly a straight line".
        if not terminated:
            try:
                cmd_code = int(self.mission_cmd.get("command_code", 0))
            except Exception:
                cmd_code = 0
            if cmd_code == 3 and self.waypoints:
                idx = int(getattr(self, "waypoint_idx", 0))
                if idx < 0:
                    idx = 0
                n = int(len(self.waypoints))
                if idx < n:
                    wp = self.waypoints[idx]
                    dx = float(wp.get("x", 0.0)) - float(getattr(truth, "x", 0.0))
                    dy = float(wp.get("y", 0.0)) - float(getattr(truth, "y", 0.0))
                    dist_m = float(math.sqrt(dx * dx + dy * dy))

                    # Use status slots for quick debugging in logs/viz tools.
                    status[0] = dist_m
                    status[1] = float(idx)
                    status[2] = float(n)

                    mode = self._normalize_waypoint_mode(wp.get("waypoint_mode", self.mission_cmd.get("waypoint_mode", "flyby")))

                    w_prog = float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_progress_weight", mode, 0.0))
                    if w_prog != 0.0 and self._waypoint_prev_dist_m is not None:
                        prog_delta_m = float(self._waypoint_prev_dist_m) - dist_m
                        if prog_delta_m < 0.0:
                            neg_scale = float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_progress_negative_scale", mode, 1.0))
                            prog_delta_m *= max(0.0, neg_scale)
                        _add_reward_term("waypoint_progress", prog_delta_m * w_prog)
                    self._waypoint_prev_dist_m = dist_m

                    # Reward geometry must match the active LNAV guidance mode.
                    gstate = self._compute_waypoint_guidance_state(truth=truth, inst=inst)
                    ex = float(wp.get("x", 0.0))
                    ey = float(wp.get("y", 0.0))
                    lx = 0.0
                    ly = 0.0
                    leg_len = 0.0
                    along = None
                    xtk = None
                    dtg = None
                    if isinstance(gstate, dict) and int(gstate.get("idx", -1)) == idx:
                        lx = float(gstate.get("lx", 0.0))
                        ly = float(gstate.get("ly", 0.0))
                        leg_len = float(gstate.get("leg_len_m", 0.0))
                        along = float(gstate.get("along_m", 0.0))
                        xtk = float(gstate.get("reward_xtk_m", 0.0))
                        dtg = float(gstate.get("reward_dtg_m", dist_m))
                    else:
                        if idx <= 0:
                            sx = float(getattr(self, "_waypoint_leg_origin_x", getattr(truth, "x", 0.0)))
                            sy = float(getattr(self, "_waypoint_leg_origin_y", getattr(truth, "y", 0.0)))
                        else:
                            prev = self.waypoints[idx - 1]
                            sx = float(prev.get("x", 0.0))
                            sy = float(prev.get("y", 0.0))
                        lx = ex - sx
                        ly = ey - sy
                        leg_len = float(math.hypot(lx, ly))
                        if leg_len > 1.0e-6:
                            ux = lx / leg_len
                            uy = ly / leg_len
                            px = float(getattr(truth, "x", 0.0)) - sx
                            py = float(getattr(truth, "y", 0.0)) - sy
                            along = float(px * ux + py * uy)
                            xtk = float(px * uy - py * ux)
                            dtg = max(0.0, float(leg_len - along))

                    w_dist = float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_distance_weight", mode, 0.0))
                    if w_dist != 0.0:
                        dist_term_m = float(dist_m)
                        clip_m = float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_distance_clip_m", mode, 0.0))
                        if clip_m > 0.0:
                            dist_term_m = min(dist_term_m, clip_m)
                        dist_scale = 1.0
                        if bool(self._cfg_value_for_waypoint_mode(cfg, "waypoint_distance_scale_by_route", mode, False)):
                            route_len_m = float(getattr(self, "waypoint_total_route_length_m", 0.0))
                            route_ref_m = float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_distance_route_ref_m", mode, 55000.0))
                            if route_len_m > 1.0e-6 and route_ref_m > 1.0e-6:
                                dist_scale = route_ref_m / route_len_m
                                scale_min = float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_distance_route_scale_min", mode, 0.5))
                                scale_max = float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_distance_route_scale_max", mode, 1.0))
                                if scale_max < scale_min:
                                    scale_min, scale_max = scale_max, scale_min
                                dist_scale = float(np.clip(dist_scale, scale_min, scale_max))
                        _add_reward_term("waypoint_distance", dist_term_m * w_dist * dist_scale)

                    w_xtk = float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_cross_track_weight", mode, 0.0))
                    if w_xtk != 0.0 and xtk is not None:
                        dead_m = float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_cross_track_deadband_m", mode, 0.0))
                        norm_m = float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_cross_track_norm_m", mode, 1000.0))
                        if norm_m <= 1.0e-6:
                            norm_m = 1000.0
                        p = float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_cross_track_power", mode, 1.0))
                        if p < 1.0:
                            p = 1.0
                        if p > 8.0:
                            p = 8.0
                        xtk_err_m = abs(float(xtk)) - max(0.0, dead_m)
                        if xtk_err_m > 0.0:
                            x = xtk_err_m / norm_m
                            clip_x = float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_cross_track_clip", mode, 0.0))
                            if clip_x > 0.0:
                                x = min(x, clip_x)
                            turn_relief_max = float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_max", mode, 0.0))
                            turn_relief_max = float(np.clip(turn_relief_max, 0.0, 0.95))
                            xtk_penalty_scale = 1.0 - turn_relief_max * waypoint_turn_relief_activation
                            _add_reward_term("waypoint_cross_track", w_xtk * (x**p) * xtk_penalty_scale)

                    # Arrival / sequencing check.
                    # Cruise uses a more realistic fly-by LNAV style by default: intermediate waypoints
                    # are sequenced with turn anticipation based on speed + bank limit.
                    try:
                        rad = float(wp.get("radius_m", cfg.get("waypoint_radius_m", 500.0)))
                    except Exception:
                        rad = float(cfg.get("waypoint_radius_m", 500.0))
                    rad = max(1.0, float(rad))

                    prox_w = float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_proximity_weight", mode, 0.0))
                    if prox_w != 0.0:
                        prox_ref_m = float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_proximity_ref_m", mode, max(2.5 * rad, rad + 1500.0)))
                        if prox_ref_m > 1.0e-6:
                            prox_p = float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_proximity_power", mode, 1.0))
                            prox_p = float(np.clip(prox_p, 1.0, 8.0))
                            prox_x = 1.0 - min(dist_m, prox_ref_m) / prox_ref_m
                            if prox_x > 0.0:
                                _add_reward_term("waypoint_proximity", prox_w * (prox_x**prox_p))

                    # Compute leg-relative metrics for fly-by sequencing.
                    arrived = False
                    if mode == "flyby" and idx < (n - 1):
                        if leg_len > 1.0e-6 and xtk is not None and dtg is not None:
                            # Turn anticipation lead distance (simple constant-radius geometry).
                            next_wp = self.waypoints[idx + 1]
                            nx = float(next_wp.get("x", 0.0)) - ex
                            ny = float(next_wp.get("y", 0.0)) - ey
                            cur_trk = float(self._bearing_to_deg(lx, ly))
                            next_trk = float(self._bearing_to_deg(nx, ny)) if (nx * nx + ny * ny) > 1.0e-9 else cur_trk
                            delta = (next_trk - cur_trk + 180.0) % 360.0 - 180.0
                            delta = abs(float(delta))
                            bank_lim = float(self.mission_cmd.get("lnav_bank_limit_deg", 30.0))
                            bank_lim = float(np.clip(bank_lim, 5.0, 70.0))
                            bank_rad = math.radians(bank_lim)
                            tanb = math.tan(bank_rad)
                            if abs(tanb) < 1.0e-6:
                                lead = 0.0
                            else:
                                v = max(30.0, float(curr_ias))
                                r_turn = (v * v) / (9.80665 * abs(tanb))
                                lead = float(r_turn * math.tan(math.radians(delta) * 0.5))
                                lead = max(0.0, lead)
                            seq_gate_scale = float(self.mission_cmd.get("lnav_sequence_gate_scale", 0.35))
                            seq_gate_min = float(self.mission_cmd.get("lnav_sequence_gate_min_m", rad))
                            seq_gate_max = float(self.mission_cmd.get("lnav_sequence_gate_max_m", max(2.5 * rad, rad + 1500.0)))
                            seq_gate_m = max(seq_gate_min, min(seq_gate_max, rad + seq_gate_scale * max(0.0, lead)))
                            passed_fix = bool(along is not None and float(along) >= float(leg_len))

                            # Realistic fly-by LNAV does not require overflying the exact fix center.
                            # Sequence if we are within the turn-anticipation region and reasonably close
                            # to the active fix, or if we have already passed abeam the fix.
                            if dist_m <= rad:
                                arrived = True
                            elif (not passed_fix) and abs(xtk) <= seq_gate_m and dtg <= max(lead, 0.0):
                                arrived = True
                            elif passed_fix and dist_m <= max(seq_gate_m, rad + 500.0):
                                arrived = True
                    else:
                        # Fly-over: require entering a radial acceptance radius around the fix.
                        arrived = bool(dist_m <= rad)

                    if arrived:
                        _add_reward_term(
                            "waypoint_reached_bonus",
                            float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_reached_bonus", mode, 0.0)),
                        )
                        self.waypoint_idx = idx + 1
                        status[1] = float(self.waypoint_idx)
                        if self.waypoint_idx < n:
                            next_wp = self.waypoints[self.waypoint_idx]
                            next_dx = float(next_wp.get("x", 0.0)) - float(getattr(truth, "x", 0.0))
                            next_dy = float(next_wp.get("y", 0.0)) - float(getattr(truth, "y", 0.0))
                            status[0] = float(math.hypot(next_dx, next_dy))
                        else:
                            status[0] = 0.0
                        self._waypoint_prev_dist_m = None
                        if self.waypoint_idx >= n:
                            transitioned = self._activate_post_waypoint_transition()
                            if isinstance(transitioned, dict):
                                _add_reward_term(
                                    "phase_transition_bonus",
                                    float(transitioned.get("transition_reward", cfg.get("phase_transition_bonus", 600.0))),
                                )
                                status[0] = 0.0
                                status[1] = 0.0
                            else:
                                _add_reward_term("waypoint_success_bonus", float(cfg.get("waypoint_mission_success_bonus", 1000.0)))
                                terminated = True
                                status[3] = 1.0
                                term_reason = "success_waypoint"
            
        # 5. Objectives (Binary Success)
        # Only evaluate success conditions if we did not already terminate due to a failure mode.
        if not terminated:
            for obj in rules:
                if obj["type"] == "conditional":
                    conds_met = True
                    for i, cond in enumerate(obj.get("conditions", [])):
                        prop = cond.get("property")
                        op = cond.get("op", ">=")

                        tgt = cond.get("value", 0.0)

                        # Optional dynamic target resolution (opt-in).
                        # If a scenario wants a condition to follow the randomized mission command, it can
                        # set `"value": "CMD_ALT"` / `"CMD_SPEED"` / `"CMD_HDG"` (optionally with `"scale": ...`).
                        if isinstance(tgt, str):
                            key = tgt.strip().upper()
                            if key in ("CMD_ALT", "CMD_ALTITUDE"):
                                scale = float(cond.get("scale", 0.95))
                                tgt = float(self.mission_cmd.get("target_altitude", 0.0)) * scale
                            elif key in ("CMD_SPEED",):
                                scale = float(cond.get("scale", 0.90))
                                tgt = float(self.mission_cmd.get("target_speed", 0.0)) * scale
                            elif key in ("CMD_HDG", "CMD_HEADING"):
                                tgt = float(self.mission_cmd.get("target_heading", 0.0))

                        val = 0.0
                        if prop == "altitude":
                            val = float(truth.z)
                        elif prop == "altitude_agl":
                            try:
                                val = float(inst.alt_radar)
                            except Exception:
                                val = float(inst[3]) if len(inst) > 3 else 0.0
                        elif prop == "speed":
                            val = float(curr_ias)
                        elif prop == "ground_speed":
                            val = float(curr_ground_speed)
                        elif prop == "gear":
                            try:
                                val = float(curr_gear)
                            except Exception:
                                val = 0.0
                        elif prop == "heading_error_deg":
                            val = float(self._command_tracking_error_deg(inst, truth.heading))
                        elif prop == "command_code":
                            try:
                                val = float(int(self.mission_cmd.get("command_code", 0)))
                            except Exception:
                                val = 0.0
                        elif prop == "ground_track_error_deg":
                            ground_track_deg = self._ground_track_from_inst(inst, truth.heading)
                            tgt_hdg = float(self.mission_cmd.get("target_heading", 0.0))
                            val = abs(self._wrap_angle_deg(tgt_hdg - ground_track_deg))
                        elif prop == "runway_cross_abs_m":
                            if runway_cross_m is None:
                                val = float("inf")
                            else:
                                val = abs(float(runway_cross_m))
                        elif prop == "runway_from_threshold_m":
                            if runway_from_threshold_m is None:
                                val = float("inf")
                            else:
                                val = float(runway_from_threshold_m)
                        elif prop == "on_runway_geom":
                            val = 1.0 if bool(on_runway_geom) else 0.0
                        elif prop == "on_runway":
                            val = 1.0 if bool(on_runway_task) else 0.0
                        elif prop == "on_ground":
                            val = 1.0 if bool(on_ground) else 0.0
                        elif prop == "sink_rate_abs_mps" or prop == "vertical_speed_abs_mps":
                            try:
                                val = abs(float(inst[4]))
                            except Exception:
                                val = 0.0
                        elif prop == "ils_localizer_abs":
                            try:
                                val = abs(float(inst[-3]))
                            except Exception:
                                val = float("inf")
                        elif prop == "ils_glideslope_abs":
                            try:
                                val = abs(float(inst[-2]))
                            except Exception:
                                val = float("inf")
                        elif prop == "dme_m":
                            try:
                                val = float(inst[-1])
                            except Exception:
                                val = float("inf")
                        elif prop == "heading":
                            val = float(truth.heading)
                        elif prop == "x":
                            val = float(truth.x)
                        elif prop == "y":
                            val = float(truth.y)
                        else:
                            # Unknown objective property should not silently pass.
                            conds_met = False
                            continue

                        # Status for TensorBoard (log up to first 3 values; slot 3 is reserved for terminal flag).
                        if i < 3:
                            status[i] = val

                        # Check
                        if op == ">=" and val < tgt:
                            conds_met = False
                        elif op == ">" and val <= tgt:
                            conds_met = False
                        elif op == "<=" and val > tgt:
                            conds_met = False
                        elif op == "<" and val >= tgt:
                            conds_met = False

                    if conds_met:
                        success_cross_w = float(cfg.get("success_runway_cross_penalty_weight", 0.0))
                        if success_cross_w != 0.0 and runway_cross_m is not None:
                            dead_m = max(0.0, float(cfg.get("success_runway_cross_deadband_m", 0.0)))
                            norm_m = float(cfg.get("success_runway_cross_norm_m", 20.0))
                            if norm_m <= 1.0e-6:
                                norm_m = 20.0
                            p_m = float(cfg.get("success_runway_cross_power", 2.0))
                            p_m = min(8.0, max(1.0, p_m))
                            err_m = abs(float(runway_cross_m)) - dead_m
                            if err_m > 0.0:
                                x_m = err_m / norm_m
                                clip_m = float(cfg.get("success_runway_cross_clip", 0.0))
                                if clip_m > 0.0:
                                    x_m = min(x_m, clip_m)
                                _add_reward_term("success_runway_cross_penalty", success_cross_w * (x_m**p_m))

                        success_track_w = float(cfg.get("success_ground_track_error_penalty_weight", 0.0))
                        if success_track_w != 0.0:
                            ground_track_deg = self._ground_track_from_inst(inst, truth.heading)
                            tgt_hdg = float(self.mission_cmd.get("target_heading", 0.0))
                            track_err = abs(self._wrap_angle_deg(tgt_hdg - ground_track_deg))
                            dead_deg = max(0.0, float(cfg.get("success_ground_track_error_deadband_deg", 0.0)))
                            norm_deg = float(cfg.get("success_ground_track_error_norm_deg", 10.0))
                            if norm_deg <= 1.0e-6:
                                norm_deg = 10.0
                            p_deg = float(cfg.get("success_ground_track_error_power", 2.0))
                            p_deg = min(8.0, max(1.0, p_deg))
                            err_deg = track_err - dead_deg
                            if err_deg > 0.0:
                                x_deg = err_deg / norm_deg
                                clip_deg = float(cfg.get("success_ground_track_error_clip", 0.0))
                                if clip_deg > 0.0:
                                    x_deg = min(x_deg, clip_deg)
                                _add_reward_term("success_ground_track_error_penalty", success_track_w * (x_deg**p_deg))

                        _add_reward_term("objective_bonus", obj.get("reward", 1000.0))
                        terminated = True
                        # Convention: status[3] is a terminal outcome flag.
                        # -1.0 = failure (set by fail-fast blocks above)
                        # +1.0 = success
                        status[3] = 1.0
                        term_reason = "success_objective"
                    
        tracked_total = float(sum(rb.values())) if rb else 0.0
        rb["tracked_total"] = tracked_total
        rb["untracked"] = float(reward - tracked_total)
        rb["total"] = float(reward)
        self.last_reward_breakdown = rb
        if terminated:
            if term_reason == "running":
                try:
                    flag = float(status[3])
                except Exception:
                    flag = 0.0
                if flag > 0.5:
                    term_reason = "success"
                elif flag < -0.5:
                    term_reason = "failure_unknown"
                else:
                    term_reason = "terminated_unknown"
        elif truncated:
            term_reason = "timeout"
        else:
            term_reason = "running"
        self.last_termination_reason = term_reason

        return reward, terminated, truncated, status
