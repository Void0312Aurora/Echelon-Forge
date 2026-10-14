from __future__ import annotations

from dataclasses import replace
from copy import deepcopy
import math

import pytest

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path

ensure_repo_imports()

from python.scenario.force_package import (
    AssemblyReference,
    CompiledRelationship,
    ForcePackage,
    ForcePackageError,
    PackageMember,
    PackageRelationship,
    compile_force_package,
)
from python.scenario.force_package_csg_adapter import (
    _digest,
    load_qualified_csg_scenario,
    qualify_force_package_against_csg,
)
from python.scenario.compiler import ScenarioCompiler
from python.scenario.runtime.csg_replay import _csg_replay_unit_frame, capture_csg_replay
from python.simulation import create_scenario_runtime_adapter


OOB_REF = "docs/domains/naval/reviews/csg_order_of_battle_20260928/csg_order_of_battle_ford_20260928.md"
SHIP_TYPE = "CSG_US_CVN-78_Gerald_R_Ford"


def _scenario() -> dict:
    return {
        "environment": {
            "geodetic_anchor": {"latitude_deg": 21.0, "longitude_deg": 125.0},
        },
        "groups": [
            {
                "group_id": "BLUE_CSG12",
                "side": "Blue",
                "oob_ref": OOB_REF,
                "guide": {
                    "geo": {"latitude_deg": 20.993905, "longitude_deg": 123.555086},
                    "axis_deg": 89.48,
                },
                "members": [
                    {
                        "member_id": "cvn78",
                        "oob_row": "cvn78_ford",
                        "type": SHIP_TYPE,
                        "role": "carrier",
                        "station": {"range_m": 0.0},
                        "provenance": {"count_basis": "sourced", "source_ids": ["fixture"]},
                        "hull": "CVN-78 Gerald R. Ford",
                    }
                ],
            }
        ],
    }


def _package() -> tuple[ForcePackage, dict[str, AssemblyReference]]:
    package = ForcePackage(
        "qualification.csg", "1", "Blue",
        (PackageMember("BLUE_CSG12__cvn78", "assembly", SHIP_TYPE, "carrier", "Blue"),),
        reference_frame="geodetic",
        anchor_ref="BLUE_CSG12",
    )
    assemblies = {
        SHIP_TYPE: AssemblyReference(SHIP_TYPE, "Blue", frozenset({"mobility"}))
    }
    return package, assemblies


def _compiled_scenario():
    return ScenarioCompiler.compile_data(_scenario())


def _full_package(group):
    gid, side = group["group_id"], group["side"]
    members = tuple(
        PackageMember(name, "assembly", row["type"], row["role"], side)
        for row in group["ships"]
        for name in row["entity_names"]
    )
    package = ForcePackage(
        f"qualification.{gid}", "1", side, members,
        reference_frame="geodetic", anchor_ref=gid, provenance_ref=group["oob_ref"],
    )
    assemblies = {
        member.ref: AssemblyReference(member.ref, side, frozenset({"mobility"}))
        for member in members
    }
    role_capabilities = {member.role: frozenset({"mobility"}) for member in members}
    bindings = {
        f"{package.package_id}/{member.member_id}": member.member_id
        for member in members
    }
    return package, assemblies, role_capabilities, bindings, {member.ref: member.ref for member in members}


def _nested_package(group):
    """Build one explicit nested package for the CSG migration seam."""
    gid, side = group["group_id"], group["side"]
    items = tuple(
        (row, name)
        for row in group["ships"]
        for name in row.get("entity_names", ())
    )
    nested_items, direct_items = items[:2], items[2:]

    child = ForcePackage(
        f"qualification.{gid}.screen",
        "1",
        side,
        tuple(
            PackageMember(name, "assembly", row["type"], row["role"], side)
            for row, name in nested_items
        ),
        relationships=(
            PackageRelationship(
                "membership", nested_items[0][1], nested_items[1][1]
            ),
        ),
        reference_frame="geodetic",
        anchor_ref=gid,
        provenance_ref=group["oob_ref"],
    )
    root = ForcePackage(
        f"qualification.{gid}",
        "1",
        side,
        (
            PackageMember("screen", "package", child.ref, "screen", side),
            *(
                PackageMember(name, "assembly", row["type"], row["role"], side)
                for row, name in direct_items
            ),
        ),
        relationships=(
            PackageRelationship("communication", "screen", direct_items[0][1]),
        ),
        reference_frame="geodetic",
        anchor_ref=gid,
        provenance_ref=group["oob_ref"],
    )
    assemblies = {
        row["type"]: AssemblyReference(row["type"], side, frozenset({"mobility"}))
        for row, _ in items
    }
    role_capabilities = {row["role"]: frozenset({"mobility"}) for row, _ in items}
    role_capabilities["screen"] = frozenset({"mobility"})
    return root, {child.ref: child}, assemblies, role_capabilities


def _compile_package(package, assemblies, role_capabilities):
    return compile_force_package(
        package,
        packages={},
        assemblies=assemblies,
        role_capabilities=role_capabilities,
    )


def test_force_package_projection_matches_existing_csg_entity_identity_and_geometry() -> None:
    package, assemblies = _package()
    scenario = _compiled_scenario()
    generic_id = "qualification.csg/BLUE_CSG12__cvn78"
    result = qualify_force_package_against_csg(
        package=package,
        packages={},
        assemblies=assemblies,
        role_capabilities={"carrier": frozenset({"mobility"})},
        scenario=scenario,
        group_id="BLUE_CSG12",
        entity_bindings={generic_id: "BLUE_CSG12__cvn78"},
        assembly_type_names={SHIP_TYPE: SHIP_TYPE},
    )
    assert result.entity_bindings == ((generic_id, "BLUE_CSG12__cvn78"),)
    assert result.csg_schema == "csg.group_composition.v2"
    assert len(result.geometry_digest) == 64
    assert result.relationship_edges == ()
    assert "scenario.csg.group_composition.v2" in result.evidence_refs


@pytest.mark.parametrize("stem", ["csg_s0_ford_vs_fujian_named_v1", "csg_s0_ford_mirror_v1"])
def test_full_csg_qualification_preserves_native_geometry_inventory_and_replay(stem) -> None:
    scenario_path = resolve_repo_path("scenarios", "naval", "csg", f"{stem}.json")
    scenario = ScenarioCompiler.compile_path(scenario_path)
    snapshot = scenario.instantiate()
    results = []
    compiled_packages = {}
    for group in snapshot["meta"]["csg"]["groups"]:
        package, assemblies, role_capabilities, bindings, type_names = _full_package(group)
        compiled = _compile_package(package, assemblies, role_capabilities)
        compiled_packages[compiled.package_ref] = compiled
        results.append(qualify_force_package_against_csg(
            package=package, packages={}, assemblies=assemblies, role_capabilities=role_capabilities,
            scenario=scenario, group_id=group["group_id"], entity_bindings=bindings,
            assembly_type_names=type_names,
        ))
        assert len(results[-1].entity_bindings) == 7
    reference = capture_csg_replay(scenario_path, seed=3)
    adapter = create_scenario_runtime_adapter(1)
    assert adapter.load_database(resolve_repo_path("examples", "config", "database"))
    loader = adapter.make_scenario_loader(0)
    assert load_qualified_csg_scenario(
        loader,
        scenario=scenario,
        qualifications=results,
        compiled_packages=compiled_packages,
        seed=3,
    ) is None
    assert {key: loader.scenario_data[key] for key in snapshot} == snapshot
    assert loader._compiled_runtime_metadata.meta_config["csg"] == snapshot["meta"]["csg"]

    # Bind the qualification result to the native materialization directly.
    # The replay helper is intentionally a separate spectator projection; its
    # equality alone would not prove that the qualified package names resolve
    # to the expected native entities and anchored coordinates.
    entity_config = {
        str(entity["name"]): entity
        for entity in snapshot["entities"]
        if isinstance(entity, dict) and str(entity.get("name", "")).strip()
    }
    groups = {str(group["group_id"]): group for group in snapshot["meta"]["csg"]["groups"]}
    initial_positions = {}
    for qualification in results:
        group = groups[qualification.group_id]
        inventory = group["embarked_inventory"]
        assert inventory
        assert sum(int(row["count"]) for row in inventory) > 0
        assert all(str(row["embarked_on"]).strip() for row in inventory)
        assert all(str(row["type"]).strip() for row in inventory)
        for _, name in qualification.entity_bindings:
            assert name in loader.entities
            expected = entity_config[name]
            runtime_id = int(loader.entities[name])
            native_position = tuple(float(value) for value in loader.sim.get_unit_position(runtime_id))
            assert native_position == pytest.approx(tuple(float(value) for value in expected["pos"]))
            assert all(math.isfinite(value) for value in native_position)
            initial_positions[runtime_id] = native_position

    for frame in reference["frames"]:
        if frame["tick"]:
            loader.sim.step()
        assert _csg_replay_unit_frame(loader.sim, loader) == frame["units"]
    assert len(reference["frames"]) == 241

    # The S0 scenarios are static.  A real native step must retain the
    # qualified hull layout while still advancing the native world.
    loader.sim.step()
    for runtime_id, expected in initial_positions.items():
        assert tuple(float(value) for value in loader.sim.get_unit_position(runtime_id)) == pytest.approx(expected)
    assert scenario.instantiate() == snapshot


@pytest.mark.parametrize("stem", ["csg_s0_ford_vs_fujian_named_v1", "csg_s0_ford_mirror_v1"])
def test_nested_force_package_qualification_reaches_existing_csg_loader(stem) -> None:
    scenario_path = resolve_repo_path("scenarios", "naval", "csg", f"{stem}.json")
    scenario = ScenarioCompiler.compile_path(scenario_path)
    snapshot = scenario.instantiate()
    qualifications = []
    compiled_packages = {}
    for index, group in enumerate(snapshot["meta"]["csg"]["groups"]):
        if index == 0:
            package, packages, assemblies, role_capabilities = _nested_package(group)
            bindings = None
        else:
            package, assemblies, role_capabilities, bindings, type_names = _full_package(group)
            packages = {}
        compiled = _compile_package(
            package,
            assemblies,
            role_capabilities,
        ) if not packages else compile_force_package(
            package,
            packages=packages,
            assemblies=assemblies,
            role_capabilities=role_capabilities,
        )
        if bindings is None:
            bindings = {
                entity.entity_id: entity.provenance[-1]
                for entity in compiled.entities
            }
            type_names = {assembly_id: assembly_id for assembly_id in assemblies}
        compiled_packages[compiled.package_ref] = compiled
        qualifications.append(
            qualify_force_package_against_csg(
                package=package,
                packages=packages,
                assemblies=assemblies,
                role_capabilities=role_capabilities,
                scenario=scenario,
                group_id=group["group_id"],
                entity_bindings=bindings,
                assembly_type_names=type_names,
            )
        )

    nested = qualifications[0]
    entity_names = [
        name
        for row in snapshot["meta"]["csg"]["groups"][0]["ships"]
        for name in row.get("entity_names", ())
    ]
    assert nested.relationship_edges == (
        (
            "communication",
            f"qualification.{snapshot['meta']['csg']['groups'][0]['group_id']}/screen",
            f"qualification.{snapshot['meta']['csg']['groups'][0]['group_id']}/{entity_names[2]}",
        ),
        (
            "membership",
            f"qualification.{snapshot['meta']['csg']['groups'][0]['group_id']}/screen/{entity_names[0]}",
            f"qualification.{snapshot['meta']['csg']['groups'][0]['group_id']}/screen/{entity_names[1]}",
        ),
    )
    adapter = create_scenario_runtime_adapter(1)
    assert adapter.load_database(resolve_repo_path("examples", "config", "database"))
    loader = adapter.make_scenario_loader(0)
    assert load_qualified_csg_scenario(
        loader,
        scenario=scenario,
        qualifications=qualifications,
        compiled_packages=compiled_packages,
        seed=3,
    ) is None
    assert {key: loader.scenario_data[key] for key in snapshot} == snapshot


@pytest.mark.parametrize(
    "mutator, expected",
    [
        (lambda p, a: (p, {SHIP_TYPE: AssemblyReference(SHIP_TYPE, "Red", frozenset({"mobility"}))}), "side_conflict"),
        (lambda p, a: (p, {SHIP_TYPE: AssemblyReference(SHIP_TYPE, "Blue", frozenset({"escort"}))}), "role_capability_missing"),
        (lambda p, a: (replace(p, members=(PackageMember("wrong", "assembly", SHIP_TYPE, "carrier", "Blue"),)), a), "binding_scope_mismatch"),
        (lambda p, a: (replace(p, reference_frame="local_enu"), a), "frame_anchor_mismatch"),
        (lambda p, a: (replace(p, anchor_ref="other"), a), "frame_anchor_mismatch"),
    ],
)
def test_force_package_projection_rejects_identity_drift(mutator, expected) -> None:
    package, assemblies = _package()
    package, assemblies = mutator(package, assemblies)
    with pytest.raises(ForcePackageError, match=expected):
        qualify_force_package_against_csg(
            package=package,
            packages={},
            assemblies=assemblies,
            role_capabilities={"carrier": frozenset({"mobility"}), "escort": frozenset({"escort"})},
            scenario=_compiled_scenario(),
            group_id="BLUE_CSG12",
            entity_bindings={"qualification.csg/BLUE_CSG12__cvn78": "BLUE_CSG12__cvn78"},
            assembly_type_names={SHIP_TYPE: SHIP_TYPE},
        )


def _minimal_qualification(scenario):
    package, assemblies = _package()
    return qualify_force_package_against_csg(
        package=package, packages={}, assemblies=assemblies,
        role_capabilities={"carrier": frozenset({"mobility"})}, scenario=scenario,
        group_id="BLUE_CSG12", entity_bindings={"qualification.csg/BLUE_CSG12__cvn78": "BLUE_CSG12__cvn78"},
        assembly_type_names={SHIP_TYPE: SHIP_TYPE},
    )


def _minimal_compiled_package():
    package, assemblies = _package()
    return _compile_package(package, assemblies, {"carrier": frozenset({"mobility"})})


class _RecordingLoader:
    def __init__(self):
        self.calls = []

    def load_compiled_scenario(self, scenario, seed=42):
        self.calls.append((scenario, seed))


@pytest.mark.parametrize("target", ["position", "inventory", "geometry", "runtime_metadata"])
def test_csg_snapshot_drift_rejects_before_loader_mutation(target) -> None:
    scenario = _compiled_scenario()
    qualification = _minimal_qualification(scenario)
    compiled = _minimal_compiled_package()
    loader = _RecordingLoader()
    if target == "position":
        scenario.merged_scenario_data["entities"][0]["pos"][0] += 100.0
    elif target == "inventory":
        scenario.merged_scenario_data["meta"]["csg"]["groups"][0]["embarked_inventory"].append({"count": 1})
    elif target == "geometry":
        scenario.merged_scenario_data["meta"]["csg"]["geometry"]["anchor"]["latitude_deg"] = 0.0
    else:
        scenario.runtime_metadata.meta_config["csg"]["groups"][0]["side"] = "Red"
    with pytest.raises(ForcePackageError, match="csg_scenario_stale|csg_runtime_metadata_mismatch"):
        load_qualified_csg_scenario(
            loader,
            scenario=scenario,
            qualifications=[qualification],
            compiled_packages={compiled.package_ref: compiled},
        )
    assert loader.calls == []


def test_csg_load_requires_complete_qualification_and_same_snapshot() -> None:
    scenario = _compiled_scenario()
    qualification = _minimal_qualification(scenario)
    compiled = _minimal_compiled_package()
    loader = _RecordingLoader()
    for results in ([], [qualification, qualification]):
        with pytest.raises(ForcePackageError, match="qualification_scope_mismatch"):
            load_qualified_csg_scenario(
                loader,
                scenario=scenario,
                qualifications=results,
                compiled_packages={compiled.package_ref: compiled},
            )
    with pytest.raises(ForcePackageError, match="qualification_snapshot_mismatch"):
        load_qualified_csg_scenario(
            loader,
            scenario=scenario,
            qualifications=[replace(qualification, scenario_digest="0" * 64)],
            compiled_packages={compiled.package_ref: compiled},
        )
    assert loader.calls == []


def test_csg_load_rejects_compiled_package_identity_or_relationship_drift() -> None:
    scenario = _compiled_scenario()
    qualification = _minimal_qualification(scenario)
    compiled = _minimal_compiled_package()
    loader = _RecordingLoader()

    with pytest.raises(ForcePackageError, match="compiled_package_identity_mismatch"):
        load_qualified_csg_scenario(
            loader,
            scenario=scenario,
            qualifications=[qualification],
            compiled_packages={
                compiled.package_ref: replace(compiled, identity_digest="0" * 64)
            },
        )

    with pytest.raises(ForcePackageError, match="compiled_package_identity_mismatch"):
        load_qualified_csg_scenario(
            loader,
            scenario=scenario,
            qualifications=[qualification],
            compiled_packages={
                qualification.package_ref: replace(compiled, package_ref="other.package@1")
            },
        )

    relationship_drift = replace(
        compiled,
        relationships=(
            CompiledRelationship(
                "communication",
                "qualification.csg/BLUE_CSG12__cvn78",
                "qualification.csg/BLUE_CSG12__cvn78",
                compiled.package_ref,
            ),
        ),
    )
    with pytest.raises(ForcePackageError, match="compiled_package_identity_mismatch"):
        load_qualified_csg_scenario(
            loader,
            scenario=scenario,
            qualifications=[qualification],
            compiled_packages={compiled.package_ref: relationship_drift},
        )
    assert loader.calls == []


def test_csg_qualification_keeps_non_authoritative_relationship_edges_explicit() -> None:
    package, assemblies = _package()
    package = replace(
        package,
        relationships=(
            PackageRelationship(
                "communication",
                "BLUE_CSG12__cvn78",
                "BLUE_CSG12__cvn78",
            ),
        ),
    )
    scenario = _compiled_scenario()
    qualification = qualify_force_package_against_csg(
        package=package,
        packages={},
        assemblies=assemblies,
        role_capabilities={"carrier": frozenset({"mobility"})},
        scenario=scenario,
        group_id="BLUE_CSG12",
        entity_bindings={"qualification.csg/BLUE_CSG12__cvn78": "BLUE_CSG12__cvn78"},
        assembly_type_names={SHIP_TYPE: SHIP_TYPE},
    )
    assert qualification.relationship_edges == (
        ("communication", "qualification.csg/BLUE_CSG12__cvn78", "qualification.csg/BLUE_CSG12__cvn78"),
    )
    compiled = _compile_package(package, assemblies, {"carrier": frozenset({"mobility"})})
    loader = _RecordingLoader()
    with pytest.raises(ForcePackageError, match="compiled_package_identity_mismatch"):
        load_qualified_csg_scenario(
            loader,
            scenario=scenario,
            qualifications=[replace(qualification, relationship_edges=())],
            compiled_packages={compiled.package_ref: compiled},
        )
    assert loader.calls == []


def test_csg_binding_permutation_rejects_before_loader_mutation() -> None:
    scenario_path = resolve_repo_path("scenarios", "naval", "csg", "csg_s0_ford_vs_fujian_named_v1.json")
    scenario = ScenarioCompiler.compile_path(scenario_path)
    group = scenario.instantiate()["meta"]["csg"]["groups"][0]
    package, assemblies, role_capabilities, bindings, type_names = _full_package(group)
    qualification = qualify_force_package_against_csg(
        package=package,
        packages={},
        assemblies=assemblies,
        role_capabilities=role_capabilities,
        scenario=scenario,
        group_id=group["group_id"],
        entity_bindings=bindings,
        assembly_type_names=type_names,
    )
    pairs = list(qualification.entity_bindings)
    pairs[0], pairs[1] = (pairs[0][0], pairs[1][1]), (pairs[1][0], pairs[0][1])
    loader = _RecordingLoader()
    compiled = _compile_package(package, assemblies, role_capabilities)
    with pytest.raises(ForcePackageError, match="binding_identity_mismatch"):
        load_qualified_csg_scenario(
            loader,
            scenario=scenario,
            qualifications=[replace(qualification, entity_bindings=tuple(pairs))],
            compiled_packages={compiled.package_ref: compiled},
            seed=3,
        )
    assert loader.calls == []


def test_csg_correlated_binding_tamper_rejects_against_compiled_package() -> None:
    scenario_path = resolve_repo_path("scenarios", "naval", "csg", "csg_s0_ford_vs_fujian_named_v1.json")
    scenario = ScenarioCompiler.compile_path(scenario_path)
    group = scenario.instantiate()["meta"]["csg"]["groups"][0]
    package, assemblies, role_capabilities, bindings, type_names = _full_package(group)
    qualification = qualify_force_package_against_csg(
        package=package,
        packages={},
        assemblies=assemblies,
        role_capabilities=role_capabilities,
        scenario=scenario,
        group_id=group["group_id"],
        entity_bindings=bindings,
        assembly_type_names=type_names,
    )
    compiled = _compile_package(package, assemblies, role_capabilities)
    pairs = list(qualification.entity_bindings)
    projection = list(qualification.entity_binding_projection)
    first, second = projection[0], projection[1]
    pairs[0], pairs[1] = (pairs[0][0], pairs[1][1]), (pairs[1][0], pairs[0][1])
    projection[0] = (first[0], second[1], second[2], second[3], second[4], first[5])
    projection[1] = (second[0], first[1], first[2], first[3], first[4], second[5])
    tampered = replace(
        qualification,
        entity_bindings=tuple(pairs),
        entity_bindings_digest=_digest(tuple(pairs)),
        entity_binding_projection=tuple(projection),
    )
    loader = _RecordingLoader()
    with pytest.raises(ForcePackageError, match="compiled_package_mismatch"):
        load_qualified_csg_scenario(
            loader,
            scenario=scenario,
            qualifications=[tampered],
            compiled_packages={compiled.package_ref: compiled},
            seed=3,
        )
    assert loader.calls == []


def test_csg_group_metadata_conflicts_reject_before_qualification() -> None:
    original = _compiled_scenario().instantiate()
    for mutator, expected in (
        (lambda data: data["meta"]["csg"]["groups"][0]["ships"][0]["entity_names"].clear(), "group_entity_metadata_mismatch"),
        (lambda data: data["meta"]["csg"]["groups"][0]["embarked_inventory"].append({"count": 1, "embarked_on": "missing"}), "inventory_host_unknown"),
    ):
        data = deepcopy(original)
        mutator(data)
        scenario = ScenarioCompiler.compile_data(data)
        with pytest.raises(ForcePackageError, match=expected):
            _minimal_qualification(scenario)


def test_csg_qualification_rejects_ambiguous_guide_frame() -> None:
    scenario = _compiled_scenario()
    scenario.merged_scenario_data["meta"]["csg"]["groups"][0]["guide"].clear()
    scenario.runtime_metadata.meta_config["csg"]["groups"][0]["guide"].clear()
    scenario = replace(scenario, semantic_digest="")
    with pytest.raises(ForcePackageError, match="csg_guide_frame_ambiguous"):
        _minimal_qualification(scenario)


def test_csg_qualification_rejects_malformed_group_container() -> None:
    scenario = _compiled_scenario()
    scenario.merged_scenario_data["meta"]["csg"]["groups"] = {}
    scenario.runtime_metadata.meta_config["csg"]["groups"] = {}
    scenario = replace(scenario, semantic_digest="")
    with pytest.raises(ForcePackageError, match="csg_groups_required"):
        _minimal_qualification(scenario)


def test_csg_loader_rejects_malformed_group_metadata_before_loader_mutation() -> None:
    scenario = _compiled_scenario()
    qualification = _minimal_qualification(scenario)
    compiled = _minimal_compiled_package()
    scenario.merged_scenario_data["meta"]["csg"]["groups"][0].pop("group_id")
    scenario.runtime_metadata.meta_config["csg"]["groups"][0].pop("group_id")
    scenario = replace(scenario, semantic_digest="")
    loader = _RecordingLoader()
    with pytest.raises(ForcePackageError, match="csg_group_metadata_invalid"):
        load_qualified_csg_scenario(
            loader,
            scenario=scenario,
            qualifications=[qualification],
            compiled_packages={compiled.package_ref: compiled},
        )
    assert loader.calls == []
