import math

import ef_py
import numpy as np

from python.rl.control.mission_defs import is_landing_command_code

from .shaping import apply_legacy_flight_shaping_terms


def _apply_combat_terminal_override(loader, sim, truth, reward, terminated, truncated, status, rb):
    target_id = int(getattr(loader, "primary_target_id", 0) or 0)
    if target_id <= 0:
        return reward, terminated, truncated, status, rb, None

    self_active = bool(sim.is_unit_active(loader.agent_id)) if loader.agent_id is not None else False
    target_active = bool(sim.is_unit_active(target_id))
    if target_active and self_active and not bool(truncated):
        return reward, terminated, truncated, status, rb, None

    next_rb = dict(rb or {})
    reason_override = None
    if (not target_active) and self_active:
        bonus = float(getattr(loader, "_compiled_meta_cfg", {}).get("combat_win_bonus", 1500.0))
        reward += bonus
        loader._add_breakdown_term(next_rb, "combat_win_bonus", bonus)
        terminated = True
        status[3] = 1.0
        reason_override = "combat_win"
    elif (not self_active) and target_active:
        penalty = float(getattr(loader, "_compiled_meta_cfg", {}).get("combat_loss_penalty", -1500.0))
        reward += penalty
        loader._add_breakdown_term(next_rb, "combat_loss_penalty", penalty)
        terminated = True
        status[3] = -1.0
        reason_override = "combat_loss"
    elif (not self_active) and (not target_active):
        draw_reward = float(getattr(loader, "_compiled_meta_cfg", {}).get("combat_draw_reward", 0.0))
        reward += draw_reward
        if draw_reward != 0.0:
            loader._add_breakdown_term(next_rb, "combat_draw_reward", draw_reward)
        terminated = True
        status[3] = 0.0
        reason_override = "combat_draw"
    elif bool(truncated):
        reason_override = "combat_timeout"
    return reward, terminated, truncated, status, next_rb, reason_override


def consume_compiled_episode_runtime(
    loader,
    *,
    cfg: dict,
    safety_cfg,
    truth,
    step_eval: dict,
    frame_products,
    track_structural_state_change: bool = False,
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
    structural_state_changed = False

    execution_step = (
        frame_products.execution_step if bool(getattr(frame_products, "execution_step_evaluated", False)) else None
    )
    if execution_step is None:
        tracked_total = 0.0
        rb["tracked_total"] = tracked_total
        rb["untracked"] = float(reward - tracked_total)
        rb["total"] = float(reward)
        loader.last_reward_breakdown = rb
        loader.last_termination_reason = str(
            ef_py.termination_reason_name(
                getattr(frame_products, "final_reason_code", ef_py.TerminationReasonCode.Running)
            )
        )
        if track_structural_state_change:
            return reward, terminated, status, structural_state_changed
        return reward, terminated, status

    def _add_reward_term(name: str, value: float) -> None:
        loader._add_breakdown_term(rb, name, value)

    safety_terms = execution_step.safety
    if float(getattr(safety_terms, "crash_penalty", 0.0)) != 0.0:
        _add_reward_term("crash_penalty", float(safety_terms.crash_penalty))
        nan_guard_marker = float(getattr(safety_terms, "nan_guard_marker", 0.0))
        if nan_guard_marker != 0.0:
            _add_reward_term("nan_guard", nan_guard_marker)
    else:
        _add_reward_term("survival", float(getattr(safety_terms, "survival", 0.0)))
        if bool(getattr(frame_products, "flight_shaping_evaluated", False)):
            loader._apply_compiled_flight_shaping_terms(
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
            if approach_inputs.dme_progress_weight != 0.0 and approach_inputs.has_prev_dme and math.isfinite(
                float(approach_inputs.ils_dme_m)
            ):
                _add_reward_term("approach_dme_progress", float(approach_terms.approach_dme_progress))
            if float(getattr(approach_terms, "approach_capture_bonus", 0.0)) != 0.0:
                _add_reward_term("approach_capture_bonus", float(approach_terms.approach_capture_bonus))
            if float(getattr(approach_terms, "landing_sink_rate_penalty", 0.0)) != 0.0:
                _add_reward_term("landing_sink_rate_penalty", float(approach_terms.landing_sink_rate_penalty))

            if bool(getattr(approach_terms, "clear_history", False)):
                loader._approach_prev_dme_m = None
                loader._approach_prev_loc_abs = None
                loader._approach_prev_gs_abs = None
            elif bool(getattr(approach_terms, "next_prev_valid", False)):
                loader._approach_prev_dme_m = float(approach_terms.next_prev_dme_m)
                loader._approach_prev_loc_abs = float(approach_terms.next_prev_loc_abs)
                loader._approach_prev_gs_abs = float(approach_terms.next_prev_gs_abs)

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

            loader._waypoint_prev_dist_m = (
                float(waypoint_terms.next_prev_dist_m)
                if bool(getattr(waypoint_terms, "next_prev_dist_valid", False))
                else None
            )
            arrived = bool(getattr(waypoint_terms, "arrived", False))
            if arrived:
                _add_reward_term("waypoint_reached_bonus", float(waypoint_terms.waypoint_reached_bonus))
                loader.waypoint_idx = idx + 1
                loader._waypoint_prev_dist_m = None
                if not objective_has_status:
                    status[1] = float(loader.waypoint_idx)
                    if loader.waypoint_idx < n:
                        next_wp = loader.waypoints[loader.waypoint_idx]
                        next_dx = float(next_wp.get("x", 0.0)) - float(getattr(truth, "x", 0.0))
                        next_dy = float(next_wp.get("y", 0.0)) - float(getattr(truth, "y", 0.0))
                        status[0] = float(math.hypot(next_dx, next_dy))
                    else:
                        status[0] = 0.0
                if loader.waypoint_idx >= n:
                    landing_transition_pending = bool(
                        isinstance(loader.post_waypoint_transition, dict)
                        and loader.post_waypoint_transition
                        and is_landing_command_code(loader.post_waypoint_transition.get("command_code", 4))
                    )
                    transitioned = None
                    deferred_landing_transition = loader._defer_landing_post_transition_until_next_update()
                    if not deferred_landing_transition:
                        transitioned = loader._maybe_activate_post_waypoint_transition()
                    if isinstance(transitioned, dict):
                        structural_state_changed = True
                        transition_reward = float(
                            transitioned.get("transition_reward", cfg.get("phase_transition_bonus", 600.0))
                        )
                        _add_reward_term("phase_transition_bonus", transition_reward)
                        extra_reward += transition_reward
                        if not objective_has_status:
                            status[0] = 0.0
                            status[1] = 0.0
                    elif landing_transition_pending:
                        if not deferred_landing_transition:
                            structural_state_changed = True
                        if not objective_has_status:
                            status[0] = 0.0
                            status[1] = float(loader.waypoint_idx)
                    elif bool(getattr(execution_step, "waypoint_episode_success", False)):
                        _add_reward_term(
                            "waypoint_success_bonus",
                            float(
                                getattr(
                                    execution_step,
                                    "waypoint_episode_success_bonus",
                                    safety_cfg.waypoint_mission_success_bonus,
                                )
                            ),
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
    loader.last_reward_breakdown = rb
    loader.last_termination_reason = str(
        ef_py.termination_reason_name(
            getattr(frame_products, "final_reason_code", ef_py.TerminationReasonCode.Running)
        )
    )
    if track_structural_state_change:
        return reward, terminated, status, structural_state_changed
    return reward, terminated, status


def consume_execution_episode_controller_mainline_step(
    loader,
    *,
    truth,
    step_eval: dict,
    frame_products,
    controller_state,
):
    cfg = (
        loader._compiled_rewards_cfg
        if isinstance(loader._compiled_rewards_cfg, dict) and loader._compiled_rewards_cfg
        else loader.scenario_data.get("rewards", {})
    )
    reward, terminated, status, structural_state_changed = consume_compiled_episode_runtime(
        loader,
        cfg=cfg,
        safety_cfg=loader._safety_reward_cfg,
        truth=truth,
        step_eval=step_eval,
        frame_products=frame_products,
        track_structural_state_change=True,
    )
    truncated = bool(step_eval.get("truncated", False))
    mirrored_state = None
    if hasattr(ef_py, "ExecutionEpisodeState") and isinstance(controller_state, ef_py.ExecutionEpisodeState):
        loader.apply_execution_episode_runtime_fields(
            controller_state,
            include_navigation_state=not structural_state_changed,
        )
    if structural_state_changed and hasattr(ef_py, "ExecutionEpisodeState"):
        mirrored_state = loader.build_execution_episode_state()
    return reward, terminated, truncated, status, mirrored_state


def compute_full_step(loader, obs, sim, steps, max_steps, *, truth=None, inst_state=None, step_evaluation=None):
    cfg = (
        loader._compiled_rewards_cfg
        if isinstance(loader._compiled_rewards_cfg, dict) and loader._compiled_rewards_cfg
        else loader.scenario_data.get("rewards", {})
    )
    safety_cfg = loader._safety_reward_cfg
    compiled_runtime_enabled = loader._compiled_execution_step_enabled()
    flight_shaping_backend = loader._flight_shaping_backend_mode()
    term_reason_code = ef_py.TerminationReasonCode.Running

    if truth is None:
        truth = sim.get_agent_observation(loader.agent_id)

    inst = obs["instruments"]
    inst_obj = inst_state
    if inst_obj is None:
        try:
            inst_obj = sim.get_instrument_state(loader.agent_id)
        except Exception:
            inst_obj = None

    step_eval = step_evaluation if isinstance(step_evaluation, dict) else None
    if step_eval is not None:
        if truth is not None and step_eval.get("truth_obj") is not truth:
            step_eval = None
        elif inst_obj is not None and step_eval.get("inst_obj") is not inst_obj:
            step_eval = None
        elif int(step_eval.get("steps", -1)) != int(steps):
            step_eval = None
        elif int(step_eval.get("max_steps", -1)) != int(max_steps):
            step_eval = None
    if step_eval is None:
        step_eval = loader._prepare_step_evaluation(
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
    curr_ground_speed = float(
        step_eval.get(
            "curr_ground_speed",
            math.hypot(float(getattr(truth, "vx", 0.0)), float(getattr(truth, "vy", 0.0))),
        )
    )
    curr_alt_agl = float(
        step_eval.get("curr_alt_agl", inst[3] if len(inst) > 3 else float(getattr(truth, "z", 0.0)))
    )
    heading_error_deg = float(step_eval.get("heading_error_deg", 0.0))
    ground_track_error_deg = float(step_eval.get("ground_track_error_deg", 0.0))
    finite_state_valid = bool(step_eval.get("finite_state_valid", True))

    if not finite_state_valid:
        if frame_products is not None and bool(getattr(frame_products, "execution_step_evaluated", False)):
            guard_products = frame_products.execution_step.safety
        else:
            guard_inputs = ef_py.SafetyRuntimeInputs()
            guard_inputs.finite_state_valid = False
            guard_inputs.crash_penalty = float(safety_cfg.crash_penalty)
            if compiled_runtime_enabled:
                guard_products = loader._compute_execution_step_runtime_products(
                    truncated=bool(truncated),
                    safety_inputs=guard_inputs,
                ).safety
            else:
                guard_products = ef_py.compute_safety_runtime(guard_inputs)
        status = [0.0] * 4
        status[3] = float(guard_products.status_flag)
        crash_pen = float(guard_products.crash_penalty)
        loader.last_reward_breakdown = {
            "crash_penalty": crash_pen,
            "nan_guard": float(guard_products.nan_guard_marker),
            "total": crash_pen,
            "untracked": 0.0,
        }
        loader.last_termination_reason = str(ef_py.termination_reason_name(guard_products.reason_code))
        return crash_pen, True, truncated, status

    loader.off_runway_steps = int(step_eval.get("next_off_runway_steps", 0))
    if (
        compiled_runtime_enabled
        and frame_products is not None
        and bool(getattr(frame_products, "outcome_evaluated", False))
        and flight_shaping_backend == "compiled"
    ):
        reward, terminated, status = consume_compiled_episode_runtime(
            loader,
            cfg=cfg,
            safety_cfg=safety_cfg,
            truth=truth,
            step_eval=step_eval,
            frame_products=frame_products,
        )
        reward, terminated, truncated, status, rb_override, reason_override = _apply_combat_terminal_override(
            loader,
            sim,
            truth,
            reward,
            terminated,
            truncated,
            status,
            loader.last_reward_breakdown,
        )
        tracked_total = float(sum(rb_override.values())) if rb_override else 0.0
        rb_override["tracked_total"] = tracked_total
        rb_override["untracked"] = float(reward - tracked_total)
        rb_override["total"] = float(reward)
        loader.last_reward_breakdown = rb_override
        if isinstance(reason_override, str) and reason_override:
            loader.last_termination_reason = reason_override
        loader.prev_alt = truth.z
        loader.prev_speed = curr_ias
        return reward, terminated, truncated, status

    curr_ground_speed = float(curr_ground_speed)
    on_ground = bool(step_eval.get("on_ground", False))
    airborne = bool(step_eval.get("airborne", False))
    preliftoff = bool(step_eval.get("preliftoff", True))
    on_runway_geom = step_eval.get("on_runway_geom")
    runway_cross_m = step_eval.get("runway_cross_m")
    runway_from_threshold_m = step_eval.get("runway_from_threshold_m")
    runway_wid_m = step_eval.get("runway_wid_m")
    on_runway_task = bool(step_eval.get("on_runway_task", False))
    safety_inputs = step_eval.get("safety_inputs")
    approach_inputs = step_eval.get("approach_inputs")
    ils_valid = float(step_eval.get("ils_valid", 0.0))
    ils_loc = float(step_eval.get("ils_loc", 0.0))
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
        safety_approach_runtime = loader._compute_execution_step_runtime_products(
            truncated=bool(truncated),
            safety_inputs=safety_inputs,
            approach_inputs=approach_inputs,
        )
        safety_terms = safety_approach_runtime.safety
    else:
        safety_terms = ef_py.compute_safety_runtime(safety_inputs)

    reward = 0.0
    terminated = False
    status = [0.0] * 4
    rb = {}

    def _add_reward_term(name: str, value: float):
        nonlocal reward
        v = float(value)
        reward += v
        rb[name] = float(rb.get(name, 0.0) + v)

    if float(safety_terms.crash_penalty) != 0.0:
        _add_reward_term("crash_penalty", float(safety_terms.crash_penalty))
        terminated = True
        status[3] = float(safety_terms.status_flag)
        term_reason_code = safety_terms.reason_code
    else:
        _add_reward_term("survival", float(safety_terms.survival))

    if not terminated:
        waypoint_turn_relief_activation = float(step_eval.get("waypoint_turn_relief_activation", 0.0))
        shaping_inputs = step_eval.get("shaping_inputs")
        compiled_flight_shaping = step_eval.get("flight_shaping_products_override")
        if (
            compiled_flight_shaping is None
            and flight_shaping_backend == "compiled"
            and compiled_runtime_enabled
            and frame_products is not None
            and bool(getattr(frame_products, "flight_shaping_evaluated", False))
        ):
            compiled_flight_shaping = frame_products.flight_shaping
        elif compiled_flight_shaping is None and flight_shaping_backend in {"compiled", "gpu_host"}:
            compiled_flight_shaping = loader._compute_flight_shaping_products(
                shaping_inputs,
                use_gpu=flight_shaping_backend == "gpu_host",
            )
            if compiled_flight_shaping is not None and isinstance(step_eval, dict):
                step_eval["flight_shaping_products_override"] = compiled_flight_shaping

        if compiled_flight_shaping is not None:
            loader._apply_compiled_flight_shaping_terms(
                compiled_flight_shaping,
                _add_reward_term,
                include_roll_stability=bool(truth.z < 100.0),
            )
        else:
            apply_legacy_flight_shaping_terms(
                loader,
                cfg,
                truth=truth,
                inst=inst,
                curr_ias=float(curr_ias),
                curr_alt_agl=float(curr_alt_agl),
                curr_gear=float(step_eval.get("curr_gear", inst[18])),
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
            if approach_inputs.dme_progress_weight != 0.0 and approach_inputs.has_prev_dme and math.isfinite(
                float(ils_dme)
            ):
                _add_reward_term("approach_dme_progress", float(approach_terms.approach_dme_progress))
            if float(approach_terms.approach_capture_bonus) != 0.0:
                _add_reward_term("approach_capture_bonus", float(approach_terms.approach_capture_bonus))
            if float(approach_terms.landing_sink_rate_penalty) != 0.0:
                _add_reward_term("landing_sink_rate_penalty", float(approach_terms.landing_sink_rate_penalty))

            if bool(approach_terms.clear_history):
                loader._approach_prev_dme_m = None
                loader._approach_prev_loc_abs = None
                loader._approach_prev_gs_abs = None
            elif bool(approach_terms.next_prev_valid):
                loader._approach_prev_dme_m = float(approach_terms.next_prev_dme_m)
                loader._approach_prev_loc_abs = float(approach_terms.next_prev_loc_abs)
                loader._approach_prev_gs_abs = float(approach_terms.next_prev_gs_abs)

    loader.prev_alt = truth.z
    loader.prev_speed = curr_ias

    if not terminated:
        waypoint_turn_relief_activation = float(step_eval.get("waypoint_turn_relief_activation", 0.0))
        waypoint_state = step_eval.get("waypoint_state")
        if waypoint_state is None and loader.waypoints:
            waypoint_state = loader._build_waypoint_step_state(
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
                waypoint_runtime = loader._compute_execution_step_runtime_products(
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

            loader._waypoint_prev_dist_m = (
                float(waypoint_terms.next_prev_dist_m) if bool(waypoint_terms.next_prev_dist_valid) else None
            )
            arrived = bool(waypoint_terms.arrived)

            if arrived:
                _add_reward_term("waypoint_reached_bonus", float(waypoint_terms.waypoint_reached_bonus))
                loader.waypoint_idx = idx + 1
                status[1] = float(loader.waypoint_idx)
                if loader.waypoint_idx < n:
                    next_wp = loader.waypoints[loader.waypoint_idx]
                    next_dx = float(next_wp.get("x", 0.0)) - float(getattr(truth, "x", 0.0))
                    next_dy = float(next_wp.get("y", 0.0)) - float(getattr(truth, "y", 0.0))
                    status[0] = float(math.hypot(next_dx, next_dy))
                else:
                    status[0] = 0.0
                loader._waypoint_prev_dist_m = None
                if loader.waypoint_idx >= n:
                    landing_transition_pending = bool(
                        isinstance(loader.post_waypoint_transition, dict)
                        and loader.post_waypoint_transition
                        and is_landing_command_code(loader.post_waypoint_transition.get("command_code", 4))
                    )
                    transitioned = None
                    if not loader._defer_landing_post_transition_until_next_update():
                        transitioned = loader._maybe_activate_post_waypoint_transition()
                    if isinstance(transitioned, dict):
                        _add_reward_term(
                            "phase_transition_bonus",
                            float(transitioned.get("transition_reward", cfg.get("phase_transition_bonus", 600.0))),
                        )
                        status[0] = 0.0
                        status[1] = 0.0
                    elif landing_transition_pending:
                        status[0] = 0.0
                        status[1] = float(loader.waypoint_idx)
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
                            _add_reward_term(
                                "waypoint_success_bonus",
                                float(safety_cfg.waypoint_mission_success_bonus),
                            )
                            term_reason_code = ef_py.TerminationReasonCode.SuccessWaypoint
                        terminated = True
                        status[3] = 1.0

    if not terminated:
        objective_inputs = step_eval.get("objective_inputs")
        if objective_inputs is None:
            objective_inputs = loader._build_conditional_objective_inputs(
                truth,
                inst,
                curr_ias=float(curr_ias),
                curr_ground_speed=float(curr_ground_speed),
                curr_gear=float(step_eval.get("curr_gear", inst[18])),
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
            objective_runtime = loader._compute_execution_step_runtime_products(
                truncated=bool(truncated),
                objective_specs=loader._compiled_conditional_objectives,
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
            for obj in loader._compiled_conditional_objectives:
                products = ef_py.evaluate_conditional_objective(obj, objective_inputs, loader._objective_shaping_cfg)
                if int(products.status_count) >= 1:
                    status[0] = float(products.status0)
                if int(products.status_count) >= 2:
                    status[1] = float(products.status1)
                if int(products.status_count) >= 3:
                    status[2] = float(products.status2)
                if not bool(products.matched):
                    continue
                if float(products.success_runway_cross_penalty) != 0.0:
                    _add_reward_term(
                        "success_runway_cross_penalty",
                        float(products.success_runway_cross_penalty),
                    )
                if float(products.success_ground_track_error_penalty) != 0.0:
                    _add_reward_term(
                        "success_ground_track_error_penalty",
                        float(products.success_ground_track_error_penalty),
                    )
                _add_reward_term("objective_bonus", float(products.objective_bonus))
                terminated = True
                status[3] = 1.0
                term_reason_code = ef_py.TerminationReasonCode.SuccessObjective
                break

    reward, terminated, truncated, status, rb, reason_override = _apply_combat_terminal_override(
        loader,
        sim,
        truth,
        reward,
        terminated,
        truncated,
        status,
        rb,
    )
    tracked_total = float(sum(rb.values())) if rb else 0.0
    rb["tracked_total"] = tracked_total
    rb["untracked"] = float(reward - tracked_total)
    rb["total"] = float(reward)
    loader.last_reward_breakdown = rb
    if isinstance(reason_override, str) and reason_override:
        loader.last_termination_reason = reason_override
    else:
        final_reason = ef_py.finalize_termination_reason(
            term_reason_code,
            bool(terminated),
            bool(truncated),
            float(status[3]),
        )
        loader.last_termination_reason = str(ef_py.termination_reason_name(final_reason))

    return reward, terminated, truncated, status
