from __future__ import annotations

from dataclasses import dataclass

import torch as th

from python.rl.mission_defs import (
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


def route_from_mission_observation(
    mission: th.Tensor | None,
    *,
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

    family = th.where(is_takeoff, th.full_like(family, FAMILY_TAKEOFF_GROUND), family)
    family = th.where(is_landing, th.full_like(family, FAMILY_RECOVERY_LANDING), family)
    if has_formation_semantics:
        family = th.where(
            is_vector_or_route,
            th.full_like(family, FAMILY_FORMATION_COOPERATIVE),
            family,
        )

    subexpert = _zeros_long(batch, device=dev)

    if _cooperative_takeoff_layout(dim):
        takeoff_procedure_code = _safe_round_long(mission[:, 14])
        formation_role_code = _safe_round_long(mission[:, 22])
    elif _formation_role_layout(dim):
        takeoff_procedure_code = _zeros_long(batch, device=dev)
        formation_role_code = _safe_round_long(mission[:, 18])
    else:
        takeoff_procedure_code = _zeros_long(batch, device=dev)
        formation_role_code = _zeros_long(batch, device=dev)

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
