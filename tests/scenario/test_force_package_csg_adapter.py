from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from python.scenario.force_package import (
    AssemblyReference,
    ForcePackage,
    ForcePackageError,
    PackageMember,
)
from python.scenario.force_package_csg_adapter import qualify_force_package_against_csg
from python.scenario.compiler import ScenarioCompiler


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
    return ScenarioCompiler.compile_data(_scenario(), source_path=str(Path.cwd() / "README.md"))


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
    assert "scenario.csg.group_composition.v2" in result.evidence_refs


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
