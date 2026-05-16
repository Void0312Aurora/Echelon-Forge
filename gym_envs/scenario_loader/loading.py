import numpy as np

from python.scenario_compiler import (
    ApproachRewardConfig,
    CompiledScenario,
    LNavRuntimeConfig,
    SafetyRewardConfig,
    ScenarioCompiler,
    _build_lnav_runtime_config,
    _clone_runtime_mission_command,
    _normalize_runtime_mission_command,
    invalidate_runtime_waypoint_cache,
    materialize_runtime_waypoint_cache,
    rotate_ils_beacon_templates,
)
from python.scenario_runtime import (
    active_roster_world_entity_refs,
    apply_world_layout_to_kernel,
    find_active_roster_member,
    prepare_scenario_world_layout,
)
from python.rl.tasking.bridge import make_rule_based_leader_phase_manager, normalize_task_order_spec


def get_active_roster_member(loader, *, entity_id=None, entity_name=None, role_code=None, formation_role_id=None):
    return find_active_roster_member(
        getattr(loader, "active_roster", None),
        entity_id=entity_id,
        entity_name=entity_name,
        role_code=role_code,
        formation_role_id=formation_role_id,
    )


def get_active_roster_refs(loader, *, world_index: int | None = None):
    return active_roster_world_entity_refs(
        getattr(loader, "active_roster", None),
        world_index=world_index,
    )


def task_order_spec(loader) -> dict:
    task_cfg = loader.scenario_data.get("task_order", None)
    return normalize_task_order_spec(task_cfg if isinstance(task_cfg, dict) else {}, loader=loader)


def normalize_mission_command_dict(loader, cmd: dict | None) -> dict:
    return _normalize_runtime_mission_command(cmd, task_order_spec(loader))


def align_task_only_mission_shell_with_task_order(loader) -> None:
    if not isinstance(loader.mission_cmd, dict):
        return
    waypoints = loader.mission_cmd.get("waypoints", [])
    if isinstance(waypoints, (list, tuple)) and len(waypoints) > 0:
        return
    try:
        command_code = int(loader.mission_cmd.get("command_code", 0))
    except Exception:
        command_code = 0
    if command_code not in (0, 1, 2):
        return
    task_cfg = task_order_spec(loader)
    if not isinstance(task_cfg, dict) or not task_cfg:
        return
    if "target_altitude_m" in task_cfg:
        try:
            loader.mission_cmd["target_altitude"] = float(
                task_cfg.get("target_altitude_m", loader.mission_cmd.get("target_altitude", 0.0))
            )
        except Exception:
            pass
    if "target_speed_mps" in task_cfg:
        try:
            loader.mission_cmd["target_speed"] = float(
                task_cfg.get("target_speed_mps", loader.mission_cmd.get("target_speed", 0.0))
            )
        except Exception:
            pass


def set_randomization_overrides(loader, overrides: dict | None) -> None:
    if overrides is None:
        loader.randomization_overrides = {}
        return
    if not isinstance(overrides, dict):
        raise TypeError(f"randomization overrides must be a dict or None, got {type(overrides)}")
    loader.randomization_overrides = dict(overrides)


def prepare_load_seed(loader, seed=42) -> int:
    if seed is None:
        seed = np.random.randint(0, 2**32 - 1)
    seed = int(seed) & 0xFFFFFFFF
    loader.rng = np.random.RandomState(seed)
    return seed


def begin_loaded_world(loader, *, scenario_data: dict) -> None:
    if loader._compiled_runtime_metadata is None and isinstance(loader._compiled_scenario, CompiledScenario):
        loader._compiled_runtime_metadata = loader._compiled_scenario.runtime_metadata
    loader.scenario_data = scenario_data
    loader._leader_phase_manager = make_rule_based_leader_phase_manager(loader)
    loader._cached_route_ref_id = None
    mission_cmd = loader.scenario_data.get("mission_command", None)
    if not isinstance(mission_cmd, dict) and loader._compiled_runtime_metadata is not None:
        mission_cmd = _clone_runtime_mission_command(loader._compiled_runtime_metadata.mission_command_template)
        loader.scenario_data["mission_command"] = mission_cmd
    loader.mission_cmd = mission_cmd if isinstance(mission_cmd, dict) else {
        "command_code": 0,
        "target_heading": 0.0,
        "target_altitude": 0.0,
        "target_speed": 0.0,
    }
    loader.scripted_opponents = {}
    loader.scripted_opponent_reports = {}


def apply_compiled_runtime_metadata(loader) -> None:
    metadata = loader._compiled_runtime_metadata
    if metadata is None:
        loader._compiled_conditional_objectives = loader._compile_conditional_objectives()
        loader._objective_shaping_cfg = loader._build_objective_shaping_config(loader.scenario_data.get("rewards", {}))
        loader._compiled_rewards_cfg = loader.scenario_data.get("rewards", {})
        loader._compiled_meta_cfg = loader.scenario_data.get("meta", {}) if isinstance(loader.scenario_data.get("meta", {}), dict) else {}
        loader._waypoint_mode_reward_cfgs = {}
        loader._approach_reward_cfg = ApproachRewardConfig()
        loader._safety_reward_cfg = SafetyRewardConfig()
        loader._lnav_runtime_cfg = LNavRuntimeConfig()
        return
    loader._compiled_conditional_objectives = list(metadata.compiled_conditional_objectives)
    loader._objective_shaping_cfg = metadata.objective_shaping_cfg
    loader._compiled_rewards_cfg = dict(metadata.rewards_config)
    loader._compiled_meta_cfg = dict(metadata.meta_config)
    loader._waypoint_mode_reward_cfgs = dict(metadata.waypoint_mode_configs)
    loader._approach_reward_cfg = metadata.approach_reward_config
    loader._safety_reward_cfg = metadata.safety_reward_config
    loader._lnav_runtime_cfg = metadata.lnav_config


def _resolve_primary_target(loader) -> tuple[int | None, str]:
    mission_cmd = getattr(loader, "mission_cmd", None)
    scenario_data = getattr(loader, "scenario_data", None)
    entities = getattr(loader, "entities", None)

    target_name = ""
    target_id = None

    if isinstance(mission_cmd, dict):
        target_name = str(mission_cmd.get("assigned_target_name", "") or "").strip()
        try:
            mission_target_id = int(mission_cmd.get("assigned_target_id", 0))
        except Exception:
            mission_target_id = 0
        if mission_target_id > 0:
            target_id = mission_target_id

    if target_id is None and target_name and isinstance(entities, dict):
        resolved = entities.get(target_name)
        if resolved is not None:
            target_id = int(resolved)

    if target_id is None and isinstance(scenario_data, dict) and isinstance(entities, dict):
        for ent_cfg in scenario_data.get("entities", []):
            if not isinstance(ent_cfg, dict):
                continue
            if bool(ent_cfg.get("is_agent", False)):
                continue
            ent_name = str(ent_cfg.get("name", "")).strip()
            if not ent_name:
                continue
            resolved = entities.get(ent_name)
            if resolved is None:
                continue
            target_name = ent_name
            target_id = int(resolved)
            break

    if isinstance(mission_cmd, dict):
        mission_cmd["assigned_target_id"] = int(target_id or 0)
        if target_name:
            mission_cmd["assigned_target_name"] = target_name

    return target_id, target_name


def mission_cmd_has_valid_runtime_waypoint_cache(mission_cmd) -> bool:
    if not isinstance(mission_cmd, dict):
        return False
    cached_waypoints = mission_cmd.get("_normalized_waypoints", None)
    return bool(mission_cmd.get("_runtime_waypoint_cache_valid", False)) and isinstance(cached_waypoints, list)


def finalize_loaded_world(loader, *, initial_truth=None, initial_inst=None, sync_to_kernel: bool = True):
    loader.steps = 0
    loader.captured_time = 0.0
    loader.prev_alt = 0.0
    loader.prev_speed = 0.0
    loader.gear_bonus_awarded = False
    loader.liftoff_awarded = False
    loader.off_runway_steps = 0
    loader.last_reward_breakdown = {}
    loader.last_termination_reason = "running"
    loader._approach_prev_dme_m = None
    loader._approach_prev_loc_abs = None
    loader._approach_prev_gs_abs = None
    loader.post_waypoint_transition = None
    loader.mission_phase_name = "primary"
    loader.primary_target_id = None
    loader.primary_target_name = ""
    loader.scripted_opponents = {}
    loader.scripted_opponent_reports = {}

    loader._randomize_mission()
    loader._randomize_task_order()
    task_cfg = task_order_spec(loader)
    if isinstance(loader.scenario_data, dict):
        loader.scenario_data["task_order"] = dict(task_cfg)
    align_task_only_mission_shell_with_task_order(loader)
    preserve_waypoint_cache = bool(mission_cmd_has_valid_runtime_waypoint_cache(loader.mission_cmd))
    loader.mission_cmd = _normalize_runtime_mission_command(loader.mission_cmd, task_cfg)
    if preserve_waypoint_cache:
        materialize_runtime_waypoint_cache(loader.mission_cmd)
    else:
        invalidate_runtime_waypoint_cache(loader.mission_cmd)
        materialize_runtime_waypoint_cache(loader.mission_cmd)
    loader.scenario_data["mission_command"] = loader.mission_cmd
    loader._cached_route_ref_id = None
    apply_compiled_runtime_metadata(loader)
    loader._lnav_runtime_cfg = _build_lnav_runtime_config(loader.mission_cmd)

    post_transition_cfg = loader.mission_cmd.get("post_waypoint_transition", None)
    if isinstance(post_transition_cfg, dict) and post_transition_cfg:
        loader.post_waypoint_transition = _clone_runtime_mission_command(post_transition_cfg)

    if loader.rotate_mission_heading_with_world and loader.world_yaw_deg != 0.0:
        try:
            loader.mission_cmd["target_heading"] = float(loader.mission_cmd.get("target_heading", 0.0)) + float(
                loader.world_yaw_deg
            )
        except Exception:
            pass
        loader.mission_cmd["target_heading"] = float(loader.mission_cmd.get("target_heading", 0.0)) % 360.0

    loader._parse_waypoints()
    loader.primary_target_id, loader.primary_target_name = _resolve_primary_target(loader)
    loader.build_scripted_opponents()

    if loader.agent_id is not None:
        truth = initial_truth if initial_truth is not None else loader.sim.get_agent_observation(loader.agent_id)
        loader.prev_alt = truth.z
        loader._waypoint_leg_origin_x = float(getattr(truth, "x", 0.0))
        loader._waypoint_leg_origin_y = float(getattr(truth, "y", 0.0))
        try:
            inst0 = initial_inst if initial_inst is not None else loader.sim.get_instrument_state(loader.agent_id)
            loader.prev_speed = float(inst0.ias)
        except Exception:
            loader.prev_speed = truth.speed
    if loader._compiled_runtime_metadata is not None:
        loader.ils_beacons = rotate_ils_beacon_templates(
            loader._compiled_runtime_metadata.ils_beacon_templates,
            yaw_deg=float(loader.world_yaw_deg),
            origin_x=float(loader.world_yaw_origin_x),
            origin_y=float(loader.world_yaw_origin_y),
        )
    else:
        loader.ils_beacons = loader._extract_ils_beacons()
    loader._rebuild_spatial_geometry()
    loader._apply_waypoint_guidance_update(truth=initial_truth, inst=initial_inst)
    loader._reset_command_chain(
        initial_truth=initial_truth,
        initial_inst=initial_inst,
        sync_to_kernel=False,
    )
    if sync_to_kernel:
        loader._sync_kernel_mission_command()
        loader._sync_kernel_command_chain()
    return loader.agent_id


def load_scenario(loader, json_path, seed=42):
    compiled = ScenarioCompiler.compile_path(json_path)
    return load_compiled_scenario(loader, compiled, seed=seed)


def load_compiled_scenario(loader, compiled_scenario: CompiledScenario, seed=42):
    if not isinstance(compiled_scenario, CompiledScenario):
        raise TypeError("compiled_scenario must be a CompiledScenario")
    loader._compiled_scenario = compiled_scenario
    loader._compiled_runtime_metadata = compiled_scenario.runtime_metadata
    loader._scenario_source_path = compiled_scenario.source_path
    loader.scenario_data = compiled_scenario.instantiate_runtime()
    return load_instantiated_scenario(loader, seed=seed)


def load_scenario_data(loader, scenario_data: dict, seed=42, *, source_path: str | None = None):
    compiled = ScenarioCompiler.compile_data(scenario_data, source_path=source_path)
    return load_compiled_scenario(loader, compiled, seed=seed)


def load_prepared_world(
    loader,
    prepared_world,
    *,
    seed=42,
    initial_truth=None,
    initial_inst=None,
    sync_to_kernel: bool = True,
):
    seed = prepare_load_seed(loader, seed)
    layout = prepared_world.layout
    begin_loaded_world(loader, scenario_data=layout.scenario_data)
    loader.rotate_mission_heading_with_world = bool(layout.rotate_mission_heading_with_world)
    loader.world_yaw_deg = float(layout.world_yaw_deg)
    loader.world_yaw_origin_x = float(layout.world_yaw_origin_x)
    loader.world_yaw_origin_y = float(layout.world_yaw_origin_y)
    loader.entities = dict(prepared_world.entities)
    loader.active_roster = list(getattr(prepared_world, "active_roster", []) or [])
    loader.agent_id = prepared_world.agent_id
    _ = seed
    return finalize_loaded_world(
        loader,
        initial_truth=initial_truth,
        initial_inst=initial_inst,
        sync_to_kernel=sync_to_kernel,
    )


def load_instantiated_scenario(loader, seed=42):
    seed = prepare_load_seed(loader, seed)
    begin_loaded_world(loader, scenario_data=loader.scenario_data)

    world_layout = prepare_scenario_world_layout(
        loader.scenario_data,
        seed=seed,
        rng=loader.rng,
        randomization_overrides=loader.randomization_overrides,
    )
    loader.scenario_data = world_layout.scenario_data
    loader.rotate_mission_heading_with_world = bool(world_layout.rotate_mission_heading_with_world)
    loader.world_yaw_deg = float(world_layout.world_yaw_deg)
    loader.world_yaw_origin_x = float(world_layout.world_yaw_origin_x)
    loader.world_yaw_origin_y = float(world_layout.world_yaw_origin_y)
    applied_world = apply_world_layout_to_kernel(loader.sim, world_layout)
    loader.entities = dict(applied_world.entities)
    loader.active_roster = list(getattr(applied_world, "active_roster", []) or [])
    loader.agent_id = applied_world.agent_id
    initial_truth = None
    initial_inst = None
    if loader.agent_id is not None:
        try:
            initial_truth = loader.sim.get_agent_observation(loader.agent_id)
        except Exception:
            initial_truth = None
        try:
            initial_inst = loader.sim.get_instrument_state(loader.agent_id)
        except Exception:
            initial_inst = None
    return finalize_loaded_world(
        loader,
        initial_truth=initial_truth,
        initial_inst=initial_inst,
        sync_to_kernel=True,
    )
