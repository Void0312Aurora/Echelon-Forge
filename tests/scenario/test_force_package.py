from __future__ import annotations

import pytest

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
        "community.joint_patrol", "1", "Blue",
        members=(
            PackageMember("air_pair", "package", "air.pair@1", "air_screen"),
            PackageMember("escort", "assembly", "naval.escort", "surface_screen"),
            PackageMember("squad", "assembly", "ground.squad", "ground_security"),
        ),
        relationships=(PackageRelationship("task_authority", "air_pair", "escort"),),
    )
    air = ForcePackage(
        "air.pair", "1", "Blue",
        members=(
            PackageMember("lead", "assembly", "air.lead", "air_control"),
            PackageMember("wing", "assembly", "air.wing", "air_screen"),
        ),
    )
    compiled = compile_force_package(
        package, packages={air.ref: air}, assemblies=_assemblies(),
        role_capabilities={"air_screen": frozenset({"air_screen"}), "air_control": frozenset({"air_control"}), "surface_screen": frozenset({"surface_screen"}), "ground_security": frozenset({"ground_security"})},
    )
    assert [entity.entity_id for entity in compiled.entities] == [
        "community.joint_patrol/air_pair/lead", "community.joint_patrol/air_pair/wing",
        "community.joint_patrol/escort", "community.joint_patrol/squad",
    ]
    assert len(compiled.identity_digest) == 64


def test_nested_package_order_does_not_change_identity() -> None:
    child = ForcePackage("child", "1", "Blue", (PackageMember("a", "assembly", "air.lead", "air_control"),))
    left = ForcePackage("root", "1", "Blue", (PackageMember("child", "package", child.ref, "air_control"),))
    right = ForcePackage("root", "1", "Blue", (PackageMember("child", "package", child.ref, "air_control"),))
    kwargs = dict(packages={child.ref: child}, assemblies=_assemblies(), role_capabilities={"air_control": frozenset({"air_control"})})
    assert compile_force_package(left, **kwargs).identity_digest == compile_force_package(right, **kwargs).identity_digest


@pytest.mark.parametrize(
    "mutator, expected",
    [
        (lambda members: members + (PackageMember("bad", "assembly", "missing", "air_screen"),), "assembly_unknown"),
        (lambda members: members + (PackageMember("bad", "package", "missing@1", "air_screen"),), "package_unknown"),
    ],
)
def test_unknown_references_fail_before_entity_publication(mutator, expected) -> None:
    root = ForcePackage("root", "1", "Blue", mutator((PackageMember("ok", "assembly", "air.lead", "air_control"),)))
    with pytest.raises(ForcePackageError, match=expected):
        compile_force_package(root, packages={}, assemblies=_assemblies(), role_capabilities={"air_control": frozenset({"air_control"}), "air_screen": frozenset({"air_screen"})})


def test_cycle_duplicate_side_and_role_capability_fail_closed() -> None:
    a = ForcePackage("a", "1", "Blue", (PackageMember("b", "package", "b@1", "air_screen"),))
    b = ForcePackage("b", "1", "Blue", (PackageMember("a", "package", "a@1", "air_screen"),))
    with pytest.raises(ForcePackageError, match="membership_cycle"):
        compile_force_package(a, packages={b.ref: b}, assemblies=_assemblies(), role_capabilities={"air_screen": frozenset({"air_screen"})})
    bad_side = ForcePackage("root", "1", "Blue", (PackageMember("x", "assembly", "naval.escort", "surface_screen", "Red"),))
    with pytest.raises(ForcePackageError, match="side_conflict"):
        compile_force_package(bad_side, packages={}, assemblies=_assemblies(), role_capabilities={"surface_screen": frozenset({"surface_screen"})})
    bad_role = ForcePackage("root", "1", "Blue", (PackageMember("x", "assembly", "air.wing", "air_control"),))
    with pytest.raises(ForcePackageError, match="role_capability_missing"):
        compile_force_package(bad_role, packages={}, assemblies=_assemblies(), role_capabilities={"air_control": frozenset({"air_control"})})


def test_relationship_endpoint_is_checked() -> None:
    root = ForcePackage(
        "root", "1", "Blue", (PackageMember("x", "assembly", "air.lead", "air_control"),),
        relationships=(PackageRelationship("task_authority", "x", "missing"),),
    )
    with pytest.raises(ForcePackageError, match="relationship_endpoint_unknown"):
        compile_force_package(root, packages={}, assemblies=_assemblies(), role_capabilities={"air_control": frozenset({"air_control"})})
