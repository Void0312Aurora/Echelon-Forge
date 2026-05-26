import os
import math
from typing import Any
import ef_py
import numpy as np
from python.scenario_compiler import (
    ApproachRewardConfig,
    LNavRuntimeConfig,
    SafetyRewardConfig,
    WaypointModeRewardConfig,
    _build_lnav_runtime_config,
)
from python.scenario.runtime import (
    resolve_active_controllable_roster,
)
from .common import (
    execution_step_runtime_mode_enabled,
    normalize_execution_step_runtime_mode,
    normalize_flight_shaping_backend,
    safe_json_dict_loads as _safe_json_dict_loads,
    stable_json_dumps as _stable_json_dumps,
)
from .loading import (
    align_task_only_mission_shell_with_task_order as _align_task_only_mission_shell_with_task_order_impl,
    apply_compiled_runtime_metadata as _apply_compiled_runtime_metadata_impl,
    begin_loaded_world as _begin_loaded_world_impl,
    finalize_loaded_world as _finalize_loaded_world_impl,
    get_active_roster_member as _get_active_roster_member_impl,
    get_active_roster_refs as _get_active_roster_refs_impl,
    load_compiled_scenario as _load_compiled_scenario_impl,
    load_instantiated_scenario as _load_instantiated_scenario_impl,
    load_prepared_world as _load_prepared_world_impl,
    load_scenario as _load_scenario_impl,
    load_scenario_data as _load_scenario_data_impl,
    mission_cmd_has_valid_runtime_waypoint_cache as _mission_cmd_has_valid_runtime_waypoint_cache_impl,
    normalize_mission_command_dict as _normalize_mission_command_dict_impl,
    prepare_load_seed as _prepare_load_seed_impl,
    set_randomization_overrides as _set_randomization_overrides_impl,
    task_order_spec as _task_order_spec_impl,
)
from .route_generation import (
    generate_route_waypoints as _generate_route_waypoints_impl,
    rotate_waypoints_inplace as _rotate_waypoints_inplace_impl,
    route_turn_cost_m as _route_turn_cost_m_impl,
    sample_entity_spawn as _sample_entity_spawn_impl,
    sample_int as _sample_int_impl,
    sample_uniform as _sample_uniform_impl,
    turn_radius_m as _turn_radius_m_impl,
)
from .runtime_state import (
    SCENARIO_LOADER_STATE_SHELL_ATTRS as _SCENARIO_LOADER_STATE_SHELL_ATTRS,
    apply_execution_episode_runtime_fields as _apply_execution_episode_runtime_fields_impl,
    apply_execution_episode_state as _apply_execution_episode_state_impl,
    build_execution_episode_state as _build_execution_episode_state_impl,
    make_scenario_loader_state_shell as _make_scenario_loader_state_shell_impl,
)
from .mission_observation import (
    build_mission_nav_products as _build_mission_nav_products_impl,
    build_mission_observation_runtime_inputs as _build_mission_observation_runtime_inputs_impl,
    compiled_mission_observation_enabled as _compiled_mission_observation_enabled_impl,
    compute_mission_observation_products as _compute_mission_observation_products_impl,
    get_mission_observation as _get_mission_observation_impl,
    get_waypoint_nav_products as _get_waypoint_nav_products_impl,
    mission_nav_inputs as _mission_nav_inputs_impl,
    mission_observation_mode_code as _mission_observation_mode_code_impl,
    python_owned_mission_observation_mode as _python_owned_mission_observation_mode_impl,
)
from .step_evaluation import (
    build_step_evaluation_batch_env_state as _build_step_evaluation_batch_env_state_impl,
    build_step_evaluation_inputs as _build_step_evaluation_inputs_impl,
    build_step_info_runtime_inputs as _build_step_info_runtime_inputs_impl,
    compiled_step_info_enabled as _compiled_step_info_enabled_impl,
    compute_step_info_runtime_products as _compute_step_info_runtime_products_impl,
    get_cached_step_evaluation as _get_cached_step_evaluation_impl,
    prepare_step_evaluation as _prepare_step_evaluation_impl,
)
from .execution_runtime import (
    apply_legacy_flight_shaping_terms as _apply_legacy_flight_shaping_terms_impl,
    build_execution_episode_controller_shadow_config as _build_execution_episode_controller_shadow_config_impl,
    compare_execution_episode_controller_shadow as _compare_execution_episode_controller_shadow_impl,
    compare_execution_episode_runtime_products as _compare_execution_episode_runtime_products_impl,
    compute_full_step as _compute_full_step_impl,
    consume_compiled_episode_runtime as _consume_compiled_episode_runtime_impl,
    consume_execution_episode_controller_mainline_step as _consume_execution_episode_controller_mainline_step_impl,
    execution_episode_status_vector as _execution_episode_status_vector_impl,
)
from .navigation_runtime import (
    active_waypoint_arrival_products as _active_waypoint_arrival_products_impl,
    active_waypoint_mode as _active_waypoint_mode_impl,
    active_waypoint_turn_relief_activation as _active_waypoint_turn_relief_activation_impl,
    apply_waypoint_guidance_update as _apply_waypoint_guidance_update_impl,
    build_waypoint_reward_inputs as _build_waypoint_reward_inputs_impl,
    build_waypoint_step_state as _build_waypoint_step_state_impl,
    cfg_value_for_waypoint_mode as _cfg_value_for_waypoint_mode_impl,
    command_tracking_error_deg as _command_tracking_error_deg_impl,
    compute_waypoint_guidance_state as _compute_waypoint_guidance_state_impl,
    current_route_target_altitude_m as _current_route_target_altitude_m_impl,
    formation_slot_offsets_m as _formation_slot_offsets_m_impl,
    get_waypoint_visualization_products as _get_waypoint_visualization_products_impl,
    ground_track_from_inst as _ground_track_from_inst_impl,
    normalize_waypoint_mode as _normalize_waypoint_mode_impl,
    query_route_guidance_result as _query_route_guidance_result_impl,
    route_leg_frame as _route_leg_frame_impl,
    route_reference_xy as _route_reference_xy_impl,
    slot_target_altitude_for_waypoint as _slot_target_altitude_for_waypoint_impl,
    turn_lead_distance_m as _turn_lead_distance_m_impl,
)
from .behavior_runtime import (
    BEHAVIOR_PHASE_OWNER_ATTRS as _BEHAVIOR_PHASE_OWNER_ATTRS,
    COMMAND_CHAIN_OWNER_ATTRS as _COMMAND_CHAIN_OWNER_ATTRS,
    activate_post_waypoint_transition as _activate_post_waypoint_transition_impl,
    apply_pending_landing_vector as _apply_pending_landing_vector_impl,
    build_scripted_opponents as _build_scripted_opponents_impl,
    defer_landing_post_transition_until_next_update as _defer_landing_post_transition_until_next_update_impl,
    ensure_behavior_phase_owner as _ensure_behavior_phase_owner_impl,
    ensure_command_chain_owner as _ensure_command_chain_owner_impl,
    hierarchical_command_chain_active as _hierarchical_command_chain_active_impl,
    landing_post_transition_terminal_ready as _landing_post_transition_terminal_ready_impl,
    make_behavior_phase_owner as _make_behavior_phase_owner_impl,
    make_command_chain_owner as _make_command_chain_owner_impl,
    make_scripted_opponent_runtime as _make_scripted_opponent_runtime_impl,
    maybe_activate_post_waypoint_transition as _maybe_activate_post_waypoint_transition_impl,
    post_waypoint_transition_ready as _post_waypoint_transition_ready_impl,
    reset_behavior_phase_owner as _reset_behavior_phase_owner_impl,
    reset_command_chain as _reset_command_chain_impl,
    reset_command_chain_owner as _reset_command_chain_owner_impl,
    reset_scripted_opponents as _reset_scripted_opponents_impl,
    sync_kernel_command_chain as _sync_kernel_command_chain_impl,
    sync_kernel_mission_command as _sync_kernel_mission_command_impl,
    update_behaviors as _update_behaviors_impl,
    update_command_chain as _update_command_chain_impl,
    update_command_chain_only as _update_command_chain_only_impl,
    update_nonhierarchical_behaviors as _update_nonhierarchical_behaviors_impl,
    update_scripted_opponents as _update_scripted_opponents_impl,
)
from .reward_runtime import (
    add_breakdown_term as _add_breakdown_term_impl,
    apply_air_combat_reward_surface as _apply_air_combat_reward_surface_impl,
    apply_naval_reward_surface as _apply_naval_reward_surface_impl,
    apply_compiled_flight_shaping_terms as _apply_compiled_flight_shaping_terms_impl,
    build_approach_reward_inputs as _build_approach_reward_inputs_impl,
    build_conditional_objective_inputs as _build_conditional_objective_inputs_impl,
    build_flight_shaping_runtime_inputs as _build_flight_shaping_runtime_inputs_impl,
    build_neutral_execution_safety_inputs as _build_neutral_execution_safety_inputs_impl,
    build_objective_shaping_config as _build_objective_shaping_config_impl,
    build_safety_runtime_inputs as _build_safety_runtime_inputs_impl,
    compile_conditional_objectives as _compile_conditional_objectives_impl,
    compiled_execution_episode_enabled as _compiled_execution_episode_enabled_impl,
    compiled_execution_frame_enabled as _compiled_execution_frame_enabled_impl,
    compiled_execution_step_enabled as _compiled_execution_step_enabled_impl,
    compute_execution_step_runtime_products as _compute_execution_step_runtime_products_impl,
    compute_flight_shaping_products as _compute_flight_shaping_products_impl,
)
from .preparation_runtime import (
    parse_waypoints as _parse_waypoints_impl,
    randomize_mission as _randomize_mission_impl,
    randomize_task_order as _randomize_task_order_impl,
)
from .spatial_runtime import (
    apply_world_yaw as _apply_world_yaw_impl,
    bearing_to_deg as _bearing_to_deg_impl,
    extract_ils_beacons as _extract_ils_beacons_impl,
    get_ils_observation as _get_ils_observation_impl,
    get_runway_local_frame as _get_runway_local_frame_impl,
    instrument_scalar as _instrument_scalar_impl,
    nearest_ils_beacon as _nearest_ils_beacon_impl,
    query_runway_frame_result as _query_runway_frame_result_impl,
    rebuild_spatial_geometry as _rebuild_spatial_geometry_impl,
    rotate_xy_clockwise as _rotate_xy_clockwise_impl,
    wrap_angle_deg as _wrap_angle_deg_impl,
)


class ScenarioLoader:
    _STATE_SHELL_ATTRS = _SCENARIO_LOADER_STATE_SHELL_ATTRS
    _BEHAVIOR_PHASE_OWNER_ATTRS = _BEHAVIOR_PHASE_OWNER_ATTRS
    _COMMAND_CHAIN_OWNER_ATTRS = _COMMAND_CHAIN_OWNER_ATTRS

    def __getattr__(self, name):
        if name in self._BEHAVIOR_PHASE_OWNER_ATTRS:
            owner = self.__dict__.get("_behavior_phase_owner", None)
            if owner is None:
                owner = _ensure_behavior_phase_owner_impl(self)
            return getattr(owner, name)
        state_shell = self.__dict__.get("_state_shell", None)
        if state_shell is not None and name in self._STATE_SHELL_ATTRS:
            return getattr(state_shell, name)
        if name in self._COMMAND_CHAIN_OWNER_ATTRS:
            owner = self.__dict__.get("_command_chain_owner", None)
            if owner is None:
                owner = _ensure_command_chain_owner_impl(self)
            return getattr(owner, name)
        raise AttributeError(f"{type(self).__name__!s} object has no attribute {name!r}")

    def __setattr__(self, name, value):
        if name in self._BEHAVIOR_PHASE_OWNER_ATTRS:
            owner = self.__dict__.get("_behavior_phase_owner", None)
            if owner is None:
                owner = _ensure_behavior_phase_owner_impl(self)
            setattr(owner, name, value)
            state_shell = self.__dict__.get("_state_shell", None)
            if state_shell is not None and name in self._STATE_SHELL_ATTRS:
                setattr(state_shell, name, value)
            return
        state_shell = self.__dict__.get("_state_shell", None)
        if state_shell is not None and name in self._STATE_SHELL_ATTRS:
            setattr(state_shell, name, value)
            return
        if name in self._COMMAND_CHAIN_OWNER_ATTRS:
            owner = self.__dict__.get("_command_chain_owner", None)
            if owner is None:
                owner = _ensure_command_chain_owner_impl(self)
            setattr(owner, name, value)
            return
        object.__setattr__(self, name, value)

    def __init__(self, sim_kernel):
        self.sim = sim_kernel
        self.scenario_data = {}
        self.entities = {} # map name -> entity_id
        self.active_roster = []
        self.agent_id = None
        self.steps = 0
        self.captured_time = 0.0
        self.max_contacts = 10
        self.max_rwr = 4
        self._state_shell = _make_scenario_loader_state_shell_impl()

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
        self._behavior_phase_owner = _make_behavior_phase_owner_impl()
        self._command_chain_owner = _make_command_chain_owner_impl(self)
        self._spatial_geometry = None
        self._compiled_scenario = None
        self._compiled_runtime_metadata = None
        self._scenario_source_path = None
        self._compiled_conditional_objectives = []
        self._objective_shaping_cfg = None
        self._compiled_rewards_cfg: dict = {}
        self._compiled_meta_cfg: dict = {}
        self._waypoint_mode_reward_cfgs: dict[str, WaypointModeRewardConfig] = {}
        self._approach_reward_cfg = ApproachRewardConfig()
        self._safety_reward_cfg = SafetyRewardConfig()
        self._lnav_runtime_cfg = LNavRuntimeConfig()
        self._runtime_eval_cache: dict[str, object] = {}
        self.primary_target_id: int | None = None
        self.primary_target_name: str = ""
        self._air_combat_reward_last_report_id = 0
        self._scripted_opponent_runtime = _make_scripted_opponent_runtime_impl()
        self.scripted_opponents: dict[int, Any] = self._scripted_opponent_runtime.controllers
        self.scripted_opponent_reports: dict[int, dict[str, Any]] = self._scripted_opponent_runtime.reports
        self.set_execution_step_runtime_mode("compiled")
        self.set_flight_shaping_backend(None)

    def set_execution_step_runtime_mode(self, mode: str | None) -> None:
        self.execution_step_runtime_mode = normalize_execution_step_runtime_mode(mode)
        self.use_compiled_execution_step_runtime = execution_step_runtime_mode_enabled(self.execution_step_runtime_mode)

    def set_flight_shaping_backend(self, backend: str | None) -> None:
        normalized = normalize_flight_shaping_backend(backend)
        if normalized not in {"auto", "legacy", "compiled", "gpu_host"}:
            raise ValueError(f"Unknown flight_shaping_backend: {backend!r}")
        self.flight_shaping_backend = normalized

    def _flight_shaping_backend_mode(self) -> str:
        backend = str(getattr(self, "flight_shaping_backend", "auto") or "auto").strip().lower()
        if backend == "auto":
            return "compiled" if bool(getattr(self, "use_compiled_execution_step_runtime", True)) else "legacy"
        return backend

    def reset_runtime_eval_cache(self) -> None:
        self._runtime_eval_cache = {}

    def build_execution_episode_state(self):
        return _build_execution_episode_state_impl(self)

    def apply_execution_episode_state(self, state) -> None:
        _apply_execution_episode_state_impl(self, state)

    def apply_execution_episode_runtime_fields(
        self,
        state,
        *,
        include_navigation_state: bool = True,
        include_navigation_structure: bool = True,
    ) -> None:
        _apply_execution_episode_runtime_fields_impl(
            self,
            state,
            include_navigation_state=include_navigation_state,
            include_navigation_structure=include_navigation_structure,
        )

    def _task_order_spec(self) -> dict:
        return _task_order_spec_impl(self)

    def _normalize_mission_command_dict(self, cmd: dict | None) -> dict:
        return _normalize_mission_command_dict_impl(self, cmd)

    def _align_task_only_mission_shell_with_task_order(self) -> None:
        _align_task_only_mission_shell_with_task_order_impl(self)

    def _sample_uniform(self, value, default: float) -> float:
        return _sample_uniform_impl(self, value, default)

    def _sample_int(self, value, default: int) -> int:
        return _sample_int_impl(self, value, default)

    def _sample_entity_spawn(self, ent_cfg: dict) -> tuple[list[float], list[float], float, float, float]:
        return _sample_entity_spawn_impl(self, ent_cfg)

    def _rotate_waypoints_inplace(self, waypoints: list[dict]) -> None:
        _rotate_waypoints_inplace_impl(self, waypoints)

    def _generate_route_waypoints(self, cfg: dict) -> list[dict]:
        return _generate_route_waypoints_impl(self, cfg)

    def _turn_radius_m(self, speed_mps: float, bank_limit_deg: float) -> float:
        return _turn_radius_m_impl(self, speed_mps, bank_limit_deg)

    def _route_turn_cost_m(
        self,
        turn_abs_deg: float,
        *,
        speed_mps: float,
        bank_limit_deg: float,
        cost_scale: float,
    ) -> float:
        return _route_turn_cost_m_impl(
            self,
            turn_abs_deg,
            speed_mps=speed_mps,
            bank_limit_deg=bank_limit_deg,
            cost_scale=cost_scale,
        )

    def set_randomization_overrides(self, overrides: dict | None) -> None:
        _set_randomization_overrides_impl(self, overrides)

    def load_scenario(self, json_path, seed=42):
        return _load_scenario_impl(self, json_path, seed=seed)

    def load_compiled_scenario(self, compiled_scenario, seed=42):
        return _load_compiled_scenario_impl(self, compiled_scenario, seed=seed)

    def load_scenario_data(self, scenario_data: dict, seed=42, *, source_path: str | None = None):
        return _load_scenario_data_impl(self, scenario_data, seed=seed, source_path=source_path)

    def get_active_roster_member(
        self,
        *,
        entity_id: int | None = None,
        entity_name: str | None = None,
        role_code: int | None = None,
        formation_role_id: str | None = None,
    ):
        return _get_active_roster_member_impl(
            self,
            entity_id=entity_id,
            entity_name=entity_name,
            role_code=role_code,
            formation_role_id=formation_role_id,
        )

    def get_active_roster_refs(self, *, world_index: int | None = None):
        return _get_active_roster_refs_impl(self, world_index=world_index)

    def _prepare_load_seed(self, seed=42) -> int:
        return _prepare_load_seed_impl(self, seed=seed)

    def _begin_loaded_world(self, *, scenario_data: dict) -> None:
        _begin_loaded_world_impl(self, scenario_data=scenario_data)

    def _ensure_command_chain_owner(self):
        return _ensure_command_chain_owner_impl(self)

    def _reset_command_chain_owner(self):
        return _reset_command_chain_owner_impl(self)

    def _ensure_behavior_phase_owner(self):
        return _ensure_behavior_phase_owner_impl(self)

    def _reset_behavior_phase_owner(self):
        return _reset_behavior_phase_owner_impl(self)

    def _apply_compiled_runtime_metadata(self) -> None:
        _apply_compiled_runtime_metadata_impl(self)

    def _finalize_loaded_world(self, *, initial_truth=None, initial_inst=None, sync_to_kernel: bool = True):
        return _finalize_loaded_world_impl(
            self,
            initial_truth=initial_truth,
            initial_inst=initial_inst,
            sync_to_kernel=sync_to_kernel,
        )

    @staticmethod
    def _mission_cmd_has_valid_runtime_waypoint_cache(mission_cmd: dict[str, Any] | None) -> bool:
        return _mission_cmd_has_valid_runtime_waypoint_cache_impl(mission_cmd)

    def load_prepared_world(
        self,
        prepared_world,
        *,
        seed=42,
        initial_truth=None,
        initial_inst=None,
        sync_to_kernel: bool = True,
    ):
        return _load_prepared_world_impl(
            self,
            prepared_world,
            seed=seed,
            initial_truth=initial_truth,
            initial_inst=initial_inst,
            sync_to_kernel=sync_to_kernel,
        )

    def _load_instantiated_scenario(self, seed=42):
        return _load_instantiated_scenario_impl(self, seed=seed)

    def _extract_ils_beacons(self):
        return _extract_ils_beacons_impl(self)

    def _nearest_ils_beacon(self, x_m: float, y_m: float):
        return _nearest_ils_beacon_impl(self, x_m, y_m)

    def _rebuild_spatial_geometry(self) -> None:
        _rebuild_spatial_geometry_impl(self)

    def _query_route_guidance_result(self, truth=None, inst=None):
        return _query_route_guidance_result_impl(self, truth=truth, inst=inst)

    def _query_runway_frame_result(self, x_m: float, y_m: float):
        return _query_runway_frame_result_impl(self, x_m, y_m)

    def get_runway_local_frame(self, x_m: float, y_m: float):
        return _get_runway_local_frame_impl(self, x_m, y_m)

    def get_ils_observation(self, x_m: float, y_m: float, alt_m: float):
        return _get_ils_observation_impl(self, x_m, y_m, alt_m)

    def _randomize_mission(self):
        _randomize_mission_impl(self)

    def _randomize_task_order(self):
        _randomize_task_order_impl(self)

    @staticmethod
    def _rotate_xy_clockwise(x, y, origin_x, origin_y, yaw_deg):
        return _rotate_xy_clockwise_impl(x, y, origin_x, origin_y, yaw_deg)

    def _apply_world_yaw(self, yaw_deg, origin_x=0.0, origin_y=0.0):
        _apply_world_yaw_impl(self, yaw_deg, origin_x=origin_x, origin_y=origin_y)

    def _parse_waypoints(self) -> None:
        _parse_waypoints_impl(self)

    def _normalize_waypoint_mode(self, mode_value) -> str:
        return _normalize_waypoint_mode_impl(mode_value)

    def _cfg_value_for_waypoint_mode(self, cfg: dict, key: str, mode_value, default=None):
        return _cfg_value_for_waypoint_mode_impl(self, cfg, key, mode_value, default)

    def _active_waypoint_mode(self, idx: int | None = None) -> str:
        return _active_waypoint_mode_impl(self, idx=idx)

    def _active_waypoint_arrival_products(self):
        return _active_waypoint_arrival_products_impl(self)

    def get_waypoint_visualization_products(self):
        return _get_waypoint_visualization_products_impl(self)

    @staticmethod
    def _bearing_to_deg(dx: float, dy: float) -> float:
        return _bearing_to_deg_impl(dx, dy)

    @staticmethod
    def _wrap_angle_deg(angle_deg: float) -> float:
        return _wrap_angle_deg_impl(angle_deg)

    @staticmethod
    def _instrument_scalar(inst, attr_name: str, index: int | None = None, default: float = float("nan")) -> float:
        return _instrument_scalar_impl(inst, attr_name, index=index, default=default)

    def _command_tracking_error_deg(self, inst, truth_heading_deg: float) -> float:
        return _command_tracking_error_deg_impl(self, inst, truth_heading_deg)

    @staticmethod
    def _ground_track_from_inst(inst, fallback_heading_deg: float) -> float:
        return _ground_track_from_inst_impl(None, inst, fallback_heading_deg)

    def _formation_slot_offsets_m(self) -> tuple[float, float, float]:
        return _formation_slot_offsets_m_impl(self)

    def _route_leg_frame(self, waypoint_index: int) -> tuple[float, float, float, float] | None:
        return _route_leg_frame_impl(self, waypoint_index)

    def _route_reference_xy(self, own_x_m: float, own_y_m: float, waypoint_index: int) -> tuple[float, float]:
        return _route_reference_xy_impl(self, own_x_m, own_y_m, waypoint_index)

    def _slot_target_altitude_for_waypoint(self, waypoint: dict | None, *, fallback_m: float | None = None) -> float:
        return _slot_target_altitude_for_waypoint_impl(self, waypoint, fallback_m=fallback_m)

    def _current_route_target_altitude_m(self, *, truth=None, inst=None) -> float | None:
        return _current_route_target_altitude_m_impl(self, truth=truth, inst=inst)

    def _mission_nav_inputs(self, truth, inst, route_result):
        return _mission_nav_inputs_impl(self, truth, inst, route_result)

    def _build_mission_nav_products(self, route_result, truth, inst):
        return _build_mission_nav_products_impl(self, route_result, truth, inst)

    @staticmethod
    def _mission_observation_mode_code(mode: str) -> int:
        return _mission_observation_mode_code_impl(mode)

    @staticmethod
    def _python_owned_mission_observation_mode(mode: str | None) -> bool:
        return _python_owned_mission_observation_mode_impl(mode)

    def _build_mission_observation_runtime_inputs(self, mode: str, *, truth=None, inst=None):
        return _build_mission_observation_runtime_inputs_impl(self, mode, truth=truth, inst=inst)

    def _compiled_mission_observation_enabled(self) -> bool:
        return _compiled_mission_observation_enabled_impl(self)

    def _compute_mission_observation_products(self, mode: str, *, truth=None, inst=None):
        return _compute_mission_observation_products_impl(self, mode, truth=truth, inst=inst)

    def _build_step_info_runtime_inputs(self, *, inst_now=None, truth_now=None, runway_frame=None):
        return _build_step_info_runtime_inputs_impl(
            self,
            inst_now=inst_now,
            truth_now=truth_now,
            runway_frame=runway_frame,
        )

    def _compiled_step_info_enabled(self) -> bool:
        return _compiled_step_info_enabled_impl(self)

    def _compute_step_info_runtime_products(self, *, inst_now=None, truth_now=None):
        return _compute_step_info_runtime_products_impl(self, inst_now=inst_now, truth_now=truth_now)

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
        return _build_flight_shaping_runtime_inputs_impl(
            self,
            cfg,
            steps=steps,
            truth=truth,
            inst_vec=inst_vec,
            curr_ias=curr_ias,
            curr_alt_agl=curr_alt_agl,
            curr_gear=curr_gear,
            curr_roll=curr_roll,
            heading_error_deg=heading_error_deg,
            ground_track_error_deg=ground_track_error_deg,
            waypoint_turn_relief_activation=waypoint_turn_relief_activation,
            preliftoff=preliftoff,
            on_runway_task=on_runway_task,
            airborne=airborne,
            runway_cross_m=runway_cross_m,
            runway_wid_m=runway_wid_m,
            ils_valid=ils_valid,
            ils_loc=ils_loc,
        )

    def _apply_compiled_flight_shaping_terms(self, products, add_reward_term, *, include_roll_stability: bool) -> None:
        _apply_compiled_flight_shaping_terms_impl(
            self,
            products,
            add_reward_term,
            include_roll_stability=include_roll_stability,
        )

    def _compute_flight_shaping_products(self, shaping_inputs, *, use_gpu: bool):
        return _compute_flight_shaping_products_impl(self, shaping_inputs, use_gpu=use_gpu)

    @staticmethod
    def _add_breakdown_term(breakdown: dict, name: str, value: float) -> None:
        _add_breakdown_term_impl(breakdown, name, value)

    def _apply_naval_reward_surface(
        self,
        sim,
        truth,
        *,
        reward: float,
        terminated: bool,
        truncated: bool,
        status: list[float],
        reward_breakdown: dict | None,
    ):
        return _apply_naval_reward_surface_impl(
            self,
            sim,
            truth,
            reward=reward,
            terminated=terminated,
            truncated=truncated,
            status=status,
            reward_breakdown=reward_breakdown,
        )

    def _apply_air_combat_reward_surface(
        self,
        sim,
        truth,
        *,
        reward: float,
        terminated: bool,
        truncated: bool,
        status: list[float],
        reward_breakdown: dict | None,
    ):
        return _apply_air_combat_reward_surface_impl(
            self,
            sim,
            truth,
            reward=reward,
            terminated=terminated,
            truncated=truncated,
            status=status,
            reward_breakdown=reward_breakdown,
        )

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
        _apply_legacy_flight_shaping_terms_impl(
            self,
            cfg,
            truth=truth,
            inst=inst,
            curr_ias=curr_ias,
            curr_alt_agl=curr_alt_agl,
            curr_gear=curr_gear,
            curr_roll=curr_roll,
            heading_error_deg=heading_error_deg,
            ground_track_error_deg=ground_track_error_deg,
            waypoint_turn_relief_activation=waypoint_turn_relief_activation,
            airborne=airborne,
            preliftoff=preliftoff,
            on_runway_task=on_runway_task,
            runway_cross_m=runway_cross_m,
            runway_wid_m=runway_wid_m,
            ils_valid=ils_valid,
            ils_loc=ils_loc,
            steps=steps,
            add_reward_term=add_reward_term,
        )

    def _consume_compiled_episode_runtime(
        self,
        *,
        cfg: dict,
        safety_cfg,
        truth,
        step_eval: dict,
        frame_products,
        track_structural_state_change: bool = False,
    ):
        return _consume_compiled_episode_runtime_impl(
            self,
            cfg=cfg,
            safety_cfg=safety_cfg,
            truth=truth,
            step_eval=step_eval,
            frame_products=frame_products,
            track_structural_state_change=track_structural_state_change,
        )

    def consume_execution_episode_controller_mainline_step(
        self,
        *,
        truth,
        step_eval: dict,
        frame_products,
        controller_state,
    ):
        return _consume_execution_episode_controller_mainline_step_impl(
            self,
            truth=truth,
            step_eval=step_eval,
            frame_products=frame_products,
            controller_state=controller_state,
        )

    def _build_waypoint_step_state(self, cfg: dict, *, truth=None, inst=None, turn_relief_activation: float = 0.0):
        return _build_waypoint_step_state_impl(
            self,
            cfg,
            truth=truth,
            inst=inst,
            turn_relief_activation=turn_relief_activation,
        )

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
        return _build_waypoint_reward_inputs_impl(
            self,
            cfg,
            idx=idx,
            count=count,
            mode=mode,
            dist_m=dist_m,
            leg_len_m=leg_len_m,
            xtk_m=xtk_m,
            dtg_m=dtg_m,
            waypoint_radius_m=waypoint_radius_m,
            lead_turn_m=lead_turn_m,
            sequence_gate_m=sequence_gate_m,
            passed_fix=passed_fix,
            turn_relief_activation=turn_relief_activation,
        )

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
        return _build_approach_reward_inputs_impl(
            self,
            cfg,
            ils_valid=ils_valid,
            ils_loc=ils_loc,
            ils_gs=ils_gs,
            ils_dme=ils_dme,
            curr_alt_agl=curr_alt_agl,
            sink_rate_mps=sink_rate_mps,
        )

    def _compile_conditional_objectives(self):
        return _compile_conditional_objectives_impl(self)

    @staticmethod
    def _build_objective_shaping_config(cfg: dict, *, required: bool = False):
        return _build_objective_shaping_config_impl(cfg, required=required)

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
        return _build_conditional_objective_inputs_impl(
            self,
            truth,
            inst,
            curr_ias=curr_ias,
            curr_ground_speed=curr_ground_speed,
            curr_gear=curr_gear,
            curr_alt_agl=curr_alt_agl,
            heading_error_deg=heading_error_deg,
            ground_track_error_deg=ground_track_error_deg,
            runway_cross_m=runway_cross_m,
            runway_from_threshold_m=runway_from_threshold_m,
            on_runway_geom=on_runway_geom,
            on_runway_task=on_runway_task,
            on_ground=on_ground,
        )

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
        return _build_safety_runtime_inputs_impl(
            self,
            cfg,
            finite_state_valid=finite_state_valid,
            truth=truth,
            airborne=airborne,
            aoa_valid=aoa_valid,
            curr_aoa=curr_aoa,
            curr_g=curr_g,
            curr_alt_agl=curr_alt_agl,
            curr_roll=curr_roll,
            gear_collapsed=gear_collapsed,
            runway_surface_phase=runway_surface_phase,
            on_runway_task=on_runway_task,
            gear_stress=gear_stress,
            off_runway_steps=off_runway_steps,
            time_step_s=time_step_s,
        )

    def _compiled_execution_step_enabled(self) -> bool:
        return _compiled_execution_step_enabled_impl(self)

    @staticmethod
    def _build_neutral_execution_safety_inputs():
        return _build_neutral_execution_safety_inputs_impl()

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
        return _compute_execution_step_runtime_products_impl(
            self,
            truncated=truncated,
            safety_inputs=safety_inputs,
            approach_inputs=approach_inputs,
            waypoint_inputs=waypoint_inputs,
            waypoint_episode_success=waypoint_episode_success,
            waypoint_episode_success_bonus=waypoint_episode_success_bonus,
            objective_specs=objective_specs,
            objective_inputs=objective_inputs,
        )

    def _compiled_execution_frame_enabled(self) -> bool:
        return _compiled_execution_frame_enabled_impl(self)

    def _compiled_execution_episode_enabled(self) -> bool:
        return _compiled_execution_episode_enabled_impl(self)

    def _build_step_evaluation_inputs(
        self,
        *,
        truth,
        inst_obj,
        inst_vec,
        ils_vec,
        steps: int,
        max_steps: int,
        mission_obs_mode: str | None = None,
        mission_observation_inputs=None,
    ):
        return _build_step_evaluation_inputs_impl(
            self,
            truth=truth,
            inst_obj=inst_obj,
            inst_vec=inst_vec,
            ils_vec=ils_vec,
            steps=steps,
            max_steps=max_steps,
            mission_obs_mode=mission_obs_mode,
            mission_observation_inputs=mission_observation_inputs,
        )

    def _build_step_evaluation_batch_env_state(
        self,
        *,
        truth,
        inst_obj,
        inst_vec,
        ils_vec,
        steps: int,
        max_steps: int,
        mission_obs_mode: str | None = None,
        mission_observation_inputs=None,
        include_episode_state: bool = True,
        return_prepared: bool = False,
        prepared_entry: dict | None = None,
    ):
        return _build_step_evaluation_batch_env_state_impl(
            self,
            truth=truth,
            inst_obj=inst_obj,
            inst_vec=inst_vec,
            ils_vec=ils_vec,
            steps=steps,
            max_steps=max_steps,
            mission_obs_mode=mission_obs_mode,
            mission_observation_inputs=mission_observation_inputs,
            include_episode_state=include_episode_state,
            return_prepared=return_prepared,
            prepared_entry=prepared_entry,
        )

    def _get_cached_step_evaluation(
        self,
        *,
        truth=None,
        inst_obj=None,
        steps=None,
        max_steps=None,
        mission_obs_mode=None,
    ):
        return _get_cached_step_evaluation_impl(
            self,
            truth=truth,
            inst_obj=inst_obj,
            steps=steps,
            max_steps=max_steps,
            mission_obs_mode=mission_obs_mode,
        )

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
        defer_compiled_runtime: bool = False,
        compact_output: bool = False,
    ):
        return _prepare_step_evaluation_impl(
            self,
            truth=truth,
            inst_obj=inst_obj,
            inst_vec=inst_vec,
            ils_vec=ils_vec,
            steps=steps,
            max_steps=max_steps,
            mission_obs_mode=mission_obs_mode,
            defer_compiled_runtime=defer_compiled_runtime,
            compact_output=compact_output,
        )

    def _build_execution_episode_controller_shadow_config(self):
        return _build_execution_episode_controller_shadow_config_impl(self)

    @staticmethod
    def _execution_episode_status_vector(products):
        return _execution_episode_status_vector_impl(products)

    @staticmethod
    def _compare_execution_episode_runtime_products(reference, shadow, *, abs_tol: float = 1.0e-6):
        return _compare_execution_episode_runtime_products_impl(reference, shadow, abs_tol=abs_tol)

    def compare_execution_episode_controller_shadow(
        self,
        *,
        truth,
        inst_obj,
        inst_vec,
        ils_vec,
        steps: int,
        max_steps: int,
        mission_obs_mode: str | None = None,
        abs_tol: float = 1.0e-6,
        advance_state: bool = False,
    ):
        return _compare_execution_episode_controller_shadow_impl(
            self,
            truth=truth,
            inst_obj=inst_obj,
            inst_vec=inst_vec,
            ils_vec=ils_vec,
            steps=steps,
            max_steps=max_steps,
            mission_obs_mode=mission_obs_mode,
            abs_tol=abs_tol,
            advance_state=advance_state,
        )

    def _turn_lead_distance_m(self, turn_angle_deg: float, speed_mps: float, bank_limit_deg: float) -> float:
        return _turn_lead_distance_m_impl(self, turn_angle_deg, speed_mps, bank_limit_deg)

    def _active_waypoint_turn_relief_activation(self, cfg: dict, truth=None, inst=None) -> float:
        return _active_waypoint_turn_relief_activation_impl(self, cfg, truth=truth, inst=inst)

    def _compute_waypoint_guidance_state(self, truth=None, inst=None):
        return _compute_waypoint_guidance_state_impl(self, truth=truth, inst=inst)

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

    def get_policy_agent_observation(self, agent_id: int | None = None):
        resolved_agent_id = self.agent_id if agent_id is None else agent_id
        if resolved_agent_id is None:
            return None
        try:
            return self.sim.get_agent_observation(resolved_agent_id)
        except Exception:
            return None

    def get_policy_instrument_state(self, agent_id: int | None = None):
        resolved_agent_id = self.agent_id if agent_id is None else agent_id
        if resolved_agent_id is None:
            return None
        try:
            return self.sim.get_instrument_state(resolved_agent_id)
        except Exception:
            return None

    def _sync_kernel_mission_command(self) -> None:
        _sync_kernel_mission_command_impl(self)

    def _sync_kernel_command_chain(self) -> None:
        _sync_kernel_command_chain_impl(self)

    def _hierarchical_command_chain_active(self) -> bool:
        return _hierarchical_command_chain_active_impl(self)

    def _reset_command_chain(self, *, initial_truth=None, initial_inst=None, sync_to_kernel: bool = True) -> None:
        _reset_command_chain_impl(
            self,
            initial_truth=initial_truth,
            initial_inst=initial_inst,
            sync_to_kernel=sync_to_kernel,
        )

    def _update_command_chain(self, sim_time: float, *, truth=None, inst=None, sync_to_kernel: bool = True) -> None:
        _update_command_chain_impl(
            self,
            sim_time,
            truth=truth,
            inst=inst,
            sync_to_kernel=sync_to_kernel,
        )

    def _landing_post_transition_terminal_ready(self) -> bool:
        return _landing_post_transition_terminal_ready_impl(self)

    def _post_waypoint_transition_ready(self) -> bool:
        return _post_waypoint_transition_ready_impl(self)

    def _apply_pending_landing_vector(self, *, sync_to_kernel: bool = True) -> bool:
        return _apply_pending_landing_vector_impl(self, sync_to_kernel=sync_to_kernel)

    def _maybe_activate_post_waypoint_transition(self, *, sync_to_kernel: bool = True) -> dict | None:
        return _maybe_activate_post_waypoint_transition_impl(self, sync_to_kernel=sync_to_kernel)

    def _defer_landing_post_transition_until_next_update(self) -> bool:
        return _defer_landing_post_transition_until_next_update_impl(self)

    def _activate_post_waypoint_transition(self, *, sync_to_kernel: bool = True) -> dict | None:
        return _activate_post_waypoint_transition_impl(self, sync_to_kernel=sync_to_kernel)

    def get_entity_id(self, name):
        return self.entities.get(name)

    def build_scripted_opponents(self) -> None:
        _build_scripted_opponents_impl(self)

    def update_scripted_opponents(self, sim_time: float) -> None:
        _update_scripted_opponents_impl(self, sim_time)

    def reset_scripted_opponents(self) -> None:
        _reset_scripted_opponents_impl(self)

    def get_mission_observation(self, mode: str = "basic", *, truth=None, inst=None):
        return _get_mission_observation_impl(self, mode=mode, truth=truth, inst=inst)

    def _get_waypoint_nav_products(self, *, truth=None, inst=None):
        return _get_waypoint_nav_products_impl(self, truth=truth, inst=inst)

    def _apply_waypoint_guidance_update(self, *, truth=None, inst=None) -> None:
        _apply_waypoint_guidance_update_impl(self, truth=truth, inst=inst)
    def update_behaviors(self, sim_time, *, truth=None, inst=None, sync_to_kernel: bool = True):
        _update_behaviors_impl(self, sim_time, truth=truth, inst=inst, sync_to_kernel=sync_to_kernel)

    def update_command_chain_only(self, sim_time, *, truth=None, inst=None, sync_to_kernel: bool = True):
        _update_command_chain_only_impl(self, sim_time, truth=truth, inst=inst, sync_to_kernel=sync_to_kernel)

    def update_nonhierarchical_behaviors(self, *, truth=None, inst=None, sync_to_kernel: bool = True):
        _update_nonhierarchical_behaviors_impl(self, truth=truth, inst=inst, sync_to_kernel=sync_to_kernel)

    def compute_full_step(self, obs, sim, steps, max_steps, *, truth=None, inst_state=None, step_evaluation=None):
        return _compute_full_step_impl(
            self,
            obs,
            sim,
            steps,
            max_steps,
            truth=truth,
            inst_state=inst_state,
            step_evaluation=step_evaluation,
        )
