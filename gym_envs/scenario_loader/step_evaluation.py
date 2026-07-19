import math

import ef_py

from python.tasking_contracts.mission_defs import is_landing_command_code
from python.tasking_contracts.bridge_views import resolve_loader_time_step

from .mission_observation import build_mission_observation_runtime_inputs


def build_step_info_runtime_inputs(loader, *, inst_now=None, truth_now=None, runway_frame=None):
    inputs = ef_py.StepInfoInputs()
    if inst_now is None:
        inst_now = loader.get_policy_instrument_state(loader.agent_id)
    inputs.on_runway = bool(getattr(inst_now, "on_runway", True))
    inputs.gear_collapsed = bool(getattr(inst_now, "gear_collapsed", False))
    inputs.gear_stress = float(getattr(inst_now, "gear_stress", 0.0))
    inputs.alt_agl_m = float(getattr(inst_now, "alt_radar", 0.0))

    cfg = loader.get_rewards_config()
    inputs.on_ground_alt_threshold_m = float(cfg.get("on_ground_alt_threshold", 2.5))
    inputs.airborne_alt_threshold_m = float(
        cfg.get("airborne_alt_threshold", cfg.get("liftoff_alt_threshold", 5.0))
    )
    inputs.runway_width_margin_m = float(cfg.get("runway_width_margin_m", 2.0))
    inputs.runway_length_margin_m = float(cfg.get("runway_length_margin_m", 0.0))

    if runway_frame is None and truth_now is None:
        truth_now = loader.get_policy_agent_observation(loader.agent_id)
    if runway_frame is None and loader._spatial_geometry is not None and truth_now is not None:
        runway_frame = loader._query_runway_frame_result(float(truth_now.x), float(truth_now.y))
    if runway_frame is not None and bool(getattr(runway_frame, "valid", False)):
        inputs.has_runway_frame = True
        inputs.runway_frame = runway_frame
    return inputs


def compiled_step_info_enabled(loader) -> bool:
    return bool(getattr(loader, "use_compiled_execution_step_runtime", True)) and hasattr(
        ef_py, "StepInfoInputs"
    ) and hasattr(ef_py, "compute_step_info_runtime")


def compute_step_info_runtime_products(loader, *, inst_now=None, truth_now=None):
    cached = loader._get_cached_step_evaluation(truth=truth_now, inst_obj=inst_now)
    if isinstance(cached, dict):
        frame_products = cached.get("frame_products")
        if frame_products is not None and bool(getattr(frame_products, "step_info_evaluated", False)):
            return frame_products.step_info
    inputs = build_step_info_runtime_inputs(loader, inst_now=inst_now, truth_now=truth_now)
    return ef_py.compute_step_info_runtime(inputs)


def build_step_evaluation_inputs(
    loader,
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
    cfg = loader._compiled_rewards_cfg if isinstance(loader._compiled_rewards_cfg, dict) and loader._compiled_rewards_cfg else loader.scenario_data.get("rewards", {})
    safety_cfg = loader._safety_reward_cfg
    approach_cfg = loader._approach_reward_cfg
    truncated = bool(int(steps) >= int(max_steps))

    curr_aoa = float(inst_vec[5])
    curr_roll = float(inst_vec[8])
    curr_g = float(inst_vec[10])
    curr_gear = float(inst_vec[18])
    curr_ias = float(inst_vec[0])
    curr_ground_speed = float(inst_vec[29]) if len(inst_vec) > 29 else math.hypot(float(getattr(truth, "vx", 0.0)), float(getattr(truth, "vy", 0.0)))
    curr_alt_agl = float(inst_vec[3]) if len(inst_vec) > 3 else float(getattr(truth, "z", 0.0))
    tgt_hdg = float(loader.mission_cmd.get("target_heading", 0.0))
    inst_source = inst_obj if inst_obj is not None else inst_vec
    inst_ground_track = loader._instrument_scalar(inst_source, "ground_track", 30)
    heading_error_deg = float(loader._command_tracking_error_deg(inst_source, getattr(truth, "heading", 0.0)))
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
    if truth is not None and loader._spatial_geometry is not None:
        runway_frame = loader._query_runway_frame_result(float(truth.x), float(truth.y))
    step_info_inputs = build_step_info_runtime_inputs(
        loader,
        inst_now=inst_obj,
        truth_now=truth,
        runway_frame=runway_frame,
    )

    mission_inputs = mission_observation_inputs
    if mission_obs_mode is not None and mission_inputs is None:
        mission_inputs = build_mission_observation_runtime_inputs(
            loader,
            mission_obs_mode,
            truth=truth,
            inst=inst_obj,
        )

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
        cmd_code = int(loader.mission_cmd.get("command_code", 0))
    except Exception:
        cmd_code = 0
    landing_mode = str(loader.mission_cmd.get("landing_mode", "")).strip().lower()
    is_landing_task = bool(is_landing_command_code(cmd_code) or landing_mode)
    # Deferred: profile dispatch stays python.rl-resident (see I24/I27).
    from python.rl.tasking.bridge import resolve_tasking_profile, tasking_profile_for_loader

    naval_runtime_profile = tasking_profile_for_loader(loader) is resolve_tasking_profile("naval")
    runway_surface_phase = bool(on_ground) if is_landing_task else bool(preliftoff)
    on_runway_task = bool(on_paved) if runway_surface_phase else False
    if on_runway_geom is not None:
        on_runway_task = bool(on_runway_geom) if runway_surface_phase else False
    if naval_runtime_profile:
        runway_surface_phase = False
        on_runway_task = False
    next_off_runway_steps = int(getattr(loader, "off_runway_steps", 0)) + 1 if runway_surface_phase and (not on_runway_task) else 0

    if not finite_state_valid:
        guard_inputs = ef_py.SafetyRuntimeInputs()
        guard_inputs.finite_state_valid = False
        guard_inputs.crash_penalty = float(safety_cfg.crash_penalty)
        safety_inputs = guard_inputs
    else:
        dt = float(resolve_loader_time_step(loader, default=0.05))
        dt = dt if dt > 1.0e-6 else 0.05
        aoa_valid = math.isfinite(float(curr_aoa)) and (abs(float(curr_aoa)) < 89.0) and (curr_ias > 10.0)
        safety_inputs = loader._build_safety_runtime_inputs(
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
            approach_inputs = loader._build_approach_reward_inputs(
                cfg,
                ils_valid=float(ils_valid),
                ils_loc=float(ils_loc),
                ils_gs=float(ils_gs),
                ils_dme=float(ils_dme),
                curr_alt_agl=float(curr_alt_agl),
                sink_rate_mps=float(sink_rate),
            )

        if loader.waypoints:
            waypoint_turn_relief_activation = loader._active_waypoint_turn_relief_activation(cfg, truth=truth, inst=inst_obj)
            waypoint_state = loader._build_waypoint_step_state(
                cfg,
                truth=truth,
                inst=inst_obj,
                turn_relief_activation=float(waypoint_turn_relief_activation),
            )

        if not naval_runtime_profile:
            shaping_inputs = loader._build_flight_shaping_runtime_inputs(
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

        objective_inputs = loader._build_conditional_objective_inputs(
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

    return {
        "mission_observation_inputs": mission_inputs,
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
        "domain_flight_shaping_enabled": not bool(naval_runtime_profile),
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


def build_step_evaluation_batch_env_state(
    loader,
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
    state = ef_py.StepEvaluationBatchEnvState()
    state.steps = int(steps)
    state.max_steps = int(max_steps)
    state.truncated = bool(int(steps) >= int(max_steps))

    state.truth_x = float(getattr(truth, "x", 0.0))
    state.truth_y = float(getattr(truth, "y", 0.0))
    state.truth_z = float(getattr(truth, "z", 0.0))
    state.truth_vx = float(getattr(truth, "vx", 0.0))
    state.truth_vy = float(getattr(truth, "vy", 0.0))
    state.truth_vz = float(getattr(truth, "vz", 0.0))
    state.truth_speed = float(getattr(truth, "speed", 0.0))
    state.truth_pitch = float(getattr(truth, "pitch", 0.0))
    state.truth_roll = float(getattr(truth, "roll", 0.0))
    state.truth_heading = float(getattr(truth, "heading", 0.0))
    state.truth_health = float(getattr(truth, "health", 100.0))
    state.inst_vec = [float(x) for x in inst_vec]
    state.ils_vec = [float(x) for x in ils_vec]
    state.liftoff_awarded = bool(getattr(loader, "liftoff_awarded", False))
    state.gear_bonus_awarded = bool(getattr(loader, "gear_bonus_awarded", False))
    state.prev_altitude_m = float(getattr(loader, "prev_alt", 0.0))
    state.prev_ias_mps = float(getattr(loader, "prev_speed", 0.0))
    state.defer_landing_post_transition = bool(loader._defer_landing_post_transition_until_next_update())

    if include_episode_state and hasattr(ef_py, "ExecutionEpisodeState"):
        try:
            state.episode_state = loader.build_execution_episode_state()
            state.has_episode_state = True
        except Exception:
            state.has_episode_state = False

    prepared = prepared_entry if isinstance(prepared_entry, dict) else None
    if prepared is None:
        prepared = build_step_evaluation_inputs(
            loader,
            truth=truth,
            inst_obj=inst_obj,
            inst_vec=inst_vec,
            ils_vec=ils_vec,
            steps=int(steps),
            max_steps=int(max_steps),
            mission_obs_mode=mission_obs_mode,
            mission_observation_inputs=mission_observation_inputs,
        )

    mission_inputs = prepared.get("mission_observation_inputs")
    if mission_inputs is not None and mission_obs_mode is not None:
        state.has_mission_observation = True
        state.mission_observation = mission_inputs

    step_info_inputs = prepared.get("step_info_inputs")
    if step_info_inputs is not None:
        state.has_step_info = True
        state.step_info = step_info_inputs

    safety_inputs = prepared.get("safety_inputs")
    if safety_inputs is not None:
        state.has_safety = True
        state.safety = safety_inputs

    waypoint_state = prepared.get("waypoint_state")
    if isinstance(waypoint_state, dict) and waypoint_state.get("inputs") is not None:
        state.has_waypoint = True
        state.waypoint = waypoint_state["inputs"]
        state.waypoint_episode_success = bool(waypoint_state.get("episode_success", False))
        state.waypoint_episode_success_bonus = float(loader._safety_reward_cfg.waypoint_mission_success_bonus)

    approach_inputs = prepared.get("approach_inputs")
    if approach_inputs is not None:
        state.has_approach = True
        state.approach = approach_inputs

    objective_inputs = prepared.get("objective_inputs")
    if loader._compiled_conditional_objectives and objective_inputs is not None:
        state.has_objectives = True
        state.objectives = list(loader._compiled_conditional_objectives)
        state.objective_inputs = objective_inputs
        state.objective_shaping = loader._objective_shaping_cfg

    shaping_inputs = prepared.get("shaping_inputs")
    if shaping_inputs is not None:
        state.has_flight_shaping = True
        state.flight_shaping = shaping_inputs
        state.include_roll_stability = bool(float(getattr(truth, "z", 0.0)) < 100.0)

    if bool(return_prepared):
        return state, prepared
    return state


def get_cached_step_evaluation(
    loader,
    *,
    truth=None,
    inst_obj=None,
    steps=None,
    max_steps=None,
    mission_obs_mode=None,
):
    cache = getattr(loader, "_runtime_eval_cache", None)
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


def prepare_step_evaluation(
    loader,
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
    cached = get_cached_step_evaluation(
        loader,
        truth=truth,
        inst_obj=inst_obj,
        steps=steps,
        max_steps=max_steps,
        mission_obs_mode=mission_obs_mode,
    )
    if isinstance(cached, dict):
        return cached

    entry = loader._build_step_evaluation_inputs(
        truth=truth,
        inst_obj=inst_obj,
        inst_vec=inst_vec,
        ils_vec=ils_vec,
        steps=int(steps),
        max_steps=int(max_steps),
        mission_obs_mode=mission_obs_mode,
    )
    frame_products = None
    episode_runtime_inputs = None
    truncated = bool(entry["truncated"])
    mission_inputs = entry.get("mission_observation_inputs")
    step_info_inputs = entry.get("step_info_inputs")
    safety_inputs = entry.get("safety_inputs")
    approach_inputs = entry.get("approach_inputs")
    waypoint_state = entry.get("waypoint_state")
    objective_inputs = entry.get("objective_inputs")
    shaping_inputs = entry.get("shaping_inputs")
    if bool(compact_output) and mission_obs_mode is None:
        step_info_inputs = None

    deferred_kind = None
    deferred_inputs = None

    if loader._compiled_execution_episode_enabled():
        runtime_inputs = ef_py.ExecutionEpisodeRuntimeInputs()
        if mission_inputs is not None and mission_obs_mode is not None:
            runtime_inputs.has_mission_observation = True
            runtime_inputs.mission_observation = mission_inputs
        if step_info_inputs is not None:
            runtime_inputs.has_step_info = True
            runtime_inputs.step_info = step_info_inputs
        runtime_inputs.has_execution_step = True
        exec_inputs = ef_py.ExecutionStepRuntimeInputs()
        exec_inputs.truncated = bool(truncated)
        if safety_inputs is not None:
            exec_inputs.safety = safety_inputs
        if approach_inputs is not None:
            exec_inputs.has_approach = True
            exec_inputs.approach = approach_inputs
        if isinstance(waypoint_state, dict):
            exec_inputs.has_waypoint = True
            exec_inputs.waypoint = waypoint_state["inputs"]
            exec_inputs.waypoint_episode_success = bool(waypoint_state["episode_success"])
            exec_inputs.waypoint_episode_success_bonus = float(loader._safety_reward_cfg.waypoint_mission_success_bonus)
        if loader._compiled_conditional_objectives and objective_inputs is not None:
            exec_inputs.has_objectives = True
            exec_inputs.objectives = list(loader._compiled_conditional_objectives)
            exec_inputs.objective_inputs = objective_inputs
            exec_inputs.objective_shaping = loader._objective_shaping_cfg
        runtime_inputs.execution_step = exec_inputs
        if shaping_inputs is not None:
            runtime_inputs.has_flight_shaping = True
            runtime_inputs.flight_shaping = shaping_inputs
        runtime_inputs.include_roll_stability = bool(float(getattr(truth, "z", 0.0)) < 100.0)
        episode_runtime_inputs = runtime_inputs
        if bool(defer_compiled_runtime):
            deferred_kind = "episode"
            deferred_inputs = runtime_inputs
        else:
            frame_products = ef_py.compute_execution_episode_runtime(runtime_inputs)
    elif loader._compiled_execution_frame_enabled():
        frame_inputs = ef_py.ExecutionFrameRuntimeInputs()
        if mission_inputs is not None and mission_obs_mode is not None:
            frame_inputs.has_mission_observation = True
            frame_inputs.mission_observation = mission_inputs
        if step_info_inputs is not None:
            frame_inputs.has_step_info = True
            frame_inputs.step_info = step_info_inputs
        frame_inputs.has_execution_step = True
        exec_inputs = ef_py.ExecutionStepRuntimeInputs()
        exec_inputs.truncated = bool(truncated)
        if safety_inputs is not None:
            exec_inputs.safety = safety_inputs
        if approach_inputs is not None:
            exec_inputs.has_approach = True
            exec_inputs.approach = approach_inputs
        if isinstance(waypoint_state, dict):
            exec_inputs.has_waypoint = True
            exec_inputs.waypoint = waypoint_state["inputs"]
            exec_inputs.waypoint_episode_success = bool(waypoint_state["episode_success"])
            exec_inputs.waypoint_episode_success_bonus = float(loader._safety_reward_cfg.waypoint_mission_success_bonus)
        if loader._compiled_conditional_objectives and objective_inputs is not None:
            exec_inputs.has_objectives = True
            exec_inputs.objectives = list(loader._compiled_conditional_objectives)
            exec_inputs.objective_inputs = objective_inputs
            exec_inputs.objective_shaping = loader._objective_shaping_cfg
        frame_inputs.execution_step = exec_inputs
        if shaping_inputs is not None:
            frame_inputs.has_flight_shaping = True
            frame_inputs.flight_shaping = shaping_inputs
        if bool(defer_compiled_runtime):
            deferred_kind = "frame"
            deferred_inputs = frame_inputs
        else:
            frame_products = ef_py.compute_execution_frame_runtime(frame_inputs)

    entry = {
        "truth_obj": truth,
        "inst_obj": inst_obj,
        "steps": int(steps),
        "max_steps": int(max_steps),
        "mission_obs_mode": "" if mission_obs_mode is None else str(mission_obs_mode),
        "frame_products": frame_products,
        "episode_runtime_inputs": episode_runtime_inputs,
        **entry,
    }
    if bool(defer_compiled_runtime):
        entry["_runtime_deferred_kind"] = deferred_kind
        entry["_runtime_deferred_inputs"] = deferred_inputs
    if bool(compact_output):
        entry["_compact_output"] = True
    if isinstance(loader._runtime_eval_cache, dict):
        loader._runtime_eval_cache["step_evaluation"] = entry
    return entry
