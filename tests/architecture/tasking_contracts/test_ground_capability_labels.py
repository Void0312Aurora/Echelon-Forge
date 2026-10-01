"""Ground capability labels: admitted-bounded vs held, and fail-closed requests."""

from __future__ import annotations

import pytest

from python.tasking_contracts.common.scripted_capability import (
    SCRIPTED_CAPABILITY_LABELS,
    resolve_scripted_model_id,
)
from python.tasking_contracts.ground.capability import (
    GROUND_CAPABILITIES,
    GROUND_CAPABILITY_ADMITTED_BOUNDED,
    GROUND_CAPABILITY_HELD,
    GROUND_INFANTRY_SCRIPTED_REQUIRED_CAPABILITIES,
    GROUND_PLAYABLE_GATE,
    GroundCapability,
    GroundCapabilityHeldError,
    ground_domain_label,
    held_ground_capabilities,
    require_ground_capabilities,
)
from python.tasking_contracts.ground.execution import (
    GROUND_INFANTRY_CONTROLLER_ROLE_ID,
    GROUND_INFANTRY_SCRIPTED_CAPABILITY,
    GROUND_INFANTRY_SCRIPTED_MODEL_ID,
    GROUND_SCRIPTED_MODEL_REGISTRY,
    GroundInfantryObjectiveTask,
)


# The held list is the WP5 boundary; it must not shrink without an owner
# admission package and a matching change to this test.
EXPECTED_HELD = {
    "route_planning",
    "general_passability",
    "line_of_sight_cover_concealment",
    "ground_sensing_track_export",
    "observation_export",
    "effects_damage_consequence",
    "indirect_fire",
    "suppression",
    "logistics",
    "multi_unit_formation",
}
EXPECTED_ADMITTED = {
    "single_unit_movement",
    "static_hold",
    "local_terrain_interaction",
    "bounded_direct_fire_request",
}


def _task() -> GroundInfantryObjectiveTask:
    return GroundInfantryObjectiveTask(objective_xy_m=(10.0, 0.0), objective_radius_m=1.0)


def test_ground_capability_labels_are_exactly_the_admitted_and_held_sets() -> None:
    admitted = {
        key for key, item in GROUND_CAPABILITIES.items() if item.state == GROUND_CAPABILITY_ADMITTED_BOUNDED
    }
    held = {key for key, item in GROUND_CAPABILITIES.items() if item.state == GROUND_CAPABILITY_HELD}
    assert admitted == EXPECTED_ADMITTED
    assert held == EXPECTED_HELD
    assert set(held_ground_capabilities()) == EXPECTED_HELD
    for key in admitted:
        assert GROUND_CAPABILITIES[key].owner.strip(), key
    assert set(GROUND_INFANTRY_SCRIPTED_REQUIRED_CAPABILITIES) == EXPECTED_ADMITTED


def test_ground_domain_label_is_never_playable_while_a_gate_capability_is_held() -> None:
    assert ground_domain_label() == "bounded_adapter"
    assert ground_domain_label() not in {"playable", "playable_candidate"}
    gate_capabilities = {item for values in GROUND_PLAYABLE_GATE.values() for item in values}
    assert set(GROUND_PLAYABLE_GATE) == {
        "movement",
        "terrain_interaction",
        "sensing",
        "fires",
        "effects",
        "damage",
        "observation_export",
    }
    assert gate_capabilities <= set(GROUND_CAPABILITIES)
    assert gate_capabilities & EXPECTED_HELD


def test_ground_manifest_routes_the_model_but_does_not_claim_playable() -> None:
    manifest = GROUND_INFANTRY_SCRIPTED_CAPABILITY
    assert manifest.label == "bounded_adapter"
    assert manifest.label in SCRIPTED_CAPABILITY_LABELS
    assert set(manifest.deferred_claims) == EXPECTED_HELD
    assert resolve_scripted_model_id(
        manifest,
        expected_domain="ground",
        expected_role_id=GROUND_INFANTRY_CONTROLLER_ROLE_ID,
    ) == GROUND_INFANTRY_SCRIPTED_MODEL_ID


@pytest.mark.parametrize("capability_id", sorted(EXPECTED_HELD))
def test_requesting_a_held_ground_capability_fails_closed(capability_id: str) -> None:
    with pytest.raises(GroundCapabilityHeldError, match=capability_id):
        require_ground_capabilities((capability_id,))
    model = GROUND_SCRIPTED_MODEL_REGISTRY.create(GROUND_INFANTRY_SCRIPTED_MODEL_ID)
    with pytest.raises(GroundCapabilityHeldError, match=capability_id):
        model.reset(context={"task": _task(), "requested_capabilities": [capability_id]})
    # A failed reset leaves no task armed.
    with pytest.raises(RuntimeError, match="reset"):
        model.decide(observation=None, context={}, dt=0.0)


def test_admitted_and_unknown_capability_requests() -> None:
    assert require_ground_capabilities(sorted(EXPECTED_ADMITTED)) == tuple(sorted(EXPECTED_ADMITTED))
    with pytest.raises(KeyError, match="unknown Ground capability"):
        require_ground_capabilities(("full_combat",))
    model = GROUND_SCRIPTED_MODEL_REGISTRY.create(GROUND_INFANTRY_SCRIPTED_MODEL_ID)
    model.reset(context={"task": _task(), "requested_capabilities": ["static_hold"]})
    with pytest.raises(TypeError, match="requested_capabilities"):
        model.reset(context={"task": _task(), "requested_capabilities": "route_planning"})


def test_admitted_capability_requires_a_named_owner() -> None:
    with pytest.raises(ValueError, match="requires an owner"):
        GroundCapability("x", GROUND_CAPABILITY_ADMITTED_BOUNDED, " ", "boundary")
    with pytest.raises(ValueError, match="unknown Ground capability state"):
        GroundCapability("x", "playable", "owner", "boundary")
