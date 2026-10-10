from __future__ import annotations

import pytest

from python.content.platform_blueprint import (
    ModuleRecord,
    ModuleSelection,
    PlatformAssemblyError,
    PlatformBlueprint,
    resolve_platform_assembly,
)


@pytest.fixture
def blueprint() -> PlatformBlueprint:
    return PlatformBlueprint(
        "builtin.air.f16c", "1", "aircraft",
        slots=(("propulsion", "engine"), ("primary_sensor", "sensor"), ("station_1", "weapon")),
        required_capabilities=frozenset({"mobility", "sensing", "launching"}),
        override_types=(("fuel_fraction", "float"),),
    )


@pytest.fixture
def modules() -> dict[str, ModuleRecord]:
    return {
        "builtin.engine.f110": ModuleRecord("builtin.engine.f110", "engine", frozenset({"mobility"}), evidence_refs=("e:engine",)),
        "builtin.radar.apg": ModuleRecord("builtin.radar.apg", "sensor", frozenset({"sensing"}), evidence_refs=("e:radar",)),
        "builtin.aim120": ModuleRecord("builtin.aim120", "weapon", frozenset({"launching"}), evidence_refs=("e:missile",)),
    }


def _selections() -> tuple[ModuleSelection, ...]:
    return (
        ModuleSelection("propulsion", "builtin.engine.f110"),
        ModuleSelection("primary_sensor", "builtin.radar.apg"),
        ModuleSelection("station_1", "builtin.aim120"),
    )


def test_air_assembly_resolves_to_deterministic_native_plan(blueprint, modules) -> None:
    plan = resolve_platform_assembly(
        assembly_id="community.f16c.training.v1",
        blueprint=blueprint,
        selections=_selections(),
        modules=modules,
        parameter_overrides={"fuel_fraction": 0.8},
    )
    assert plan.blueprint_ref == "builtin.air.f16c@1"
    assert plan.modules[0] == ("primary_sensor", "builtin.radar.apg@1")
    assert plan.capabilities == ("launching", "mobility", "sensing")
    assert len(plan.identity_digest) == 64


def test_resolution_is_independent_of_selection_and_override_order(blueprint, modules) -> None:
    left = resolve_platform_assembly(
        assembly_id="a.v1", blueprint=blueprint, selections=_selections(), modules=modules,
        parameter_overrides={"fuel_fraction": 0.8},
    )
    right = resolve_platform_assembly(
        assembly_id="a.v1", blueprint=blueprint, selections=tuple(reversed(_selections())), modules=modules,
        parameter_overrides={"fuel_fraction": 0.8},
    )
    assert left.identity_digest == right.identity_digest


@pytest.mark.parametrize(
    "selection, expected",
    [
        (ModuleSelection("primary_sensor", "missing"), "module_unknown"),
        (ModuleSelection("primary_sensor", "builtin.engine.f110"), "module_kind_mismatch"),
        (ModuleSelection("unknown", "builtin.radar.apg"), "unknown_slot"),
    ],
)
def test_reference_and_slot_errors_fail_closed(blueprint, modules, selection, expected) -> None:
    selections = list(_selections())
    selections[1] = selection
    with pytest.raises(PlatformAssemblyError, match=expected):
        resolve_platform_assembly(
            assembly_id="bad.v1", blueprint=blueprint, selections=selections, modules=modules,
        )


def test_missing_capability_and_illegal_override_fail_before_publication(blueprint, modules) -> None:
    limited = dict(modules)
    limited["builtin.radar.apg"] = ModuleRecord("builtin.radar.apg", "sensor", frozenset(), evidence_refs=("e:radar",))
    with pytest.raises(PlatformAssemblyError, match="required_capability_missing"):
        resolve_platform_assembly(
            assembly_id="bad.v1", blueprint=blueprint, selections=_selections(), modules=limited,
        )
    with pytest.raises(PlatformAssemblyError, match="override_not_allowlisted"):
        resolve_platform_assembly(
            assembly_id="bad.v1", blueprint=blueprint, selections=_selections(), modules=modules,
            parameter_overrides={"hidden_field": 1},
        )


def test_duplicate_slot_and_bad_override_type_fail_closed(blueprint, modules) -> None:
    with pytest.raises(PlatformAssemblyError, match="duplicate_slot"):
        resolve_platform_assembly(
            assembly_id="bad.v1", blueprint=blueprint,
            selections=_selections() + (ModuleSelection("station_1", "builtin.aim120"),), modules=modules,
        )
    with pytest.raises(PlatformAssemblyError, match="override_type_mismatch"):
        resolve_platform_assembly(
            assembly_id="bad.v1", blueprint=blueprint, selections=_selections(), modules=modules,
            parameter_overrides={"fuel_fraction": "0.8"},
        )
