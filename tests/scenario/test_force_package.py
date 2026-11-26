from __future__ import annotations

import pytest
from dataclasses import replace

from python.scenario.force_package import (
    AssemblyReference,
    ForcePackage,
    ForcePackageError,
    PackageMember,
    PackageRelationship,
    compile_force_package,
)


def _assemblies() -> dict[str, AssemblyReference]:
    return {
        "air.lead": AssemblyReference("air.lead", "Blue", frozenset({"air_screen", "air_control"})),
        "air.wing": AssemblyReference("air.wing", "Blue", frozenset({"air_screen"})),
        "naval.escort": AssemblyReference("naval.escort", "Blue", frozenset({"surface_screen"})),
        "ground.squad": AssemblyReference("ground.squad", "Blue", frozenset({"ground_security"})),
    }


def test_air_naval_ground_members_compile_through_same_schema() -> None:
    package = ForcePackage(
        "community.joint_patrol",
        "1",
        "Blue",
        members=(
            PackageMember("air_pair", "package", "air.pair@1", "air_screen"),
            PackageMember("escort", "assembly", "naval.escort", "surface_screen"),
            PackageMember("squad", "assembly", "ground.squad", "ground_security"),
        ),
        relationships=(PackageRelationship("task_authority", "air_pair", "escort"),),
    )
    air = ForcePackage(
        "air.pair",
        "1",
        "Blue",
        members=(
            PackageMember("lead", "assembly", "air.lead", "air_control"),
            PackageMember("wing", "assembly", "air.wing", "air_screen"),
        ),
    )
    compiled = compile_force_package(
        package,
        packages={air.ref: air},
        assemblies=_assemblies(),
        role_capabilities={
            "air_screen": frozenset({"air_screen"}),
            "air_control": frozenset({"air_control"}),
            "surface_screen": frozenset({"surface_screen"}),
            "ground_security": frozenset({"ground_security"}),
        },
    )
    assert [entity.entity_id for entity in compiled.entities] == [
        "community.joint_patrol/air_pair/lead",
        "community.joint_patrol/air_pair/wing",
        "community.joint_patrol/escort",
        "community.joint_patrol/squad",
    ]
    assert len(compiled.identity_digest) == 64


def test_nested_package_order_does_not_change_identity() -> None:
    child = ForcePackage(
        "child", "1", "Blue", (PackageMember("a", "assembly", "air.lead", "air_control"),)
    )
    left = ForcePackage(
        "root", "1", "Blue", (PackageMember("child", "package", child.ref, "air_control"),)
    )
    right = ForcePackage(
        "root", "1", "Blue", (PackageMember("child", "package", child.ref, "air_control"),)
    )
    kwargs = dict(
        packages={child.ref: child},
        assemblies=_assemblies(),
        role_capabilities={"air_control": frozenset({"air_control"})},
    )
    assert (
        compile_force_package(left, **kwargs).identity_digest
        == compile_force_package(right, **kwargs).identity_digest
    )


def test_shared_child_package_is_expanded_for_each_scoped_reference() -> None:
    child = ForcePackage(
        "child", "1", "Blue", (PackageMember("wingman", "assembly", "air.wing", "air_screen"),)
    )
    root = ForcePackage(
        "root",
        "1",
        "Blue",
        (
            PackageMember("alpha", "package", child.ref, "air_screen"),
            PackageMember("bravo", "package", child.ref, "air_screen"),
        ),
    )
    compiled = compile_force_package(
        root,
        packages={child.ref: child},
        assemblies=_assemblies(),
        role_capabilities={"air_screen": frozenset({"air_screen"})},
    )
    assert [entity.entity_id for entity in compiled.entities] == [
        "root/alpha/wingman",
        "root/bravo/wingman",
    ]


def test_referenced_child_side_must_match_parent_side() -> None:
    child = ForcePackage(
        "red_child", "1", "Red", (PackageMember("wing", "assembly", "air.wing", "air_screen"),)
    )
    root = ForcePackage(
        "root", "1", "Blue", (PackageMember("child", "package", child.ref, "air_screen"),)
    )
    with pytest.raises(ForcePackageError, match="side_conflict"):
        compile_force_package(
            root,
            packages={child.ref: child},
            assemblies=_assemblies(),
            role_capabilities={"air_screen": frozenset({"air_screen"})},
        )


@pytest.mark.parametrize(
    "mutator, expected",
    [
        (
            lambda members: members + (PackageMember("bad", "assembly", "missing", "air_screen"),),
            "assembly_unknown",
        ),
        (
            lambda members: members + (PackageMember("bad", "package", "missing@1", "air_screen"),),
            "package_unknown",
        ),
    ],
)
def test_unknown_references_fail_before_entity_publication(mutator, expected) -> None:
    root = ForcePackage(
        "root", "1", "Blue", mutator((PackageMember("ok", "assembly", "air.lead", "air_control"),))
    )
    with pytest.raises(ForcePackageError, match=expected):
        compile_force_package(
            root,
            packages={},
            assemblies=_assemblies(),
            role_capabilities={
                "air_control": frozenset({"air_control"}),
                "air_screen": frozenset({"air_screen"}),
            },
        )


def test_cycle_duplicate_side_and_role_capability_fail_closed() -> None:
    a = ForcePackage("a", "1", "Blue", (PackageMember("b", "package", "b@1", "air_screen"),))
    b = ForcePackage("b", "1", "Blue", (PackageMember("a", "package", "a@1", "air_screen"),))
    with pytest.raises(ForcePackageError, match="membership_cycle"):
        compile_force_package(
            a,
            packages={b.ref: b},
            assemblies=_assemblies(),
            role_capabilities={"air_screen": frozenset({"air_screen"})},
        )
    bad_side = ForcePackage(
        "root",
        "1",
        "Blue",
        (PackageMember("x", "assembly", "naval.escort", "surface_screen", "Red"),),
    )
    with pytest.raises(ForcePackageError, match="side_conflict"):
        compile_force_package(
            bad_side,
            packages={},
            assemblies=_assemblies(),
            role_capabilities={"surface_screen": frozenset({"surface_screen"})},
        )
    bad_role = ForcePackage(
        "root", "1", "Blue", (PackageMember("x", "assembly", "air.wing", "air_control"),)
    )
    with pytest.raises(ForcePackageError, match="role_capability_missing"):
        compile_force_package(
            bad_role,
            packages={},
            assemblies=_assemblies(),
            role_capabilities={"air_control": frozenset({"air_control"})},
        )


def test_relationship_endpoint_is_checked() -> None:
    root = ForcePackage(
        "root",
        "1",
        "Blue",
        (PackageMember("x", "assembly", "air.lead", "air_control"),),
        relationships=(PackageRelationship("task_authority", "x", "missing"),),
    )
    with pytest.raises(ForcePackageError, match="relationship_endpoint_unknown"):
        compile_force_package(
            root,
            packages={},
            assemblies=_assemblies(),
            role_capabilities={"air_control": frozenset({"air_control"})},
        )


def test_relationship_only_change_is_preserved_and_changes_identity() -> None:
    root = ForcePackage(
        "root",
        "1",
        "Blue",
        (
            PackageMember("lead", "assembly", "air.lead", "air_control"),
            PackageMember("wing", "assembly", "air.wing", "air_screen"),
        ),
        relationships=(PackageRelationship("task_authority", "lead", "wing"),),
    )
    kwargs = dict(
        packages={},
        assemblies=_assemblies(),
        role_capabilities={
            "air_control": frozenset({"air_control"}),
            "air_screen": frozenset({"air_screen"}),
        },
    )
    command = compile_force_package(root, **kwargs)
    communication = compile_force_package(
        replace(root, relationships=(PackageRelationship("communication", "lead", "wing"),)),
        **kwargs,
    )
    assert command.identity_digest != communication.identity_digest
    assert command.as_dict()["relationships"] == [
        {
            "relationship_type": "task_authority",
            "source": "root/lead",
            "target": "root/wing",
            "package_ref": "root@1",
        }
    ]


def test_reused_package_relationships_are_scoped_per_instance() -> None:
    child = ForcePackage(
        "child",
        "1",
        "Blue",
        (
            PackageMember("lead", "assembly", "air.lead", "air_control"),
            PackageMember("wing", "assembly", "air.wing", "air_screen"),
        ),
        relationships=(PackageRelationship("communication", "lead", "wing"),),
    )
    root = ForcePackage(
        "root",
        "1",
        "Blue",
        (
            PackageMember("a", "package", child.ref, "air_screen"),
            PackageMember("b", "package", child.ref, "air_screen"),
        ),
    )
    compiled = compile_force_package(
        root,
        packages={child.ref: child},
        assemblies=_assemblies(),
        role_capabilities={
            "air_control": frozenset({"air_control"}),
            "air_screen": frozenset({"air_screen"}),
        },
    )
    assert [(r.source, r.target) for r in compiled.relationships] == [
        ("root/a/lead", "root/a/wing"),
        ("root/b/lead", "root/b/wing"),
    ]


def test_nested_package_role_is_checked_against_child_capabilities() -> None:
    child = ForcePackage(
        "child", "1", "Blue", (PackageMember("wing", "assembly", "air.wing", "air_screen"),)
    )
    root = ForcePackage(
        "root", "1", "Blue", (PackageMember("child", "package", child.ref, "air_control"),)
    )
    with pytest.raises(ForcePackageError, match="role_capability_missing"):
        compile_force_package(
            root,
            packages={child.ref: child},
            assemblies=_assemblies(),
            role_capabilities={
                "air_control": frozenset({"air_control"}),
                "air_screen": frozenset({"air_screen"}),
            },
        )


def test_frame_and_anchor_metadata_are_preserved_in_identity() -> None:
    root = ForcePackage(
        "root", "1", "Blue", (PackageMember("lead", "assembly", "air.lead", "air_control"),)
    )
    kwargs = dict(
        packages={},
        assemblies=_assemblies(),
        role_capabilities={"air_control": frozenset({"air_control"})},
    )
    first = compile_force_package(root, **kwargs)
    second = compile_force_package(
        replace(root, reference_frame="geodetic", anchor_ref="a@1"), **kwargs
    )
    assert first.identity_digest != second.identity_digest
    assert second.as_dict()["package_instances"][0]["anchor_ref"] == "a@1"


def _compiled_snapshot():
    root = ForcePackage(
        "root.海", "1", "Blue",
        (PackageMember("lead", "assembly", "air.lead", "air_control"),),
        relationships=(PackageRelationship("communication", "lead", "lead"),),
        anchor_ref="anchor", provenance_ref="source",
    )
    return compile_force_package(
        root, packages={}, assemblies=_assemblies(),
        role_capabilities={"air_control": frozenset({"air_control"})},
        assembly_type_names={"air.lead": "NativeLead"},
    )


def test_compiled_identity_preserves_v1_digest_and_exports_detached_evidence() -> None:
    compiled = _compiled_snapshot()
    # Recorded from the v1 compiler before the identity implementation was shared.
    assert compiled.identity_digest == "8bceb1dee5bea428bdcece9fbe64b65be2581aa1012400af482985cccb5a3181"
    original = compiled.as_dict()
    exported = compiled.as_dict()
    exported["entities"][0]["role"] = "changed"
    exported["relationships"][0]["target"] = "elsewhere"
    exported["package_instances"][0]["anchor_ref"] = "elsewhere"
    exported["assembly_type_bindings"][0]["native_type"] = "OtherType"
    assert compiled.as_dict() == original
    assert compiled.is_fresh()


@pytest.mark.parametrize(
    "mutator",
    [
        lambda c: replace(c, schema_version="other.schema"),
        lambda c: replace(c, package_ref="other@1"),
        lambda c: replace(c, identity_digest="0" * 64),
        lambda c: replace(c, entities=()),
        lambda c: replace(c, entities=(replace(c.entities[0], provenance=("changed",)),)),
        lambda c: replace(c, relationships=(replace(c.relationships[0], target="elsewhere"),)),
        lambda c: replace(c, package_instances=(replace(c.package_instances[0], anchor_ref="elsewhere"),)),
        lambda c: replace(c, assembly_type_bindings=(("air.lead", "OtherType"),)),
    ],
    ids=["schema", "package_ref", "digest", "membership", "provenance", "graph", "anchor", "native_type"],
)
def test_compiled_snapshot_rejects_replacement_with_retained_identity(mutator) -> None:
    assert not mutator(_compiled_snapshot()).is_fresh()


def test_compiled_snapshot_detects_mutation_bypassing_frozen_records() -> None:
    compiled = _compiled_snapshot()
    object.__setattr__(compiled.package_instances[0], "reference_frame", "geodetic")
    assert not compiled.is_fresh()
