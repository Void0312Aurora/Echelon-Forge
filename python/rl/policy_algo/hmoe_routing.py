from __future__ import annotations

from dataclasses import dataclass

import torch as th

from python.rl.control.mission_defs import (
    COMMAND_CODE_LANDING,
    COMMAND_CODE_ROUTE,
    COMMAND_CODE_TAKEOFF,
    COMMAND_CODE_VECTOR,
)


FAMILY_TAKEOFF_GROUND = 0
FAMILY_DEPARTURE_NAV = 1
FAMILY_FORMATION_COOPERATIVE = 2
FAMILY_RECOVERY_LANDING = 3

FAMILY_NAMES = {
    FAMILY_TAKEOFF_GROUND: "takeoff_ground",
    FAMILY_DEPARTURE_NAV: "departure_nav",
    FAMILY_FORMATION_COOPERATIVE: "formation_cooperative",
    FAMILY_RECOVERY_LANDING: "recovery_landing",
}

DEFAULT_FAMILY_SUBEXPERT_COUNTS = (
    3,  # takeoff: single / interval / wing
    2,  # departure_nav: vector / route
    3,  # formation: generic / lead / wingman
    1,  # recovery: generic
)

DEFAULT_SUBEXPERT_NAMES = {
    FAMILY_TAKEOFF_GROUND: ("single_ship", "interval", "wing"),
    FAMILY_DEPARTURE_NAV: ("vector", "route"),
    FAMILY_FORMATION_COOPERATIVE: ("generic", "element_lead", "wingman"),
    FAMILY_RECOVERY_LANDING: ("generic",),
}


@dataclass(frozen=True)
class HMoERouteBatch:
    family_index: th.Tensor
    subexpert_index: th.Tensor


_INSTRUMENT_IAS_IDX = 0
_INSTRUMENT_ALT_RADAR_IDX = 3


def family_name(family_id: int) -> str:
    return str(FAMILY_NAMES.get(int(family_id), f"family_{int(family_id)}"))


def subexpert_name(family_id: int, subexpert_id: int) -> str:
    names = DEFAULT_SUBEXPERT_NAMES.get(int(family_id), ())
    if 0 <= int(subexpert_id) < len(names):
        return str(names[int(subexpert_id)])
    return f"subexpert_{int(subexpert_id)}"


def _zeros_long(batch_size: int, *, device: th.device | None = None) -> th.Tensor:
    return th.zeros((int(batch_size),), dtype=th.long, device=device)


def _safe_round_long(values: th.Tensor) -> th.Tensor:
    return th.round(values.float()).to(dtype=th.long)


def _cooperative_takeoff_layout(dim: int) -> bool:
    return int(dim) >= 25


def _formation_role_layout(dim: int) -> bool:
    return int(dim) >= 21 and not _cooperative_takeoff_layout(dim)


def _formation_layout(dim: int) -> bool:
    return int(dim) >= 17 and not _formation_role_layout(dim) and not _cooperative_takeoff_layout(dim)


def _mission_field(mission: th.Tensor, index: int, batch: int, device: th.device) -> th.Tensor:
    if mission.ndim != 2 or int(mission.shape[1]) <= int(index):
        return mission.new_zeros((batch,), device=device)
    return mission[:, int(index)]


def _instrument_field(instruments: th.Tensor | None, index: int, batch: int, device: th.device) -> th.Tensor:
    if instruments is None or instruments.ndim != 2 or int(instruments.shape[1]) <= int(index):
        return th.zeros((batch,), dtype=th.float32, device=device)
    return instruments[:, int(index)].to(device=device, dtype=th.float32)


def route_from_mission_observation(
    mission: th.Tensor | None,
    *,
    instruments: th.Tensor | None = None,
    batch_size: int | None = None,
    device: th.device | None = None,
) -> HMoERouteBatch:
    """
    Build a deterministic routing decision from the maintained mission observation vector.

    This first HMoE skeleton intentionally uses only already-exposed execution-layer
    semantics instead of introducing a new observation contract.
    """
    if mission is None:
        if batch_size is None:
            raise ValueError("batch_size is required when mission is None")
        family = th.full((int(batch_size),), FAMILY_DEPARTURE_NAV, dtype=th.long, device=device)
        subexpert = _zeros_long(int(batch_size), device=device)
        return HMoERouteBatch(family_index=family, subexpert_index=subexpert)

    if mission.ndim != 2:
        raise ValueError(f"mission tensor must have shape [batch, dim], got {tuple(mission.shape)}")

    batch = int(mission.shape[0])
    dim = int(mission.shape[1])
    dev = mission.device if device is None else device

    command_code = _safe_round_long(mission[:, 0]) if dim >= 1 else _zeros_long(batch, device=dev)
    family = th.full((batch,), FAMILY_DEPARTURE_NAV, dtype=th.long, device=dev)

    is_takeoff = command_code == int(COMMAND_CODE_TAKEOFF)
    is_landing = command_code == int(COMMAND_CODE_LANDING)
    is_vector_or_route = (command_code == int(COMMAND_CODE_VECTOR)) | (command_code == int(COMMAND_CODE_ROUTE))
    has_formation_semantics = bool(dim >= 17)

    takeoff_procedure_code = _zeros_long(batch, device=dev)
    takeoff_clearance_code = _zeros_long(batch, device=dev)
    runway_slot_code = _zeros_long(batch, device=dev)
    formation_role_code = _zeros_long(batch, device=dev)
    track_angle_error_deg = _mission_field(mission, 10, batch, dev)
    cdi_norm = _mission_field(mission, 9, batch, dev)
    alt_delta_m = _mission_field(mission, 8, batch, dev)

    if _cooperative_takeoff_layout(dim):
        takeoff_procedure_code = _safe_round_long(mission[:, 14])
        takeoff_clearance_code = _safe_round_long(mission[:, 15])
        runway_slot_code = _safe_round_long(mission[:, 17])
        formation_role_code = _safe_round_long(mission[:, 22])
    elif _formation_role_layout(dim):
        formation_role_code = _safe_round_long(mission[:, 18])

    alt_radar = _instrument_field(instruments, _INSTRUMENT_ALT_RADAR_IDX, batch, dev)
    ias = _instrument_field(instruments, _INSTRUMENT_IAS_IDX, batch, dev)
    abs_track_err = track_angle_error_deg.abs()
    abs_cdi = cdi_norm.abs()

    takeoff_clearance_active = takeoff_clearance_code > 0
    takeoff_ground_hint = takeoff_clearance_active & ((alt_radar < 160.0) | (ias < 95.0))
    departure_hint = takeoff_clearance_active & ~takeoff_ground_hint & (
        (alt_radar < 900.0)
        | (abs_track_err > 20.0)
        | (abs_cdi > 0.35)
        | (alt_delta_m.abs() > 250.0)
    )
    cooperative_role_active = formation_role_code > 0
    if has_formation_semantics:
        formation_hint = cooperative_role_active & is_vector_or_route & ~takeoff_ground_hint & ~departure_hint
    else:
        formation_hint = th.zeros((batch,), dtype=th.bool, device=dev)
    landing_hint = is_landing | (
        is_vector_or_route
        & (alt_radar < 900.0)
        & (alt_delta_m < -250.0)
        & (abs_track_err < 25.0)
        & ~takeoff_clearance_active
    )

    family = th.where(is_takeoff | takeoff_ground_hint, th.full_like(family, FAMILY_TAKEOFF_GROUND), family)
    family = th.where(landing_hint, th.full_like(family, FAMILY_RECOVERY_LANDING), family)
    family = th.where(departure_hint, th.full_like(family, FAMILY_DEPARTURE_NAV), family)
    family = th.where(
        formation_hint,
        th.full_like(family, FAMILY_FORMATION_COOPERATIVE),
        family,
    )

    subexpert = _zeros_long(batch, device=dev)

    takeoff_sub = th.clamp(takeoff_procedure_code - 1, min=0)
    route_sub = (command_code == int(COMMAND_CODE_ROUTE)).to(dtype=th.long)

    # FormationRole: 0=Unspecified, 1=ElementLead, 2=Wingman
    formation_sub = th.where(
        formation_role_code == 1,
        th.ones_like(formation_role_code),
        th.where(
            formation_role_code == 2,
            th.full_like(formation_role_code, 2),
            th.zeros_like(formation_role_code),
        ),
    )

    subexpert = th.where(family == FAMILY_TAKEOFF_GROUND, takeoff_sub, subexpert)
    subexpert = th.where(family == FAMILY_DEPARTURE_NAV, route_sub, subexpert)
    subexpert = th.where(family == FAMILY_FORMATION_COOPERATIVE, formation_sub, subexpert)

    return HMoERouteBatch(family_index=family, subexpert_index=subexpert)
