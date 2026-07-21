import ef_py

from gym_envs.scenario_loader._generated import safety_runtime_inputs_builder


# G4 information-state declaration (architecture design doc §3/§15; facility in
# python/architecture/information_layer.py). This reward-input builder consumes
# own-ship authoritative truth directly (truth.health / z / pitch / speed),
# catalogued in the G4 truth-leak inventory as an own-ship read pending T8 view
# convergence. Reward inputs are an output, not an information layer, so PRODUCED
# is empty. Pure metadata; no runtime cost.
INFORMATION_LAYER_CONSUMED = ("World Truth",)
INFORMATION_LAYER_PRODUCED = ()
SEMANTIC_STAGE = ("P10 ObservationExport",)


_CFG_FIELDS = (
    "crash_penalty",
    "survival_reward",
    "stall_threshold_deg",
    "stall_penalty_weight",
    "stall_penalty_clip",
    "overload_g_threshold",
    "overload_penalty_weight",
    "overload_penalty_clip",
    "overload_min_alt_agl_m",
    "failfast_penalty",
    "gear_collapse_penalty",
    "gear_stress_penalty_weight",
    "off_runway_penalty",
    "off_runway_terminate_speed",
    "off_runway_terminate_grace_s",
    "off_runway_terminate_penalty",
)


def build_safety_runtime_inputs(
    loader,
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
    safety_cfg = loader._safety_reward_cfg

    safety_runtime_inputs_builder.assign_from_object(inputs, safety_cfg, _CFG_FIELDS)

    inputs.finite_state_valid = bool(finite_state_valid)
    inputs.health = float(getattr(truth, "health", 100.0))

    inputs.airborne = bool(airborne)
    inputs.aoa_valid = bool(aoa_valid)
    inputs.aoa_abs_deg = abs(float(curr_aoa))

    inputs.g_abs = abs(float(curr_g))
    inputs.curr_alt_agl_m = float(curr_alt_agl)

    inputs.altitude_m = float(getattr(truth, "z", 0.0))
    inputs.roll_abs_deg = abs(float(curr_roll))
    inputs.pitch_abs_deg = abs(float(getattr(truth, "pitch", 0.0)))

    inputs.gear_collapsed = bool(gear_collapsed)

    inputs.runway_surface_phase = bool(runway_surface_phase)
    inputs.on_runway_task = bool(on_runway_task)
    inputs.gear_stress = float(gear_stress)
    inputs.speed_mps = float(getattr(truth, "speed", 0.0))
    inputs.off_runway_steps = int(off_runway_steps)
    inputs.time_step_s = float(time_step_s)
    return inputs


def build_neutral_execution_safety_inputs():
    inputs = ef_py.SafetyRuntimeInputs()
    inputs.finite_state_valid = True
    inputs.health = 100.0
    inputs.survival_reward = 0.0
    return inputs
