from __future__ import annotations

import math
from collections.abc import Sequence

import torch


# Indices into `obs_vec` (which begins with `obs["instruments"]`) that correspond
# to angular quantities in degrees (NAV convention, clockwise from North).
#
# These angles are discontinuous at 0/360 which can make it hard for MLP policies
# to learn correct relationships (e.g., crosswind sign). We provide sin/cos
# features derived from the *raw* degree values to give the policy a smooth
# representation without leaking any privileged information.
DEFAULT_ANGLE_DEG_INDICES: tuple[int, ...] = (
    9,   # inst.heading
    30,  # inst.ground_track
    32,  # inst.wind_dir (from)
)


def angle_sincos_features(
    obs_raw_deg: torch.Tensor,
    *,
    angle_deg_indices: Sequence[int] = DEFAULT_ANGLE_DEG_INDICES,
) -> torch.Tensor:
    """
    Compute sin/cos features for selected degree-valued indices.

    Returns a tensor with shape (..., 2 * len(angle_deg_indices)).
    """
    if not angle_deg_indices:
        shape = list(obs_raw_deg.shape)
        shape[-1] = 0
        return obs_raw_deg.new_zeros(shape)

    idx = torch.as_tensor(list(angle_deg_indices), device=obs_raw_deg.device, dtype=torch.long)
    angles = torch.index_select(obs_raw_deg, dim=-1, index=idx)
    rad = angles * (math.pi / 180.0)
    return torch.cat([torch.sin(rad), torch.cos(rad)], dim=-1)


def append_angle_sincos_features(
    *,
    obs_raw_deg: torch.Tensor,
    obs_norm: torch.Tensor,
    angle_deg_indices: Sequence[int] = DEFAULT_ANGLE_DEG_INDICES,
) -> torch.Tensor:
    """
    Append sin/cos(angle) features for selected degree-valued indices.

    Args:
        obs_raw_deg: Raw (unnormalized) observation tensor in degrees, (..., D).
        obs_norm: Normalized observation tensor, same shape as obs_raw_deg.
        angle_deg_indices: Indices into the last dimension to be encoded.

    Returns:
        Feature tensor (..., D + 2*len(angle_deg_indices)).
    """
    if obs_raw_deg.shape != obs_norm.shape:
        raise ValueError(f"obs_raw_deg and obs_norm must have same shape, got {obs_raw_deg.shape} vs {obs_norm.shape}")

    if not angle_deg_indices:
        return obs_norm

    feats = angle_sincos_features(obs_raw_deg, angle_deg_indices=angle_deg_indices)
    return torch.cat([obs_norm, feats], dim=-1)


def nav_tracking_features(
    obs_raw: torch.Tensor,
    *,
    cmd_code_idx: int | None = 42,
    heading_idx: int = 9,
    target_heading_idx: int = 43,
    ground_track_idx: int = 30,
    wind_speed_idx: int = 31,
    wind_dir_from_idx: int = 32,
    alt_idx: int = 2,
    target_alt_idx: int = 44,
    spd_idx: int = 0,
    target_spd_idx: int = 45,
    alt_norm_m: float = 100.0,
    spd_norm_mps: float = 30.0,
    wind_norm_mps: float = 20.0,
    clip: float = 10.0,
) -> torch.Tensor:
    """
    Compute realism-safe closed-loop tracking features derived from existing observations.

    This intentionally does NOT add any privileged information: it only transforms already-available
    pilot/avionics channels (instruments + mission command).

    Output shape: (..., 8)
      [0] alt_err_norm   = (target_alt - alt_baro) / alt_norm_m
      [1] spd_err_norm   = (target_spd - ias) / spd_norm_mps
      [2] sin(hdg_err)   where hdg_err = wrap_deg(target_heading - heading) in NAV convention
                         For waypoint navigation (command_code==3), interpret target_heading as a *track* bug
                         and compute the error against ground_track instead of heading.
      [3] cos(hdg_err)
      [4] wind_head_norm = headwind component (from) / wind_norm_mps  (positive = headwind)
      [5] wind_cross_norm= crosswind component (from) / wind_norm_mps (positive = wind from right)
      [6] sin(drift)     where drift = wrap_deg(ground_track - heading)
      [7] cos(drift)
    """
    d = int(obs_raw.shape[-1])
    need = [
        (cmd_code_idx if cmd_code_idx is not None else 0),
        heading_idx,
        target_heading_idx,
        ground_track_idx,
        wind_speed_idx,
        wind_dir_from_idx,
        alt_idx,
        target_alt_idx,
        spd_idx,
        target_spd_idx,
    ]
    if d <= max(need):
        shape = list(obs_raw.shape)
        shape[-1] = 8
        return obs_raw.new_zeros(shape)

    cmd_code = None
    if cmd_code_idx is not None:
        cmd_code = obs_raw[..., int(cmd_code_idx)]

    heading = obs_raw[..., heading_idx]
    target_heading = obs_raw[..., target_heading_idx]
    ground_track = obs_raw[..., ground_track_idx]
    wind_speed = obs_raw[..., wind_speed_idx]
    wind_dir_from = obs_raw[..., wind_dir_from_idx]

    alt = obs_raw[..., alt_idx]
    target_alt = obs_raw[..., target_alt_idx]
    spd = obs_raw[..., spd_idx]
    target_spd = obs_raw[..., target_spd_idx]

    # Signed tracking errors (positive => need to increase the state)
    alt_err = (target_alt - alt) / max(float(alt_norm_m), 1.0e-6)
    spd_err = (target_spd - spd) / max(float(spd_norm_mps), 1.0e-6)

    # Angle differences in degrees, wrapped to [-180, 180)
    hdg_err_heading_deg = torch.remainder((target_heading - heading) + 180.0, 360.0) - 180.0
    if cmd_code is not None:
        # command_code is a float channel; treat 3 as waypoint navigation.
        is_wp = (cmd_code > 2.5) & (cmd_code < 3.5)
        hdg_err_track_deg = torch.remainder((target_heading - ground_track) + 180.0, 360.0) - 180.0
        hdg_err_deg = torch.where(is_wp, hdg_err_track_deg, hdg_err_heading_deg)
    else:
        hdg_err_deg = hdg_err_heading_deg
    drift_deg = torch.remainder((ground_track - heading) + 180.0, 360.0) - 180.0

    hdg_err_rad = hdg_err_deg * (math.pi / 180.0)
    drift_rad = drift_deg * (math.pi / 180.0)

    # Wind components relative to aircraft heading (using wind FROM direction).
    # headwind positive => wind from ahead; crosswind positive => wind from right.
    rel_rad = (wind_dir_from - heading) * (math.pi / 180.0)
    wind_head = wind_speed * torch.cos(rel_rad) / max(float(wind_norm_mps), 1.0e-6)
    wind_cross = wind_speed * torch.sin(rel_rad) / max(float(wind_norm_mps), 1.0e-6)

    out = torch.stack(
        [
            alt_err,
            spd_err,
            torch.sin(hdg_err_rad),
            torch.cos(hdg_err_rad),
            wind_head,
            wind_cross,
            torch.sin(drift_rad),
            torch.cos(drift_rad),
        ],
        dim=-1,
    )
    if clip is not None and float(clip) > 0.0:
        out = torch.clamp(out, -float(clip), float(clip))
    return out
