from __future__ import annotations

import math
from typing import Any

import numpy as np


def _normalize_spawn_ammo_override(entity_cfg: dict[str, Any]) -> tuple[bool, int, int]:
    ammo_cfg = entity_cfg.get("ammo", None)
    if not isinstance(ammo_cfg, dict):
        return False, 0, 0
    try:
        missiles_remaining = max(0, int(ammo_cfg.get("missiles_remaining", ammo_cfg.get("count", 0))))
    except Exception:
        missiles_remaining = 0
    try:
        max_missiles = int(ammo_cfg.get("max_missiles", ammo_cfg.get("capacity", missiles_remaining)))
    except Exception:
        max_missiles = missiles_remaining
    max_missiles = max(missiles_remaining, max(0, max_missiles))
    return True, missiles_remaining, max_missiles


def _normalize_spawn_weapon_cooldown_override(entity_cfg: dict[str, Any]) -> tuple[bool, float, float]:
    cooldown_cfg = entity_cfg.get("weapon_cooldown", None)
    if not isinstance(cooldown_cfg, dict):
        return False, 2.0, -1.0
    try:
        cooldown_s = float(cooldown_cfg.get("cooldown_s", 2.0))
    except Exception:
        cooldown_s = 2.0
    try:
        last_fire_time = float(cooldown_cfg.get("last_fire_time", -1.0))
    except Exception:
        last_fire_time = -1.0
    return True, cooldown_s, last_fire_time


def _sample_uniform(rng: np.random.RandomState, value: Any, default: float) -> float:
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        try:
            return float(rng.uniform(float(value[0]), float(value[1])))
        except Exception:
            return float(default)
    try:
        return float(value)
    except Exception:
        return float(default)


def _apply_spawn_randomization(
    rng: np.random.RandomState,
    pos: list[float],
    vel: list[float],
    heading: float,
    pitch: float,
    roll: float,
    rand_cfg: dict[str, Any] | None,
) -> tuple[list[float], list[float], float, float, float]:
    if not isinstance(rand_cfg, dict):
        return pos, vel, float(heading), float(pitch), float(roll)

    heading += _sample_uniform(rng, rand_cfg.get("heading_offset_deg_range", [0.0, 0.0]), 0.0)
    pitch += _sample_uniform(rng, rand_cfg.get("pitch_offset_deg_range", [0.0, 0.0]), 0.0)
    roll += _sample_uniform(rng, rand_cfg.get("roll_offset_deg_range", [0.0, 0.0]), 0.0)

    h_rad = math.radians(float(heading))
    fwd_x = math.sin(h_rad)
    fwd_y = math.cos(h_rad)
    right_x = math.cos(h_rad)
    right_y = -math.sin(h_rad)

    along_off = _sample_uniform(rng, rand_cfg.get("along_body_m_range", [0.0, 0.0]), 0.0)
    cross_off = _sample_uniform(rng, rand_cfg.get("cross_body_m_range", [0.0, 0.0]), 0.0)
    alt_off = _sample_uniform(rng, rand_cfg.get("altitude_offset_m_range", [0.0, 0.0]), 0.0)

    try:
        pos[0] = float(pos[0]) + along_off * fwd_x + cross_off * right_x
        pos[1] = float(pos[1]) + along_off * fwd_y + cross_off * right_y
        pos[2] = float(pos[2]) + alt_off
    except Exception:
        pass

    try:
        base_horiz_speed = math.sqrt(float(vel[0]) * float(vel[0]) + float(vel[1]) * float(vel[1]))
    except Exception:
        base_horiz_speed = 0.0
    speed_scale = _sample_uniform(rng, rand_cfg.get("speed_scale_range", [1.0, 1.0]), 1.0)
    speed_off = _sample_uniform(rng, rand_cfg.get("speed_offset_mps_range", [0.0, 0.0]), 0.0)
    horiz_speed = max(0.0, float(base_horiz_speed) * float(speed_scale) + float(speed_off))
    sink_default = float(vel[2]) if len(vel) > 2 else 0.0
    sink_rate = _sample_uniform(
        rng,
        rand_cfg.get("sink_rate_mps_range", [sink_default, sink_default]),
        sink_default,
    )

    if len(vel) < 3:
        vel = [0.0, 0.0, 0.0]
    vel[0] = float(horiz_speed * fwd_x)
    vel[1] = float(horiz_speed * fwd_y)
    vel[2] = float(sink_rate)

    return pos, vel, float(heading), float(pitch), float(roll)


def _sample_entity_spawn(
    rng: np.random.RandomState,
    ent_cfg: dict[str, Any],
) -> tuple[list[float], list[float], float, float, float]:
    pos = list(ent_cfg.get("pos", [0.0, 0.0, 0.0]))
    vel = list(ent_cfg.get("vel", [0.0, 0.0, 0.0]))
    heading = float(ent_cfg.get("heading", 0.0))
    pitch = float(ent_cfg.get("pitch", 0.0))
    roll = float(ent_cfg.get("roll", 0.0))
    return _apply_spawn_randomization(
        rng,
        pos,
        vel,
        heading,
        pitch,
        roll,
        ent_cfg.get("randomization", None),
    )
