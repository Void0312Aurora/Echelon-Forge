"""CSG-S0 group-composition contract (Carrier Strike Group Engagement, S0-D, S0-B).

Pins the ``groups`` scenario schema, its fail-closed validation, and that the
named and symmetric-mirror CSG-S0 scenarios spawn every order-of-battle row:
one live entity per ship and submarine hull, the embarked air wing as an
inventory whose totals match the S0-A pages, and every referenced unit record
present in the database with provenance.

S0-B: both scenarios place their groups through the shared geodetic frame. The
guide is a latitude/longitude, stations are great-circle offsets from it, and
every spawned hull maps back (through the runtime's own projection) to the
geodetic point its station names. Expected values come from the direct and
inverse geodesic problems on the model sphere, not from the compiler.
"""

from __future__ import annotations

import copy
import json
import math
import unittest
from pathlib import Path

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path

ensure_repo_imports()

import ef_py  # noqa: E402

from gym_envs.scenario_loader import ScenarioLoader  # noqa: E402
from python.scenario.compiler import (  # noqa: E402
    ScenarioCompiler,
    expand_group_composition,
    geodesic_destination_deg,
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
    "BLUE_CSG12": {"hulls": 7, "aircraft": 74, "stowed_helos": 4},
    "RED_CV18": {"hulls": 7, "aircraft": 55, "stowed_helos": 6},
    "RED_MIRROR_CSG12": {"hulls": 7, "aircraft": 74, "stowed_helos": 4},
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


ANCHOR = (21.0, 125.0, 0.0)


def _geo_scenario(guide_geo: dict, axis_deg: float = 90.0, members=None) -> dict:
    group = _minimal_group(guide={"geo": guide_geo, "axis_deg": axis_deg})
    if members is not None:
        group["members"] = members
    return {
        "environment": {"geodetic_anchor": {"latitude_deg": ANCHOR[0], "longitude_deg": ANCHOR[1]}},
        "groups": [group],
    }


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371009.0 * math.asin(math.sqrt(h))


class GeodeticPlacementTests(unittest.TestCase):
    def test_binding_projection_round_trips_and_preserves_anchor_range(self) -> None:
        # Azimuthal-equidistant identity: distance from the anchor is exact.
        lat, lon = 23.5, 128.0
        east, north, up = ef_py.geodesy_geodetic_to_local(*ANCHOR, lat, lon, 0.0)
        self.assertAlmostEqual(
            (east**2 + north**2) ** 0.5, _haversine_m(ANCHOR[0], ANCHOR[1], lat, lon), delta=1e-3
        )
        back = ef_py.geodesy_local_to_geodetic(*ANCHOR, east, north, up)
        self.assertAlmostEqual(back[0], lat, places=10)
        self.assertAlmostEqual(back[1], lon, places=10)
        with self.assertRaises(ValueError):
            ef_py.geodesy_geodetic_to_local(90.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    def test_direct_geodesic_matches_inverse_on_the_sphere(self) -> None:
        for bearing in (0.0, 45.0, 137.0, 270.0):
            for dist in (1.0e3, 2.2e4, 3.0e5):
                lat, lon = geodesic_destination_deg(21.0, 122.0, bearing, dist)
                self.assertAlmostEqual(_haversine_m(21.0, 122.0, lat, lon), dist, delta=1e-4 * dist)
                self.assertAlmostEqual(
                    ef_py.geodesy_initial_bearing_deg(21.0, 122.0, lat, lon) % 360.0, bearing % 360.0, places=6
                )

    def test_geodetic_guide_places_stations_along_great_circles(self) -> None:
        cvn = _minimal_group()["members"][0]
        screen = {**cvn, "member_id": "ddg", "station": {"range_m": 22000.0, "bearing_rel_deg": -30.0}}
        guide = {"latitude_deg": 21.4, "longitude_deg": 123.6}
        entities, meta = expand_group_composition(
            _geo_scenario(guide, axis_deg=90.0, members=[cvn, screen]), project_root=REPO
        )
        by_name = {e["name"]: e for e in entities}
        # The guide hull sits exactly on the declared latitude/longitude.
        lat, lon, _ = ef_py.geodesy_local_to_geodetic(*ANCHOR, *by_name["G__cvn"]["pos"][:2], 0.0)
        self.assertAlmostEqual(lat, 21.4, places=9)
        self.assertAlmostEqual(lon, 123.6, places=9)
        # The screen hull is 22 km from the guide on true bearing 90 - 30 = 60 deg.
        lat2, lon2, _ = ef_py.geodesy_local_to_geodetic(*ANCHOR, *by_name["G__ddg"]["pos"][:2], 0.0)
        self.assertAlmostEqual(_haversine_m(21.4, 123.6, lat2, lon2), 22000.0, delta=1e-3)
        self.assertAlmostEqual(ef_py.geodesy_initial_bearing_deg(21.4, 123.6, lat2, lon2), 60.0, places=6)
        geometry = meta["geometry"]
        self.assertEqual(geometry["placement"], "geodetic")
        self.assertEqual(geometry["anchor_source"], "explicit")
        self.assertEqual(meta["groups"][0]["guide"]["geo"], guide)

    def test_geodetic_guide_requires_a_declared_anchor_and_one_position(self) -> None:
        guide = {"latitude_deg": 21.4, "longitude_deg": 123.6}
        no_anchor = _geo_scenario(guide)
        no_anchor["environment"] = {}
        both = _geo_scenario(guide)
        both["groups"][0]["guide"]["pos"] = [0.0, 0.0, 0.0]
        pole = _geo_scenario({"latitude_deg": 90.0, "longitude_deg": 0.0})
        stray = _geo_scenario({**guide, "height_m": 3.0})
        for label, scenario in {"no anchor": no_anchor, "pos and geo": both, "pole": pole,
                                "unknown geo key": stray}.items():
            with self.subTest(case=label), self.assertRaises(ValueError):
                validate_group_composition(scenario, project_root=REPO)


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
        self.assertEqual(merged["meta"]["csg"]["schema"], "csg.group_composition.v2")
        self.assertEqual(merged["meta"]["csg"]["geometry"]["placement"], "local")
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
        self.assertEqual(kernel.get_geodetic_anchor(), ANCHOR)
        self.assertEqual(meta["geometry"]["placement"], "geodetic")
        source = json.loads(Path(path).read_text(encoding="utf-8"))
        declared = {g["group_id"]: g for g in source["groups"]}
        for group in meta["groups"]:
            gid = group["group_id"]
            # Every hull maps back, through the runtime projection, to the great-circle
            # point its station names.
            guide = declared[gid]["guide"]
            glat, glon = guide["geo"]["latitude_deg"], guide["geo"]["longitude_deg"]
            stations = {m["member_id"]: m.get("station") for m in declared[gid]["members"]}
            axis = math.radians(guide["axis_deg"])
            for row in group["ships"]:
                st = stations[row["member_id"]]
                count = len(row["entity_names"])
                rel = math.radians(guide["axis_deg"] + st.get("bearing_rel_deg", 0.0))
                for n, name in enumerate(row["entity_names"]):
                    # Station offset from the guide, hulls spaced across the axis.
                    lateral = (n - (count - 1) / 2.0) * st.get("spacing_m", 0.0)
                    dx = st.get("range_m", 0.0) * math.sin(rel) + lateral * math.cos(axis)
                    dy = st.get("range_m", 0.0) * math.cos(rel) - lateral * math.sin(axis)
                    x, y, _z = kernel.get_unit_position(int(loader.entities[name]))
                    lat, lon, _ = ef_py.geodesy_local_to_geodetic(*ANCHOR, x, y, 0.0)
                    self.assertAlmostEqual(
                        _haversine_m(glat, glon, lat, lon), math.hypot(dx, dy), delta=0.5, msg=name
                    )
                    if math.hypot(dx, dy) > 1.0:
                        self.assertAlmostEqual(
                            ef_py.geodesy_initial_bearing_deg(glat, glon, lat, lon),
                            math.degrees(math.atan2(dx, dy)) % 360.0, delta=1e-4, msg=name,
                        )
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
        units = {int(u.id): u for u in kernel.get_all_units()}
        for group in meta["groups"]:
            gid = group["group_id"]
            side = int(ef_py.Side.Blue if group["side"] == "Blue" else ef_py.Side.Red)
            group_units = [u for u in units.values() if int(u.side) == side]
            self.assertEqual(len(group_units), EXPECTED[gid]["hulls"] + EXPECTED[gid]["stowed_helos"], gid)
            self.assertEqual(sum(int(u.type) == int(ef_py.UnitType.Aircraft) for u in group_units),
                             EXPECTED[gid]["stowed_helos"], gid)
            for row in group["ships"]:
                for name in row["entity_names"]:
                    self.assertEqual(int(units[int(loader.entities[name])].side), side, name)

        # Use the declared duration. The first tick pins automatically spawned
        # stowed helicopters to their host; hulls must remain static from spawn.
        before = {n: kernel.get_unit_position(int(i)) for n, i in loader.entities.items()}
        self.assertAlmostEqual(kernel.get_time_step(), source["environment"]["time_step"])
        settled = None
        for _ in range(source["environment"]["max_steps"]):
            kernel.step()
            current = {int(u.id): (float(u.x), float(u.y), float(u.z)) for u in kernel.get_all_units()}
            self.assertEqual(set(current), set(units))
            for name, pos in before.items():
                after = current[int(loader.entities[name])]
                self.assertLess(max(abs(a - b) for a, b in zip(after, pos)), 1.0e-6, name)
            if settled is None:
                settled = current
            for eid, pos in current.items():
                self.assertTrue(all(math.isfinite(v) for v in pos), eid)
                self.assertLess(max(abs(a - b) for a, b in zip(pos, settled[eid])), 1.0e-6, eid)

    def test_named_variant_spawns_the_full_order_of_battle(self) -> None:
        self._check(NAMED, {"BLUE_CSG12", "RED_CV18"})

    def test_groups_face_each_other_along_the_great_circle(self) -> None:
        # Each group's threat axis is the initial great-circle bearing to the other
        # guide, so the two screens face each other on the sphere.
        for path in (NAMED, MIRROR):
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            blue, red = data["groups"]
            b, r = blue["guide"], red["guide"]
            bg, rg = b["geo"], r["geo"]
            to_red = ef_py.geodesy_initial_bearing_deg(
                bg["latitude_deg"], bg["longitude_deg"], rg["latitude_deg"], rg["longitude_deg"])
            to_blue = ef_py.geodesy_initial_bearing_deg(
                rg["latitude_deg"], rg["longitude_deg"], bg["latitude_deg"], bg["longitude_deg"])
            self.assertAlmostEqual(b["axis_deg"], to_red, delta=0.05, msg=path)
            self.assertAlmostEqual(r["axis_deg"], to_blue, delta=0.05, msg=path)

    def test_mirror_variant_fields_the_same_platform_set_on_both_sides(self) -> None:
        self._check(MIRROR, {"BLUE_CSG12", "RED_MIRROR_CSG12"})
        data = json.loads(Path(MIRROR).read_text(encoding="utf-8"))
        blue, red = data["groups"]
        strip = lambda g: [(m["oob_row"], m["type"], m.get("count", 1)) for m in g["members"]]  # noqa: E731
        self.assertEqual(strip(blue), strip(red))
        self.assertEqual((blue["side"], red["side"]), ("Blue", "Red"))


if __name__ == "__main__":
    unittest.main()
