from __future__ import annotations

from dataclasses import replace

import pytest

from python.content.capability_bundles import SpawnPlacement
from python.content.platform_blueprint import (
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


def _expand(blueprint, modules, plan):
    return to_expanded_typed_platform_request(
        plan=plan,
        blueprint=blueprint,
        modules=modules,
        source_type_name="FixturePlatform",
        request_id="fixture:request",
        placement=SpawnPlacement(entity_name="Fixture"),
    )


def test_native_typed_projection_is_deterministic_and_evidence_bound() -> None:
    blueprint, modules, plan = _fixture()
    expanded = _expand(blueprint, modules, plan)

    assert expanded.capability_bundle.bundle_id == f"platform.bundle.{plan.identity_digest}"
    assert expanded.resolved_spawn_plan.plan_id == f"platform.spawn.{plan.identity_digest}"
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
