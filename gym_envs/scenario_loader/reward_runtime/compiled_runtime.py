import ef_py


def compiled_execution_step_enabled(loader) -> bool:
    return bool(getattr(loader, "use_compiled_execution_step_runtime", True)) and hasattr(
        ef_py, "ExecutionStepRuntimeInputs"
    ) and hasattr(ef_py, "compute_execution_step_runtime")


def compiled_execution_frame_enabled(loader) -> bool:
    return bool(getattr(loader, "use_compiled_execution_step_runtime", True)) and hasattr(
        ef_py, "ExecutionFrameRuntimeInputs"
    ) and hasattr(ef_py, "compute_execution_frame_runtime")


def compiled_execution_episode_enabled(loader) -> bool:
    return bool(getattr(loader, "use_compiled_execution_step_runtime", True)) and hasattr(
        ef_py, "ExecutionEpisodeRuntimeInputs"
    ) and hasattr(ef_py, "compute_execution_episode_runtime")


def compute_execution_step_runtime_products(
    loader,
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
    inputs.safety = safety_inputs if safety_inputs is not None else loader._build_neutral_execution_safety_inputs()
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
        inputs.objective_shaping = loader._objective_shaping_cfg
    return ef_py.compute_execution_step_runtime(inputs)
