"""CSG-S0 group-composition contract (Carrier Strike Group Engagement, S0-D).

Pins the ``groups`` scenario schema, its fail-closed validation, and that the
named and symmetric-mirror CSG-S0 scenarios spawn every order-of-battle row:
one live entity per ship and submarine hull, the embarked air wing as an
inventory whose totals match the S0-A pages, and every referenced unit record
present in the database with provenance.
"""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path

ensure_repo_imports()

import ef_py  # noqa: E402

from gym_envs.scenario_loader import ScenarioLoader  # noqa: E402
from python.scenario.compiler import (  # noqa: E402
    ScenarioCompiler,
    expand_group_composition,
    station_local_offset_m,
    validate_group_composition,
)

REPO = Path(resolve_repo_path("."))
DATABASE = resolve_repo_path("examples", "config", "database")
NAMED = resolve_repo_path("scenarios", "naval", "csg", "csg_s0_ford_vs_fujian_named_v1.json")
MIRROR = resolve_repo_path("scenarios", "naval", "csg", "csg_s0_ford_mirror_v1.json")

# Nominal S0-A totals: Ford CVW-8 74 aircraft (incl. the MH-60R detachments on
# the Flight IIA hulls); Fujian planning wing 48 plus 7 escort and AOE organic
# helicopters.
EXPECTED = {
    "BLUE_CSG12": {"hulls": 7, "aircraft": 74},
    "RED_CV18": {"hulls": 7, "aircraft": 55},
    "RED_MIRROR_CSG12": {"hulls": 7, "aircraft": 74},
}
UNIT_TYPE = {"Ship": 2, "Submarine": 10}


def _load(path: str):
    kernel = ef_py.SimulationKernel()
    kernel.reset(1)
    assert kernel.load_database(DATABASE)
    loader = ScenarioLoader(kernel)
    loader.load_scenario(path, seed=3)
    return kernel, loader


def _record_names() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for f in Path(DATABASE).rglob("*.json"):
        if "vulnerability_evidence" in f.parts:
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        for rec in data.get("units", [data]) if isinstance(data, dict) else data:
            if isinstance(rec, dict) and "name" in rec:
                out[rec["name"]] = rec
    return out


def _minimal_group(**overrides) -> dict:
    group = {
        "group_id": "G",
        "side": "Blue",
        "oob_ref": "docs/domains/naval/reviews/csg_order_of_battle_20260928/csg_order_of_battle_ford_20260928.md",
        "guide": {"pos": [0.0, 0.0, 0.0], "axis_deg": 90.0},
        "members": [
            {"member_id": "cvn", "oob_row": "cvn78_ford", "type": "CSG_US_CVN-78_Gerald_R_Ford",
             "station": {"range_m": 0.0}, "provenance": {"count_basis": "sourced", "source_ids": []}},
        ],
    }
    group.update(overrides)
    return group


class GroupSchemaTests(unittest.TestCase):
    def test_station_offset_uses_nav_bearings_from_the_axis(self) -> None:
        east, north = station_local_offset_m({"range_m": 1000.0, "bearing_rel_deg": 90.0}, 0.0)
        self.assertAlmostEqual(east, 1000.0)
        self.assertAlmostEqual(north, 0.0, places=9)
        east, north = station_local_offset_m({"range_m": 1000.0, "bearing_rel_deg": 0.0}, 270.0)
        self.assertAlmostEqual(east, -1000.0)

    def test_malformed_groups_fail_closed(self) -> None:
        good = _minimal_group()
        cvn = good["members"][0]
        bad_cases = {
            "unknown side": _minimal_group(side="Green"),
            "missing oob file": _minimal_group(oob_ref="docs/does_not_exist.md"),
            "unknown group key": {**good, "formation": "circle"},
            "ship without station": _minimal_group(members=[{k: v for k, v in cvn.items() if k != "station"}]),
            "embarked on unknown host": _minimal_group(members=[cvn, {
                "member_id": "vfa", "oob_row": "ac_fa18e", "type": "CSG_US_FA-18E_Block_III",
                "count": 2, "embarked_on": "nobody",
                "provenance": {"count_basis": "sourced", "source_ids": []}}]),
            "undeclared branch": _minimal_group(members=[{**cvn, "branch": "nope"}]),
            "bad count basis": _minimal_group(members=[{**cvn, "provenance": {"count_basis": "guess"}}]),
            "negative count": _minimal_group(members=[{**cvn, "count": -1}]),
        }
        for label, group in bad_cases.items():
            with self.subTest(case=label), self.assertRaises(ValueError):
                validate_group_composition({"groups": [group]}, project_root=REPO)

    def test_branch_gated_rows_expand_to_zero(self) -> None:
        group = _minimal_group(branches={"extra": False})
        group["members"].append({**group["members"][0], "member_id": "cvn2", "branch": "extra",
                                 "station": {"range_m": 5000.0}})
        entities, meta = expand_group_composition({"groups": [group]}, project_root=REPO)
        self.assertEqual([e["name"] for e in entities], ["G__cvn"])
        self.assertEqual([r["count"] for r in meta["groups"][0]["ships"]], [1, 0])

    def test_compile_pops_groups_and_writes_meta(self) -> None:
        data = {"scenario_name": "t", "environment": {"time_step": 0.5}, "groups": [_minimal_group()]}
        compiled = ScenarioCompiler.compile_data(copy.deepcopy(data))
        merged = compiled.merged_scenario_data
        self.assertNotIn("groups", merged)
        self.assertEqual([e["name"] for e in merged["entities"]], ["G__cvn"])
        self.assertEqual(merged["meta"]["csg"]["schema"], "csg.group_composition.v1")
        # Recompiling the expanded output must not expand twice.
        again = ScenarioCompiler.compile_data(copy.deepcopy(merged))
        self.assertEqual(len(again.merged_scenario_data["entities"]), 1)

    def test_generated_names_collide_with_hand_written_entities(self) -> None:
        data = {"scenario_name": "t", "groups": [_minimal_group()],
                "entities": [{"name": "G__cvn", "type": "CSG_US_CVN-78_Gerald_R_Ford", "side": "Blue",
                              "pos": [0.0, 0.0, 0.0]}]}
        with self.assertRaises(ValueError):
            ScenarioCompiler.compile_data(data)


class CsgS0ScenarioTests(unittest.TestCase):
    records = _record_names()

    def _check(self, path: str, groups: set[str]) -> None:
        kernel, loader = _load(path)
        meta = loader._compiled_runtime_metadata.meta_config["csg"]
        self.assertEqual({g["group_id"] for g in meta["groups"]}, groups)
        self.assertEqual(kernel.get_geodetic_anchor(), (21.0, 125.0, 0.0))
        for group in meta["groups"]:
            gid = group["group_id"]
            spawned = [n for row in group["ships"] for n in row["entity_names"]]
            self.assertEqual(len(spawned), EXPECTED[gid]["hulls"], gid)
            for row in group["ships"]:
                self.assertEqual(len(row["entity_names"]), row["count"], row["member_id"])
                rec = self.records.get(row["type"])
                self.assertIsNotNone(rec, row["type"])
                self.assertTrue((rec.get("_provenance") or {}).get("sources"), row["type"])
                for name in row["entity_names"]:
                    eid = int(loader.entities[name])
                    self.assertGreater(eid, 0, name)
                    self.assertEqual(kernel.get_unit_type(eid), UNIT_TYPE[rec["type"]], name)
            aircraft = sum(r["count"] for r in group["embarked_inventory"])
            self.assertEqual(aircraft, EXPECTED[gid]["aircraft"], gid)
            for row in group["embarked_inventory"]:
                self.assertIn(row["type"], self.records, row["member_id"])
                self.assertIn(row["embarked_on"], {r["member_id"] for r in group["ships"]})
        # CSG-S0 is static: no spawned hull moves in 20 steps.
        before = {n: kernel.get_unit_position(int(i)) for n, i in loader.entities.items()}
        for _ in range(20):
            kernel.step()
        for name, pos in before.items():
            after = kernel.get_unit_position(int(loader.entities[name]))
            self.assertLess(max(abs(a - b) for a, b in zip(after, pos)), 1.0e-6, name)

    def test_named_variant_spawns_the_full_order_of_battle(self) -> None:
        self._check(NAMED, {"BLUE_CSG12", "RED_CV18"})

    def test_mirror_variant_fields_the_same_platform_set_on_both_sides(self) -> None:
        self._check(MIRROR, {"BLUE_CSG12", "RED_MIRROR_CSG12"})
        data = json.loads(Path(MIRROR).read_text(encoding="utf-8"))
        blue, red = data["groups"]
        strip = lambda g: [(m["oob_row"], m["type"], m.get("count", 1)) for m in g["members"]]  # noqa: E731
        self.assertEqual(strip(blue), strip(red))
        self.assertEqual((blue["side"], red["side"]), ("Blue", "Red"))


if __name__ == "__main__":
    unittest.main()
