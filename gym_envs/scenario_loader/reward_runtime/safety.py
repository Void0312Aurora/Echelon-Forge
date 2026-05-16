import ef_py


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


def build_neutral_execution_safety_inputs():
    inputs = ef_py.SafetyRuntimeInputs()
    inputs.finite_state_valid = True
    inputs.health = 100.0
    inputs.survival_reward = 0.0
    return inputs
