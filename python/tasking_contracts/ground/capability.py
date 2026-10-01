"""Per-capability admission labels for the Ground scripted line.

Each Ground capability is either ``admitted_bounded`` (a named runtime owner
and evidence exist for a bounded slice) or ``held`` (no admitted owner). The
labels describe evidence posture; they grant nothing at runtime. A scripted
model that requests a held capability fails closed.

The domain label follows the plan's Ground gate: Ground may not be labelled
``playable`` (or ``playable_candidate``) until movement, terrain interaction,
sensing, fires, effects, damage, and observation export each have an admitted
runtime owner. While any of them is held the domain label stays
``bounded_adapter``.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping



GROUND_CAPABILITY_ADMITTED_BOUNDED = "admitted_bounded"
GROUND_CAPABILITY_HELD = "held"
GROUND_CAPABILITY_STATES: frozenset[str] = frozenset(
    {GROUND_CAPABILITY_ADMITTED_BOUNDED, GROUND_CAPABILITY_HELD}
)


class GroundCapabilityHeldError(ValueError):
    """Raised when a request depends on a Ground capability that is held."""


@dataclass(frozen=True)
class GroundCapability:
    capability_id: str
    state: str
    owner: str
    boundary: str

    def __post_init__(self) -> None:
        if self.state not in GROUND_CAPABILITY_STATES:
            raise ValueError(f"unknown Ground capability state: {self.state!r}")
        if self.state == GROUND_CAPABILITY_ADMITTED_BOUNDED and not self.owner.strip():
            raise ValueError(f"admitted Ground capability {self.capability_id!r} requires an owner")


_ADMITTED = GROUND_CAPABILITY_ADMITTED_BOUNDED
_HELD = GROUND_CAPABILITY_HELD

GROUND_CAPABILITIES: Mapping[str, GroundCapability] = MappingProxyType(
    {
        item.capability_id: item
        for item in (
            GroundCapability(
                "single_unit_movement",
                _ADMITTED,
                "src/systems/domains/ground/movement_system.h (GroundInfantryMovement)",
                "one infantry soldier; MoveStatic heading/speed/stance one-tick kinematic step",
            ),
            GroundCapability(
                "static_hold",
                _ADMITTED,
                "src/systems/domains/ground/movement_system.h (GroundInfantryMovement)",
                "OccupyStatic/SupportStatic as zero-velocity position hold; no cover or concealment",
            ),
            GroundCapability(
                "local_terrain_interaction",
                _ADMITTED,
                "src/systems/domains/ground/movement_effects.h plus the shared IEnvironmentModel",
                "surface/slope/vegetation/stance speed cost and sampled one-tick transition block; "
                "not a route product",
            ),
            GroundCapability(
                "bounded_direct_fire_request",
                _ADMITTED,
                "SimulationKernel.fire_ground_weapon_from_mission_command (native release gate)",
                "rifle release only for an assigned, authorized, tracked target; close-range proxy "
                "without line of sight, ballistics, or target selection",
            ),
            GroundCapability(
                "route_planning", _HELD, "", "no route graph, waypoint planner, or route intent field"
            ),
            GroundCapability("general_passability", _HELD, "", "no route-level passability mask"),
            GroundCapability(
                "line_of_sight_cover_concealment", _HELD, "", "no line-of-sight, cover, or concealment owner"
            ),
            GroundCapability(
                "ground_sensing_track_export", _HELD, "", "no Ground sensor, track fusion, or track export"
            ),
            GroundCapability(
                "observation_export", _HELD, "", "no formal Ground ObservationPacket/TrackPacket"
            ),
            GroundCapability(
                "effects_damage_consequence",
                _HELD,
                "",
                "GroundPlatformDamageState is a reachable mechanism, not a released effects capability",
            ),
            GroundCapability("indirect_fire", _HELD, "", "no indirect-fire owner"),
            GroundCapability("suppression", _HELD, "", "no suppression owner"),
            GroundCapability("logistics", _HELD, "", "no logistics or sustainment owner"),
            GroundCapability("multi_unit_formation", _HELD, "", "single-soldier slice only"),
        )
    }
)

# The capability families the plan's Ground gate names before any playable
# label: movement, terrain interaction, sensing, fires, effects, damage, and
# observation export. Fires require every Ground fire owner, not the bounded
# direct-fire request alone.
GROUND_PLAYABLE_GATE: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "movement": ("single_unit_movement", "route_planning", "multi_unit_formation"),
        "terrain_interaction": ("local_terrain_interaction", "general_passability"),
        "sensing": ("ground_sensing_track_export", "line_of_sight_cover_concealment"),
        "fires": ("bounded_direct_fire_request", "indirect_fire", "suppression"),
        "effects": ("effects_damage_consequence",),
        "damage": ("effects_damage_consequence",),
        "observation_export": ("observation_export",),
    }
)

GROUND_INFANTRY_SCRIPTED_REQUIRED_CAPABILITIES: tuple[str, ...] = (
    "single_unit_movement",
    "static_hold",
    "local_terrain_interaction",
    "bounded_direct_fire_request",
)


def held_ground_capabilities() -> tuple[str, ...]:
    return tuple(
        capability_id
        for capability_id, item in GROUND_CAPABILITIES.items()
        if item.state == GROUND_CAPABILITY_HELD
    )


def require_ground_capabilities(capability_ids: Iterable[str]) -> tuple[str, ...]:
    """Return the requested ids if all are admitted; fail closed otherwise."""

    requested = tuple(str(item).strip() for item in capability_ids)
    unknown = sorted(item for item in requested if item not in GROUND_CAPABILITIES)
    if unknown:
        raise KeyError(f"unknown Ground capability: {unknown!r}")
    held = sorted(
        item for item in requested if GROUND_CAPABILITIES[item].state == GROUND_CAPABILITY_HELD
    )
    if held:
        raise GroundCapabilityHeldError(f"Ground capability is held: {held!r}")
    return requested


def ground_domain_label() -> str:
    """Derive the Ground domain label from the per-capability states."""

    gate_open = all(
        GROUND_CAPABILITIES[capability_id].state == GROUND_CAPABILITY_ADMITTED_BOUNDED
        for capability_ids in GROUND_PLAYABLE_GATE.values()
        for capability_id in capability_ids
    )
    if not gate_open:
        return "bounded_adapter"
    # Every gate owner being admitted is necessary, not sufficient: the plan's
    # promotion gate (scenario, CLI, visualization, replay records) still
    # decides between playable_candidate and playable.
    return "playable_candidate"


__all__ = [
    "GROUND_CAPABILITIES",
    "GROUND_CAPABILITY_ADMITTED_BOUNDED",
    "GROUND_CAPABILITY_HELD",
    "GROUND_CAPABILITY_STATES",
    "GROUND_INFANTRY_SCRIPTED_REQUIRED_CAPABILITIES",
    "GROUND_PLAYABLE_GATE",
    "GroundCapability",
    "GroundCapabilityHeldError",
    "ground_domain_label",
    "held_ground_capabilities",
    "require_ground_capabilities",
]
