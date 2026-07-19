import ef_py
import numpy as np
from python.tasking_contracts.bridge_views import resolve_loader_time_step


def build_execution_episode_controller_shadow_config(loader):
    config = ef_py.StepEvaluationBatchConfig()
    rewards_cfg = loader.get_rewards_config()
    config.target_altitude_m = float(
        rewards_cfg.get("altitude_progress_target", loader.mission_cmd.get("target_altitude", 0.0)) or 0.0
    )
    config.target_speed_mps = float(
        rewards_cfg.get("speed_progress_target", loader.mission_cmd.get("target_speed", 0.0)) or 0.0
    )
    config.target_heading_deg = float(loader.mission_cmd.get("target_heading", 0.0) or 0.0)
    config.time_step_s = float(resolve_loader_time_step(loader, default=0.05))
    config.crash_penalty = float(getattr(loader._safety_reward_cfg, "crash_penalty", -1000.0))
    return config


def execution_episode_status_vector(products):
    return np.asarray(
        [
            float(getattr(products, "status0", 0.0)),
            float(getattr(products, "status1", 0.0)),
            float(getattr(products, "status2", 0.0)),
            float(getattr(products, "status3", 0.0)),
        ],
        dtype=np.float32,
    )


def compare_execution_episode_runtime_products(reference, shadow, *, abs_tol: float = 1.0e-6):
    reward_total_delta = float(
        float(getattr(shadow, "compiled_reward_total", 0.0))
        - float(getattr(reference, "compiled_reward_total", 0.0))
    )
    reward_total_match = bool(abs(reward_total_delta) <= float(abs_tol))

    reference_status = execution_episode_status_vector(reference)
    shadow_status = execution_episode_status_vector(shadow)
    status_abs_diff = np.abs(reference_status - shadow_status)
    status_match = bool(np.all(status_abs_diff <= float(abs_tol)))

    reference_mission_eval = bool(getattr(reference, "mission_observation_evaluated", False))
    shadow_mission_eval = bool(getattr(shadow, "mission_observation_evaluated", False))
    mission_observation_match = bool(reference_mission_eval == shadow_mission_eval)
    mission_observation_max_abs_diff = 0.0
    if reference_mission_eval and shadow_mission_eval:
        ref_mission = reference.mission_observation
        shadow_mission = shadow.mission_observation
        ref_values = np.asarray(list(getattr(ref_mission, "values", [])), dtype=np.float32)
        shadow_values = np.asarray(list(getattr(shadow_mission, "values", [])), dtype=np.float32)
        if ref_values.shape != shadow_values.shape:
            mission_observation_match = False
            mission_observation_max_abs_diff = float("inf")
        else:
            if ref_values.size > 0:
                mission_observation_max_abs_diff = float(np.max(np.abs(ref_values - shadow_values)))
            mission_observation_match = bool(
                mission_observation_match
                and int(getattr(ref_mission, "mode_code", 0)) == int(getattr(shadow_mission, "mode_code", 0))
                and bool(getattr(ref_mission, "nav_valid", False))
                == bool(getattr(shadow_mission, "nav_valid", False))
                and mission_observation_max_abs_diff <= float(abs_tol)
            )

    reference_step_info_eval = bool(getattr(reference, "step_info_evaluated", False))
    shadow_step_info_eval = bool(getattr(shadow, "step_info_evaluated", False))
    step_info_match = bool(reference_step_info_eval == shadow_step_info_eval)
    step_info_max_abs_diff = 0.0
    if reference_step_info_eval and shadow_step_info_eval:
        ref_step_info = reference.step_info
        shadow_step_info = shadow.step_info
        step_info_diffs = np.asarray(
            [
                abs(
                    float(getattr(ref_step_info, "runway_cross_m", 0.0))
                    - float(getattr(shadow_step_info, "runway_cross_m", 0.0))
                ),
                abs(
                    float(getattr(ref_step_info, "runway_along_m", 0.0))
                    - float(getattr(shadow_step_info, "runway_along_m", 0.0))
                ),
            ],
            dtype=np.float32,
        )
        if step_info_diffs.size > 0:
            step_info_max_abs_diff = float(np.max(step_info_diffs))
        step_info_match = bool(
            step_info_match
            and bool(getattr(ref_step_info, "on_ground", False)) == bool(getattr(shadow_step_info, "on_ground", False))
            and bool(getattr(ref_step_info, "airborne", False)) == bool(getattr(shadow_step_info, "airborne", False))
            and bool(getattr(ref_step_info, "on_runway_geom", False))
            == bool(getattr(shadow_step_info, "on_runway_geom", False))
            and step_info_max_abs_diff <= float(abs_tol)
        )

    reference_exec_eval = bool(getattr(reference, "execution_step_evaluated", False))
    shadow_exec_eval = bool(getattr(shadow, "execution_step_evaluated", False))
    execution_step_match = bool(reference_exec_eval == shadow_exec_eval)
    execution_step_reward_delta = 0.0
    if reference_exec_eval and shadow_exec_eval:
        ref_exec = reference.execution_step
        shadow_exec = shadow.execution_step
        execution_step_reward_delta = float(
            float(getattr(shadow_exec, "compiled_reward_total", 0.0))
            - float(getattr(ref_exec, "compiled_reward_total", 0.0))
        )
        execution_step_match = bool(
            execution_step_match
            and abs(execution_step_reward_delta) <= float(abs_tol)
            and bool(getattr(ref_exec, "terminated", False)) == bool(getattr(shadow_exec, "terminated", False))
            and int(getattr(ref_exec, "matched_objective_index", -1))
            == int(getattr(shadow_exec, "matched_objective_index", -1))
            and bool(getattr(ref_exec, "waypoint_evaluated", False))
            == bool(getattr(shadow_exec, "waypoint_evaluated", False))
            and bool(getattr(ref_exec, "approach_evaluated", False))
            == bool(getattr(shadow_exec, "approach_evaluated", False))
            and bool(getattr(ref_exec, "objective_evaluated", False))
            == bool(getattr(shadow_exec, "objective_evaluated", False))
            and getattr(ref_exec, "reason_code", None) == getattr(shadow_exec, "reason_code", None)
            and getattr(ref_exec, "final_reason_code", None) == getattr(shadow_exec, "final_reason_code", None)
        )

    comparison = {
        "valid_match": bool(bool(getattr(reference, "valid", False)) == bool(getattr(shadow, "valid", False))),
        "reward_total_match": bool(reward_total_match),
        "reward_total_delta": float(reward_total_delta),
        "terminated_match": bool(
            bool(getattr(reference, "terminated", False)) == bool(getattr(shadow, "terminated", False))
        ),
        "reason_code_match": bool(getattr(reference, "reason_code", None) == getattr(shadow, "reason_code", None)),
        "final_reason_code_match": bool(
            getattr(reference, "final_reason_code", None) == getattr(shadow, "final_reason_code", None)
        ),
        "status_match": bool(status_match),
        "status_abs_diff": [float(x) for x in status_abs_diff.tolist()],
        "mission_observation_match": bool(mission_observation_match),
        "mission_observation_max_abs_diff": float(mission_observation_max_abs_diff),
        "step_info_match": bool(step_info_match),
        "step_info_max_abs_diff": float(step_info_max_abs_diff),
        "execution_step_match": bool(execution_step_match),
        "execution_step_reward_delta": float(execution_step_reward_delta),
    }
    comparison["overall_match"] = bool(
        comparison["valid_match"]
        and comparison["reward_total_match"]
        and comparison["terminated_match"]
        and comparison["reason_code_match"]
        and comparison["final_reason_code_match"]
        and comparison["status_match"]
        and comparison["mission_observation_match"]
        and comparison["step_info_match"]
        and comparison["execution_step_match"]
    )
    return comparison


def compare_execution_episode_controller_shadow(
    loader,
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
    if not hasattr(ef_py, "ExecutionEpisodeController"):
        raise RuntimeError("ef_py.ExecutionEpisodeController is not available")

    step_eval = loader._prepare_step_evaluation(
        truth=truth,
        inst_obj=inst_obj,
        inst_vec=inst_vec,
        ils_vec=ils_vec,
        steps=int(steps),
        max_steps=int(max_steps),
        mission_obs_mode=mission_obs_mode,
    )
    reference_products = step_eval.get("frame_products")
    if reference_products is None:
        raise RuntimeError("step evaluation did not produce frame_products")

    mission_inputs = step_eval.get("mission_observation_inputs")
    batch_state = loader._build_step_evaluation_batch_env_state(
        truth=truth,
        inst_obj=inst_obj,
        inst_vec=inst_vec,
        ils_vec=ils_vec,
        steps=int(steps),
        max_steps=int(max_steps),
        mission_obs_mode=mission_obs_mode,
        mission_observation_inputs=mission_inputs,
    )
    config = build_execution_episode_controller_shadow_config(loader)
    controller = ef_py.ExecutionEpisodeController()
    if hasattr(ef_py, "ExecutionEpisodeState"):
        controller.import_state(loader.build_execution_episode_state())
    shadow_products = (
        controller.step(config, batch_state) if bool(advance_state) else controller.evaluate(config, batch_state)
    )
    shadow_state = controller.export_state()

    report = {
        "reference_frame_products": reference_products,
        "shadow_frame_products": shadow_products,
        "shadow_state": shadow_state,
        "advance_state": bool(advance_state),
        "comparison": compare_execution_episode_runtime_products(
            reference_products,
            shadow_products,
            abs_tol=float(abs_tol),
        ),
    }
    cache = getattr(loader, "_runtime_eval_cache", None)
    if isinstance(cache, dict):
        cache["execution_episode_controller_shadow"] = report
    return report
