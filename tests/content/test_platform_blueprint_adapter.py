from __future__ import annotations

from dataclasses import replace

import pytest

from python.content.capability_bundles import SpawnPlacement
from python.content.platform_blueprint import (
    LegacyUnitProjection,
    ModuleRecord,
    ModuleSelection,
    PlatformAssemblyError,
    PlatformBlueprint,
    resolve_platform_assembly,
)
from python.content.platform_blueprint_adapter import (
    to_expanded_typed_platform_request,
)


def _fixture():
    modules = {
        "engine": ModuleRecord(
            "fixture.engine",
            "engine",
            frozenset({"mobility"}),
            evidence_refs=("fixture:engine",),
            content_digest="engine-digest",
            native_ref="FixtureEngine",
        ),
        "sensor": ModuleRecord(
            "fixture.sensor",
            "sensor",
            frozenset({"sensing"}),
            evidence_refs=("fixture:sensor",),
            content_digest="sensor-digest",
            native_ref="FixtureSensor",
        ),
    }
    blueprint = PlatformBlueprint(
        "fixture.air",
        "1",
        "aircraft",
        slots=(("propulsion", "engine"), ("primary_sensor", "sensor")),
        required_capabilities=frozenset({"mobility", "sensing"}),
    )
    plan = resolve_platform_assembly(
        assembly_id="fixture.assembly.v1",
        blueprint=blueprint,
        selections=(
            ModuleSelection("propulsion", "engine"),
            ModuleSelection("primary_sensor", "sensor"),
        ),
        modules=modules,
    )
    return blueprint, modules, plan


def _projection(plan, **changes):
    definition = {
        "name": "FixturePlatform",
        "type": "aircraft",
        "propulsion": "FixtureEngine",
        "primary_sensor": "FixtureSensor",
        "max_speed_mps": 300.0,
    }
    definition.update(changes)
    return LegacyUnitProjection(
        plan.blueprint_ref,
        definition,
        slot_paths=(("propulsion", "propulsion"), ("primary_sensor", "primary_sensor")),
        override_paths=(("max_speed_mps", "max_speed_mps"),),
    )


def _expand(blueprint, modules, plan, *, projection=None, source_type_name="FixturePlatform"):
    return to_expanded_typed_platform_request(
        plan=plan,
        blueprint=blueprint,
        modules=modules,
        projection=projection or _projection(plan),
        source_type_name=source_type_name,
        request_id="fixture:request",
        placement=SpawnPlacement(entity_name="Fixture"),
    )


def test_native_typed_projection_is_deterministic_and_evidence_bound() -> None:
    blueprint, modules, plan = _fixture()
    expanded = _expand(blueprint, modules, plan)

    assert expanded.capability_bundle.bundle_id.startswith("platform.bundle.")
    assert expanded.resolved_spawn_plan.plan_id.startswith("platform.spawn.")
    assert expanded.capability_bundle.bundle_id != f"platform.bundle.{plan.identity_digest}"
    assert [cap.family for cap in expanded.capability_bundle.capabilities] == [
        "sensing",
        "mobility",
    ]
    assert all(
        f"platform.identity:{plan.identity_digest}" in cap.evidence_refs
        for cap in expanded.capability_bundle.capabilities
    )
    assert not expanded.type_name_projection_preserved
    assert not expanded.resolved_spawn_plan.type_name_projection_preserved
    assert expanded == _expand(blueprint, dict(reversed(list(modules.items()))), plan)
    changed = _expand(blueprint, modules, plan, projection=_projection(plan, max_speed_mps=350.0))
    assert changed.resolved_spawn_plan.plan_id != expanded.resolved_spawn_plan.plan_id


def test_native_typed_projection_rejects_slot_cardinality_before_publication() -> None:
    blueprint, modules, plan = _fixture()
    broken = replace(plan, modules=plan.modules[:1])

    with pytest.raises(PlatformAssemblyError, match="native_slot_cardinality_mismatch"):
        _expand(blueprint, modules, broken)


def test_native_typed_projection_rejects_changed_module_digest_before_publication() -> None:
    blueprint, modules, plan = _fixture()
    changed = dict(modules)
    changed["engine"] = replace(changed["engine"], content_digest="changed-digest")

    with pytest.raises(PlatformAssemblyError, match="native_module_digest_mismatch"):
        _expand(blueprint, changed, plan)


def test_native_typed_projection_rejects_unmaintained_capability_family() -> None:
    modules = {
        "engine": ModuleRecord(
            "fixture.engine",
            "engine",
            frozenset({"unmaintained"}),
            evidence_refs=("fixture:engine",),
            content_digest="engine-digest",
            native_ref="FixtureEngine",
        )
    }
    blueprint = PlatformBlueprint(
        "fixture.air",
        "1",
        "aircraft",
        slots=(("propulsion", "engine"),),
        required_capabilities=frozenset({"unmaintained"}),
    )
    plan = resolve_platform_assembly(
        assembly_id="fixture.assembly.v1",
        blueprint=blueprint,
        selections=(ModuleSelection("propulsion", "engine"),),
        modules=modules,
    )

    with pytest.raises(PlatformAssemblyError, match="native_capability_family_unsupported"):
        _expand(blueprint, modules, plan)


def test_native_typed_projection_rejects_parameter_overrides_until_definition_is_lowered() -> None:
    blueprint, modules, _ = _fixture()
    blueprint = replace(blueprint, override_types=(("max_speed_mps", "float"),))
    plan = resolve_platform_assembly(
        assembly_id="fixture.assembly.override",
        blueprint=blueprint,
        selections=(
            ModuleSelection("propulsion", "engine"),
            ModuleSelection("primary_sensor", "sensor"),
        ),
        modules=modules,
        parameter_overrides={"max_speed_mps": 321.0},
    )

    with pytest.raises(PlatformAssemblyError, match="native_definition_projection_mismatch"):
        _expand(blueprint, modules, plan)
    # Typed setup can reference the override only once that exact definition is
    # represented by the snapshot loaded through the existing native loader.
    expanded = _expand(blueprint, modules, plan, projection=_projection(plan, max_speed_mps=321.0))
    assert "FixturePlatform#" in expanded.resolved_spawn_plan.resolved_platform_definition_ref


def test_native_typed_projection_revalidates_plan_identity_and_source_binding() -> None:
    blueprint, modules, plan = _fixture()

    with pytest.raises(PlatformAssemblyError, match="native_plan_identity_mismatch"):
        _expand(blueprint, modules, replace(plan, identity_digest="0" * 64))

    projection = LegacyUnitProjection(
        plan.blueprint_ref,
        {"name": "OtherFixturePlatform", "type": "aircraft", "propulsion": "FixtureEngine", "primary_sensor": "FixtureSensor"},
        slot_paths=(("propulsion", "propulsion"), ("primary_sensor", "primary_sensor")),
    )
    with pytest.raises(PlatformAssemblyError, match="native_source_definition_name_mismatch"):
        to_expanded_typed_platform_request(
            plan=plan,
            blueprint=blueprint,
            modules=modules,
            projection=projection,
            source_type_name="FixturePlatform",
            request_id="fixture:request",
            placement=SpawnPlacement(entity_name="Fixture"),
        )


@pytest.mark.parametrize("changes,reason", [
    ({"schema_version": "unsupported"}, "schema_version_mismatch"),
    ({"platform_family": "ship"}, "platform_family_mismatch"),
    ({"parameter_overrides": (("max_speed_mps", 321.0),)}, "override_not_allowlisted"),
])
def test_native_typed_projection_revalidates_plan_contract(changes, reason) -> None:
    blueprint, modules, plan = _fixture()
    with pytest.raises(PlatformAssemblyError, match=reason):
        _expand(blueprint, modules, replace(plan, **changes))


def test_native_typed_projection_rejects_duplicate_slot_even_without_capabilities() -> None:
    blueprint, modules, plan = _fixture()
    # A module with no capability cannot evade the canonical slot check.
    modules["engine"] = replace(modules["engine"], capabilities=frozenset())
    blueprint = replace(blueprint, required_capabilities=frozenset({"sensing"}))
    plan = resolve_platform_assembly(
        assembly_id=plan.assembly_id,
        blueprint=blueprint,
        modules=modules,
        selections=(ModuleSelection("propulsion", "engine"), ModuleSelection("primary_sensor", "sensor")),
    )
    with pytest.raises(PlatformAssemblyError, match="duplicate_slot"):
        _expand(blueprint, modules, replace(plan, modules=plan.modules + (("propulsion", "fixture.engine@1"),)))


def test_native_typed_projection_rejects_module_selection_not_loaded_in_snapshot() -> None:
    blueprint, modules, _ = _fixture()
    modules["engine"] = replace(modules["engine"], native_ref="OtherFixtureEngine")
    plan = resolve_platform_assembly(
        assembly_id="changed.engine",
        blueprint=blueprint,
        modules=modules,
        selections=(ModuleSelection("propulsion", "engine"), ModuleSelection("primary_sensor", "sensor")),
    )
    with pytest.raises(PlatformAssemblyError, match="native_definition_projection_mismatch"):
        _expand(blueprint, modules, plan)
