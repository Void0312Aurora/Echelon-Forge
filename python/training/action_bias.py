"""Action-head initialization biases for training entrypoints.

These helpers shape the initial policy output distribution (throttle/gear
defaults, combat switch priors, leader phase defaults) before learning starts.
Torch is imported lazily so this module stays importable on dependency-free
CLI preflight paths.
"""

from __future__ import annotations

import argparse
import json
import math
from typing import Any

import numpy as np


_TORCH: Any | None = None


def _require_torch() -> Any:
    global _TORCH
    if _TORCH is None:
        import torch as torch_module

        if hasattr(torch_module, "set_float32_matmul_precision"):
            torch_module.set_float32_matmul_precision("high")
        _TORCH = torch_module
    return _TORCH


def _unit_to_presquash(value: float) -> float:
    x = float(np.clip(2.0 * float(value) - 1.0, -0.999, 0.999))
    return float(math.atanh(x))


def infer_full_action_safe_defaults(scenario_path: str) -> tuple[float, float, float, float]:
    """
    Infer reasonable initial throttle/gear defaults from the scenario.

    Full-action tasks are not all takeoff tasks. Airborne/cruise scenarios should not
    inherit a takeoff-style "gear down, near-max throttle" bias, otherwise PPO can get
    stuck around a bad initial mean for configuration controls.
    """
    throttle_default = 0.95
    gear_default = 1.0
    flaps_default = 0.0
    speedbrake_default = 0.0
    try:
        with open(scenario_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        mission = data.get("mission_command", {}) if isinstance(data, dict) else {}
        entities = data.get("entities", []) if isinstance(data, dict) else []
        agent = next((e for e in entities if isinstance(e, dict) and bool(e.get("is_agent", False))), None)
        pos = agent.get("pos", []) if isinstance(agent, dict) else []
        spawn_alt_m = float(pos[2]) if isinstance(pos, list) and len(pos) > 2 else 0.0
        spawn_speed_mps = 0.0
        vel = agent.get("vel", []) if isinstance(agent, dict) else []
        if isinstance(vel, list) and len(vel) >= 3:
            try:
                vx = float(vel[0])
                vy = float(vel[1])
                vz = float(vel[2])
                spawn_speed_mps = float(math.sqrt(vx * vx + vy * vy + vz * vz))
            except Exception:
                spawn_speed_mps = 0.0
        cmd_code = int(mission.get("command_code", 0)) if isinstance(mission, dict) else 0

        airborne_start = spawn_alt_m > 50.0
        runway_start = (spawn_alt_m <= 10.0) and (spawn_speed_mps <= 15.0)
        if cmd_code == 4:
            throttle_default = 0.45
            gear_default = 1.0
            flaps_default = 1.0
            speedbrake_default = 0.0
        elif airborne_start or (cmd_code == 3 and not runway_start):
            throttle_default = 0.60
            gear_default = 0.0
            flaps_default = 0.0
            speedbrake_default = 0.0
    except Exception:
        pass
    return float(throttle_default), float(gear_default), float(flaps_default), float(speedbrake_default)


def apply_safe_action_bias(
    model: Any,
    action_mode: str,
    scenario_path: str,
    train_config: dict[str, Any] | None = None,
):
    """
    Improve early exploration for mixed-range action spaces.

    SB3 PPO uses an (unbounded) Gaussian policy. For dimensions with bounds [0, 1],
    the default mean initialization at 0.0 tends to clip to 0.0 (e.g. throttle=0),
    which can trap learning in the "stationary on runway" regime. We bias those
    outputs toward realistic neutral/safe defaults.
    """
    try:
        policy = getattr(model, "policy", None)
        action_net = getattr(policy, "action_net", None)
        hmoe_head_bank = getattr(policy, "hmoe_head_bank", None)

        def _apply_bias_vector(b):
            if b is None:
                return
            if action_mode == "full":
                if int(b.shape[0]) < 17:
                    return
                throttle_default, gear_default, flaps_default, speedbrake_default = infer_full_action_safe_defaults(scenario_path)
                # Safe defaults for the 17D "full" action layout in `gym_envs/universal_env.py`.
                # - throttle/gear are scenario-aware: takeoff starts on-ground, cruise starts airborne
                # - keep brakes/speedbrake/flaps and combat switches off by default
                if squash:
                    # With tanh-squash + unscale, bias=0 maps to the midpoint of [low,high].
                    # Push "off" switches below 0.5 by using negative pre-squash means.
                    b[3] = _unit_to_presquash(throttle_default)
                    b[4] = _unit_to_presquash(gear_default)
                    b[5] = _unit_to_presquash(flaps_default)
                    b[6] = _unit_to_presquash(speedbrake_default)

                    off_pre = -2.0
                    for idx in (7, 8, 9, 12, 13, 14, 15, 16):
                        b[idx] = off_pre
                else:
                    # Unbounded Gaussian + clip: bias directly corresponds to env action value.
                    b[3] = throttle_default
                    b[4] = gear_default
                    b[5] = flaps_default
                    b[6] = speedbrake_default
                    for idx in (7, 8, 9, 12, 13, 14, 15, 16):
                        b[idx] = 0.0
            elif action_mode == "takeoff2":
                if int(b.shape[0]) < 2:
                    return
                throttle_default = 1.0
                if squash:
                    b[1] = _unit_to_presquash(throttle_default)
                else:
                    b[1] = throttle_default
            elif action_mode == "takeoff4":
                if int(b.shape[0]) < 4:
                    return
                throttle_default = 1.0
                if squash:
                    b[3] = _unit_to_presquash(throttle_default)
                else:
                    b[3] = throttle_default
                # Keep lateral controls neutral at initialization so the early rollout explores
                # "accelerate straight" before searching over crosswind corrections.
                b[0] = 0.02
                b[1] = 0.0
                b[2] = 0.0
            elif action_mode == "naval_station3":
                if int(b.shape[0]) < 3:
                    return
                b[0] = 0.0
                b[1] = 0.0
                b[2] = 0.0
            elif action_mode == "air_combat_hybrid_v1":
                if int(b.shape[0]) < 20:
                    return
                throttle_default, _gear_default, _flaps_default, _speedbrake_default = infer_full_action_safe_defaults(
                    scenario_path
                )
                b[0] = 0.0
                b[1] = 0.0
                b[2] = 0.0
                b[3] = _unit_to_presquash(throttle_default)
                b[4] = 0.0
                b[5] = 0.0
                # Hybrid layout params: 0-5 continuous means, 6-10 binary logits,
                # 11 fire-event hold logit, 12-19 weapon-select categorical logits.
                b[6] = 3.0   # radar_active held on
                b[7] = -4.0  # tms_up pulse, sparse but reachable
                b[8] = 3.0   # master_arm held on
                # Keep the stochastic first-shot prior conservative. A7 event-policy
                # margin learns from legal-open/hindsight labels; relaxing this bias
                # makes pre-window releases almost certain and starves legal-open data.
                b[9] = -6.0  # fire_weapon pulse
                b[10] = -8.0  # fire_gun pulse
                b[11] = 0.0  # fire-event hold logit starts above fire.
                b[12:20] = -0.5
                b[13] = 1.0  # prefer station 1 over "no selected station" at startup

        has_standard_bias = action_net is not None and getattr(action_net, "bias", None) is not None
        has_hmoe_bias = hmoe_head_bank is not None
        if not has_standard_bias and not has_hmoe_bias:
            return
        squash = bool(getattr(policy, "squash_output", False))
        torch_module = _require_torch()
        with torch_module.no_grad():
            if has_standard_bias:
                _apply_bias_vector(action_net.bias)
                if action_mode in {"naval_station3", "air_combat_hybrid_v1"}:
                    weight = getattr(action_net, "weight", None)
                    if weight is not None:
                        weight.zero_()
            if has_hmoe_bias:
                for head in getattr(hmoe_head_bank, "family_heads", []):
                    bias = getattr(head, "bias", None)
                    if bias is not None:
                        bias.zero_()
                for family_subheads in getattr(hmoe_head_bank, "subexpert_heads", []):
                    for head in family_subheads:
                        bias = getattr(head, "bias", None)
                        if bias is not None:
                            bias.zero_()
    except Exception:
        return


def maybe_initialize_hmoe_from_shared(
    model: Any,
    *,
    train_config: dict,
    args: argparse.Namespace,
) -> bool:
    policy = getattr(model, "policy", None)
    init_fn = getattr(policy, "initialize_hmoe_from_shared_action_head", None)
    if not callable(init_fn):
        return False

    hmoe_cfg = train_config.get("hmoe", {}) if isinstance(train_config.get("hmoe", {}), dict) else {}
    bootstrap_mode = str(hmoe_cfg.get("bootstrap_from_shared_action_head", "auto")).strip().lower()
    if bootstrap_mode in ("", "none", "off", "false", "0", "disable", "disabled"):
        return False
    if args.resume_path:
        return False
    # When init_from is provided, honor the checkpoint weights as-is.
    if args.init_from:
        return False

    init_fn()
    return True


def apply_leader_action_bias(model: Any):
    """
    Bias leader policies toward a mild post-departure route-selection default.

    The leader phase action uses:
    - near 0.0 -> teacher
    - moderately negative -> route

    A small negative bias helps the policy discover "leave departure / start route
    tasking" much earlier, while low-altitude guardrails in `LeaderTrainingEnv`
    still keep takeoff and early departure safe.
    """
    try:
        action_net = getattr(model.policy, "action_net", None)
        if action_net is None or getattr(action_net, "bias", None) is None:
            return
        b = action_net.bias
        if b is None or int(b.shape[0]) < 4:
            return
        squash = bool(getattr(model.policy, "squash_output", False))
        torch_module = _require_torch()
        with torch_module.no_grad():
            phase_default = -0.35
            b[0] = float(np.arctanh(np.clip(phase_default, -0.999, 0.999))) if squash else phase_default
            b[1] = 0.0
            b[2] = 0.0
            b[3] = 0.0
    except Exception:
        return


__all__ = [
    "apply_leader_action_bias",
    "apply_safe_action_bias",
    "infer_full_action_safe_defaults",
    "maybe_initialize_hmoe_from_shared",
]
