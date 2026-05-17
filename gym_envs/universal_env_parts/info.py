from __future__ import annotations

import numpy as np


def _base_step_info(
    loader,
    *,
    mission_status,
    terminated: bool,
    truncated: bool,
) -> dict[str, object]:
    info: dict[str, object] = {
        "mission_status": np.array(mission_status, dtype=np.float32),
        "terminated": float(bool(terminated)),
        "truncated": float(bool(truncated)),
    }
    try:
        tr = getattr(loader, "last_termination_reason", None)
        if isinstance(tr, str) and tr:
            info["termination_reason"] = tr
    except Exception:
        pass
    try:
        rb = getattr(loader, "last_reward_breakdown", None)
        if isinstance(rb, dict) and rb:
            info["reward_terms"] = {k: float(v) for k, v in rb.items()}
    except Exception:
        pass
    return info


def build_step_info(
    loader,
    sim,
    agent_id: int,
    *,
    mission_status,
    terminated: bool,
    truncated: bool,
    inst_now=None,
    truth_now=None,
):
    info = _base_step_info(
        loader,
        mission_status=mission_status,
        terminated=terminated,
        truncated=truncated,
    )
    compiled_runtime_enabled = bool(
        hasattr(loader, "_compiled_step_info_enabled")
        and loader._compiled_step_info_enabled()
        and hasattr(loader, "_compute_step_info_runtime_products")
    )
    try:
        inst_now = inst_now if inst_now is not None else sim.get_instrument_state(agent_id)
        if compiled_runtime_enabled:
            truth_now = truth_now if truth_now is not None else sim.get_agent_observation(agent_id)
            products = loader._compute_step_info_runtime_products(inst_now=inst_now, truth_now=truth_now)
            info["on_runway"] = float(bool(products.on_runway))
            info["gear_collapsed"] = float(bool(products.gear_collapsed))
            info["gear_stress"] = float(products.gear_stress)
            info["on_ground"] = float(bool(products.on_ground))
            if bool(products.has_runway_frame):
                info["on_runway_geom"] = float(bool(products.on_runway_geom))
                info["runway_cross_m"] = float(products.runway_cross_m)
                info["runway_along_m"] = float(products.runway_along_m)
        else:
            info["on_runway"] = float(bool(getattr(inst_now, "on_runway", True)))
            info["gear_collapsed"] = float(bool(getattr(inst_now, "gear_collapsed", False)))
            info["gear_stress"] = float(getattr(inst_now, "gear_stress", 0.0))
            alt_agl = float(getattr(inst_now, "alt_radar", 0.0))
            cfg = loader.get_rewards_config()
            on_ground_alt_threshold = float(cfg.get("on_ground_alt_threshold", 2.5))
            airborne_alt_threshold = float(cfg.get("airborne_alt_threshold", cfg.get("liftoff_alt_threshold", 5.0)))
            on_ground = alt_agl <= on_ground_alt_threshold
            airborne = alt_agl >= airborne_alt_threshold
            preliftoff = not airborne
            info["on_ground"] = float(on_ground)
            try:
                truth_now = truth_now if truth_now is not None else sim.get_agent_observation(agent_id)
                valid_rf, along_m, cross_m, rw_len, rw_wid = loader.get_runway_local_frame(
                    float(truth_now.x), float(truth_now.y)
                )
                if valid_rf and rw_len > 1.0 and rw_wid > 1.0:
                    runway_width_margin_m = float(cfg.get("runway_width_margin_m", 2.0))
                    runway_length_margin_m = float(cfg.get("runway_length_margin_m", 0.0))
                    info["on_runway_geom"] = float(
                        bool(
                            preliftoff
                            and abs(cross_m) <= 0.5 * rw_wid + runway_width_margin_m
                            and abs(along_m) <= 0.5 * rw_len + runway_length_margin_m
                        )
                    )
                    info["runway_cross_m"] = float(cross_m)
                    info["runway_along_m"] = float(along_m)
            except Exception:
                pass
    except Exception:
        pass
    return info


def build_step_info_minimal(
    loader,
    *,
    mission_status,
    terminated: bool,
    truncated: bool,
):
    return _base_step_info(
        loader,
        mission_status=mission_status,
        terminated=terminated,
        truncated=truncated,
    )


__all__ = ["build_step_info", "build_step_info_minimal"]
