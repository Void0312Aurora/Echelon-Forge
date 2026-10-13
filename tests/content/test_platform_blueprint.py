from __future__ import annotations

import math
from dataclasses import replace

import pytest

from python.content.platform_blueprint import (
    HardpointContract,
    LegacyUnitProjection,
    LoadoutSelection,
    ModuleRecord,
    ModuleSelection,
    PlatformAssemblyError,
    PlatformBlueprint,
    resolve_platform_assembly,
    lower_to_legacy_unit_definition,
)


@pytest.fixture
def blueprint() -> PlatformBlueprint:
    return PlatformBlueprint(
        "builtin.air.f16c",
        "1",
        "aircraft",
        slots=(("propulsion", "engine"), ("primary_sensor", "sensor"), ("station_1", "weapon")),
        required_capabilities=frozenset({"mobility", "sensing", "launching"}),
        override_types=(("fuel_fraction", "float"),),
        mass_limit_kg=1200.0,
        power_budget_kw=20.0,
        slot_mount_requirements=(("primary_sensor", "nose"),),
    )


@pytest.fixture
def modules() -> dict[str, ModuleRecord]:
    return {
        "builtin.engine.f110": ModuleRecord(
            "builtin.engine.f110", "engine", frozenset({"mobility"}), evidence_refs=("e:engine",),
            mass_kg=700.0, power_draw_kw=0.0, mount_classes=frozenset({"engine_bay"})
        ),
        "builtin.radar.apg": ModuleRecord(
            "builtin.radar.apg", "sensor", frozenset({"sensing"}), evidence_refs=("e:radar",),
            mass_kg=200.0, power_draw_kw=8.0, mount_classes=frozenset({"nose"})
        ),
        "builtin.aim120": ModuleRecord(
            "builtin.aim120", "weapon", frozenset({"launching"}), evidence_refs=("e:missile",),
            mass_kg=100.0, power_draw_kw=0.0, mount_classes=frozenset({"station"})
        ),
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
        assembly_id="a.v1",
        blueprint=blueprint,
        selections=_selections(),
        modules=modules,
        parameter_overrides={"fuel_fraction": 0.8},
    )
    right = resolve_platform_assembly(
        assembly_id="a.v1",
        blueprint=blueprint,
        selections=tuple(reversed(_selections())),
        modules=modules,
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
            assembly_id="bad.v1",
            blueprint=blueprint,
            selections=selections,
            modules=modules,
        )


def test_missing_capability_and_illegal_override_fail_before_publication(
    blueprint, modules
) -> None:
    limited = dict(modules)
    limited["builtin.radar.apg"] = ModuleRecord(
        "builtin.radar.apg", "sensor", frozenset(), evidence_refs=("e:radar",)
    )
    with pytest.raises(PlatformAssemblyError, match="required_capability_missing"):
        resolve_platform_assembly(
            assembly_id="bad.v1",
            blueprint=blueprint,
            selections=_selections(),
            modules=limited,
        )
    with pytest.raises(PlatformAssemblyError, match="override_not_allowlisted"):
        resolve_platform_assembly(
            assembly_id="bad.v1",
            blueprint=blueprint,
            selections=_selections(),
            modules=modules,
            parameter_overrides={"hidden_field": 1},
        )


def test_physical_compatibility_constraints_fail_closed_before_publication(blueprint, modules) -> None:
    too_heavy = dict(modules)
    too_heavy["builtin.aim120"] = replace(too_heavy["builtin.aim120"], mass_kg=400.0)
    with pytest.raises(PlatformAssemblyError, match="mass_limit_exceeded"):
        resolve_platform_assembly(
            assembly_id="heavy.v1", blueprint=blueprint, selections=_selections(), modules=too_heavy
        )

    too_powerful = dict(modules)
    too_powerful["builtin.radar.apg"] = replace(too_powerful["builtin.radar.apg"], power_draw_kw=30.0)
    with pytest.raises(PlatformAssemblyError, match="power_budget_exceeded"):
        resolve_platform_assembly(
            assembly_id="power.v1", blueprint=blueprint, selections=_selections(), modules=too_powerful
        )

    wrong_mount = dict(modules)
    wrong_mount["builtin.radar.apg"] = replace(wrong_mount["builtin.radar.apg"], mount_classes=frozenset({"wing"}))
    with pytest.raises(PlatformAssemblyError, match="mount_class_mismatch"):
        resolve_platform_assembly(
            assembly_id="mount.v1", blueprint=blueprint, selections=_selections(), modules=wrong_mount
        )


@pytest.mark.parametrize("field", ["mass_kg", "power_draw_kw"])
def test_constrained_blueprint_requires_physical_metadata(blueprint, modules, field) -> None:
    incomplete = dict(modules)
    incomplete["builtin.aim120"] = replace(incomplete["builtin.aim120"], **{field: None})
    with pytest.raises(PlatformAssemblyError, match=f"physical_metadata_missing:modules.station_1:physical.{field}"):
        resolve_platform_assembly(
            assembly_id="incomplete.v1",
            blueprint=blueprint,
            selections=_selections(),
            modules=incomplete,
        )
    unconstrained = replace(blueprint, mass_limit_kg=None, power_budget_kw=None)
    assert resolve_platform_assembly(
        assembly_id="legacy.v1", blueprint=unconstrained, selections=_selections(), modules=incomplete
    )


@pytest.mark.parametrize("value", [True, "1", -1.0, math.nan, math.inf, 10 ** 400])
def test_physical_metadata_and_budget_reject_invalid_values(blueprint, modules, value) -> None:
    with pytest.raises(ValueError, match="finite and non-negative"):
        replace(modules["builtin.aim120"], mass_kg=value)
    with pytest.raises(ValueError, match="finite and non-negative"):
        replace(blueprint, power_budget_kw=value)


def test_physical_sum_overflow_rejects_before_publication(blueprint, modules) -> None:
    large = {ref: replace(module, mass_kg=1.0e308) for ref, module in modules.items()}
    with pytest.raises(PlatformAssemblyError, match="mass_limit_exceeded"):
        resolve_platform_assembly(
            assembly_id="overflow.v1", blueprint=blueprint, selections=_selections(), modules=large
        )


def test_duplicate_slot_and_bad_override_type_fail_closed(blueprint, modules) -> None:
    with pytest.raises(PlatformAssemblyError, match="duplicate_slot"):
        resolve_platform_assembly(
            assembly_id="bad.v1",
            blueprint=blueprint,
            selections=_selections() + (ModuleSelection("station_1", "builtin.aim120"),),
            modules=modules,
        )
    with pytest.raises(PlatformAssemblyError, match="override_type_mismatch"):
        resolve_platform_assembly(
            assembly_id="bad.v1",
            blueprint=blueprint,
            selections=_selections(),
            modules=modules,
            parameter_overrides={"fuel_fraction": "0.8"},
        )


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_non_finite_numeric_override_fails_closed(blueprint, modules, value) -> None:
    with pytest.raises(PlatformAssemblyError, match="override_type_mismatch"):
        resolve_platform_assembly(
            assembly_id="bad.v1",
            blueprint=blueprint,
            selections=_selections(),
            modules=modules,
            parameter_overrides={"fuel_fraction": value},
        )


def test_physical_override_bounds_and_module_content_are_bound_to_plan_identity(
    blueprint, modules
) -> None:
    bounded = replace(blueprint, override_ranges=(("fuel_fraction", 0.0, 1.0),))
    with pytest.raises(PlatformAssemblyError, match="override_out_of_bounds"):
        resolve_platform_assembly(
            assembly_id="a",
            blueprint=bounded,
            selections=_selections(),
            modules=modules,
            parameter_overrides={"fuel_fraction": 1.1},
        )
    left = resolve_platform_assembly(
        assembly_id="a", blueprint=bounded, selections=_selections(), modules=modules
    )
    changed = dict(modules)
    changed["builtin.engine.f110"] = replace(
        changed["builtin.engine.f110"], content_digest="0" * 64
    )
    right = resolve_platform_assembly(
        assembly_id="a", blueprint=bounded, selections=_selections(), modules=changed
    )
    assert left.identity_digest != right.identity_digest
    changed_physical = dict(modules)
    changed_physical["builtin.engine.f110"] = replace(
        changed_physical["builtin.engine.f110"], mass_kg=701.0
    )
    physical = resolve_platform_assembly(
        assembly_id="a", blueprint=bounded, selections=_selections(), modules=changed_physical
    )
    assert left.identity_digest != physical.identity_digest


def test_hardpoint_loadout_is_validated_and_bound_to_plan_identity(blueprint, modules) -> None:
    loadout_blueprint = replace(
        blueprint,
        slots=(("propulsion", "engine"), ("primary_sensor", "sensor")),
        hardpoints=(
            HardpointContract(
                "station_1", "station", capacity_kg=250.0, allowed_kinds=frozenset({"weapon"})
            ),
        ),
    )
    selections = (
        ModuleSelection("propulsion", "builtin.engine.f110"),
        ModuleSelection("primary_sensor", "builtin.radar.apg"),
    )
    plan = resolve_platform_assembly(
        assembly_id="loadout.v1",
        blueprint=loadout_blueprint,
        selections=selections,
        modules=modules,
        loadout=(LoadoutSelection("station_1", "builtin.aim120"),),
    )
    assert plan.loadout == (("station_1", "builtin.aim120@1", 1),)
    changed = resolve_platform_assembly(
        assembly_id="loadout.v1",
        blueprint=loadout_blueprint,
        selections=selections,
        modules=modules,
        loadout=(LoadoutSelection("station_1", "builtin.aim120", 2),),
    )
    assert changed.identity_digest != plan.identity_digest

    with pytest.raises(PlatformAssemblyError, match="loadout_mount_class_mismatch"):
        resolve_platform_assembly(
            assembly_id="loadout.bad.mount",
            blueprint=loadout_blueprint,
            selections=selections,
            modules={
                **modules,
                "builtin.aim120": replace(
                    modules["builtin.aim120"], mount_classes=frozenset({"wing"})
                ),
            },
            loadout=(LoadoutSelection("station_1", "builtin.aim120"),),
        )
    with pytest.raises(PlatformAssemblyError, match="loadout_capacity_exceeded"):
        capacity_limited = replace(
            loadout_blueprint,
            hardpoints=(
                HardpointContract(
                    "station_1",
                    "station",
                    capacity_kg=120.0,
                    allowed_kinds=frozenset({"weapon"}),
                ),
            ),
        )
        resolve_platform_assembly(
            assembly_id="loadout.bad.capacity",
            blueprint=capacity_limited,
            selections=selections,
            modules=modules,
            loadout=(LoadoutSelection("station_1", "builtin.aim120", 2),),
        )


def test_legacy_projection_requires_explicit_loadout_path(blueprint, modules) -> None:
    loadout_blueprint = replace(
        blueprint,
        slots=(("propulsion", "engine"), ("primary_sensor", "sensor")),
        hardpoints=(HardpointContract("station_1", "station", 120.0, frozenset({"weapon"})),),
    )
    loadout_modules = {
        "builtin.engine.f110": replace(
            modules["builtin.engine.f110"],
            content_digest="engine-digest",
            native_ref="Engine",
        ),
        "builtin.radar.apg": replace(
            modules["builtin.radar.apg"],
            content_digest="radar-digest",
            native_ref="Radar",
        ),
        "builtin.aim120": replace(
            modules["builtin.aim120"], content_digest="weapon-digest", native_ref="Aim120"
        ),
    }
    plan = resolve_platform_assembly(
        assembly_id="loadout.projection",
        blueprint=loadout_blueprint,
        selections=(
            ModuleSelection("propulsion", "builtin.engine.f110"),
            ModuleSelection("primary_sensor", "builtin.radar.apg"),
        ),
        modules=loadout_modules,
        loadout=(LoadoutSelection("station_1", "builtin.aim120"),),
    )
    base = {
        "name": "F16Loadout",
        "type": "aircraft",
        "propulsion": "Engine",
        "sensor": "Radar",
        "default_loadout": {"1": "Unresolved"},
    }
    projection = LegacyUnitProjection(
        plan.blueprint_ref,
        base,
        slot_paths=(("propulsion", "propulsion"), ("primary_sensor", "sensor")),
    )
    with pytest.raises(PlatformAssemblyError, match="native_loadout_projection_missing"):
        lower_to_legacy_unit_definition(plan, projection, modules=loadout_modules)
    projected = LegacyUnitProjection(
        plan.blueprint_ref,
        base,
        slot_paths=(("propulsion", "propulsion"), ("primary_sensor", "sensor")),
        loadout_paths=(("station_1", "default_loadout.1"),),
    )
    lowered = lower_to_legacy_unit_definition(plan, projected, modules=loadout_modules)
    assert lowered["default_loadout"]["1"] == "Aim120"
