import json
import os
import math
import ef_py
import numpy as np
from python.scenario_compiler import (
    ApproachRewardConfig,
    CompiledScenario,
    LNavRuntimeConfig,
    SafetyRewardConfig,
    ScenarioCompiler,
    WaypointModeRewardConfig,
    _build_lnav_runtime_config,
    cache_runtime_waypoint_cache,
    _clone_runtime_mission_command,
    _clone_scenario_value,
    _normalize_runtime_mission_command,
    invalidate_runtime_waypoint_cache,
    materialize_runtime_waypoint_cache,
    rotate_ils_beacon_templates,
)
from python.scenario_runtime import apply_world_layout_to_kernel, prepare_scenario_world_layout
from python.rl.common_core_profile import normalize_task_order_spec
from python.rl.leader_tasking import RuleBasedLeaderPhaseManager, build_kernel_mission_command
from python.rl.mission_defs import is_landing_command_code

_LEGACY_EXECUTION_STEP_RUNTIME_MODES = {"legacy", "python", "off", "0", "false"}

_OBJECTIVE_PROPERTY_MAP = {
    "altitude": ef_py.ConditionalObjectiveProperty.Altitude,
    "altitude_agl": ef_py.ConditionalObjectiveProperty.AltitudeAGL,
    "speed": ef_py.ConditionalObjectiveProperty.Speed,
    "ground_speed": ef_py.ConditionalObjectiveProperty.GroundSpeed,
    "gear": ef_py.ConditionalObjectiveProperty.Gear,
    "heading_error_deg": ef_py.ConditionalObjectiveProperty.HeadingErrorDeg,
    "command_code": ef_py.ConditionalObjectiveProperty.CommandCode,
    "ground_track_error_deg": ef_py.ConditionalObjectiveProperty.GroundTrackErrorDeg,
    "runway_cross_abs_m": ef_py.ConditionalObjectiveProperty.RunwayCrossAbsM,
    "runway_from_threshold_m": ef_py.ConditionalObjectiveProperty.RunwayFromThresholdM,
    "on_runway_geom": ef_py.ConditionalObjectiveProperty.OnRunwayGeom,
    "on_runway": ef_py.ConditionalObjectiveProperty.OnRunway,
    "on_ground": ef_py.ConditionalObjectiveProperty.OnGround,
    "sink_rate_abs_mps": ef_py.ConditionalObjectiveProperty.SinkRateAbsMps,
    "vertical_speed_abs_mps": ef_py.ConditionalObjectiveProperty.SinkRateAbsMps,
    "ils_localizer_abs": ef_py.ConditionalObjectiveProperty.IlsLocalizerAbs,
    "ils_glideslope_abs": ef_py.ConditionalObjectiveProperty.IlsGlideslopeAbs,
    "dme_m": ef_py.ConditionalObjectiveProperty.DmeM,
    "heading": ef_py.ConditionalObjectiveProperty.Heading,
    "x": ef_py.ConditionalObjectiveProperty.X,
    "y": ef_py.ConditionalObjectiveProperty.Y,
}

_OBJECTIVE_OP_MAP = {
    ">=": ef_py.ConditionalObjectiveOp.GreaterEqual,
    ">": ef_py.ConditionalObjectiveOp.GreaterThan,
    "<=": ef_py.ConditionalObjectiveOp.LessEqual,
    "<": ef_py.ConditionalObjectiveOp.LessThan,
}

_OBJECTIVE_DYNAMIC_TARGET_MAP = {
    "CMD_ALT": (ef_py.ConditionalObjectiveTargetKind.CommandAltitude, 0.95),
    "CMD_ALTITUDE": (ef_py.ConditionalObjectiveTargetKind.CommandAltitude, 0.95),
    "CMD_SPEED": (ef_py.ConditionalObjectiveTargetKind.CommandSpeed, 0.90),
    "CMD_HDG": (ef_py.ConditionalObjectiveTargetKind.CommandHeading, 1.0),
    "CMD_HEADING": (ef_py.ConditionalObjectiveTargetKind.CommandHeading, 1.0),
}


def _coerce_nonnegative_int(value, default: int = 0) -> int:
    try:
        out = int(value)
    except Exception:
        return int(default)
    return out if out >= 0 else int(default)


def normalize_execution_step_runtime_mode(mode: str | None) -> str:
    raw_mode = os.environ.get("CMO_EXECUTION_STEP_RUNTIME", "compiled") if mode is None else mode
    normalized = str(raw_mode).strip().lower()
    if normalized in _LEGACY_EXECUTION_STEP_RUNTIME_MODES:
        return "legacy"
    if normalized in {"", "compiled", "on", "1", "true"}:
        return "compiled"
    return normalized


def execution_step_runtime_mode_enabled(mode: str | None) -> bool:
    return normalize_execution_step_runtime_mode(mode) != "legacy"


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
        self._spatial_geometry = None
        self._compiled_scenario = None
        self._compiled_runtime_metadata = None
        self._scenario_source_path = None
        self._compiled_conditional_objectives = []
        self._objective_shaping_cfg = ef_py.ObjectiveShapingConfig()
        self._compiled_rewards_cfg: dict = {}
        self._waypoint_mode_reward_cfgs: dict[str, WaypointModeRewardConfig] = {}
        self._approach_reward_cfg = ApproachRewardConfig()
        self._safety_reward_cfg = SafetyRewardConfig()
        self._lnav_runtime_cfg = LNavRuntimeConfig()
        self._cached_route_ref_id: int | None = None
        self._runtime_eval_cache: dict[str, object] = {}
        self.set_execution_step_runtime_mode(None)

    def set_execution_step_runtime_mode(self, mode: str | None) -> None:
        self.execution_step_runtime_mode = normalize_execution_step_runtime_mode(mode)
        self.use_compiled_execution_step_runtime = execution_step_runtime_mode_enabled(self.execution_step_runtime_mode)

    def reset_runtime_eval_cache(self) -> None:
        self._runtime_eval_cache = {}

    def _task_order_spec(self) -> dict:
        task_cfg = self.scenario_data.get("task_order", None)
        return normalize_task_order_spec(task_cfg if isinstance(task_cfg, dict) else {})

    def _normalize_mission_command_dict(self, cmd: dict | None) -> dict:
        return _normalize_runtime_mission_command(cmd, self._task_order_spec())

    def _align_task_only_mission_shell_with_task_order(self) -> None:
        if not isinstance(self.mission_cmd, dict):
            return
        if list(self.mission_cmd.get("waypoints", []) or []):
            return
        try:
            command_code = int(self.mission_cmd.get("command_code", 0))
        except Exception:
            command_code = 0
        if command_code not in (0, 1, 2):
            return
        task_cfg = self._task_order_spec()
        if not isinstance(task_cfg, dict) or not task_cfg:
            return
        if "target_altitude_m" in task_cfg:
            try:
                self.mission_cmd["target_altitude"] = float(task_cfg.get("target_altitude_m", self.mission_cmd.get("target_altitude", 0.0)))
            except Exception:
                pass
        if "target_speed_mps" in task_cfg:
            try:
                self.mission_cmd["target_speed"] = float(task_cfg.get("target_speed_mps", self.mission_cmd.get("target_speed", 0.0)))
            except Exception:
                pass

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

        spawn = None
        runtime_spawn = self.scenario_data.get("_runtime_agent_spawn", None)
        if isinstance(runtime_spawn, dict):
            spawn = runtime_spawn
        else:
            entities = self.scenario_data.get("entities", [])
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
        compiled = ScenarioCompiler.compile_path(json_path)
        return self.load_compiled_scenario(compiled, seed=seed)

    def load_compiled_scenario(self, compiled_scenario: CompiledScenario, seed=42):
        if not isinstance(compiled_scenario, CompiledScenario):
            raise TypeError("compiled_scenario must be a CompiledScenario")
        self._compiled_scenario = compiled_scenario
        self._compiled_runtime_metadata = compiled_scenario.runtime_metadata
        self._scenario_source_path = compiled_scenario.source_path
        self.scenario_data = compiled_scenario.instantiate_runtime()
        return self._load_instantiated_scenario(seed=seed)

    def load_scenario_data(self, scenario_data: dict, seed=42, *, source_path: str | None = None):
        compiled = ScenarioCompiler.compile_data(scenario_data, source_path=source_path)
        return self.load_compiled_scenario(compiled, seed=seed)

    def _prepare_load_seed(self, seed=42) -> int:
        if seed is None:
            seed = np.random.randint(0, 2**32 - 1)
        seed = int(seed) & 0xFFFFFFFF
        self.rng = np.random.RandomState(seed)
        return seed

    def _begin_loaded_world(self, *, scenario_data: dict) -> None:
        if self._compiled_runtime_metadata is None and isinstance(self._compiled_scenario, CompiledScenario):
            self._compiled_runtime_metadata = self._compiled_scenario.runtime_metadata
        self.scenario_data = scenario_data
        self._cached_route_ref_id = None
        mission_cmd = self.scenario_data.get("mission_command", None)
        if not isinstance(mission_cmd, dict) and self._compiled_runtime_metadata is not None:
            mission_cmd = _clone_runtime_mission_command(self._compiled_runtime_metadata.mission_command_template)
            self.scenario_data["mission_command"] = mission_cmd
        self.mission_cmd = mission_cmd if isinstance(mission_cmd, dict) else {
            "command_code": 0,
            "target_heading": 0.0,
            "target_altitude": 0.0,
            "target_speed": 0.0,
        }

    def _apply_compiled_runtime_metadata(self) -> None:
        metadata = self._compiled_runtime_metadata
        if metadata is None:
            self._compiled_conditional_objectives = self._compile_conditional_objectives()
            self._objective_shaping_cfg = self._build_objective_shaping_config(self.scenario_data.get("rewards", {}))
            self._compiled_rewards_cfg = self.scenario_data.get("rewards", {})
            self._waypoint_mode_reward_cfgs = {}
            self._approach_reward_cfg = ApproachRewardConfig()
            self._safety_reward_cfg = SafetyRewardConfig()
            self._lnav_runtime_cfg = LNavRuntimeConfig()
            return
        self._compiled_conditional_objectives = list(metadata.compiled_conditional_objectives)
        self._objective_shaping_cfg = metadata.objective_shaping_cfg
        self._compiled_rewards_cfg = dict(metadata.rewards_config)
        self._waypoint_mode_reward_cfgs = dict(metadata.waypoint_mode_configs)
        self._approach_reward_cfg = metadata.approach_reward_config
        self._safety_reward_cfg = metadata.safety_reward_config
        self._lnav_runtime_cfg = metadata.lnav_config

    def _finalize_loaded_world(self, *, initial_truth=None, initial_inst=None, sync_to_kernel: bool = True):
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
        task_cfg = self._task_order_spec()
        if isinstance(self.scenario_data, dict):
            self.scenario_data["task_order"] = dict(task_cfg)
        self._align_task_only_mission_shell_with_task_order()
        self.mission_cmd = _normalize_runtime_mission_command(self.mission_cmd, task_cfg)
        materialize_runtime_waypoint_cache(self.mission_cmd)
        self.scenario_data["mission_command"] = self.mission_cmd
        self._cached_route_ref_id = None
        self._apply_compiled_runtime_metadata()
        self._lnav_runtime_cfg = _build_lnav_runtime_config(self.mission_cmd)

        post_transition_cfg = self.mission_cmd.get("post_waypoint_transition", None)
        if isinstance(post_transition_cfg, dict) and post_transition_cfg:
            self.post_waypoint_transition = _clone_runtime_mission_command(post_transition_cfg)

        if self.rotate_mission_heading_with_world and self.world_yaw_deg != 0.0:
            try:
                self.mission_cmd["target_heading"] = float(self.mission_cmd.get("target_heading", 0.0)) + float(self.world_yaw_deg)
            except Exception:
                pass
            self.mission_cmd["target_heading"] = float(self.mission_cmd.get("target_heading", 0.0)) % 360.0

        self._parse_waypoints()

        if self.agent_id is not None:
            truth = initial_truth if initial_truth is not None else self.sim.get_agent_observation(self.agent_id)
            self.prev_alt = truth.z
            self._waypoint_leg_origin_x = float(getattr(truth, "x", 0.0))
            self._waypoint_leg_origin_y = float(getattr(truth, "y", 0.0))
            try:
                inst0 = initial_inst if initial_inst is not None else self.sim.get_instrument_state(self.agent_id)
                self.prev_speed = float(inst0.ias)
            except Exception:
                self.prev_speed = truth.speed
        if self._compiled_runtime_metadata is not None:
            self.ils_beacons = rotate_ils_beacon_templates(
                self._compiled_runtime_metadata.ils_beacon_templates,
                yaw_deg=float(self.world_yaw_deg),
                origin_x=float(self.world_yaw_origin_x),
                origin_y=float(self.world_yaw_origin_y),
            )
        else:
            self.ils_beacons = self._extract_ils_beacons()
        self._rebuild_spatial_geometry()
        self._apply_waypoint_guidance_update(truth=initial_truth, inst=initial_inst)
        self._reset_command_chain(
            initial_truth=initial_truth,
            initial_inst=initial_inst,
            sync_to_kernel=False,
        )
        if sync_to_kernel:
            self._sync_kernel_mission_command()
            self._sync_kernel_command_chain()
        return self.agent_id

    def load_prepared_world(
        self,
        prepared_world,
        *,
        seed=42,
        initial_truth=None,
        initial_inst=None,
        sync_to_kernel: bool = True,
    ):
        seed = self._prepare_load_seed(seed)
        layout = prepared_world.layout
        self._begin_loaded_world(scenario_data=layout.scenario_data)
        self.rotate_mission_heading_with_world = bool(layout.rotate_mission_heading_with_world)
        self.world_yaw_deg = float(layout.world_yaw_deg)
        self.world_yaw_origin_x = float(layout.world_yaw_origin_x)
        self.world_yaw_origin_y = float(layout.world_yaw_origin_y)
        self.entities = dict(prepared_world.entities)
        self.agent_id = prepared_world.agent_id
        _ = seed
        return self._finalize_loaded_world(
            initial_truth=initial_truth,
            initial_inst=initial_inst,
            sync_to_kernel=sync_to_kernel,
        )

    def _load_instantiated_scenario(self, seed=42):
        seed = self._prepare_load_seed(seed)
        self._begin_loaded_world(scenario_data=self.scenario_data)

        world_layout = prepare_scenario_world_layout(
            self.scenario_data,
            seed=seed,
            rng=self.rng,
            randomization_overrides=self.randomization_overrides,
        )
        self.scenario_data = world_layout.scenario_data
        self.rotate_mission_heading_with_world = bool(world_layout.rotate_mission_heading_with_world)
        self.world_yaw_deg = float(world_layout.world_yaw_deg)
        self.world_yaw_origin_x = float(world_layout.world_yaw_origin_x)
        self.world_yaw_origin_y = float(world_layout.world_yaw_origin_y)
        applied_world = apply_world_layout_to_kernel(self.sim, world_layout)
        self.entities = dict(applied_world.entities)
        self.agent_id = applied_world.agent_id
        initial_truth = None
        initial_inst = None
        if self.agent_id is not None:
            try:
                initial_truth = self.sim.get_agent_observation(self.agent_id)
            except Exception:
                initial_truth = None
            try:
                initial_inst = self.sim.get_instrument_state(self.agent_id)
            except Exception:
                initial_inst = None
        return self._finalize_loaded_world(
            initial_truth=initial_truth,
            initial_inst=initial_inst,
            sync_to_kernel=True,
        )

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

    def _rebuild_spatial_geometry(self) -> None:
        if not hasattr(ef_py, "CompiledScenarioGeometry"):
            self._spatial_geometry = None
            return

        geom = ef_py.CompiledScenarioGeometry()

        for idx, beacon in enumerate(self.ils_beacons or []):
            runway = ef_py.SpatialRunwayDefinition()
            runway.runway_id = int(beacon.get("runway_id", idx))
            runway.name = str(beacon.get("name", f"Runway_{idx}"))
            runway.center_x_m = float(beacon.get("cx", 0.0))
            runway.center_y_m = float(beacon.get("cy", 0.0))
            runway.threshold_x_m = float(beacon.get("thr_x", 0.0))
            runway.threshold_y_m = float(beacon.get("thr_y", 0.0))
            runway.heading_deg = float(beacon.get("heading", 0.0))
            runway.length_m = float(beacon.get("length", 0.0))
            runway.width_m = float(beacon.get("width", 0.0))
            runway.elevation_m = float(beacon.get("elev_m", 0.0))
            runway.glide_slope_deg = float(beacon.get("glide_slope_deg", 3.0))
            runway.localizer_max_deg = float(beacon.get("loc_max_deg", 10.0))
            runway.glideslope_max_deg = float(beacon.get("gs_max_deg", 3.0))
            runway.range_m = float(beacon.get("range_m", 30000.0))
            geom.add_runway(runway)

        geom.set_route_leg_origin(
            float(getattr(self, "_waypoint_leg_origin_x", 0.0)),
            float(getattr(self, "_waypoint_leg_origin_y", 0.0)),
        )
        for wp in self.waypoints:
            waypoint = ef_py.SpatialRouteWaypoint()
            waypoint.x_m = float(wp.get("x", 0.0))
            waypoint.y_m = float(wp.get("y", 0.0))
            waypoint.z_m = float(wp.get("z", 0.0))
            waypoint.radius_m = float(wp.get("radius_m", self.mission_cmd.get("waypoint_radius_m", 500.0)))
            waypoint.altitude_m = float(wp.get("altitude_m", waypoint.z_m))
            waypoint.speed_mps = float(wp.get("speed_mps", self.mission_cmd.get("target_speed", 0.0)))
            waypoint.waypoint_mode = str(
                self._normalize_waypoint_mode(wp.get("waypoint_mode", self.mission_cmd.get("waypoint_mode", "flyby")))
            )
            geom.add_route_waypoint(waypoint)

        self._spatial_geometry = geom

    def _query_route_guidance_result(self, truth=None, inst=None):
        if self._spatial_geometry is None or not self.waypoints or self.agent_id is None:
            return None
        try:
            cmd_code = int(self.mission_cmd.get("command_code", 0))
        except Exception:
            cmd_code = 0
        if cmd_code != 3:
            return None

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

        speed_mps = float(getattr(truth, "speed", 0.0))
        if inst is not None:
            try:
                ias = float(getattr(inst, "ias", speed_mps))
                if math.isfinite(ias) and ias > 1.0:
                    speed_mps = ias
            except Exception:
                pass
        cache_key = (
            int(cmd_code),
            int(np.clip(int(getattr(self, "waypoint_idx", 0)), 0, max(0, len(self.waypoints) - 1))),
            float(getattr(truth, "x", 0.0)),
            float(getattr(truth, "y", 0.0)),
            float(speed_mps),
        )
        cache = getattr(self, "_runtime_eval_cache", None)
        if isinstance(cache, dict) and cache.get("route_guidance_key") == cache_key:
            cached_result = cache.get("route_guidance_result")
            return cached_result if cached_result is not None else None

        opts = ef_py.SpatialRouteQueryOptions()
        opts.waypoint_index = int(cache_key[1])
        opts.own_x_m = float(getattr(truth, "x", 0.0))
        opts.own_y_m = float(getattr(truth, "y", 0.0))
        opts.own_speed_mps = float(speed_mps)
        lnav_cfg = self._lnav_runtime_cfg
        opts.base_lookahead_m = float(lnav_cfg.lookahead_m)
        opts.lnav_max_intercept_deg = float(lnav_cfg.max_intercept_deg)
        opts.lnav_capture_max_intercept_deg = float(lnav_cfg.capture_max_intercept_deg)
        opts.lnav_capture_xtrack_m = float(lnav_cfg.capture_xtrack_m)
        opts.lnav_capture_course_error_deg = float(lnav_cfg.capture_course_error_deg)
        opts.lnav_direct_to_final_fix = bool(lnav_cfg.direct_to_final_fix)
        opts.lnav_flyover_capture_window_m = (
            0.0 if lnav_cfg.flyover_capture_window_m is None else float(lnav_cfg.flyover_capture_window_m)
        )
        opts.lnav_bank_limit_deg = float(lnav_cfg.bank_limit_deg)
        opts.lnav_sequence_gate_scale = float(lnav_cfg.sequence_gate_scale)
        opts.lnav_sequence_gate_min_m = (
            0.0 if lnav_cfg.sequence_gate_min_m is None else float(lnav_cfg.sequence_gate_min_m)
        )
        opts.lnav_sequence_gate_max_m = (
            0.0 if lnav_cfg.sequence_gate_max_m is None else float(lnav_cfg.sequence_gate_max_m)
        )

        result = self._spatial_geometry.query_route_guidance(opts)
        out = result if bool(getattr(result, "valid", False)) else None
        if isinstance(cache, dict):
            cache["route_guidance_key"] = cache_key
            cache["route_guidance_result"] = out
        return out

    def _query_runway_frame_result(self, x_m: float, y_m: float):
        if self._spatial_geometry is None:
            return None
        cache_key = (float(x_m), float(y_m))
        cache = getattr(self, "_runtime_eval_cache", None)
        if isinstance(cache, dict) and cache.get("runway_frame_key") == cache_key:
            cached_result = cache.get("runway_frame_result")
            return cached_result if cached_result is not None else None
        frame = self._spatial_geometry.query_runway_local_frame(float(x_m), float(y_m))
        out = frame if bool(getattr(frame, "valid", False)) else None
        if isinstance(cache, dict):
            cache["runway_frame_key"] = cache_key
            cache["runway_frame_result"] = out
        return out

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
        frame = self._query_runway_frame_result(float(x_m), float(y_m))
        if frame is None:
            return False, 0.0, 0.0, 0.0, 0.0
        return (
            bool(frame.valid),
            float(frame.along_m),
            float(frame.cross_m),
            float(frame.length_m),
            float(frame.width_m),
        )

    def get_ils_observation(self, x_m: float, y_m: float, alt_m: float):
        """
        Returns a small navigation observation vector:
        [ils_valid, loc_dev, gs_dev, dme_m]

        - loc_dev, gs_dev are normalized to [-1, 1] using the configured max deflections.
        - dme_m is slant-range distance to the threshold reference point.
        - For landing tasks, glideslope is referenced to a threshold-crossing-height
          point above the runway threshold rather than the threshold pavement itself.
        """
        if self._spatial_geometry is None:
            return np.zeros((4,), dtype=np.float32)
        try:
            threshold_crossing_height_m = max(
                0.0,
                float(getattr(self, "mission_cmd", {}).get("threshold_crossing_height_m", 0.0)),
            )
        except Exception:
            threshold_crossing_height_m = 0.0
        ils = self._spatial_geometry.query_ils(float(x_m), float(y_m), float(alt_m), float(threshold_crossing_height_m))
        return np.array(
            [
                1.0 if bool(ils.valid) else 0.0,
                float(ils.loc_dev),
                float(ils.gs_dev),
                float(ils.dme_m),
            ],
            dtype=np.float32,
        )

    def _randomize_mission(self):
        """Randomize mission parameters if ranges are specified in config."""
        # Use seeded RNG (self.rng) instead of global
        base_cmd = self.scenario_data.get("mission_command", {})

        # Check for randomization config
        rand_cfg = base_cmd.get("randomization", {})
        compiled_waypoint_templates = ()
        compiled_waypoint_template_route_ref_ids = ()
        if self._compiled_runtime_metadata is not None:
            compiled_waypoint_templates = tuple(getattr(self._compiled_runtime_metadata, "normalized_waypoint_templates", ()))
            compiled_waypoint_template_route_ref_ids = tuple(
                getattr(self._compiled_runtime_metadata, "waypoint_template_route_ref_ids", ())
            )

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
                invalidate_runtime_waypoint_cache(self.mission_cmd)
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
                precompiled = compiled_waypoint_templates[idx] if idx < len(compiled_waypoint_templates) else ()
                if precompiled:
                    waypoints = _clone_scenario_value(list(precompiled))
                    self._rotate_waypoints_inplace(waypoints)
                    self.mission_cmd["waypoints"] = _clone_scenario_value(waypoints)
                    route_ref_id = (
                        int(compiled_waypoint_template_route_ref_ids[idx])
                        if idx < len(compiled_waypoint_template_route_ref_ids)
                        else 0
                    )
                    cache_runtime_waypoint_cache(self.mission_cmd, waypoints, route_ref_id=route_ref_id)
                else:
                    waypoints = _clone_scenario_value(chosen)
                    self._rotate_waypoints_inplace(waypoints)
                    self.mission_cmd["waypoints"] = waypoints
                    invalidate_runtime_waypoint_cache(self.mission_cmd)
                self.mission_cmd["_waypoint_template_idx"] = int(idx)
                self.mission_cmd["_route_generator_used"] = False

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

        def _waypoint_anchor_from_mission():
            raw_index = rand_cfg.get("anchor_from_waypoint_index", None)
            if raw_index is None:
                return None
            waypoints = list(self.mission_cmd.get("waypoints", []) or [])
            if not waypoints:
                return None
            if isinstance(raw_index, str) and str(raw_index).strip().lower() == "midpoint":
                idx = len(waypoints) // 2
            else:
                try:
                    idx = int(raw_index)
                except Exception:
                    return None
                if idx < 0:
                    idx += len(waypoints)
            if idx < 0 or idx >= len(waypoints):
                return None
            wp = waypoints[idx]
            if not isinstance(wp, dict):
                return None
            try:
                anchor_x = float(wp.get("x", 0.0))
                anchor_y = float(wp.get("y", 0.0))
                anchor_z = float(wp.get("z", wp.get("altitude_m", task_cfg.get("anchor_z_m", task_cfg.get("target_altitude_m", 0.0)))))
            except Exception:
                return None
            return idx, anchor_x, anchor_y, anchor_z

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

        waypoint_anchor = _waypoint_anchor_from_mission()
        if waypoint_anchor is not None:
            anchor_idx, anchor_x, anchor_y, anchor_z = waypoint_anchor
            task_cfg["anchor_x_m"] = float(anchor_x)
            task_cfg["anchor_y_m"] = float(anchor_y)
            task_cfg["anchor_z_m"] = float(anchor_z)
            task_cfg["_anchor_waypoint_idx"] = int(anchor_idx)

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
        self._cached_route_ref_id = None

        mc = self.scenario_data.get("mission_command", None)
        if not isinstance(mc, dict):
            return
        cached_waypoints = mc.get("_normalized_waypoints", None)
        if isinstance(cached_waypoints, list):
            self.waypoints = _clone_scenario_value(cached_waypoints)
            route_ref_id = _coerce_nonnegative_int(mc.get("route_ref_id", 0), 0)
            self._cached_route_ref_id = int(route_ref_id) if route_ref_id > 0 else None
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
        materialize_runtime_waypoint_cache(mc)
        route_ref_id = _coerce_nonnegative_int(mc.get("route_ref_id", 0), 0)
        self._cached_route_ref_id = int(route_ref_id) if route_ref_id > 0 else None
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

        gstate = self._compute_waypoint_guidance_state(truth=truth, inst=inst)
        dist_m = float(math.hypot(float(wp.get("x", 0.0)) - float(getattr(truth, "x", 0.0)), float(wp.get("y", 0.0)) - float(getattr(truth, "y", 0.0))))
        rad = max(1.0, float(wp.get("radius_m", self.mission_cmd.get("waypoint_radius_m", 500.0))))
        if isinstance(gstate, dict) and int(gstate.get("idx", -1)) == idx:
            mode = str(gstate.get("waypoint_mode", mode))
            dist_m = float(gstate.get("dist_m", dist_m))
            rad = max(1.0, float(gstate.get("waypoint_radius_m", rad)))

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

        if gstate is None:
            return out

        out["sequence_gate_m"] = float(gstate.get("sequence_gate_m", rad))
        out["turn_lead_m"] = float(gstate.get("lead_turn_m", 0.0))
        out["cross_track_m"] = float(gstate.get("reward_xtk_m", 0.0))
        out["distance_to_turn_m"] = float(
            gstate.get("distance_to_turn_m", gstate.get("reward_dtg_m", dist_m))
        )
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

    @staticmethod
    def _instrument_scalar(inst, attr_name: str, index: int | None = None, default: float = float("nan")) -> float:
        if inst is None:
            return float(default)
        try:
            value = float(getattr(inst, attr_name))
            if math.isfinite(value):
                return value
        except Exception:
            pass
        if index is not None:
            try:
                value = float(inst[index])
                if math.isfinite(value):
                    return value
            except Exception:
                pass
        return float(default)

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

        ground_track = self._instrument_scalar(inst, "ground_track", 30)
        return float(
            ef_py.compute_command_tracking_error_deg(
                float(tgt),
                float(truth_heading_deg),
                int(cmd_code),
                float(ground_track),
            )
        )

    @staticmethod
    def _ground_track_from_inst(inst, fallback_heading_deg: float) -> float:
        ground_track = ScenarioLoader._instrument_scalar(inst, "ground_track", 30)
        return float(ef_py.resolve_ground_track_deg(float(fallback_heading_deg), float(ground_track)))

    def _mission_nav_inputs(self, truth, inst, route_result):
        if route_result is None or not bool(getattr(route_result, "valid", False)):
            return None
        idx = int(getattr(route_result, "idx", -1))
        if idx < 0 or idx >= len(self.waypoints):
            return None

        wp = self.waypoints[idx]
        inputs = ef_py.MissionNavInputs()
        inputs.own_altitude_m = float(getattr(truth, "z", 0.0))
        inputs.truth_heading_deg = float(getattr(truth, "heading", 0.0))
        inputs.truth_speed_mps = float(getattr(truth, "speed", 0.0))
        inputs.inst_heading_deg = float("nan")
        inputs.inst_ground_track_deg = float("nan")
        inputs.inst_ias_mps = float("nan")
        if inst is not None:
            inputs.inst_heading_deg = self._instrument_scalar(inst, "heading", 9)
            inputs.inst_ground_track_deg = self._instrument_scalar(inst, "ground_track", 30)
            inputs.inst_ias_mps = self._instrument_scalar(inst, "ias", 0)
        inputs.waypoint_altitude_m = float(wp.get("altitude_m", wp.get("z", 0.0)))
        inputs.cdi_full_scale_m = float(self._lnav_runtime_cfg.cdi_full_scale_m)
        return inputs

    def _build_mission_nav_products(self, route_result, truth, inst):
        inputs = self._mission_nav_inputs(truth, inst, route_result)
        if inputs is None:
            return None
        products = ef_py.compute_waypoint_mission_nav(route_result, inputs)
        if not bool(getattr(products, "valid", False)):
            return None
        return {
            "active_wp_idx": float(products.active_wp_idx),
            "total_wps": float(products.total_wps),
            "selected_steerpoint": float(products.selected_steerpoint),
            "steerpoint_mode_code": float(products.steerpoint_mode_code),
            "dist_m": float(products.dist_m),
            "xtk_m": float(products.xtk_m),
            "dtg_m": float(products.dtg_m),
            "direct_bearing_deg": float(products.direct_bearing_deg),
            "desired_leg_track_deg": float(products.desired_leg_track_deg),
            "bearing_rel_deg": float(products.bearing_rel_deg),
            "altitude_delta_m": float(products.altitude_delta_m),
            "cdi_norm": float(products.cdi_norm),
            "track_angle_error_deg": float(products.track_angle_error_deg),
            "next_turn_deg": float(products.next_turn_deg),
            "distance_to_turn_m": float(products.distance_to_turn_m),
        }

    @staticmethod
    def _mission_observation_mode_code(mode: str) -> int:
        mode_norm = str(mode).strip().lower()
        if mode_norm in ("", "basic"):
            return 0
        if mode_norm == "nav_v1":
            return 1
        if mode_norm == "nav_v2":
            return 2
        raise ValueError(f"Unknown mission observation mode: {mode}")

    def _build_mission_observation_runtime_inputs(self, mode: str, *, truth=None, inst=None):
        inputs = ef_py.MissionObservationInputs()
        inputs.mode_code = int(self._mission_observation_mode_code(mode))
        inputs.command_code = float(self.mission_cmd["command_code"])
        inputs.target_heading_deg = float(self.mission_cmd["target_heading"])
        inputs.target_altitude_m = float(self.mission_cmd["target_altitude"])
        inputs.target_speed_mps = float(self.mission_cmd["target_speed"])

        if int(inputs.mode_code) == 0:
            return inputs

        if truth is None:
            try:
                truth = self.sim.get_agent_observation(self.agent_id)
            except Exception:
                truth = None
        if inst is None:
            try:
                inst = self.sim.get_instrument_state(self.agent_id)
            except Exception:
                inst = None
        if truth is not None:
            route_result = self._query_route_guidance_result(truth=truth, inst=inst)
            if route_result is not None:
                nav_inputs = self._mission_nav_inputs(truth, inst, route_result)
                if nav_inputs is not None:
                    inputs.has_route_guidance = True
                    inputs.route_guidance = route_result
                    inputs.nav_inputs = nav_inputs
        return inputs

    def _compiled_mission_observation_enabled(self) -> bool:
        return bool(getattr(self, "use_compiled_execution_step_runtime", True)) and hasattr(
            ef_py, "MissionObservationInputs"
        ) and hasattr(ef_py, "compute_mission_observation")

    def _compute_mission_observation_products(self, mode: str, *, truth=None, inst=None):
        inputs = self._build_mission_observation_runtime_inputs(mode, truth=truth, inst=inst)
        return ef_py.compute_mission_observation(inputs)

    def _build_step_info_runtime_inputs(self, *, inst_now=None, truth_now=None, runway_frame=None):
        inputs = ef_py.StepInfoInputs()
        if inst_now is None:
            inst_now = self.sim.get_instrument_state(self.agent_id)
        inputs.on_runway = bool(getattr(inst_now, "on_runway", True))
        inputs.gear_collapsed = bool(getattr(inst_now, "gear_collapsed", False))
        inputs.gear_stress = float(getattr(inst_now, "gear_stress", 0.0))
        inputs.alt_agl_m = float(getattr(inst_now, "alt_radar", 0.0))

        cfg = self.get_rewards_config()
        inputs.on_ground_alt_threshold_m = float(cfg.get("on_ground_alt_threshold", 2.5))
        inputs.airborne_alt_threshold_m = float(
            cfg.get("airborne_alt_threshold", cfg.get("liftoff_alt_threshold", 5.0))
        )
        inputs.runway_width_margin_m = float(cfg.get("runway_width_margin_m", 2.0))
        inputs.runway_length_margin_m = float(cfg.get("runway_length_margin_m", 0.0))

        if runway_frame is None and truth_now is None:
            truth_now = self.sim.get_agent_observation(self.agent_id)
        if runway_frame is None and self._spatial_geometry is not None and truth_now is not None:
            runway_frame = self._query_runway_frame_result(float(truth_now.x), float(truth_now.y))
        if runway_frame is not None and bool(getattr(runway_frame, "valid", False)):
            inputs.has_runway_frame = True
            inputs.runway_frame = runway_frame
        return inputs

    def _compiled_step_info_enabled(self) -> bool:
        return bool(getattr(self, "use_compiled_execution_step_runtime", True)) and hasattr(
            ef_py, "StepInfoInputs"
        ) and hasattr(ef_py, "compute_step_info_runtime")

    def _compute_step_info_runtime_products(self, *, inst_now=None, truth_now=None):
        cached = self._get_cached_step_evaluation(truth=truth_now, inst_obj=inst_now)
        if isinstance(cached, dict):
            frame_products = cached.get("frame_products")
            if frame_products is not None and bool(getattr(frame_products, "step_info_evaluated", False)):
                return frame_products.step_info
        inputs = self._build_step_info_runtime_inputs(inst_now=inst_now, truth_now=truth_now)
        return ef_py.compute_step_info_runtime(inputs)

    def _build_flight_shaping_runtime_inputs(
        self,
        cfg: dict,
        *,
        steps: int,
        truth,
        inst_vec,
        curr_ias: float,
        curr_alt_agl: float,
        curr_gear: float,
        curr_roll: float,
        heading_error_deg: float,
        ground_track_error_deg: float,
        waypoint_turn_relief_activation: float,
        preliftoff: bool,
        on_runway_task: bool,
        airborne: bool,
        runway_cross_m,
        runway_wid_m,
        ils_valid: float,
        ils_loc: float,
    ):
        inputs = ef_py.FlightShapingRuntimeInputs()
        inputs.truth_altitude_m = float(getattr(truth, "z", 0.0))
        inputs.truth_speed_mps = float(getattr(truth, "speed", 0.0))
        inputs.prev_altitude_m = float(getattr(self, "prev_alt", 0.0))
        inputs.prev_ias_mps = float(getattr(self, "prev_speed", 0.0))
        inputs.curr_ias_mps = float(curr_ias)
        inputs.curr_alt_baro_m = float(inst_vec[2]) if len(inst_vec) > 2 else float(getattr(truth, "z", 0.0))
        inputs.curr_alt_agl_m = float(curr_alt_agl)
        inputs.curr_gear_fraction = float(curr_gear)
        inputs.curr_roll_deg = float(curr_roll)
        inputs.curr_pitch_deg = float(inst_vec[7]) if len(inst_vec) > 7 else 0.0
        inputs.curr_beta_deg = float(inst_vec[6]) if len(inst_vec) > 6 else 0.0
        inputs.curr_yaw_rate_deg_s = float(inst_vec[14]) if len(inst_vec) > 14 else 0.0
        inputs.curr_g_load = float(inst_vec[10]) if len(inst_vec) > 10 else 1.0
        inputs.step_count = int(steps)
        inputs.target_altitude_m = float(cfg.get("altitude_progress_target", self.mission_cmd.get("target_altitude", 0.0)) or 0.0)
        inputs.target_speed_mps = float(cfg.get("speed_progress_target", self.mission_cmd.get("target_speed", 180.0)) or 0.0)
        inputs.heading_error_deg = float(heading_error_deg)
        inputs.ground_track_error_deg = float(ground_track_error_deg)
        inputs.waypoint_turn_relief_activation = float(waypoint_turn_relief_activation)
        inputs.preliftoff = bool(preliftoff)
        inputs.on_runway_task = bool(on_runway_task)
        inputs.airborne = bool(airborne)
        inputs.has_runway_cross_m = runway_cross_m is not None and runway_wid_m is not None
        if inputs.has_runway_cross_m:
            inputs.runway_cross_m = float(runway_cross_m)
            inputs.runway_width_m = float(runway_wid_m)
        inputs.ils_valid = bool(float(ils_valid) > 0.5)
        inputs.ils_loc_dev = float(ils_loc)
        inputs.liftoff_awarded = bool(getattr(self, "liftoff_awarded", False))
        inputs.gear_bonus_awarded = bool(getattr(self, "gear_bonus_awarded", False))

        inputs.altitude_progress_weight = float(cfg.get("altitude_progress_weight", 0.0))
        inputs.speed_progress_weight = float(cfg.get("speed_progress_weight", 0.0))
        inputs.speed_progress_negative_weight = float(cfg.get("speed_progress_weight_negative", 0.0))
        inputs.stationary_penalty = float(cfg.get("stationary_penalty", 0.0))
        inputs.stationary_grace_steps = int(cfg.get("stationary_grace_steps", 20))
        inputs.stationary_speed_threshold_mps = float(cfg.get("stationary_speed_threshold", 5.0))
        inputs.stationary_alt_threshold_m = float(cfg.get("stationary_alt_threshold", 5.0))
        inputs.liftoff_bonus = float(cfg.get("liftoff_bonus", 0.0))
        inputs.liftoff_speed_threshold_mps = float(cfg.get("liftoff_speed_threshold", 80.0))
        inputs.liftoff_alt_threshold_m = float(cfg.get("liftoff_alt_threshold", 5.0))
        inputs.rotation_reward_weight = float(cfg.get("rotation_reward_weight", 0.0))
        inputs.rotation_speed_threshold_mps = float(cfg.get("rotation_speed_threshold", 80.0))
        inputs.rotation_alt_threshold_m = float(cfg.get("rotation_alt_threshold", 5.0))
        inputs.rotation_pitch_cap_deg = float(cfg.get("rotation_pitch_cap", 15.0))
        inputs.rotation_overpitch_penalty_weight = float(cfg.get("rotation_overpitch_penalty_weight", 0.0))
        inputs.gear_up_bonus = float(cfg.get("gear_up_bonus", 0.0))
        inputs.gear_up_bonus_min_alt_agl_m = 50.0
        inputs.roll_stability_weight = float(cfg.get("roll_stability_weight", 0.0))
        inputs.heading_error_weight = float(cfg.get("heading_error_weight", 0.0))
        inputs.heading_hold_deadband_deg = float(cfg.get("heading_hold_deadband_deg", 0.0))
        inputs.heading_hold_bonus = float(cfg.get("heading_hold_bonus", 0.0))
        inputs.waypoint_turn_heading_relief_max = float(
            cfg.get("waypoint_turn_heading_relief_max", cfg.get("waypoint_turn_relief_max", 0.0))
        )

        inputs.altitude_error_weight = float(cfg.get("altitude_error_weight", 0.0))
        inputs.altitude_error_min_alt_m = float(cfg.get("altitude_error_min_alt", 0.0))
        inputs.altitude_error_target_m = float(
            cfg.get("altitude_error_target", self.mission_cmd.get("target_altitude", inputs.curr_alt_baro_m)) or inputs.curr_alt_baro_m
        )
        inputs.altitude_error_deadband_m = float(
            cfg.get("altitude_error_deadband_m", cfg.get("altitude_error_band_m", 0.0))
        )
        inputs.altitude_error_norm_m = float(cfg.get("altitude_error_norm_m", 100.0))
        inputs.altitude_error_power = float(cfg.get("altitude_error_power", 1.0))
        inputs.altitude_error_clip = float(cfg.get("altitude_error_clip", 0.0))
        inputs.altitude_hold_bonus = float(cfg.get("altitude_hold_bonus", 0.0))

        inputs.speed_error_weight = float(cfg.get("speed_error_weight", 0.0))
        inputs.speed_error_min_ias_mps = float(cfg.get("speed_error_min_ias", 0.0))
        inputs.speed_error_target_mps = float(
            cfg.get("speed_error_target", self.mission_cmd.get("target_speed", inputs.curr_ias_mps)) or inputs.curr_ias_mps
        )
        inputs.speed_error_deadband_mps = float(cfg.get("speed_error_deadband", cfg.get("speed_error_band", 0.0)))
        inputs.speed_error_norm_mps = float(cfg.get("speed_error_norm", 30.0))
        inputs.speed_error_power = float(cfg.get("speed_error_power", 1.0))
        inputs.speed_error_clip = float(cfg.get("speed_error_clip", 0.0))
        inputs.speed_hold_bonus = float(cfg.get("speed_hold_bonus", 0.0))

        inputs.roll_abs_weight = float(cfg.get("roll_abs_weight", 0.0))
        inputs.roll_abs_deadband_deg = float(cfg.get("roll_abs_deadband_deg", 0.0))
        inputs.roll_abs_norm_deg = float(cfg.get("roll_abs_norm_deg", 30.0))
        inputs.roll_abs_power = float(cfg.get("roll_abs_power", 1.0))
        inputs.pitch_abs_weight = float(cfg.get("pitch_abs_weight", 0.0))
        inputs.pitch_abs_deadband_deg = float(cfg.get("pitch_abs_deadband_deg", 0.0))
        inputs.pitch_abs_norm_deg = float(cfg.get("pitch_abs_norm_deg", 20.0))
        inputs.pitch_abs_power = float(cfg.get("pitch_abs_power", 1.0))
        inputs.yaw_rate_abs_weight = float(cfg.get("yaw_rate_abs_weight", 0.0))
        inputs.yaw_rate_abs_deadband_deg_s = float(cfg.get("yaw_rate_abs_deadband_deg_s", 0.0))
        inputs.yaw_rate_abs_norm_deg_s = float(cfg.get("yaw_rate_abs_norm_deg_s", 10.0))
        inputs.yaw_rate_abs_power = float(cfg.get("yaw_rate_abs_power", 1.0))
        inputs.beta_abs_weight = float(cfg.get("beta_abs_weight", 0.0))
        inputs.beta_abs_deadband_deg = float(cfg.get("beta_abs_deadband_deg", 0.0))
        inputs.beta_abs_norm_deg = float(cfg.get("beta_abs_norm_deg", 10.0))
        inputs.beta_abs_power = float(cfg.get("beta_abs_power", 1.0))
        inputs.g_deviation_weight = float(cfg.get("g_deviation_weight", 0.0))
        inputs.g_deviation_deadband = float(cfg.get("g_deviation_deadband", 0.0))
        inputs.g_deviation_norm = float(cfg.get("g_deviation_norm", 0.5))
        inputs.g_deviation_power = float(cfg.get("g_deviation_power", 1.0))
        inputs.g_deviation_min_alt_agl_m = float(cfg.get("g_deviation_min_alt_agl_m", 5.0))

        inputs.speed_reward_weight = float(cfg.get("speed_reward_weight", 0.0))
        inputs.runway_centerline_penalty_min_ias_mps = float(cfg.get("runway_centerline_penalty_min_ias", 0.0))
        inputs.runway_centerline_penalty_max_ias_mps = float(cfg.get("runway_centerline_penalty_max_ias", 0.0))
        inputs.runway_centerline_m_penalty_weight = float(cfg.get("runway_centerline_m_penalty_weight", 0.0))
        inputs.runway_centerline_m_deadband_m = float(cfg.get("runway_centerline_m_deadband_m", 0.0))
        inputs.runway_centerline_m_norm_m = float(cfg.get("runway_centerline_m_norm_m", 5.0))
        inputs.runway_centerline_m_power = float(cfg.get("runway_centerline_m_power", 2.0))
        inputs.runway_centerline_m_clip = float(cfg.get("runway_centerline_m_clip", 0.0))
        inputs.runway_centerline_penalty_weight = float(cfg.get("runway_centerline_penalty_weight", 0.0))
        inputs.runway_centerline_safe_frac = float(cfg.get("runway_centerline_safe_frac", 0.0))
        inputs.runway_centerline_penalty_power = float(cfg.get("runway_centerline_penalty_power", 2.0))
        inputs.runway_centerline_barrier_weight = float(cfg.get("runway_centerline_barrier_weight", 0.0))
        inputs.runway_centerline_barrier_clip_frac = float(cfg.get("runway_centerline_barrier_clip_frac", 0.995))
        inputs.departure_centerline_max_alt_agl_m = float(cfg.get("departure_centerline_max_alt_agl_m", 0.0))
        inputs.departure_centerline_m_penalty_weight = float(cfg.get("departure_centerline_m_penalty_weight", 0.0))
        inputs.departure_centerline_m_deadband_m = float(cfg.get("departure_centerline_m_deadband_m", 0.0))
        inputs.departure_centerline_m_norm_m = float(cfg.get("departure_centerline_m_norm_m", 20.0))
        inputs.departure_centerline_m_power = float(cfg.get("departure_centerline_m_power", 2.0))
        inputs.departure_centerline_m_clip = float(cfg.get("departure_centerline_m_clip", 0.0))
        inputs.departure_centerline_reward_weight = float(cfg.get("departure_centerline_reward_weight", 0.0))
        inputs.departure_centerline_reward_band_m = float(
            cfg.get("departure_centerline_reward_band_m", max(1.0, inputs.departure_centerline_m_deadband_m))
        )
        inputs.departure_track_error_weight = float(cfg.get("departure_track_error_weight", 0.0))
        inputs.departure_track_error_deadband_deg = float(cfg.get("departure_track_error_deadband_deg", 0.0))
        inputs.departure_track_error_norm_deg = float(cfg.get("departure_track_error_norm_deg", 10.0))
        inputs.departure_track_error_power = float(cfg.get("departure_track_error_power", 2.0))
        inputs.departure_track_error_clip = float(cfg.get("departure_track_error_clip", 0.0))
        inputs.departure_track_reward_weight = float(cfg.get("departure_track_reward_weight", 0.0))
        inputs.departure_track_reward_band_deg = float(cfg.get("departure_track_reward_band_deg", 10.0))
        inputs.alignment_reward_weight = float(cfg.get("alignment_reward_weight", 0.0))
        inputs.mission_alignment_min_alt_m = float(cfg.get("mission_alignment_min_alt", 120.0))
        return inputs

    def _apply_compiled_flight_shaping_terms(self, products, add_reward_term, *, include_roll_stability: bool) -> None:
        term_names = (
            "altitude_progress",
            "low_alt_descent_penalty",
            "speed_progress",
            "speed_regress",
            "stationary_penalty",
            "liftoff_bonus",
            "rotation_reward",
            "rotation_overpitch_penalty",
            "gear_up_bonus",
            "heading_error_penalty",
            "heading_hold_bonus",
            "altitude_error_penalty",
            "altitude_hold_bonus",
            "speed_error_penalty",
            "speed_hold_bonus",
            "roll_abs_penalty",
            "pitch_abs_penalty",
            "yaw_rate_abs_penalty",
            "beta_abs_penalty",
            "g_deviation_penalty",
            "runway_centerline_m_penalty",
            "runway_centerline_penalty",
            "runway_centerline_barrier",
            "departure_centerline_m_penalty",
            "departure_centerline_reward",
            "departure_track_error_penalty",
            "departure_track_reward",
            "alignment_reward",
        )
        for name in term_names:
            value = float(getattr(products, name, 0.0))
            if value != 0.0:
                add_reward_term(name, value)
        add_reward_term("speed_reward", float(getattr(products, "speed_reward", 0.0)))
        if include_roll_stability:
            add_reward_term("roll_stability", float(getattr(products, "roll_stability", 0.0)))
        self.liftoff_awarded = bool(getattr(products, "next_liftoff_awarded", self.liftoff_awarded))
        self.gear_bonus_awarded = bool(getattr(products, "next_gear_bonus_awarded", self.gear_bonus_awarded))

    @staticmethod
    def _add_breakdown_term(breakdown: dict, name: str, value: float) -> None:
        v = float(value)
        breakdown[name] = float(breakdown.get(name, 0.0) + v)

    def _apply_legacy_flight_shaping_terms(
        self,
        cfg: dict,
        *,
        truth,
        inst,
        curr_ias: float,
        curr_alt_agl: float,
        curr_gear: float,
        curr_roll: float,
        heading_error_deg: float,
        ground_track_error_deg: float,
        waypoint_turn_relief_activation: float,
        airborne: bool,
        preliftoff: bool,
        on_runway_task: bool,
        runway_cross_m,
        runway_wid_m,
        ils_valid: float,
        ils_loc: float,
        steps: int,
        add_reward_term,
    ) -> None:
        tgt_alt = cfg.get("altitude_progress_target", None)
        if tgt_alt is None:
            tgt_alt = self.mission_cmd.get("target_altitude", 0.0)
        try:
            tgt_alt = float(tgt_alt)
        except Exception:
            tgt_alt = 0.0
        d_alt = truth.z - self.prev_alt
        if (tgt_alt <= 0.0 or truth.z < tgt_alt) and d_alt > 0:
            add_reward_term("altitude_progress", d_alt * cfg.get("altitude_progress_weight", 0.0))
        elif truth.z < 10.0 and d_alt < -1.0:
            add_reward_term("low_alt_descent_penalty", d_alt * 0.1)

        tgt_spd = cfg.get("speed_progress_target", None)
        if tgt_spd is None:
            tgt_spd = self.mission_cmd.get("target_speed", 180.0)
        try:
            tgt_spd = float(tgt_spd)
        except Exception:
            tgt_spd = 0.0
        d_spd = curr_ias - self.prev_speed
        if (tgt_spd <= 0.0 or curr_ias < tgt_spd) and d_spd > 0:
            add_reward_term("speed_progress", d_spd * cfg.get("speed_progress_weight", 0.0))
        elif d_spd < 0:
            add_reward_term("speed_regress", d_spd * cfg.get("speed_progress_weight_negative", 0.0))

        stationary_penalty = cfg.get("stationary_penalty", 0.0)
        if stationary_penalty != 0.0:
            grace_steps = int(cfg.get("stationary_grace_steps", 20))
            speed_thr = float(cfg.get("stationary_speed_threshold", 5.0))
            alt_thr = float(cfg.get("stationary_alt_threshold", 5.0))
            if steps > grace_steps and truth.speed < speed_thr and truth.z < alt_thr:
                add_reward_term("stationary_penalty", float(stationary_penalty))

        liftoff_bonus = float(cfg.get("liftoff_bonus", 0.0))
        if liftoff_bonus != 0.0 and not self.liftoff_awarded:
            liftoff_speed_thr = float(cfg.get("liftoff_speed_threshold", 80.0))
            liftoff_alt_thr = float(cfg.get("liftoff_alt_threshold", 5.0))
            if float(inst[0]) >= liftoff_speed_thr and float(inst[3]) >= liftoff_alt_thr:
                add_reward_term("liftoff_bonus", liftoff_bonus)
                self.liftoff_awarded = True

        rotation_weight = float(cfg.get("rotation_reward_weight", 0.0))
        if rotation_weight != 0.0:
            rot_spd_thr = float(cfg.get("rotation_speed_threshold", 80.0))
            rot_alt_thr = float(cfg.get("rotation_alt_threshold", 5.0))
            rot_pitch_cap = float(cfg.get("rotation_pitch_cap", 15.0))
            if float(inst[0]) >= rot_spd_thr and float(inst[3]) <= rot_alt_thr:
                pitch_deg = float(inst[7])
                pitch_term = float(np.clip(pitch_deg, -rot_pitch_cap, rot_pitch_cap))
                add_reward_term("rotation_reward", pitch_term * rotation_weight)
                over_w = float(cfg.get("rotation_overpitch_penalty_weight", 0.0))
                if over_w != 0.0 and pitch_deg > rot_pitch_cap:
                    add_reward_term("rotation_overpitch_penalty", (pitch_deg - rot_pitch_cap) * over_w)

        if curr_alt_agl > 50.0 and curr_gear < 0.1 and not self.gear_bonus_awarded:
            add_reward_term("gear_up_bonus", cfg.get("gear_up_bonus", 0.0))
            self.gear_bonus_awarded = True

        if truth.z < 100.0:
            add_reward_term("roll_stability", abs(curr_roll) * cfg.get("roll_stability_weight", 0.0))

        if cfg.get("heading_error_weight", 0.0) != 0.0:
            diff = heading_error_deg
            turn_heading_relief_max = float(
                cfg.get("waypoint_turn_heading_relief_max", cfg.get("waypoint_turn_relief_max", 0.0))
            )
            turn_heading_relief_max = float(np.clip(turn_heading_relief_max, 0.0, 0.95))
            heading_penalty_scale = 1.0 - turn_heading_relief_max * waypoint_turn_relief_activation
            add_reward_term("heading_error_penalty", diff * cfg.get("heading_error_weight") * heading_penalty_scale)
            hold_db = float(cfg.get("heading_hold_deadband_deg", 0.0))
            hold_bonus = float(cfg.get("heading_hold_bonus", 0.0))
            if hold_bonus != 0.0 and diff <= max(0.0, hold_db):
                add_reward_term("heading_hold_bonus", hold_bonus)

        if airborne:
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
                        add_reward_term("altitude_error_penalty", w_alt_err * (x**p))
                    else:
                        hold_bonus = float(cfg.get("altitude_hold_bonus", 0.0))
                        if hold_bonus != 0.0:
                            add_reward_term("altitude_hold_bonus", hold_bonus)

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
                        add_reward_term("speed_error_penalty", w_spd_err * (x**p))
                    else:
                        hold_bonus = float(cfg.get("speed_hold_bonus", 0.0))
                        if hold_bonus != 0.0:
                            add_reward_term("speed_hold_bonus", hold_bonus)

            for name, value, deadband_key, norm_key, power_key, index in (
                ("roll_abs_penalty", float(cfg.get("roll_abs_weight", 0.0)), "roll_abs_deadband_deg", "roll_abs_norm_deg", "roll_abs_power", 8),
                ("pitch_abs_penalty", float(cfg.get("pitch_abs_weight", 0.0)), "pitch_abs_deadband_deg", "pitch_abs_norm_deg", "pitch_abs_power", 7),
                ("yaw_rate_abs_penalty", float(cfg.get("yaw_rate_abs_weight", 0.0)), "yaw_rate_abs_deadband_deg_s", "yaw_rate_abs_norm_deg_s", "yaw_rate_abs_power", 14),
                ("beta_abs_penalty", float(cfg.get("beta_abs_weight", 0.0)), "beta_abs_deadband_deg", "beta_abs_norm_deg", "beta_abs_power", 6),
            ):
                if value == 0.0:
                    continue
                state_value = abs(float(inst[index])) if len(inst) > index else 0.0
                dead = float(cfg.get(deadband_key, 0.0))
                norm = float(cfg.get(norm_key, 30.0 if "roll" in name else 20.0))
                if norm <= 1.0e-6:
                    norm = 30.0 if "roll" in name else 20.0
                p = float(cfg.get(power_key, 1.0))
                if p < 1.0:
                    p = 1.0
                if p > 8.0:
                    p = 8.0
                err = state_value - max(0.0, dead)
                if err > 0.0:
                    add_reward_term(name, value * ((err / norm) ** p))

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
                    add_reward_term("g_deviation_penalty", w_g * ((err / norm) ** p))

        add_reward_term("speed_reward", truth.speed * cfg.get("speed_reward_weight", 0.0))

        if preliftoff and on_runway_task and runway_cross_m is not None and runway_wid_m is not None:
            half_w = 0.5 * float(runway_wid_m)
            if half_w > 1.0e-6:
                frac = abs(float(runway_cross_m)) / half_w
                if frac > 2.0:
                    frac = 2.0
                min_ias = float(cfg.get("runway_centerline_penalty_min_ias", 0.0))
                max_ias = float(cfg.get("runway_centerline_penalty_max_ias", 0.0))
                scale = 1.0
                if max_ias > min_ias + 1.0e-6:
                    scale = (float(curr_ias) - min_ias) / (max_ias - min_ias)
                    scale = float(np.clip(scale, 0.0, 1.0))

                w_center_m = float(cfg.get("runway_centerline_m_penalty_weight", 0.0))
                if w_center_m != 0.0:
                    dead_m = max(0.0, float(cfg.get("runway_centerline_m_deadband_m", 0.0)))
                    norm_m = float(cfg.get("runway_centerline_m_norm_m", 5.0))
                    if norm_m <= 1.0e-6:
                        norm_m = 5.0
                    p_m = float(np.clip(float(cfg.get("runway_centerline_m_power", 2.0)), 1.0, 8.0))
                    err_m = abs(float(runway_cross_m)) - dead_m
                    if err_m > 0.0:
                        x_m = err_m / norm_m
                        clip_m = float(cfg.get("runway_centerline_m_clip", 0.0))
                        if clip_m > 0.0:
                            x_m = min(x_m, clip_m)
                        add_reward_term("runway_centerline_m_penalty", w_center_m * (x_m**p_m) * scale)

                w_center = float(cfg.get("runway_centerline_penalty_weight", 0.0))
                if w_center != 0.0:
                    safe_frac = float(np.clip(float(cfg.get("runway_centerline_safe_frac", 0.0)), 0.0, 0.99))
                    x = max(0.0, frac - safe_frac) / max(1.0 - safe_frac, 1.0e-6)
                    p = float(np.clip(float(cfg.get("runway_centerline_penalty_power", 2.0)), 1.0, 8.0))
                    add_reward_term("runway_centerline_penalty", w_center * (x**p) * scale)

                w_bar = float(cfg.get("runway_centerline_barrier_weight", 0.0))
                if w_bar != 0.0:
                    clip_frac = float(cfg.get("runway_centerline_barrier_clip_frac", 0.995))
                    clip_frac = float(np.clip(clip_frac, 1.0e-6, 0.999999))
                    frac_c = min(max(frac, 0.0), clip_frac)
                    barrier = -math.log(max(1.0e-6, 1.0 - frac_c))
                    add_reward_term("runway_centerline_barrier", w_bar * barrier * scale)

        if runway_cross_m is not None:
            dep_max_alt = float(cfg.get("departure_centerline_max_alt_agl_m", 0.0))
            if airborne and dep_max_alt > 0.0 and curr_alt_agl <= dep_max_alt:
                w_dep_m = float(cfg.get("departure_centerline_m_penalty_weight", 0.0))
                dead_m = max(0.0, float(cfg.get("departure_centerline_m_deadband_m", 0.0)))
                if w_dep_m != 0.0:
                    norm_m = float(cfg.get("departure_centerline_m_norm_m", 20.0))
                    if norm_m <= 1.0e-6:
                        norm_m = 20.0
                    p_m = float(np.clip(float(cfg.get("departure_centerline_m_power", 2.0)), 1.0, 8.0))
                    err_m = abs(float(runway_cross_m)) - dead_m
                    if err_m > 0.0:
                        x_m = err_m / norm_m
                        clip_m = float(cfg.get("departure_centerline_m_clip", 0.0))
                        if clip_m > 0.0:
                            x_m = min(x_m, clip_m)
                        add_reward_term("departure_centerline_m_penalty", w_dep_m * (x_m**p_m))
                w_dep_center = float(cfg.get("departure_centerline_reward_weight", 0.0))
                if w_dep_center != 0.0:
                    band_m = float(cfg.get("departure_centerline_reward_band_m", max(1.0, dead_m)))
                    if band_m <= 1.0e-6:
                        band_m = 1.0
                    center_frac = max(0.0, 1.0 - abs(float(runway_cross_m)) / band_m)
                    if center_frac > 0.0:
                        add_reward_term("departure_centerline_reward", w_dep_center * center_frac)

                dep_track_err = ground_track_error_deg
                w_dep_trk = float(cfg.get("departure_track_error_weight", 0.0))
                if w_dep_trk != 0.0:
                    dead_deg = max(0.0, float(cfg.get("departure_track_error_deadband_deg", 0.0)))
                    norm_deg = float(cfg.get("departure_track_error_norm_deg", 10.0))
                    if norm_deg <= 1.0e-6:
                        norm_deg = 10.0
                    p_deg = float(np.clip(float(cfg.get("departure_track_error_power", 2.0)), 1.0, 8.0))
                    err_deg = dep_track_err - dead_deg
                    if err_deg > 0.0:
                        x_deg = err_deg / norm_deg
                        clip_deg = float(cfg.get("departure_track_error_clip", 0.0))
                        if clip_deg > 0.0:
                            x_deg = min(x_deg, clip_deg)
                        add_reward_term("departure_track_error_penalty", w_dep_trk * (x_deg**p_deg))

                w_dep_trk_reward = float(cfg.get("departure_track_reward_weight", 0.0))
                if w_dep_trk_reward != 0.0:
                    band_deg = float(cfg.get("departure_track_reward_band_deg", 10.0))
                    if band_deg <= 1.0e-6:
                        band_deg = 10.0
                    track_frac = max(0.0, 1.0 - dep_track_err / band_deg)
                    if track_frac > 0.0:
                        add_reward_term("departure_track_reward", w_dep_trk_reward * track_frac)

        if cfg.get("alignment_reward_weight", 0.0) != 0.0:
            w = float(cfg.get("alignment_reward_weight"))
            if on_runway_task and preliftoff:
                if ils_valid > 0.5:
                    add_reward_term("alignment_reward", (1.0 - min(abs(ils_loc), 1.0)) * w)
            else:
                min_alt_for_cmd_align = float(cfg.get("mission_alignment_min_alt", 120.0))
                if truth.z >= min_alt_for_cmd_align:
                    diff = heading_error_deg
                    align_factor = math.cos(math.radians(diff))
                    if align_factor > 0:
                        add_reward_term("alignment_reward", align_factor * w)

    def _consume_compiled_episode_runtime(
        self,
        *,
        cfg: dict,
        safety_cfg,
        truth,
        step_eval: dict,
        frame_products,
    ):
        reward = float(getattr(frame_products, "compiled_reward_total", 0.0))
        terminated = bool(getattr(frame_products, "terminated", False))
        status = [
            float(getattr(frame_products, "status0", 0.0)),
            float(getattr(frame_products, "status1", 0.0)),
            float(getattr(frame_products, "status2", 0.0)),
            float(getattr(frame_products, "status3", 0.0)),
        ]
        rb = {}
        extra_reward = 0.0

        execution_step = frame_products.execution_step if bool(getattr(frame_products, "execution_step_evaluated", False)) else None
        if execution_step is None:
            tracked_total = 0.0
            rb["tracked_total"] = tracked_total
            rb["untracked"] = float(reward - tracked_total)
            rb["total"] = float(reward)
            self.last_reward_breakdown = rb
            self.last_termination_reason = str(
                ef_py.termination_reason_name(getattr(frame_products, "final_reason_code", ef_py.TerminationReasonCode.Running))
            )
            return reward, terminated, status

        def _add_reward_term(name: str, value: float) -> None:
            self._add_breakdown_term(rb, name, value)

        safety_terms = execution_step.safety
        if float(getattr(safety_terms, "crash_penalty", 0.0)) != 0.0:
            _add_reward_term("crash_penalty", float(safety_terms.crash_penalty))
            nan_guard_marker = float(getattr(safety_terms, "nan_guard_marker", 0.0))
            if nan_guard_marker != 0.0:
                _add_reward_term("nan_guard", nan_guard_marker)
        else:
            _add_reward_term("survival", float(getattr(safety_terms, "survival", 0.0)))
            if bool(getattr(frame_products, "flight_shaping_evaluated", False)):
                self._apply_compiled_flight_shaping_terms(
                    frame_products.flight_shaping,
                    _add_reward_term,
                    include_roll_stability=bool(float(getattr(truth, "z", 0.0)) < 100.0),
                )
            if float(getattr(safety_terms, "stall_penalty", 0.0)) != 0.0:
                _add_reward_term("stall_penalty", float(safety_terms.stall_penalty))
            if float(getattr(safety_terms, "overload_penalty", 0.0)) != 0.0:
                _add_reward_term("overload_penalty", float(safety_terms.overload_penalty))
            if float(getattr(safety_terms, "failfast_penalty", 0.0)) != 0.0:
                _add_reward_term("failfast_penalty", float(safety_terms.failfast_penalty))
            if float(getattr(safety_terms, "gear_collapse_penalty", 0.0)) != 0.0:
                _add_reward_term("gear_collapse_penalty", float(safety_terms.gear_collapse_penalty))
            if float(getattr(safety_terms, "off_runway_penalty", 0.0)) != 0.0:
                _add_reward_term("off_runway_penalty", float(safety_terms.off_runway_penalty))
            if float(getattr(safety_terms, "gear_stress_penalty", 0.0)) != 0.0:
                _add_reward_term("gear_stress_penalty", float(safety_terms.gear_stress_penalty))
            if float(getattr(safety_terms, "off_runway_terminate_penalty", 0.0)) != 0.0:
                _add_reward_term("off_runway_terminate_penalty", float(safety_terms.off_runway_terminate_penalty))

            approach_inputs = step_eval.get("approach_inputs")
            if approach_inputs is not None and bool(getattr(execution_step, "approach_evaluated", False)):
                approach_terms = execution_step.approach
                if float(getattr(approach_terms, "approach_localizer", 0.0)) != 0.0:
                    _add_reward_term("approach_localizer", float(approach_terms.approach_localizer))
                if approach_inputs.localizer_improve_weight != 0.0 and approach_inputs.has_prev_loc:
                    _add_reward_term("approach_localizer_improve", float(approach_terms.approach_localizer_improve))
                if float(getattr(approach_terms, "approach_glideslope", 0.0)) != 0.0:
                    _add_reward_term("approach_glideslope", float(approach_terms.approach_glideslope))
                if approach_inputs.glideslope_improve_weight != 0.0 and approach_inputs.has_prev_gs:
                    _add_reward_term("approach_glideslope_improve", float(approach_terms.approach_glideslope_improve))
                if approach_inputs.dme_progress_weight != 0.0 and approach_inputs.has_prev_dme and math.isfinite(float(approach_inputs.ils_dme_m)):
                    _add_reward_term("approach_dme_progress", float(approach_terms.approach_dme_progress))
                if float(getattr(approach_terms, "approach_capture_bonus", 0.0)) != 0.0:
                    _add_reward_term("approach_capture_bonus", float(approach_terms.approach_capture_bonus))
                if float(getattr(approach_terms, "landing_sink_rate_penalty", 0.0)) != 0.0:
                    _add_reward_term("landing_sink_rate_penalty", float(approach_terms.landing_sink_rate_penalty))

                if bool(getattr(approach_terms, "clear_history", False)):
                    self._approach_prev_dme_m = None
                    self._approach_prev_loc_abs = None
                    self._approach_prev_gs_abs = None
                elif bool(getattr(approach_terms, "next_prev_valid", False)):
                    self._approach_prev_dme_m = float(approach_terms.next_prev_dme_m)
                    self._approach_prev_loc_abs = float(approach_terms.next_prev_loc_abs)
                    self._approach_prev_gs_abs = float(approach_terms.next_prev_gs_abs)

            objective_has_status = bool(getattr(execution_step, "objective_evaluated", False)) and int(
                getattr(execution_step, "objective_status_count", 0)
            ) > 0
            waypoint_state = step_eval.get("waypoint_state")
            if isinstance(waypoint_state, dict) and bool(getattr(execution_step, "waypoint_evaluated", False)):
                idx = int(waypoint_state["idx"])
                n = int(waypoint_state["count"])
                if not objective_has_status:
                    status[0] = float(waypoint_state["dist_m"])
                    status[1] = float(idx)
                    status[2] = float(n)

                waypoint_inputs = waypoint_state["inputs"]
                waypoint_terms = execution_step.waypoint
                if waypoint_inputs.progress_weight != 0.0 and waypoint_inputs.has_prev_dist:
                    _add_reward_term("waypoint_progress", float(waypoint_terms.waypoint_progress))
                if waypoint_inputs.distance_weight != 0.0:
                    _add_reward_term("waypoint_distance", float(waypoint_terms.waypoint_distance))
                if float(getattr(waypoint_terms, "waypoint_cross_track", 0.0)) != 0.0:
                    _add_reward_term("waypoint_cross_track", float(waypoint_terms.waypoint_cross_track))
                if float(getattr(waypoint_terms, "waypoint_proximity", 0.0)) != 0.0:
                    _add_reward_term("waypoint_proximity", float(waypoint_terms.waypoint_proximity))

                self._waypoint_prev_dist_m = (
                    float(waypoint_terms.next_prev_dist_m)
                    if bool(getattr(waypoint_terms, "next_prev_dist_valid", False))
                    else None
                )
                arrived = bool(getattr(waypoint_terms, "arrived", False))
                if arrived:
                    _add_reward_term("waypoint_reached_bonus", float(waypoint_terms.waypoint_reached_bonus))
                    self.waypoint_idx = idx + 1
                    self._waypoint_prev_dist_m = None
                    if not objective_has_status:
                        status[1] = float(self.waypoint_idx)
                        if self.waypoint_idx < n:
                            next_wp = self.waypoints[self.waypoint_idx]
                            next_dx = float(next_wp.get("x", 0.0)) - float(getattr(truth, "x", 0.0))
                            next_dy = float(next_wp.get("y", 0.0)) - float(getattr(truth, "y", 0.0))
                            status[0] = float(math.hypot(next_dx, next_dy))
                        else:
                            status[0] = 0.0
                    if self.waypoint_idx >= n:
                        landing_transition_pending = bool(
                            isinstance(self.post_waypoint_transition, dict)
                            and self.post_waypoint_transition
                            and is_landing_command_code(self.post_waypoint_transition.get("command_code", 4))
                        )
                        transitioned = None
                        if not self._defer_landing_post_transition_until_next_update():
                            transitioned = self._maybe_activate_post_waypoint_transition()
                        if isinstance(transitioned, dict):
                            transition_reward = float(
                                transitioned.get("transition_reward", cfg.get("phase_transition_bonus", 600.0))
                            )
                            _add_reward_term("phase_transition_bonus", transition_reward)
                            extra_reward += transition_reward
                            if not objective_has_status:
                                status[0] = 0.0
                                status[1] = 0.0
                        elif landing_transition_pending:
                            if not objective_has_status:
                                status[0] = 0.0
                                status[1] = float(self.waypoint_idx)
                        elif bool(getattr(execution_step, "waypoint_episode_success", False)):
                            _add_reward_term(
                                "waypoint_success_bonus",
                                float(getattr(execution_step, "waypoint_episode_success_bonus", safety_cfg.waypoint_mission_success_bonus)),
                            )

            if bool(getattr(execution_step, "objective_evaluated", False)) and int(
                getattr(execution_step, "matched_objective_index", -1)
            ) >= 0:
                objective_terms = execution_step.objective
                if float(getattr(objective_terms, "success_runway_cross_penalty", 0.0)) != 0.0:
                    _add_reward_term(
                        "success_runway_cross_penalty",
                        float(objective_terms.success_runway_cross_penalty),
                    )
                if float(getattr(objective_terms, "success_ground_track_error_penalty", 0.0)) != 0.0:
                    _add_reward_term(
                        "success_ground_track_error_penalty",
                        float(objective_terms.success_ground_track_error_penalty),
                    )
                _add_reward_term("objective_bonus", float(objective_terms.objective_bonus))

        reward += float(extra_reward)
        tracked_total = float(sum(rb.values())) if rb else 0.0
        rb["tracked_total"] = tracked_total
        rb["untracked"] = float(reward - tracked_total)
        rb["total"] = float(reward)
        self.last_reward_breakdown = rb
        self.last_termination_reason = str(
            ef_py.termination_reason_name(getattr(frame_products, "final_reason_code", ef_py.TerminationReasonCode.Running))
        )
        return reward, terminated, status

    def _build_waypoint_step_state(self, cfg: dict, *, truth=None, inst=None, turn_relief_activation: float = 0.0):
        try:
            cmd_code = int(self.mission_cmd.get("command_code", 0))
        except Exception:
            cmd_code = 0
        if cmd_code != 3 or not self.waypoints:
            return None

        idx = int(getattr(self, "waypoint_idx", 0))
        if idx < 0:
            idx = 0
        count = int(len(self.waypoints))
        if idx >= count:
            return None

        gstate = self._compute_waypoint_guidance_state(truth=truth, inst=inst)
        wp = self.waypoints[idx]
        dist_m = float(
            math.hypot(
                float(wp.get("x", 0.0)) - float(getattr(truth, "x", 0.0)),
                float(wp.get("y", 0.0)) - float(getattr(truth, "y", 0.0)),
            )
        )
        mode = self._normalize_waypoint_mode(wp.get("waypoint_mode", self.mission_cmd.get("waypoint_mode", "flyby")))
        leg_len = 0.0
        xtk = None
        dtg = dist_m
        rad = max(1.0, float(wp.get("radius_m", self.mission_cmd.get("waypoint_radius_m", 500.0))))
        lead = 0.0
        seq_gate_m = float(rad)
        passed_fix = False
        if isinstance(gstate, dict) and int(gstate.get("idx", -1)) == idx:
            wp = gstate["wp"]
            mode = str(gstate.get("waypoint_mode", mode))
            dist_m = float(gstate.get("dist_m", dist_m))
            leg_len = float(gstate.get("leg_len_m", 0.0))
            if str(mode) == "flyby" and bool(gstate.get("final_leg", False)):
                xtk = float(gstate.get("xtk_m", gstate.get("reward_xtk_m", 0.0)))
            else:
                xtk = float(gstate.get("reward_xtk_m", 0.0))
            dtg = float(gstate.get("reward_dtg_m", dist_m))
            rad = max(1.0, float(gstate.get("waypoint_radius_m", rad)))
            lead = float(gstate.get("lead_turn_m", 0.0))
            seq_gate_m = float(gstate.get("sequence_gate_m", rad))
            passed_fix = bool(gstate.get("passed_fix", False))

        waypoint_inputs = self._build_waypoint_reward_inputs(
            cfg,
            idx=int(idx),
            count=int(count),
            mode=str(mode),
            dist_m=float(dist_m),
            leg_len_m=float(leg_len),
            xtk_m=xtk,
            dtg_m=dtg,
            waypoint_radius_m=float(rad),
            lead_turn_m=float(lead),
            sequence_gate_m=float(seq_gate_m),
            passed_fix=bool(passed_fix),
            turn_relief_activation=float(turn_relief_activation),
        )
        return {
            "idx": int(idx),
            "count": int(count),
            "dist_m": float(dist_m),
            "inputs": waypoint_inputs,
            "episode_success": bool(
                (idx + 1) >= count
                and not (isinstance(self.post_waypoint_transition, dict) and self.post_waypoint_transition)
            ),
        }

    def _build_waypoint_reward_inputs(
        self,
        cfg: dict,
        *,
        idx: int,
        count: int,
        mode: str,
        dist_m: float,
        leg_len_m: float,
        xtk_m,
        dtg_m,
        waypoint_radius_m: float,
        lead_turn_m: float,
        sequence_gate_m: float,
        passed_fix: bool,
        turn_relief_activation: float,
    ):
        inputs = ef_py.WaypointRewardInputs()
        mode_cfg = self._waypoint_mode_reward_cfgs.get(str(mode), self._waypoint_mode_reward_cfgs.get("flyby", None))
        if mode_cfg is None:
            mode_cfg = WaypointModeRewardConfig(
                progress_weight=float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_progress_weight", mode, 0.0)),
                progress_negative_scale=float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_progress_negative_scale", mode, 1.0)),
                distance_weight=float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_distance_weight", mode, 0.0)),
                distance_clip_m=float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_distance_clip_m", mode, 0.0)),
                distance_scale_by_route=bool(self._cfg_value_for_waypoint_mode(cfg, "waypoint_distance_scale_by_route", mode, False)),
                distance_route_ref_m=float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_distance_route_ref_m", mode, 55000.0)),
                distance_route_scale_min=float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_distance_route_scale_min", mode, 0.5)),
                distance_route_scale_max=float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_distance_route_scale_max", mode, 1.0)),
                cross_track_weight=float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_cross_track_weight", mode, 0.0)),
                cross_track_deadband_m=float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_cross_track_deadband_m", mode, 0.0)),
                cross_track_norm_m=float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_cross_track_norm_m", mode, 1000.0)),
                cross_track_power=float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_cross_track_power", mode, 1.0)),
                cross_track_clip=float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_cross_track_clip", mode, 0.0)),
                turn_relief_max=float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_max", mode, 0.0)),
                proximity_weight=float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_proximity_weight", mode, 0.0)),
                proximity_ref_m=float(
                    self._cfg_value_for_waypoint_mode(
                        cfg,
                        "waypoint_proximity_ref_m",
                        mode,
                        max(2.5 * float(waypoint_radius_m), float(waypoint_radius_m) + 1500.0),
                    )
                ),
                proximity_power=float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_proximity_power", mode, 1.0)),
                reached_bonus=float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_reached_bonus", mode, 0.0)),
            )
        inputs.valid = True
        inputs.waypoint_index = int(idx)
        inputs.waypoint_count = int(count)
        inputs.is_flyover = bool(str(mode) == "flyover")
        inputs.has_guidance = bool(leg_len_m > 1.0e-6 and xtk_m is not None and dtg_m is not None)
        inputs.passed_fix = bool(passed_fix)
        inputs.dist_m = float(dist_m)
        inputs.xtk_m = 0.0 if xtk_m is None else float(xtk_m)
        inputs.dtg_m = float(dist_m if dtg_m is None else dtg_m)
        inputs.waypoint_radius_m = float(waypoint_radius_m)
        inputs.leg_len_m = float(leg_len_m)
        inputs.lead_turn_m = float(lead_turn_m)
        inputs.sequence_gate_m = float(sequence_gate_m)
        inputs.has_prev_dist = self._waypoint_prev_dist_m is not None
        inputs.prev_dist_m = 0.0 if self._waypoint_prev_dist_m is None else float(self._waypoint_prev_dist_m)
        inputs.route_length_m = float(getattr(self, "waypoint_total_route_length_m", 0.0))
        inputs.turn_relief_activation = float(turn_relief_activation)

        inputs.progress_weight = float(mode_cfg.progress_weight)
        inputs.progress_negative_scale = float(mode_cfg.progress_negative_scale)
        inputs.distance_weight = float(mode_cfg.distance_weight)
        inputs.distance_clip_m = float(mode_cfg.distance_clip_m)
        inputs.distance_scale_by_route = bool(mode_cfg.distance_scale_by_route)
        inputs.distance_route_ref_m = float(mode_cfg.distance_route_ref_m)
        inputs.distance_route_scale_min = float(mode_cfg.distance_route_scale_min)
        inputs.distance_route_scale_max = float(mode_cfg.distance_route_scale_max)
        inputs.cross_track_weight = float(mode_cfg.cross_track_weight)
        inputs.cross_track_deadband_m = float(mode_cfg.cross_track_deadband_m)
        inputs.cross_track_norm_m = float(mode_cfg.cross_track_norm_m)
        inputs.cross_track_power = float(mode_cfg.cross_track_power)
        inputs.cross_track_clip = float(mode_cfg.cross_track_clip)
        inputs.turn_relief_max = float(mode_cfg.turn_relief_max)
        inputs.proximity_weight = float(mode_cfg.proximity_weight)
        inputs.proximity_ref_m = float(
            max(float(mode_cfg.proximity_ref_m), max(2.5 * float(waypoint_radius_m), float(waypoint_radius_m) + 1500.0))
        )
        inputs.proximity_power = float(mode_cfg.proximity_power)
        inputs.reached_bonus = float(mode_cfg.reached_bonus)
        return inputs

    def _build_approach_reward_inputs(
        self,
        cfg: dict,
        *,
        ils_valid: float,
        ils_loc: float,
        ils_gs: float,
        ils_dme: float,
        curr_alt_agl: float,
        sink_rate_mps: float,
    ):
        inputs = ef_py.ApproachRewardInputs()
        _ = cfg
        approach_cfg = self._approach_reward_cfg
        inputs.valid = True
        inputs.ils_valid = bool(ils_valid > 0.5)
        inputs.ils_loc_dev = float(ils_loc)
        inputs.ils_gs_dev = float(ils_gs)
        inputs.ils_dme_m = float(ils_dme)
        inputs.has_prev_loc = self._approach_prev_loc_abs is not None
        inputs.prev_loc_abs = 0.0 if self._approach_prev_loc_abs is None else float(self._approach_prev_loc_abs)
        inputs.has_prev_gs = self._approach_prev_gs_abs is not None
        inputs.prev_gs_abs = 0.0 if self._approach_prev_gs_abs is None else float(self._approach_prev_gs_abs)
        inputs.has_prev_dme = self._approach_prev_dme_m is not None
        inputs.prev_dme_m = 0.0 if self._approach_prev_dme_m is None else float(self._approach_prev_dme_m)

        inputs.localizer_weight = float(approach_cfg.localizer_weight)
        inputs.localizer_deadband = float(approach_cfg.localizer_deadband)
        inputs.localizer_norm = float(approach_cfg.localizer_norm)
        inputs.localizer_power = float(approach_cfg.localizer_power)
        inputs.localizer_clip = float(approach_cfg.localizer_clip)
        inputs.localizer_improve_weight = float(approach_cfg.localizer_improve_weight)

        inputs.glideslope_weight = float(approach_cfg.glideslope_weight)
        inputs.glideslope_deadband = float(approach_cfg.glideslope_deadband)
        inputs.glideslope_norm = float(approach_cfg.glideslope_norm)
        inputs.glideslope_power = float(approach_cfg.glideslope_power)
        inputs.glideslope_clip = float(approach_cfg.glideslope_clip)
        inputs.glideslope_improve_weight = float(approach_cfg.glideslope_improve_weight)

        inputs.dme_progress_weight = float(approach_cfg.dme_progress_weight)
        inputs.dme_progress_localizer_band = float(approach_cfg.dme_progress_localizer_band)
        inputs.dme_progress_glideslope_band = float(approach_cfg.dme_progress_glideslope_band)
        inputs.dme_progress_quality_power = float(approach_cfg.dme_progress_quality_power)

        inputs.capture_bonus = float(approach_cfg.capture_bonus)
        inputs.capture_localizer_band = float(approach_cfg.capture_localizer_band)
        inputs.capture_glideslope_band = float(approach_cfg.capture_glideslope_band)

        inputs.sink_rate_weight = float(approach_cfg.sink_rate_weight)
        inputs.flare_agl_m = float(approach_cfg.flare_agl_m)
        inputs.curr_alt_agl_m = float(curr_alt_agl)
        inputs.sink_rate_mps = float(sink_rate_mps)
        inputs.sink_rate_deadband_mps = float(approach_cfg.sink_rate_deadband_mps)
        inputs.sink_rate_norm_mps = float(approach_cfg.sink_rate_norm_mps)
        inputs.sink_rate_power = float(approach_cfg.sink_rate_power)
        inputs.sink_rate_clip = float(approach_cfg.sink_rate_clip)
        return inputs

    def _compile_conditional_objectives(self):
        compiled = []
        for obj in self.scenario_data.get("objectives", []):
            if not isinstance(obj, dict):
                continue
            if str(obj.get("type", "")).strip().lower() != "conditional":
                continue
            spec = ef_py.ConditionalObjectiveSpec()
            spec.reward_bonus = float(obj.get("reward", 1000.0))
            conds = []
            for cond in obj.get("conditions", []):
                if not isinstance(cond, dict):
                    continue
                compiled_cond = ef_py.ConditionalObjectiveCondition()
                prop_key = str(cond.get("property", "")).strip()
                compiled_cond.property_code = _OBJECTIVE_PROPERTY_MAP.get(prop_key, ef_py.ConditionalObjectiveProperty.Unknown)
                compiled_cond.op_code = _OBJECTIVE_OP_MAP.get(str(cond.get("op", ">=")).strip(), ef_py.ConditionalObjectiveOp.GreaterEqual)
                compiled_cond.target_kind = ef_py.ConditionalObjectiveTargetKind.Literal
                compiled_cond.target_scale = 1.0
                tgt = cond.get("value", 0.0)
                if isinstance(tgt, str):
                    target_info = _OBJECTIVE_DYNAMIC_TARGET_MAP.get(tgt.strip().upper())
                    if target_info is not None:
                        compiled_cond.target_kind = target_info[0]
                        compiled_cond.target_scale = float(cond.get("scale", target_info[1]))
                        compiled_cond.target_value = 0.0
                    else:
                        try:
                            compiled_cond.target_value = float(tgt)
                        except Exception:
                            compiled_cond.target_value = 0.0
                else:
                    try:
                        compiled_cond.target_value = float(tgt)
                    except Exception:
                        compiled_cond.target_value = 0.0
                conds.append(compiled_cond)
            spec.conditions = conds
            compiled.append(spec)
        return compiled

    @staticmethod
    def _build_objective_shaping_config(cfg: dict):
        shaping = ef_py.ObjectiveShapingConfig()
        shaping.runway_cross_penalty_weight = float(cfg.get("success_runway_cross_penalty_weight", 0.0))
        shaping.runway_cross_deadband_m = float(cfg.get("success_runway_cross_deadband_m", 0.0))
        shaping.runway_cross_norm_m = float(cfg.get("success_runway_cross_norm_m", 20.0))
        shaping.runway_cross_power = float(cfg.get("success_runway_cross_power", 2.0))
        shaping.runway_cross_clip = float(cfg.get("success_runway_cross_clip", 0.0))
        shaping.ground_track_penalty_weight = float(cfg.get("success_ground_track_error_penalty_weight", 0.0))
        shaping.ground_track_deadband_deg = float(cfg.get("success_ground_track_error_deadband_deg", 0.0))
        shaping.ground_track_norm_deg = float(cfg.get("success_ground_track_error_norm_deg", 10.0))
        shaping.ground_track_power = float(cfg.get("success_ground_track_error_power", 2.0))
        shaping.ground_track_clip = float(cfg.get("success_ground_track_error_clip", 0.0))
        return shaping

    def _build_conditional_objective_inputs(
        self,
        truth,
        inst,
        *,
        curr_ias: float,
        curr_ground_speed: float,
        curr_gear: float,
        curr_alt_agl: float,
        heading_error_deg: float,
        ground_track_error_deg: float,
        runway_cross_m,
        runway_from_threshold_m,
        on_runway_geom,
        on_runway_task: bool,
        on_ground: bool,
    ):
        inputs = ef_py.ConditionalObjectiveInputs()
        inputs.altitude_m = float(getattr(truth, "z", 0.0))
        inputs.altitude_agl_m = float(curr_alt_agl)
        inputs.speed_mps = float(curr_ias)
        inputs.ground_speed_mps = float(curr_ground_speed)
        inputs.gear_fraction = float(curr_gear)
        inputs.heading_error_deg = float(heading_error_deg)
        inputs.command_code = float(int(self.mission_cmd.get("command_code", 0)))
        inputs.ground_track_error_deg = float(ground_track_error_deg)
        inputs.has_runway_cross_m = runway_cross_m is not None
        inputs.runway_cross_m = 0.0 if runway_cross_m is None else float(runway_cross_m)
        inputs.has_runway_from_threshold_m = runway_from_threshold_m is not None
        inputs.runway_from_threshold_m = 0.0 if runway_from_threshold_m is None else float(runway_from_threshold_m)
        inputs.on_runway_geom = bool(on_runway_geom)
        inputs.on_runway_task = bool(on_runway_task)
        inputs.on_ground = bool(on_ground)
        inputs.sink_rate_abs_mps = abs(self._instrument_scalar(inst, "vvi", 4, 0.0))
        inputs.ils_localizer_abs = abs(self._instrument_scalar(inst, "ils_loc", -3, float("inf")))
        inputs.ils_glideslope_abs = abs(self._instrument_scalar(inst, "ils_gs", -2, float("inf")))
        inputs.dme_m = self._instrument_scalar(inst, "ils_dme", -1, float("inf"))
        inputs.heading_deg = float(getattr(truth, "heading", 0.0))
        inputs.x_m = float(getattr(truth, "x", 0.0))
        inputs.y_m = float(getattr(truth, "y", 0.0))
        inputs.target_altitude_m = float(self.mission_cmd.get("target_altitude", 0.0))
        inputs.target_speed_mps = float(self.mission_cmd.get("target_speed", 0.0))
        inputs.target_heading_deg = float(self.mission_cmd.get("target_heading", 0.0))
        return inputs

    def _build_safety_runtime_inputs(
        self,
        cfg: dict,
        *,
        finite_state_valid: bool,
        truth,
        airborne: bool,
        aoa_valid: bool,
        curr_aoa: float,
        curr_g: float,
        curr_alt_agl: float,
        curr_roll: float,
        gear_collapsed: bool,
        runway_surface_phase: bool,
        on_runway_task: bool,
        gear_stress: float,
        off_runway_steps: int,
        time_step_s: float,
    ):
        inputs = ef_py.SafetyRuntimeInputs()
        _ = cfg
        safety_cfg = self._safety_reward_cfg
        inputs.finite_state_valid = bool(finite_state_valid)
        inputs.crash_penalty = float(safety_cfg.crash_penalty)
        inputs.survival_reward = float(safety_cfg.survival_reward)
        inputs.health = float(getattr(truth, "health", 100.0))

        inputs.airborne = bool(airborne)
        inputs.aoa_valid = bool(aoa_valid)
        inputs.aoa_abs_deg = abs(float(curr_aoa))
        inputs.stall_threshold_deg = float(safety_cfg.stall_threshold_deg)
        inputs.stall_penalty_weight = float(safety_cfg.stall_penalty_weight)
        inputs.stall_penalty_clip = float(safety_cfg.stall_penalty_clip)

        inputs.g_abs = abs(float(curr_g))
        inputs.overload_g_threshold = float(safety_cfg.overload_g_threshold)
        inputs.overload_penalty_weight = float(safety_cfg.overload_penalty_weight)
        inputs.overload_penalty_clip = float(safety_cfg.overload_penalty_clip)
        inputs.curr_alt_agl_m = float(curr_alt_agl)
        inputs.overload_min_alt_agl_m = float(safety_cfg.overload_min_alt_agl_m)

        inputs.altitude_m = float(getattr(truth, "z", 0.0))
        inputs.roll_abs_deg = abs(float(curr_roll))
        inputs.pitch_abs_deg = abs(float(getattr(truth, "pitch", 0.0)))
        inputs.failfast_penalty = float(safety_cfg.failfast_penalty)

        inputs.gear_collapsed = bool(gear_collapsed)
        inputs.gear_collapse_penalty = float(safety_cfg.gear_collapse_penalty)

        inputs.runway_surface_phase = bool(runway_surface_phase)
        inputs.on_runway_task = bool(on_runway_task)
        inputs.gear_stress = float(gear_stress)
        inputs.gear_stress_penalty_weight = float(safety_cfg.gear_stress_penalty_weight)
        inputs.off_runway_penalty = float(safety_cfg.off_runway_penalty)
        inputs.speed_mps = float(getattr(truth, "speed", 0.0))
        inputs.off_runway_steps = int(off_runway_steps)
        inputs.off_runway_terminate_speed = float(safety_cfg.off_runway_terminate_speed)
        inputs.off_runway_terminate_grace_s = float(safety_cfg.off_runway_terminate_grace_s)
        inputs.time_step_s = float(time_step_s)
        inputs.off_runway_terminate_penalty = float(safety_cfg.off_runway_terminate_penalty)
        return inputs

    def _compiled_execution_step_enabled(self) -> bool:
        return bool(getattr(self, "use_compiled_execution_step_runtime", True)) and hasattr(
            ef_py, "ExecutionStepRuntimeInputs"
        ) and hasattr(ef_py, "compute_execution_step_runtime")

    @staticmethod
    def _build_neutral_execution_safety_inputs():
        inputs = ef_py.SafetyRuntimeInputs()
        inputs.finite_state_valid = True
        inputs.health = 100.0
        inputs.survival_reward = 0.0
        return inputs

    def _compute_execution_step_runtime_products(
        self,
        *,
        truncated: bool,
        safety_inputs=None,
        approach_inputs=None,
        waypoint_inputs=None,
        waypoint_episode_success: bool = False,
        waypoint_episode_success_bonus: float = 0.0,
        objective_specs=None,
        objective_inputs=None,
    ):
        inputs = ef_py.ExecutionStepRuntimeInputs()
        inputs.truncated = bool(truncated)
        inputs.safety = (
            safety_inputs if safety_inputs is not None else self._build_neutral_execution_safety_inputs()
        )
        if approach_inputs is not None:
            inputs.has_approach = True
            inputs.approach = approach_inputs
        if waypoint_inputs is not None:
            inputs.has_waypoint = True
            inputs.waypoint = waypoint_inputs
            inputs.waypoint_episode_success = bool(waypoint_episode_success)
            inputs.waypoint_episode_success_bonus = float(waypoint_episode_success_bonus)
        objective_items = list(objective_specs or [])
        if objective_items and objective_inputs is not None:
            inputs.has_objectives = True
            inputs.objectives = objective_items
            inputs.objective_inputs = objective_inputs
            inputs.objective_shaping = self._objective_shaping_cfg
        return ef_py.compute_execution_step_runtime(inputs)

    def _compiled_execution_frame_enabled(self) -> bool:
        return bool(getattr(self, "use_compiled_execution_step_runtime", True)) and hasattr(
            ef_py, "ExecutionFrameRuntimeInputs"
        ) and hasattr(ef_py, "compute_execution_frame_runtime")

    def _compiled_execution_episode_enabled(self) -> bool:
        return bool(getattr(self, "use_compiled_execution_step_runtime", True)) and hasattr(
            ef_py, "ExecutionEpisodeRuntimeInputs"
        ) and hasattr(ef_py, "compute_execution_episode_runtime")

    def _get_cached_step_evaluation(
        self,
        *,
        truth=None,
        inst_obj=None,
        steps=None,
        max_steps=None,
        mission_obs_mode=None,
    ):
        cache = getattr(self, "_runtime_eval_cache", None)
        if not isinstance(cache, dict):
            return None
        entry = cache.get("step_evaluation")
        if not isinstance(entry, dict):
            return None
        if truth is not None and entry.get("truth_obj") is not truth:
            return None
        if inst_obj is not None and entry.get("inst_obj") is not inst_obj:
            return None
        if steps is not None and int(entry.get("steps", -1)) != int(steps):
            return None
        if max_steps is not None and int(entry.get("max_steps", -1)) != int(max_steps):
            return None
        if mission_obs_mode is not None and str(entry.get("mission_obs_mode", "")) != str(mission_obs_mode):
            return None
        return entry

    def _prepare_step_evaluation(
        self,
        *,
        truth,
        inst_obj,
        inst_vec,
        ils_vec,
        steps: int,
        max_steps: int,
        mission_obs_mode: str | None = None,
    ):
        cached = self._get_cached_step_evaluation(
            truth=truth,
            inst_obj=inst_obj,
            steps=steps,
            max_steps=max_steps,
            mission_obs_mode=mission_obs_mode,
        )
        if isinstance(cached, dict):
            return cached

        cfg = self._compiled_rewards_cfg if isinstance(self._compiled_rewards_cfg, dict) and self._compiled_rewards_cfg else self.scenario_data.get("rewards", {})
        safety_cfg = self._safety_reward_cfg
        approach_cfg = self._approach_reward_cfg
        truncated = bool(int(steps) >= int(max_steps))

        curr_aoa = float(inst_vec[5])
        curr_roll = float(inst_vec[8])
        curr_g = float(inst_vec[10])
        curr_gear = float(inst_vec[18])
        curr_ias = float(inst_vec[0])
        curr_ground_speed = float(inst_vec[29]) if len(inst_vec) > 29 else math.hypot(float(getattr(truth, "vx", 0.0)), float(getattr(truth, "vy", 0.0)))
        curr_alt_agl = float(inst_vec[3]) if len(inst_vec) > 3 else float(getattr(truth, "z", 0.0))
        tgt_hdg = float(self.mission_cmd.get("target_heading", 0.0))
        inst_source = inst_obj if inst_obj is not None else inst_vec
        inst_ground_track = self._instrument_scalar(inst_source, "ground_track", 30)
        heading_error_deg = float(self._command_tracking_error_deg(inst_source, getattr(truth, "heading", 0.0)))
        ground_track_error_deg = float(
            ef_py.compute_ground_track_error_deg(
                float(tgt_hdg),
                float(getattr(truth, "heading", 0.0)),
                float(inst_ground_track),
            )
        )

        def _finite(x) -> bool:
            try:
                return math.isfinite(float(x))
            except Exception:
                return False

        finite_state_valid = all(
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
                float(inst_vec[2]),
                float(inst_vec[3]),
                curr_aoa,
                curr_roll,
                curr_g,
            )
        )

        runway_frame = None
        if truth is not None and self._spatial_geometry is not None:
            runway_frame = self._query_runway_frame_result(float(truth.x), float(truth.y))
        step_info_inputs = self._build_step_info_runtime_inputs(
            inst_now=inst_obj,
            truth_now=truth,
            runway_frame=runway_frame,
        )

        frame_products = None
        safety_inputs = None
        shaping_inputs = None
        waypoint_turn_relief_activation = 0.0
        waypoint_state = None
        objective_inputs = None
        approach_inputs = None
        gear_collapsed = bool(getattr(inst_obj, "gear_collapsed", False)) if inst_obj is not None else False
        on_paved = bool(getattr(inst_obj, "on_runway", True)) if inst_obj is not None else True
        gear_stress = float(getattr(inst_obj, "gear_stress", 0.0)) if inst_obj is not None else 0.0
        on_ground = bool(curr_alt_agl <= float(step_info_inputs.on_ground_alt_threshold_m))
        airborne = bool(curr_alt_agl >= float(step_info_inputs.airborne_alt_threshold_m))
        preliftoff = not airborne
        on_runway_geom = None
        runway_along_m = None
        runway_cross_m = None
        runway_from_threshold_m = None
        runway_len_m = None
        runway_wid_m = None

        if bool(step_info_inputs.has_runway_frame):
            frame = step_info_inputs.runway_frame
            if bool(getattr(frame, "valid", False)) and float(getattr(frame, "length_m", 0.0)) > 1.0 and float(getattr(frame, "width_m", 0.0)) > 1.0:
                runway_along_m = float(frame.along_m)
                runway_cross_m = float(frame.cross_m)
                runway_len_m = float(frame.length_m)
                runway_wid_m = float(frame.width_m)
                runway_from_threshold_m = float(frame.along_m + 0.5 * frame.length_m)
                on_runway_geom = bool(
                    abs(float(frame.cross_m)) <= (0.5 * float(frame.width_m) + float(step_info_inputs.runway_width_margin_m))
                    and abs(float(frame.along_m)) <= (0.5 * float(frame.length_m) + float(step_info_inputs.runway_length_margin_m))
                )

        try:
            cmd_code = int(self.mission_cmd.get("command_code", 0))
        except Exception:
            cmd_code = 0
        landing_mode = str(self.mission_cmd.get("landing_mode", "")).strip().lower()
        is_landing_task = bool(is_landing_command_code(cmd_code) or landing_mode)
        runway_surface_phase = bool(on_ground) if is_landing_task else bool(preliftoff)
        on_runway_task = bool(on_paved) if runway_surface_phase else False
        if on_runway_geom is not None:
            on_runway_task = bool(on_runway_geom) if runway_surface_phase else False
        next_off_runway_steps = int(getattr(self, "off_runway_steps", 0)) + 1 if runway_surface_phase and (not on_runway_task) else 0

        if not finite_state_valid:
            guard_inputs = ef_py.SafetyRuntimeInputs()
            guard_inputs.finite_state_valid = False
            guard_inputs.crash_penalty = float(safety_cfg.crash_penalty)
            safety_inputs = guard_inputs
            if self._compiled_execution_episode_enabled():
                runtime_inputs = ef_py.ExecutionEpisodeRuntimeInputs()
                if mission_obs_mode is not None:
                    runtime_inputs.has_mission_observation = True
                    runtime_inputs.mission_observation = self._build_mission_observation_runtime_inputs(
                        mission_obs_mode,
                        truth=truth,
                        inst=inst_obj,
                    )
                runtime_inputs.has_step_info = True
                runtime_inputs.step_info = step_info_inputs
                runtime_inputs.has_execution_step = True
                exec_inputs = ef_py.ExecutionStepRuntimeInputs()
                exec_inputs.truncated = bool(truncated)
                exec_inputs.safety = guard_inputs
                runtime_inputs.execution_step = exec_inputs
                runtime_inputs.include_roll_stability = bool(float(getattr(truth, "z", 0.0)) < 100.0)
                frame_products = ef_py.compute_execution_episode_runtime(runtime_inputs)
            elif self._compiled_execution_frame_enabled():
                frame_inputs = ef_py.ExecutionFrameRuntimeInputs()
                if mission_obs_mode is not None:
                    frame_inputs.has_mission_observation = True
                    frame_inputs.mission_observation = self._build_mission_observation_runtime_inputs(
                        mission_obs_mode,
                        truth=truth,
                        inst=inst_obj,
                    )
                frame_inputs.has_step_info = True
                frame_inputs.step_info = step_info_inputs
                frame_inputs.has_execution_step = True
                exec_inputs = ef_py.ExecutionStepRuntimeInputs()
                exec_inputs.truncated = bool(truncated)
                exec_inputs.safety = guard_inputs
                frame_inputs.execution_step = exec_inputs
                frame_products = ef_py.compute_execution_frame_runtime(frame_inputs)
        else:
            dt = float(getattr(self.sim, "get_time_step", lambda: 0.05)())
            dt = dt if dt > 1.0e-6 else 0.05
            aoa_valid = math.isfinite(float(curr_aoa)) and (abs(float(curr_aoa)) < 89.0) and (curr_ias > 10.0)
            safety_inputs = self._build_safety_runtime_inputs(
                cfg,
                finite_state_valid=True,
                truth=truth,
                airborne=bool(airborne),
                aoa_valid=bool(aoa_valid),
                curr_aoa=float(curr_aoa),
                curr_g=float(curr_g),
                curr_alt_agl=float(curr_alt_agl),
                curr_roll=float(curr_roll),
                gear_collapsed=bool(gear_collapsed),
                runway_surface_phase=bool(runway_surface_phase),
                on_runway_task=bool(on_runway_task),
                gear_stress=float(gear_stress),
                off_runway_steps=int(next_off_runway_steps),
                time_step_s=float(dt),
            )

            try:
                ils_valid = float(ils_vec[0])
                ils_loc = float(ils_vec[1])
                ils_gs = float(ils_vec[2])
                ils_dme = float(ils_vec[3])
            except Exception:
                ils_valid = 0.0
                ils_loc = 0.0
                ils_gs = 0.0
                ils_dme = 0.0

            sink_rate = abs(float(inst_vec[4])) if len(inst_vec) > 4 else 0.0
            if bool(approach_cfg.active):
                approach_inputs = self._build_approach_reward_inputs(
                    cfg,
                    ils_valid=float(ils_valid),
                    ils_loc=float(ils_loc),
                    ils_gs=float(ils_gs),
                    ils_dme=float(ils_dme),
                    curr_alt_agl=float(curr_alt_agl),
                    sink_rate_mps=float(sink_rate),
                )

            if self.waypoints:
                waypoint_turn_relief_activation = self._active_waypoint_turn_relief_activation(cfg, truth=truth, inst=inst_obj)
                waypoint_state = self._build_waypoint_step_state(
                    cfg,
                    truth=truth,
                    inst=inst_obj,
                    turn_relief_activation=float(waypoint_turn_relief_activation),
                )

            shaping_inputs = self._build_flight_shaping_runtime_inputs(
                cfg,
                steps=int(steps),
                truth=truth,
                inst_vec=inst_vec,
                curr_ias=float(curr_ias),
                curr_alt_agl=float(curr_alt_agl),
                curr_gear=float(curr_gear),
                curr_roll=float(curr_roll),
                heading_error_deg=float(heading_error_deg),
                ground_track_error_deg=float(ground_track_error_deg),
                waypoint_turn_relief_activation=float(waypoint_turn_relief_activation),
                preliftoff=bool(preliftoff),
                on_runway_task=bool(on_runway_task),
                airborne=bool(airborne),
                runway_cross_m=runway_cross_m,
                runway_wid_m=runway_wid_m,
                ils_valid=float(ils_valid),
                ils_loc=float(ils_loc),
            )

            objective_inputs = self._build_conditional_objective_inputs(
                truth,
                inst_vec,
                curr_ias=float(curr_ias),
                curr_ground_speed=float(curr_ground_speed),
                curr_gear=float(curr_gear),
                curr_alt_agl=float(curr_alt_agl),
                heading_error_deg=float(heading_error_deg),
                ground_track_error_deg=float(ground_track_error_deg),
                runway_cross_m=runway_cross_m,
                runway_from_threshold_m=runway_from_threshold_m,
                on_runway_geom=on_runway_geom,
                on_runway_task=bool(on_runway_task),
                on_ground=bool(on_ground),
            )

            if self._compiled_execution_episode_enabled():
                runtime_inputs = ef_py.ExecutionEpisodeRuntimeInputs()
                if mission_obs_mode is not None:
                    runtime_inputs.has_mission_observation = True
                    runtime_inputs.mission_observation = self._build_mission_observation_runtime_inputs(
                        mission_obs_mode,
                        truth=truth,
                        inst=inst_obj,
                    )
                runtime_inputs.has_step_info = True
                runtime_inputs.step_info = step_info_inputs
                runtime_inputs.has_execution_step = True
                exec_inputs = ef_py.ExecutionStepRuntimeInputs()
                exec_inputs.truncated = bool(truncated)
                exec_inputs.safety = safety_inputs
                if approach_inputs is not None:
                    exec_inputs.has_approach = True
                    exec_inputs.approach = approach_inputs
                if isinstance(waypoint_state, dict):
                    exec_inputs.has_waypoint = True
                    exec_inputs.waypoint = waypoint_state["inputs"]
                    exec_inputs.waypoint_episode_success = bool(waypoint_state["episode_success"])
                    exec_inputs.waypoint_episode_success_bonus = float(safety_cfg.waypoint_mission_success_bonus)
                if self._compiled_conditional_objectives and objective_inputs is not None:
                    exec_inputs.has_objectives = True
                    exec_inputs.objectives = list(self._compiled_conditional_objectives)
                    exec_inputs.objective_inputs = objective_inputs
                    exec_inputs.objective_shaping = self._objective_shaping_cfg
                runtime_inputs.execution_step = exec_inputs
                runtime_inputs.has_flight_shaping = True
                runtime_inputs.flight_shaping = shaping_inputs
                runtime_inputs.include_roll_stability = bool(float(getattr(truth, "z", 0.0)) < 100.0)
                frame_products = ef_py.compute_execution_episode_runtime(runtime_inputs)
            elif self._compiled_execution_frame_enabled():
                frame_inputs = ef_py.ExecutionFrameRuntimeInputs()
                if mission_obs_mode is not None:
                    frame_inputs.has_mission_observation = True
                    frame_inputs.mission_observation = self._build_mission_observation_runtime_inputs(
                        mission_obs_mode,
                        truth=truth,
                        inst=inst_obj,
                    )
                frame_inputs.has_step_info = True
                frame_inputs.step_info = step_info_inputs
                frame_inputs.has_execution_step = True
                exec_inputs = ef_py.ExecutionStepRuntimeInputs()
                exec_inputs.truncated = bool(truncated)
                exec_inputs.safety = safety_inputs
                if approach_inputs is not None:
                    exec_inputs.has_approach = True
                    exec_inputs.approach = approach_inputs
                if isinstance(waypoint_state, dict):
                    exec_inputs.has_waypoint = True
                    exec_inputs.waypoint = waypoint_state["inputs"]
                    exec_inputs.waypoint_episode_success = bool(waypoint_state["episode_success"])
                    exec_inputs.waypoint_episode_success_bonus = float(safety_cfg.waypoint_mission_success_bonus)
                if self._compiled_conditional_objectives and objective_inputs is not None:
                    exec_inputs.has_objectives = True
                    exec_inputs.objectives = list(self._compiled_conditional_objectives)
                    exec_inputs.objective_inputs = objective_inputs
                    exec_inputs.objective_shaping = self._objective_shaping_cfg
                frame_inputs.execution_step = exec_inputs
                frame_inputs.has_flight_shaping = True
                frame_inputs.flight_shaping = shaping_inputs
                frame_products = ef_py.compute_execution_frame_runtime(frame_inputs)

        entry = {
            "truth_obj": truth,
            "inst_obj": inst_obj,
            "steps": int(steps),
            "max_steps": int(max_steps),
            "mission_obs_mode": "" if mission_obs_mode is None else str(mission_obs_mode),
            "frame_products": frame_products,
            "truncated": bool(truncated),
            "curr_aoa": float(curr_aoa),
            "curr_roll": float(curr_roll),
            "curr_g": float(curr_g),
            "curr_gear": float(curr_gear),
            "curr_ias": float(curr_ias),
            "curr_ground_speed": float(curr_ground_speed),
            "curr_alt_agl": float(curr_alt_agl),
            "heading_error_deg": float(heading_error_deg),
            "ground_track_error_deg": float(ground_track_error_deg),
            "finite_state_valid": bool(finite_state_valid),
            "gear_collapsed": bool(gear_collapsed),
            "on_paved": bool(on_paved),
            "gear_stress": float(gear_stress),
            "on_ground": bool(on_ground),
            "airborne": bool(airborne),
            "preliftoff": bool(preliftoff),
            "on_runway_geom": on_runway_geom,
            "runway_along_m": runway_along_m,
            "runway_cross_m": runway_cross_m,
            "runway_from_threshold_m": runway_from_threshold_m,
            "runway_len_m": runway_len_m,
            "runway_wid_m": runway_wid_m,
            "runway_surface_phase": bool(runway_surface_phase),
            "on_runway_task": bool(on_runway_task),
            "next_off_runway_steps": int(next_off_runway_steps),
            "waypoint_turn_relief_activation": float(waypoint_turn_relief_activation),
            "waypoint_state": waypoint_state,
            "objective_inputs": objective_inputs,
            "approach_inputs": approach_inputs,
            "step_info_inputs": step_info_inputs,
            "safety_inputs": safety_inputs,
            "shaping_inputs": shaping_inputs,
            "ils_valid": float(ils_vec[0]) if len(ils_vec) > 0 else 0.0,
            "ils_loc": float(ils_vec[1]) if len(ils_vec) > 1 else 0.0,
            "ils_gs": float(ils_vec[2]) if len(ils_vec) > 2 else 0.0,
            "ils_dme": float(ils_vec[3]) if len(ils_vec) > 3 else 0.0,
        }
        if isinstance(self._runtime_eval_cache, dict):
            self._runtime_eval_cache["step_evaluation"] = entry
        return entry

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
        mode_cfg = self._waypoint_mode_reward_cfgs.get(str(mode), self._waypoint_mode_reward_cfgs.get("flyby", None))
        if mode_cfg is None:
            max_relief = float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_max", mode, 0.0))
            heading_relief = float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_turn_heading_relief_max", mode, max_relief))
            base_window_m = max(1.0, float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_window_m", mode, 3000.0)))
            min_turn_deg = max(0.0, float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_min_turn_deg", mode, 15.0)))
            angle_ref_deg = max(
                min_turn_deg + 1.0,
                float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_angle_ref_deg", mode, 90.0)),
            )
            power = float(self._cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_power", mode, 1.0))
        else:
            max_relief = float(mode_cfg.turn_relief_max)
            heading_relief = float(mode_cfg.heading_relief_max)
            base_window_m = max(1.0, float(mode_cfg.turn_relief_window_m))
            min_turn_deg = max(0.0, float(mode_cfg.turn_relief_min_turn_deg))
            angle_ref_deg = max(min_turn_deg + 1.0, float(mode_cfg.turn_relief_angle_ref_deg))
            power = float(mode_cfg.turn_relief_power)
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

        gstate = self._compute_waypoint_guidance_state(truth=truth, inst=inst)
        if gstate is None:
            return 0.0

        idx = int(gstate.get("idx", idx))
        n = int(gstate.get("count", n))

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
            next_turn_abs = abs(float(gstate.get("next_turn_abs_deg", 0.0)))
            dist_to_turn_start_m = max(
                0.0,
                float(gstate.get("dist_to_next_turn_start_m", gstate.get("distance_to_turn_m", 0.0))),
            )
            relief = max(relief, _turn_strength(next_turn_abs, dist_to_turn_start_m))

        if idx > 0:
            prev_turn_abs = abs(float(gstate.get("prev_turn_abs_deg", 0.0)))
            distance_from_prev_turn_m = max(
                0.0,
                float(gstate.get("distance_from_prev_turn_m", gstate.get("along_m", 0.0))),
            )
            relief = max(relief, _turn_strength(prev_turn_abs, distance_from_prev_turn_m))

        return float(np.clip(relief, 0.0, 1.0))

    def _compute_waypoint_guidance_state(self, truth=None, inst=None):
        result = self._query_route_guidance_result(truth=truth, inst=inst)
        if result is None:
            return None

        wp = self.waypoints[int(result.idx)]
        return {
            "idx": int(result.idx),
            "count": int(result.count),
            "wp": wp,
            "waypoint_mode": str(result.waypoint_mode),
            "sx": float(result.sx_m),
            "sy": float(result.sy_m),
            "lx": float(result.lx_m),
            "ly": float(result.ly_m),
            "dist_m": float(result.dist_m),
            "direct_to_track_deg": float(result.direct_to_track_deg),
            "desired_track_deg": float(result.desired_track_deg),
            "reward_desired_track_deg": float(result.reward_desired_track_deg),
            "xtk_m": float(result.xtk_m),
            "reward_xtk_m": float(result.reward_xtk_m),
            "along_m": float(result.along_m),
            "dtg_m": float(result.dtg_m),
            "reward_dtg_m": float(result.reward_dtg_m),
            "leg_len_m": float(result.leg_len_m),
            "ex": float(result.ex_m),
            "ey": float(result.ey_m),
            "waypoint_radius_m": float(result.waypoint_radius_m),
            "cmd_track_deg": float(result.cmd_track_deg),
            "use_direct_to": bool(result.use_direct_to),
            "direct_to_fix_guidance": bool(result.direct_to_fix_guidance),
            "next_turn_deg": float(result.next_turn_deg),
            "next_turn_abs_deg": float(result.next_turn_abs_deg),
            "prev_turn_abs_deg": float(result.prev_turn_abs_deg),
            "lead_turn_m": float(result.lead_turn_m),
            "sequence_gate_m": float(result.sequence_gate_m),
            "distance_to_turn_m": float(result.distance_to_turn_m),
            "dist_to_next_turn_start_m": float(result.dist_to_next_turn_start_m),
            "distance_from_prev_turn_m": float(result.distance_from_prev_turn_m),
            "final_leg": bool(result.final_leg),
            "passed_fix": bool(result.passed_fix),
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
        if isinstance(self._compiled_rewards_cfg, dict) and self._compiled_rewards_cfg:
            return self._compiled_rewards_cfg
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

    def _reset_command_chain(self, *, initial_truth=None, initial_inst=None, sync_to_kernel: bool = True) -> None:
        if self.agent_id is None:
            return
        try:
            sim_time_s = float(self.steps) * float(self.sim.get_time_step())
        except Exception:
            sim_time_s = 0.0
        self._leader_phase_manager.reset(
            self,
            sim_time_s=sim_time_s,
            truth=initial_truth,
            inst=initial_inst,
            sync_to_kernel=sync_to_kernel,
        )
        if sync_to_kernel:
            self._sync_kernel_mission_command()
            self._sync_kernel_command_chain()

    def _update_command_chain(self, sim_time: float, *, truth=None, inst=None, sync_to_kernel: bool = True) -> None:
        if self.agent_id is None:
            return
        self._leader_phase_manager.update(
            self,
            sim_time_s=float(sim_time),
            truth=truth,
            inst=inst,
            sync_to_kernel=sync_to_kernel,
        )
        if sync_to_kernel:
            self._sync_kernel_command_chain()

    def _landing_post_transition_terminal_ready(self) -> bool:
        if self.agent_id is None:
            return False
        try:
            truth = self.sim.get_agent_observation(self.agent_id)
        except Exception:
            truth = None
        try:
            inst = self.sim.get_instrument_state(self.agent_id)
        except Exception:
            inst = None
        if truth is None or inst is None:
            return False

        valid_runway_frame = False
        along_m = 0.0
        cross_m = 0.0
        try:
            valid_runway_frame, along_m, cross_m, _rw_len, _rw_wid = self.get_runway_local_frame(
                float(getattr(truth, "x", 0.0)),
                float(getattr(truth, "y", 0.0)),
            )
        except Exception:
            valid_runway_frame = False
        if not bool(valid_runway_frame):
            return False
        if float(along_m) < -1000.0:
            return False
        if abs(float(cross_m)) > 3500.0:
            return False

        try:
            beacon = self._nearest_ils_beacon(float(getattr(truth, "x", 0.0)), float(getattr(truth, "y", 0.0)))
        except Exception:
            beacon = None
        if beacon is None:
            return False
        runway_heading_err_deg = abs(
            (float(getattr(inst, "heading", 0.0)) - float(beacon.get("heading", 0.0)) + 180.0) % 360.0 - 180.0
        )
        if runway_heading_err_deg > 85.0:
            return False

        try:
            ils = self.get_ils_observation(
                float(getattr(truth, "x", 0.0)),
                float(getattr(truth, "y", 0.0)),
                float(getattr(inst, "alt_baro", 0.0)),
            )
        except Exception:
            return False
        dme_m = float(ils[3]) if len(ils) >= 4 else float("inf")
        return dme_m <= 18000.0

    def _post_waypoint_transition_ready(self) -> bool:
        if not isinstance(self.post_waypoint_transition, dict) or not self.post_waypoint_transition:
            return False
        next_cmd_code = int(self.post_waypoint_transition.get("command_code", 4))
        if not is_landing_command_code(next_cmd_code):
            return True

        c2_task_name = str(getattr(self, "c2_task_name", "")).strip().upper()
        if not c2_task_name:
            return self._landing_post_transition_terminal_ready()
        if bool(getattr(self, "c2_transitioned", False)):
            return False
        if c2_task_name != "TASK_RECOVER_LAND":
            return False
        if self.waypoints and int(getattr(self, "waypoint_idx", 0) or 0) >= len(self.waypoints):
            return True
        return self._landing_post_transition_terminal_ready()

    def _maybe_activate_post_waypoint_transition(self, *, sync_to_kernel: bool = True) -> dict | None:
        if not isinstance(self.post_waypoint_transition, dict) or not self.post_waypoint_transition:
            return None
        if self.waypoints and int(getattr(self, "waypoint_idx", 0) or 0) < len(self.waypoints):
            return None
        if not self._post_waypoint_transition_ready():
            return None
        return self._activate_post_waypoint_transition(sync_to_kernel=sync_to_kernel)

    def _defer_landing_post_transition_until_next_update(self) -> bool:
        if not isinstance(self.post_waypoint_transition, dict) or not self.post_waypoint_transition:
            return False
        next_cmd_code = int(self.post_waypoint_transition.get("command_code", 4))
        if not is_landing_command_code(next_cmd_code):
            return False
        scenario_data = getattr(self, "scenario_data", {}) or {}
        c2_cfg = scenario_data.get("c2_logic", None) if isinstance(scenario_data, dict) else None
        if isinstance(c2_cfg, dict) and c2_cfg:
            return True
        return bool(str(getattr(self, "c2_task_name", "")).strip())

    def _activate_post_waypoint_transition(self, *, sync_to_kernel: bool = True) -> dict | None:
        if not isinstance(self.post_waypoint_transition, dict) or not self.post_waypoint_transition:
            return None

        next_cmd = _clone_runtime_mission_command(self.post_waypoint_transition)
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

        self.mission_cmd = _normalize_runtime_mission_command(self.mission_cmd, self._task_order_spec())
        materialize_runtime_waypoint_cache(self.mission_cmd)
        self.scenario_data["mission_command"] = self.mission_cmd
        self._lnav_runtime_cfg = _build_lnav_runtime_config(self.mission_cmd)

        self.post_waypoint_transition = None
        self.mission_phase_name = str(next_cmd.get("phase_name", next_cmd.get("landing_mode", "post_waypoint"))).strip() or "post_waypoint"
        self.waypoints = []
        self.waypoint_idx = 0
        self._waypoint_prev_dist_m = None
        self.waypoint_total_route_length_m = 0.0
        self._cached_route_ref_id = None
        self._approach_prev_dme_m = None
        self._approach_prev_loc_abs = None
        self._approach_prev_gs_abs = None
        self._rebuild_spatial_geometry()
        if sync_to_kernel:
            self._sync_kernel_mission_command()
        return next_cmd

    def get_entity_id(self, name):
        return self.entities.get(name)
        
    def get_mission_observation(self, mode: str = "basic", *, truth=None, inst=None):
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
        mode_norm = str(mode).strip().lower()
        _ = self._mission_observation_mode_code(mode_norm)
        if self._compiled_mission_observation_enabled():
            cached = self._get_cached_step_evaluation(truth=truth, inst_obj=inst, mission_obs_mode=mode_norm)
            if isinstance(cached, dict):
                frame_products = cached.get("frame_products")
                if frame_products is not None and bool(getattr(frame_products, "mission_observation_evaluated", False)):
                    return np.asarray(frame_products.mission_observation.values, dtype=np.float32)
            products = self._compute_mission_observation_products(mode_norm, truth=truth, inst=inst)
            return np.asarray(products.values, dtype=np.float32)

        base = np.array(
            [
                float(self.mission_cmd["command_code"]),
                float(self.mission_cmd["target_heading"]),
                float(self.mission_cmd["target_altitude"]),
                float(self.mission_cmd["target_speed"]),
            ],
            dtype=np.float32,
        )
        if mode_norm in ("", "basic"):
            return base

        products = self._get_waypoint_nav_products(truth=truth, inst=inst)
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

    def _get_waypoint_nav_products(self, *, truth=None, inst=None):
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
        route_result = self._query_route_guidance_result(truth=truth, inst=inst)
        if route_result is None:
            return None
        return self._build_mission_nav_products(route_result, truth, inst)

    def _apply_waypoint_guidance_update(self, *, truth=None, inst=None) -> None:
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
                if truth is None:
                    try:
                        truth = self.sim.get_agent_observation(self.agent_id)
                    except Exception:
                        truth = None
                if inst is None:
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
    def update_behaviors(self, sim_time, *, truth=None, inst=None, sync_to_kernel: bool = True):
        self._apply_waypoint_guidance_update(truth=truth, inst=inst)

        self._update_command_chain(sim_time, truth=truth, inst=inst, sync_to_kernel=False)
        if not self._defer_landing_post_transition_until_next_update():
            self._maybe_activate_post_waypoint_transition(sync_to_kernel=False)
        if sync_to_kernel:
            self._sync_kernel_mission_command()
            self._sync_kernel_command_chain()

    def compute_full_step(self, obs, sim, steps, max_steps, *, truth=None, inst_state=None):
        cfg = self._compiled_rewards_cfg if isinstance(self._compiled_rewards_cfg, dict) and self._compiled_rewards_cfg else self.scenario_data.get("rewards", {})
        safety_cfg = self._safety_reward_cfg
        approach_cfg = self._approach_reward_cfg
        compiled_runtime_enabled = self._compiled_execution_step_enabled()
        term_reason_code = ef_py.TerminationReasonCode.Running
        
        # Get Truth State for Scoring
        if truth is None:
            truth = sim.get_agent_observation(self.agent_id)

        inst = obs["instruments"]
        inst_obj = inst_state
        if inst_obj is None:
            try:
                inst_obj = sim.get_instrument_state(self.agent_id)
            except Exception:
                inst_obj = None

        step_eval = self._prepare_step_evaluation(
            truth=truth,
            inst_obj=inst_obj,
            inst_vec=inst,
            ils_vec=np.asarray(inst[-4:], dtype=np.float32) if len(inst) >= 4 else np.zeros((4,), dtype=np.float32),
            steps=int(steps),
            max_steps=int(max_steps),
            mission_obs_mode=None,
        )
        frame_products = step_eval.get("frame_products") if isinstance(step_eval, dict) else None
        truncated = bool(step_eval.get("truncated", steps >= max_steps))
        curr_aoa = float(step_eval.get("curr_aoa", inst[5]))
        curr_roll = float(step_eval.get("curr_roll", inst[8]))
        curr_g = float(step_eval.get("curr_g", inst[10]))
        curr_gear = float(step_eval.get("curr_gear", inst[18]))
        curr_ias = float(step_eval.get("curr_ias", inst[0]))
        curr_ground_speed = float(step_eval.get("curr_ground_speed", math.hypot(float(getattr(truth, "vx", 0.0)), float(getattr(truth, "vy", 0.0)))))
        curr_alt_agl = float(step_eval.get("curr_alt_agl", inst[3] if len(inst) > 3 else float(getattr(truth, "z", 0.0))))
        heading_error_deg = float(step_eval.get("heading_error_deg", 0.0))
        ground_track_error_deg = float(step_eval.get("ground_track_error_deg", 0.0))
        finite_state_valid = bool(step_eval.get("finite_state_valid", True))

        if not finite_state_valid:
            if (
                frame_products is not None
                and bool(getattr(frame_products, "execution_step_evaluated", False))
            ):
                guard_products = frame_products.execution_step.safety
            else:
                guard_inputs = ef_py.SafetyRuntimeInputs()
                guard_inputs.finite_state_valid = False
                guard_inputs.crash_penalty = float(safety_cfg.crash_penalty)
                if compiled_runtime_enabled:
                    guard_products = self._compute_execution_step_runtime_products(
                        truncated=bool(truncated),
                        safety_inputs=guard_inputs,
                    ).safety
                else:
                    guard_products = ef_py.compute_safety_runtime(guard_inputs)
            status = [0.0] * 4
            status[3] = float(guard_products.status_flag)
            crash_pen = float(guard_products.crash_penalty)
            self.last_reward_breakdown = {
                "crash_penalty": crash_pen,
                "nan_guard": float(guard_products.nan_guard_marker),
                "total": crash_pen,
                "untracked": 0.0,
            }
            self.last_termination_reason = str(ef_py.termination_reason_name(guard_products.reason_code))
            return crash_pen, True, truncated, status

        self.off_runway_steps = int(step_eval.get("next_off_runway_steps", 0))
        if (
            compiled_runtime_enabled
            and frame_products is not None
            and bool(getattr(frame_products, "outcome_evaluated", False))
        ):
            reward, terminated, status = self._consume_compiled_episode_runtime(
                cfg=cfg,
                safety_cfg=safety_cfg,
                truth=truth,
                step_eval=step_eval,
                frame_products=frame_products,
            )
            self.prev_alt = truth.z
            self.prev_speed = curr_ias
            return reward, terminated, truncated, status

        gear_collapsed = bool(step_eval.get("gear_collapsed", False))
        gear_stress = float(step_eval.get("gear_stress", 0.0))
        on_ground = bool(step_eval.get("on_ground", False))
        airborne = bool(step_eval.get("airborne", False))
        preliftoff = bool(step_eval.get("preliftoff", True))
        on_runway_geom = step_eval.get("on_runway_geom")
        runway_along_m = step_eval.get("runway_along_m")
        runway_cross_m = step_eval.get("runway_cross_m")
        runway_from_threshold_m = step_eval.get("runway_from_threshold_m")
        runway_len_m = step_eval.get("runway_len_m")
        runway_wid_m = step_eval.get("runway_wid_m")
        runway_surface_phase = bool(step_eval.get("runway_surface_phase", False))
        on_runway_task = bool(step_eval.get("on_runway_task", False))
        self.off_runway_steps = int(step_eval.get("next_off_runway_steps", 0))
        safety_inputs = step_eval.get("safety_inputs")
        approach_inputs = step_eval.get("approach_inputs")
        ils_valid = float(step_eval.get("ils_valid", 0.0))
        ils_loc = float(step_eval.get("ils_loc", 0.0))
        ils_gs = float(step_eval.get("ils_gs", 0.0))
        ils_dme = float(step_eval.get("ils_dme", 0.0))

        safety_approach_runtime = None
        if (
            compiled_runtime_enabled
            and frame_products is not None
            and bool(getattr(frame_products, "execution_step_evaluated", False))
        ):
            safety_approach_runtime = frame_products.execution_step
            safety_terms = safety_approach_runtime.safety
        elif compiled_runtime_enabled:
            safety_approach_runtime = self._compute_execution_step_runtime_products(
                truncated=bool(truncated),
                safety_inputs=safety_inputs,
                approach_inputs=approach_inputs,
            )
            safety_terms = safety_approach_runtime.safety
        else:
            safety_terms = ef_py.compute_safety_runtime(safety_inputs)
        
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
        if float(safety_terms.crash_penalty) != 0.0:
            _add_reward_term("crash_penalty", float(safety_terms.crash_penalty))
            terminated = True
            status[3] = float(safety_terms.status_flag)
            term_reason_code = safety_terms.reason_code
        else:
            _add_reward_term("survival", float(safety_terms.survival))
            
        # 2. Progress Shaping (Reward for increasing Alt/Speed towards target)
        # Only apply if not crashed
        if not terminated:
            waypoint_turn_relief_activation = float(step_eval.get("waypoint_turn_relief_activation", 0.0))
            compiled_flight_shaping = None
            if (
                compiled_runtime_enabled
                and frame_products is not None
                and bool(getattr(frame_products, "flight_shaping_evaluated", False))
            ):
                compiled_flight_shaping = frame_products.flight_shaping

            if compiled_flight_shaping is not None:
                self._apply_compiled_flight_shaping_terms(
                    compiled_flight_shaping,
                    _add_reward_term,
                    include_roll_stability=bool(truth.z < 100.0),
                )
            else:
                self._apply_legacy_flight_shaping_terms(
                    cfg,
                    truth=truth,
                    inst=inst,
                    curr_ias=float(curr_ias),
                    curr_alt_agl=float(curr_alt_agl),
                    curr_gear=float(curr_gear),
                    curr_roll=float(curr_roll),
                    heading_error_deg=float(heading_error_deg),
                    ground_track_error_deg=float(ground_track_error_deg),
                    waypoint_turn_relief_activation=float(waypoint_turn_relief_activation),
                    airborne=bool(airborne),
                    preliftoff=bool(preliftoff),
                    on_runway_task=bool(on_runway_task),
                    runway_cross_m=runway_cross_m,
                    runway_wid_m=runway_wid_m,
                    ils_valid=float(ils_valid),
                    ils_loc=float(ils_loc),
                    steps=int(steps),
                    add_reward_term=_add_reward_term,
                )

            # 3. Safety Constraints (Penalties)
            if float(safety_terms.stall_penalty) != 0.0:
                _add_reward_term("stall_penalty", float(safety_terms.stall_penalty))
            if float(safety_terms.overload_penalty) != 0.0:
                _add_reward_term("overload_penalty", float(safety_terms.overload_penalty))
            if float(safety_terms.failfast_penalty) != 0.0:
                _add_reward_term("failfast_penalty", float(safety_terms.failfast_penalty))
                terminated = True
                status[3] = float(safety_terms.status_flag)
                term_reason_code = safety_terms.reason_code
            if float(safety_terms.gear_collapse_penalty) != 0.0:
                _add_reward_term("gear_collapse_penalty", float(safety_terms.gear_collapse_penalty))
                terminated = True
                status[3] = float(safety_terms.status_flag)
                term_reason_code = safety_terms.reason_code
            if float(safety_terms.off_runway_penalty) != 0.0:
                _add_reward_term("off_runway_penalty", float(safety_terms.off_runway_penalty))
            if float(safety_terms.gear_stress_penalty) != 0.0:
                _add_reward_term("gear_stress_penalty", float(safety_terms.gear_stress_penalty))
            if float(safety_terms.off_runway_terminate_penalty) != 0.0:
                _add_reward_term("off_runway_terminate_penalty", float(safety_terms.off_runway_terminate_penalty))
                terminated = True
                status[3] = float(safety_terms.status_flag)
                term_reason_code = safety_terms.reason_code

            # Approach / landing shaping via instrument-style ILS products only.
            # This keeps the task realism-first: the policy sees the same localizer /
            # glideslope / DME-style cues a pilot would see, without direct runway geometry.
            if approach_inputs is not None:
                if compiled_runtime_enabled and safety_approach_runtime is not None and bool(
                    getattr(safety_approach_runtime, "approach_evaluated", False)
                ):
                    approach_terms = safety_approach_runtime.approach
                else:
                    approach_terms = ef_py.compute_approach_reward_terms(approach_inputs)
                if float(approach_terms.approach_localizer) != 0.0:
                    _add_reward_term("approach_localizer", float(approach_terms.approach_localizer))
                if approach_inputs.localizer_improve_weight != 0.0 and approach_inputs.has_prev_loc:
                    _add_reward_term("approach_localizer_improve", float(approach_terms.approach_localizer_improve))
                if float(approach_terms.approach_glideslope) != 0.0:
                    _add_reward_term("approach_glideslope", float(approach_terms.approach_glideslope))
                if approach_inputs.glideslope_improve_weight != 0.0 and approach_inputs.has_prev_gs:
                    _add_reward_term("approach_glideslope_improve", float(approach_terms.approach_glideslope_improve))
                if approach_inputs.dme_progress_weight != 0.0 and approach_inputs.has_prev_dme and math.isfinite(float(ils_dme)):
                    _add_reward_term("approach_dme_progress", float(approach_terms.approach_dme_progress))
                if float(approach_terms.approach_capture_bonus) != 0.0:
                    _add_reward_term("approach_capture_bonus", float(approach_terms.approach_capture_bonus))
                if float(approach_terms.landing_sink_rate_penalty) != 0.0:
                    _add_reward_term("landing_sink_rate_penalty", float(approach_terms.landing_sink_rate_penalty))

                if bool(approach_terms.clear_history):
                    self._approach_prev_dme_m = None
                    self._approach_prev_loc_abs = None
                    self._approach_prev_gs_abs = None
                elif bool(approach_terms.next_prev_valid):
                    self._approach_prev_dme_m = float(approach_terms.next_prev_dme_m)
                    self._approach_prev_loc_abs = float(approach_terms.next_prev_loc_abs)
                    self._approach_prev_gs_abs = float(approach_terms.next_prev_gs_abs)

        # Update Prev State
        self.prev_alt = truth.z
        self.prev_speed = curr_ias

        # 4.x Waypoint Navigation (Cruise): reach a sequence of mission waypoints.
        # Note: This is a mission-level task (reach waypoints), not "fly a straight line".
        if not terminated:
            waypoint_state = step_eval.get("waypoint_state")
            if waypoint_state is None and self.waypoints:
                waypoint_state = self._build_waypoint_step_state(
                    cfg,
                    truth=truth,
                    inst=inst_obj,
                    turn_relief_activation=float(waypoint_turn_relief_activation),
                )
            if isinstance(waypoint_state, dict):
                idx = int(waypoint_state["idx"])
                n = int(waypoint_state["count"])
                status[0] = float(waypoint_state["dist_m"])
                status[1] = float(idx)
                status[2] = float(n)

                waypoint_inputs = waypoint_state["inputs"]
                waypoint_runtime = None
                if (
                    compiled_runtime_enabled
                    and frame_products is not None
                    and bool(getattr(frame_products, "execution_step_evaluated", False))
                    and bool(getattr(frame_products.execution_step, "waypoint_evaluated", False))
                ):
                    waypoint_runtime = frame_products.execution_step
                    waypoint_terms = waypoint_runtime.waypoint
                elif compiled_runtime_enabled:
                    waypoint_runtime = self._compute_execution_step_runtime_products(
                        truncated=bool(truncated),
                        waypoint_inputs=waypoint_inputs,
                        waypoint_episode_success=bool(waypoint_state["episode_success"]),
                        waypoint_episode_success_bonus=float(safety_cfg.waypoint_mission_success_bonus),
                    )
                    waypoint_terms = waypoint_runtime.waypoint
                else:
                    waypoint_terms = ef_py.compute_waypoint_reward_terms(waypoint_inputs)

                if waypoint_inputs.progress_weight != 0.0 and waypoint_inputs.has_prev_dist:
                    _add_reward_term("waypoint_progress", float(waypoint_terms.waypoint_progress))
                if waypoint_inputs.distance_weight != 0.0:
                    _add_reward_term("waypoint_distance", float(waypoint_terms.waypoint_distance))
                if float(waypoint_terms.waypoint_cross_track) != 0.0:
                    _add_reward_term("waypoint_cross_track", float(waypoint_terms.waypoint_cross_track))
                if float(waypoint_terms.waypoint_proximity) != 0.0:
                    _add_reward_term("waypoint_proximity", float(waypoint_terms.waypoint_proximity))

                self._waypoint_prev_dist_m = float(waypoint_terms.next_prev_dist_m) if bool(waypoint_terms.next_prev_dist_valid) else None
                arrived = bool(waypoint_terms.arrived)

                if arrived:
                    _add_reward_term("waypoint_reached_bonus", float(waypoint_terms.waypoint_reached_bonus))
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
                        landing_transition_pending = bool(
                            isinstance(self.post_waypoint_transition, dict)
                            and self.post_waypoint_transition
                            and is_landing_command_code(self.post_waypoint_transition.get("command_code", 4))
                        )
                        transitioned = None
                        if not self._defer_landing_post_transition_until_next_update():
                            transitioned = self._maybe_activate_post_waypoint_transition()
                        if isinstance(transitioned, dict):
                            _add_reward_term(
                                "phase_transition_bonus",
                                float(transitioned.get("transition_reward", cfg.get("phase_transition_bonus", 600.0))),
                            )
                            status[0] = 0.0
                            status[1] = 0.0
                        elif landing_transition_pending:
                            status[0] = 0.0
                            status[1] = float(self.waypoint_idx)
                        else:
                            if waypoint_runtime is not None and bool(
                                getattr(waypoint_runtime, "waypoint_episode_success", False)
                            ):
                                _add_reward_term(
                                    "waypoint_success_bonus",
                                    float(waypoint_runtime.waypoint_episode_success_bonus),
                                )
                                term_reason_code = waypoint_runtime.reason_code
                            else:
                                _add_reward_term("waypoint_success_bonus", float(safety_cfg.waypoint_mission_success_bonus))
                                term_reason_code = ef_py.TerminationReasonCode.SuccessWaypoint
                            terminated = True
                            status[3] = 1.0
            
        # 5. Objectives (Binary Success)
        # Only evaluate success conditions if we did not already terminate due to a failure mode.
        if not terminated:
            objective_inputs = step_eval.get("objective_inputs")
            if objective_inputs is None:
                objective_inputs = self._build_conditional_objective_inputs(
                    truth,
                    inst,
                    curr_ias=float(curr_ias),
                    curr_ground_speed=float(curr_ground_speed),
                    curr_gear=float(curr_gear),
                    curr_alt_agl=float(curr_alt_agl),
                    heading_error_deg=float(heading_error_deg),
                    ground_track_error_deg=float(ground_track_error_deg),
                    runway_cross_m=runway_cross_m,
                    runway_from_threshold_m=runway_from_threshold_m,
                    on_runway_geom=on_runway_geom,
                    on_runway_task=bool(on_runway_task),
                    on_ground=bool(on_ground),
                )
            if (
                compiled_runtime_enabled
                and frame_products is not None
                and bool(getattr(frame_products, "execution_step_evaluated", False))
                and bool(getattr(frame_products.execution_step, "objective_evaluated", False))
            ):
                objective_runtime = frame_products.execution_step
                if int(objective_runtime.objective_status_count) >= 1:
                    status[0] = float(objective_runtime.status0)
                if int(objective_runtime.objective_status_count) >= 2:
                    status[1] = float(objective_runtime.status1)
                if int(objective_runtime.objective_status_count) >= 3:
                    status[2] = float(objective_runtime.status2)
                if int(objective_runtime.matched_objective_index) >= 0:
                    if float(objective_runtime.objective.success_runway_cross_penalty) != 0.0:
                        _add_reward_term(
                            "success_runway_cross_penalty",
                            float(objective_runtime.objective.success_runway_cross_penalty),
                        )
                    if float(objective_runtime.objective.success_ground_track_error_penalty) != 0.0:
                        _add_reward_term(
                            "success_ground_track_error_penalty",
                            float(objective_runtime.objective.success_ground_track_error_penalty),
                        )
                    _add_reward_term("objective_bonus", float(objective_runtime.objective.objective_bonus))
                    terminated = True
                    status[3] = 1.0
                    term_reason_code = objective_runtime.reason_code
            elif compiled_runtime_enabled:
                objective_runtime = self._compute_execution_step_runtime_products(
                    truncated=bool(truncated),
                    objective_specs=self._compiled_conditional_objectives,
                    objective_inputs=objective_inputs,
                )
                if int(objective_runtime.objective_status_count) >= 1:
                    status[0] = float(objective_runtime.status0)
                if int(objective_runtime.objective_status_count) >= 2:
                    status[1] = float(objective_runtime.status1)
                if int(objective_runtime.objective_status_count) >= 3:
                    status[2] = float(objective_runtime.status2)
                if int(objective_runtime.matched_objective_index) >= 0:
                    if float(objective_runtime.objective.success_runway_cross_penalty) != 0.0:
                        _add_reward_term(
                            "success_runway_cross_penalty",
                            float(objective_runtime.objective.success_runway_cross_penalty),
                        )
                    if float(objective_runtime.objective.success_ground_track_error_penalty) != 0.0:
                        _add_reward_term(
                            "success_ground_track_error_penalty",
                            float(objective_runtime.objective.success_ground_track_error_penalty),
                        )
                    _add_reward_term("objective_bonus", float(objective_runtime.objective.objective_bonus))
                    terminated = True
                    status[3] = 1.0
                    term_reason_code = objective_runtime.reason_code
            else:
                for obj in self._compiled_conditional_objectives:
                    products = ef_py.evaluate_conditional_objective(obj, objective_inputs, self._objective_shaping_cfg)
                    if int(products.status_count) >= 1:
                        status[0] = float(products.status0)
                    if int(products.status_count) >= 2:
                        status[1] = float(products.status1)
                    if int(products.status_count) >= 3:
                        status[2] = float(products.status2)
                    if not bool(products.matched):
                        continue
                    if float(products.success_runway_cross_penalty) != 0.0:
                        _add_reward_term("success_runway_cross_penalty", float(products.success_runway_cross_penalty))
                    if float(products.success_ground_track_error_penalty) != 0.0:
                        _add_reward_term("success_ground_track_error_penalty", float(products.success_ground_track_error_penalty))
                    _add_reward_term("objective_bonus", float(products.objective_bonus))
                    terminated = True
                    # Convention: status[3] is a terminal outcome flag.
                    # -1.0 = failure (set by fail-fast blocks above)
                    # +1.0 = success
                    status[3] = 1.0
                    term_reason_code = ef_py.TerminationReasonCode.SuccessObjective
                    break
                    
        tracked_total = float(sum(rb.values())) if rb else 0.0
        rb["tracked_total"] = tracked_total
        rb["untracked"] = float(reward - tracked_total)
        rb["total"] = float(reward)
        self.last_reward_breakdown = rb
        final_reason = ef_py.finalize_termination_reason(
            term_reason_code,
            bool(terminated),
            bool(truncated),
            float(status[3]),
        )
        self.last_termination_reason = str(ef_py.termination_reason_name(final_reason))

        return reward, terminated, truncated, status
