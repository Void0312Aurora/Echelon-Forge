from __future__ import annotations

import hashlib
import json
from dataclasses import fields, replace
from pathlib import Path
from unittest.mock import patch

import pytest

from python.content.capability_bundles import SpawnPlacement
import python.content.platform_blueprint as blueprint_owner
from python.content.capability_bundles.schema import (
    PLATFORM_CAPABILITY_KEY_VOCABULARY,
    PlatformCapabilityKeyVocabulary,
    PlatformCapabilityKeyVocabularyEntry,
)
from python.content.platform_blueprint import (
    HardpointContract,
    LoadoutSelection,
    LegacyUnitProjection,
    ModuleRecord,
    ModuleSelection,
    PlatformAssemblyError,
    PlatformBlueprint,
    lower_to_legacy_unit_definition,
    resolve_platform_assembly,
)
from python.content.platform_blueprint_adapter import (
    to_expanded_typed_platform_request,
    validate_factory_resolved_capability_plan,
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

    with pytest.raises(PlatformAssemblyError, match="native_capability_key_unknown"):
        _expand(blueprint, modules, plan)


def test_native_typed_projection_binds_capability_key_vocabulary_identity() -> None:
    blueprint, modules, plan = _fixture()
    expanded = _expand(blueprint, modules, plan)
    vocabulary_ref = (
        f"platform.capability_vocabulary:{PLATFORM_CAPABILITY_KEY_VOCABULARY.vocabulary_id}@"
        f"{PLATFORM_CAPABILITY_KEY_VOCABULARY.version}:"
        f"{PLATFORM_CAPABILITY_KEY_VOCABULARY.identity_digest}"
    )
    assert vocabulary_ref in expanded.resolved_spawn_plan.evidence_refs

    changed_vocabulary = PlatformCapabilityKeyVocabulary(
        vocabulary_id=PLATFORM_CAPABILITY_KEY_VOCABULARY.vocabulary_id,
        version=PLATFORM_CAPABILITY_KEY_VOCABULARY.version,
        entries=tuple(
            PlatformCapabilityKeyVocabularyEntry(
                entry.key,
                entry.native_family,
                "reviewed.runtime.capability_family_vocabulary",
            )
            for entry in PLATFORM_CAPABILITY_KEY_VOCABULARY.entries
        ),
    )
    changed = _expand(
        blueprint,
        modules,
        plan,
    )
    changed_with_vocabulary = to_expanded_typed_platform_request(
        plan=plan,
        blueprint=blueprint,
        modules=modules,
        projection=_projection(plan),
        source_type_name="FixturePlatform",
        request_id="fixture:request",
        placement=SpawnPlacement(entity_name="Fixture"),
        capability_vocabulary=changed_vocabulary,
    )
    assert changed_with_vocabulary != changed
    assert changed_with_vocabulary.resolved_spawn_plan.plan_id != expanded.resolved_spawn_plan.plan_id


def test_native_typed_projection_rejects_capability_key_mapping_drift_against_factory() -> None:
    blueprint, modules, plan = _fixture()
    changed_entries = tuple(
        PlatformCapabilityKeyVocabularyEntry(
            entry.key,
            "sensing" if entry.key == "mobility" else entry.native_family,
            entry.owner_ref,
        )
        for entry in PLATFORM_CAPABILITY_KEY_VOCABULARY.entries
    )
    changed_vocabulary = PlatformCapabilityKeyVocabulary(
        vocabulary_id="fixture.capability.keys",
        version="2",
        entries=changed_entries,
    )
    expanded = to_expanded_typed_platform_request(
        plan=plan,
        blueprint=blueprint,
        modules=modules,
        projection=_projection(plan),
        source_type_name="FixturePlatform",
        request_id="fixture:request",
        placement=SpawnPlacement(entity_name="Fixture"),
        capability_vocabulary=changed_vocabulary,
    )
    factory_plan = {
        "source_type_name": expanded.source_type_name,
        "admitted": True,
        "resolved_capabilities": [
            {
                "family": "mobility",
                "capability_type": cap.capability_type,
                "implementation_ref": cap.implementation_ref,
                "required": cap.required,
                "supported": cap.supported,
            }
            if cap.capability_id.endswith(":propulsion:mobility")
            else {
                "family": cap.family,
                "capability_type": cap.capability_type,
                "implementation_ref": cap.implementation_ref,
                "required": cap.required,
                "supported": cap.supported,
            }
            for cap in expanded.resolved_spawn_plan.resolved_capabilities
        ],
    }
    with pytest.raises(PlatformAssemblyError, match="capability_semantics_mismatch"):
        validate_factory_resolved_capability_plan(expanded.resolved_spawn_plan, factory_plan)


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


def test_typed_plan_can_be_compared_with_factory_resolved_capability_identity() -> None:
    blueprint, modules, plan = _fixture()
    expanded = _expand(blueprint, modules, plan)
    factory_plan = {
        "source_type_name": expanded.source_type_name,
        "admitted": True,
        "resolved_platform_definition_ref": expanded.resolved_spawn_plan.resolved_platform_definition_ref,
        "resolved_capabilities": [
            {
                "capability_id": cap.capability_id,
                "family": cap.family,
                "capability_type": cap.capability_type,
                "implementation_ref": cap.implementation_ref,
                "required": cap.required,
                "supported": cap.supported,
            }
            for cap in expanded.resolved_spawn_plan.resolved_capabilities
        ],
    }
    validate_factory_resolved_capability_plan(expanded.resolved_spawn_plan, factory_plan)
    factory_plan["resolved_capabilities"][0]["family"] = "survivability"
    with pytest.raises(PlatformAssemblyError, match="capability_semantics_mismatch"):
        validate_factory_resolved_capability_plan(expanded.resolved_spawn_plan, factory_plan)

    factory_plan["resolved_capabilities"][0]["family"] = expanded.resolved_spawn_plan.resolved_capabilities[0].family
    factory_plan["resolved_capabilities"][0]["implementation_ref"] = "other.native.owner"
    with pytest.raises(PlatformAssemblyError, match="capability_semantics_mismatch"):
        validate_factory_resolved_capability_plan(expanded.resolved_spawn_plan, factory_plan)

    factory_plan["resolved_capabilities"][0]["implementation_ref"] = expanded.resolved_spawn_plan.resolved_capabilities[0].implementation_ref
    factory_plan["admitted"] = False
    with pytest.raises(PlatformAssemblyError, match="factory_plan_not_admitted"):
        validate_factory_resolved_capability_plan(expanded.resolved_spawn_plan, factory_plan)


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


def test_native_typed_projection_rejects_multi_store_but_keeps_legacy_import() -> None:
    blueprint, modules, _ = _fixture()
    weapon = ModuleRecord(
        "fixture.weapon",
        "weapon",
        frozenset({"launching"}),
        mount_classes=frozenset({"station"}),
        mass_kg=80.0,
        power_draw_kw=0.0,
        evidence_refs=("fixture:weapon",),
        content_digest="weapon-digest",
        native_ref="FixtureWeapon",
    )
    modules = {**modules, "weapon": weapon}
    blueprint = replace(
        blueprint,
        hardpoints=(
            HardpointContract(
                "station_1", "station", capacity_kg=200.0, allowed_kinds=frozenset({"weapon"})
            ),
        ),
    )
    plan = resolve_platform_assembly(
        assembly_id="fixture.loadout.v1",
        blueprint=blueprint,
        selections=(ModuleSelection("propulsion", "engine"), ModuleSelection("primary_sensor", "sensor")),
        modules=modules,
        loadout=(LoadoutSelection("station_1", "weapon", 2),),
    )
    projection = _projection(plan, default_loadout={"1": ["FixtureWeapon", "FixtureWeapon"]})
    projection = replace(
        projection,
        loadout_paths=(("station_1", "default_loadout.1"),),
    )
    with pytest.raises(PlatformAssemblyError, match="native_loadout_quantity_unsupported"):
        _expand(blueprint, modules, plan, projection=projection)
    lowered_multi = lower_to_legacy_unit_definition(plan, projection, modules=modules)
    assert lowered_multi["default_loadout"]["1"] == ["FixtureWeapon", "FixtureWeapon"]

    single_plan = resolve_platform_assembly(
        assembly_id="fixture.loadout.single-store.v1",
        blueprint=blueprint,
        selections=(ModuleSelection("propulsion", "engine"), ModuleSelection("primary_sensor", "sensor")),
        modules=modules,
        loadout=(LoadoutSelection("station_1", "weapon", 1),),
    )
    single_projection = _projection(single_plan, default_loadout={"1": "FixtureWeapon"})
    single_projection = replace(
        single_projection,
        loadout_paths=(("station_1", "default_loadout.1"),),
    )
    expanded = _expand(blueprint, modules, single_plan, projection=single_projection)
    lowered_single = lower_to_legacy_unit_definition(
        single_plan, single_projection, modules=modules
    )
    assert lowered_single["default_loadout"]["1"] == "FixtureWeapon"
    launching = [
        capability
        for capability in expanded.capability_bundle.capabilities
        if capability.family == "launching"
    ]
    assert len(launching) == 1
    assert "platform.hardpoint:station_1" in launching[0].evidence_refs
    assert "platform.loadout_quantity:station_1:1" in launching[0].evidence_refs


@pytest.mark.parametrize("owner_change", [
    "plan", "physical", "evidence", "capabilities", "blueprint", "hardpoint",
])
def test_canonical_plan_rejects_stale_owner_records(owner_change) -> None:
    blueprint, modules, plan = _fixture()
    if owner_change == "plan":
        object.__setattr__(plan, "assembly_id", "mutated-in-place")
    elif owner_change == "blueprint":
        blueprint = replace(blueprint, mass_limit_kg=1.0)
    elif owner_change == "hardpoint":
        blueprint = replace(blueprint, hardpoints=(HardpointContract("new", "rail"),))
    else:
        changes = {
            "physical": {"mass_kg": 1.0},
            "evidence": {"evidence_refs": ("changed:owner",)},
            # The aggregate capabilities are unchanged: sensing already exists.
            "capabilities": {"capabilities": frozenset({"mobility", "sensing"})},
        }
        modules["engine"] = replace(modules["engine"], **changes[owner_change])
    with pytest.raises(PlatformAssemblyError, match="native_plan_identity_mismatch"):
        _expand(blueprint, modules, plan)


def test_external_plan_keeps_full_validation_and_versioned_public_identity() -> None:
    blueprint, modules, plan = _fixture()
    document = json.loads(json.dumps(plan.as_dict()))
    assert document["schema_version"] == blueprint_owner.SCHEMA_VERSION
    assert not any(key.startswith("_") for key in document)
    # Reconstruct only public constructor fields, as an external adapter would.
    imported = type(plan)(**{item.name: getattr(plan, item.name) for item in fields(plan) if item.init})
    with patch.object(blueprint_owner, "resolve_platform_assembly", wraps=resolve_platform_assembly) as resolve:
        assert _expand(blueprint, modules, imported) == _expand(blueprint, modules, plan)
        assert resolve.call_count == 1
    with pytest.raises(PlatformAssemblyError, match="required_capability_missing"):
        _expand(replace(blueprint, required_capabilities=frozenset({"launching"})), modules, imported)


@pytest.mark.parametrize("field,value", [
    ("identity_digest", "0" * 64),
    ("capabilities", ("mobility",)),
    ("module_physical_parameters", ()),
    ("module_digests", ()),
    ("native_module_refs", ()),
    ("loadout_physical_parameters", (("ghost", 1.0, 0.0, (), 1),)),
])
def test_canonical_plan_detects_in_place_mutation(field, value) -> None:
    blueprint, modules, plan = _fixture()
    object.__setattr__(plan, field, value)
    with pytest.raises(PlatformAssemblyError):
        _expand(blueprint, modules, plan)


_DATABASE = Path(__file__).resolve().parents[2] / "examples/config/database"
_PARITY_UNITS = [
    "aircraft/units/f16c_block50.json",
    "ground/units/ground_infantry_soldier_mvp.json",
]


def _database_assembly(relative_path):
    """Explicit qualification mapping reviewed against DefaultUnitFactory.

    Owner references live in ignored metadata: native fields, physical values
    and station loadouts remain the exact authored content. They are not a
    second capability resolver; the integration test compares the actual owner.
    """
    original = json.loads((_DATABASE / relative_path).read_text(encoding="utf-8"))
    if original["type"] == "Aircraft":
        capabilities = {
            "sensor_ref": "sensing",
            "airframe": "mobility", "landing_gear": "mobility",
            "default_loadout": "launching", "data_link": "communication",
            "health_and_damage_model": "survivability",
            "aircraft_vulnerability_synthetic_profile": "survivability",
        }
    else:
        capabilities = {
            "ground_mobility_flat_deferred": "mobility", "land_tactics": "doctrine",
            "command_link": "command", "health_and_damage_model": "survivability",
        }
    token = original["name"].lower().replace("-", "_")
    native_owner = f"platform.definition.{token}"
    content_digest = hashlib.sha256(json.dumps(original, sort_keys=True).encode()).hexdigest()
    modules = {
        key: ModuleRecord(
            f"qualification.{token}.{key}", key, frozenset({family}),
            evidence_refs=(f"legacy-content:{relative_path}:{key}",),
            content_digest=content_digest, native_ref=native_owner,
        )
        for key, family in capabilities.items()
    }
    definition = {**original, "_qualification_native_owners": dict.fromkeys(capabilities, native_owner)}
    hardpoints, loadout, loadout_paths = [], [], []
    for station, weapon in original.get("default_loadout", {}).items():
        assert isinstance(weapon, str), "this bounded fixture requires single-store stations"
        # Physical validation remains owned by the native database/factory here;
        # the blueprint carries no invented store mass or power measurement.
        hardpoints.append(HardpointContract(station, "qualified_station"))
        key = f"station_{station}"
        modules[key] = ModuleRecord(
            f"qualification.{token}.{key}", "store", evidence_refs=(f"legacy-content:{weapon}",),
            content_digest=content_digest, native_ref=weapon,
            mount_classes=frozenset({"qualified_station"}),
        )
        loadout.append(LoadoutSelection(station, key))
        loadout_paths.append((station, f"default_loadout.{station}"))
    blueprint = PlatformBlueprint(
        f"qualification.{token}", "1", original["type"],
        slots=tuple((key, key) for key in capabilities),
        required_capabilities=frozenset(capabilities.values()), hardpoints=tuple(hardpoints),
    )
    plan = resolve_platform_assembly(
        assembly_id=f"qualification.{token}.assembly.v1", blueprint=blueprint, modules=modules,
        selections=tuple(ModuleSelection(key, key) for key in capabilities), loadout=tuple(loadout),
    )
    projection = LegacyUnitProjection(
        plan.blueprint_ref, definition,
        slot_paths=tuple((key, f"_qualification_native_owners.{key}") for key in capabilities),
        loadout_paths=tuple(loadout_paths),
    )
    return original, blueprint, modules, plan, projection


def _database_expand(blueprint, modules, plan, projection, *, factory_plan=None):
    return to_expanded_typed_platform_request(
        plan=plan, blueprint=blueprint, modules=modules, projection=projection,
        source_type_name=projection.definition["name"], request_id="qualification:parity",
        placement=SpawnPlacement(
            entity_name="ParityUnit", x=100000.0, y=100000.0,
            z=1200.0 if blueprint.platform_family == "Aircraft" else 0.0,
            vy=180.0 if blueprint.platform_family == "Aircraft" else 0.0,
        ), factory_plan=factory_plan,
    )


@pytest.mark.parametrize("relative_path", _PARITY_UNITS)
def test_database_canonical_bridge_retires_repeated_resolution_and_projection(relative_path) -> None:
    original, blueprint, modules, plan, projection = _database_assembly(relative_path)
    lowered = lower_to_legacy_unit_definition(plan, projection, modules=modules)
    assert {key: value for key, value in lowered.items() if key != "_qualification_native_owners"} == original
    # Full validation of an unsealed copy is the compatibility reference.
    reference = _database_expand(blueprint, modules, replace(plan), projection)
    with (
        patch.object(blueprint_owner, "resolve_platform_assembly", side_effect=AssertionError("second resolution")),
        patch.object(blueprint_owner, "lower_to_legacy_unit_definition", side_effect=AssertionError("second projection")),
        patch.object(blueprint_owner, "thaw_json_value", side_effect=AssertionError("snapshot roundtrip")),
    ):
        assert _database_expand(blueprint, modules, plan, projection) == reference
        assert _database_expand(blueprint, modules, plan, projection) == reference
    definition_digest = hashlib.sha256(json.dumps(
        lowered, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
    ).encode()).hexdigest()
    assert reference.resolved_spawn_plan.resolved_platform_definition_ref.endswith(f"#{definition_digest}")


@pytest.mark.parametrize("relative_path", _PARITY_UNITS)
def test_database_blueprint_native_factory_state_and_loadout_parity(relative_path, tmp_path, monkeypatch) -> None:
    ef_py = pytest.importorskip("ef_py")
    from python.content.capability_bundles.bindings_adapter import to_typed_platform_spawn_request

    original, blueprint, modules, plan, projection = _database_assembly(relative_path)
    lowered = lower_to_legacy_unit_definition(plan, projection, modules=modules)
    path = tmp_path / "resolved-unit.json"
    path.write_text(json.dumps({"units": [lowered]}), encoding="utf-8")
    runtime = ef_py.WorldBatchRuntime(1)
    assert runtime.load_database(str(_DATABASE))
    factory_plan = runtime.resolve_factory_platform_spawn_plan(0, original["name"])
    assert factory_plan.admitted
    facades = [ef_py.RuntimeFacade(1), ef_py.RuntimeFacade(1)]
    assert all(facade.load_database(str(_DATABASE)) for facade in facades)
    assert facades[1].load_unit_definitions(str(path))
    def redundant(*args, **kwargs):
        pytest.fail("canonical bridge repeated resolution or legacy projection")
    monkeypatch.setattr(blueprint_owner, "resolve_platform_assembly", redundant)
    monkeypatch.setattr(blueprint_owner, "lower_to_legacy_unit_definition", redundant)
    expanded = _database_expand(blueprint, modules, plan, projection, factory_plan=factory_plan)
    refs = []
    for index, facade in enumerate(facades):
        setup = ef_py.BatchWorldSetupRequest()
        setup.seeds, setup.time_steps = [123], [0.05]
        if index == 0:
            spawn = ef_py.WorldSpawnRequest()
            spawn.type_name, spawn.side = original["name"], ef_py.Side.Blue
            for key in ("entity_name", "x", "y", "z", "vy"):
                setattr(spawn, key, getattr(expanded.placement, key))
            setup.spawn_requests = [spawn]
            result = facade.apply_world_setup(setup)
            assert len(result.entity_ids) == 1
            entity_id = result.entity_ids[0]
        else:
            setup.typed_platform_spawn_requests = [to_typed_platform_spawn_request(ef_py, expanded)]
            result = facade.apply_world_setup(setup).typed_platform_spawn_results[0]
            assert result.admitted and result.materialized and not result.fail_closed
            assert result.setup_surface == "maintained_typed_setup"
            entity_id = result.entity_id
        assert entity_id > 0
        ref = ef_py.WorldEntityRef()
        ref.entity_id = entity_id
        refs.append(ref)
    def snapshot(observation):
        return {name: repr(getattr(observation, name)) for name in dir(observation)
                if not name.startswith("_") and not callable(getattr(observation, name))}
    for step in range(5):
        observations = [facade.get_agent_observations_batch([ref])[0] for facade, ref in zip(facades, refs)]
        instruments = [facade.get_instrument_states_batch([ref])[0] for facade, ref in zip(facades, refs)]
        assert snapshot(observations[0]) == snapshot(observations[1])
        assert snapshot(instruments[0]) == snapshot(instruments[1])
        if original["type"] == "Aircraft":
            assert lowered["default_loadout"] == original["default_loadout"]
            assert len(plan.loadout) == len(original["default_loadout"])
            assert observations[1].missiles_remaining == observations[0].missiles_remaining
        if step < 4:
            for facade in facades:
                facade.step_batch()
