"""CSG named-unit content contract (Carrier Strike Group Engagement, S0-C).

The unit loader drops unknown keys and degrades dangling refs silently, so a
clean ``load_database`` proves little. This test holds the CSG records under
``examples/config/database/**/csg/**`` to the S0-C authoring rules:

- names are unique across the whole database and every ref resolves;
- every record carries ``_provenance.sources`` and ``_provenance.parameters``;
- every damage-model component ``system`` tag routes to a damage axis
  (substring match in damage_air.h:152-195, :373-377);
- ``vls_sam`` mounts are SAM-only (the first ready one fires as an air-defence
  missile); a submarine has none;
- each sensor is listed once (the factory attaches ``sensor_refs`` and then
  ``sensor_ref`` without de-duplication);
- every ship, submarine, and aircraft record spawns.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path

ensure_repo_imports()

import ef_py  # noqa: E402

DATABASE = Path(resolve_repo_path("examples", "config", "database"))
REF_KEYS = ("sensor_ref", "engine_ref", "ew_suite_ref", "rcs_profile_ref")
SPAWNABLE = {"Ship", "Submarine", "Aircraft", "C2Node"}
ROUTING_TOKENS = (
    "flight_control", "control", "hydraulic", "radar", "sensor", "rwr", "esm",
    "engineering", "engine", "propeller", "transmission", "fuel", "wing",
    "airframe", "fuselage", "structure", "rotor", "tail", "fire_suppression",
    "fire_bottle", "suppression", "extinguish", "combat", "command", "data_link",
    "vls", "gun", "avionics", "navigation", "mission", "cockpit", "crew",
)
SAM_TOKENS = ("SM-2", "SM-6", "ESSM", "HHQ-9", "HHQ-16")


def _all_records() -> dict[str, list[Path]]:
    seen: dict[str, list[Path]] = {}
    for path in DATABASE.rglob("*.json"):
        if "vulnerability_evidence" in path.parts:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for rec in data.get("units", [data]) if isinstance(data, dict) else data:
            if isinstance(rec, dict) and "name" in rec:
                seen.setdefault(rec["name"], []).append(path)
    return seen


def _csg_records() -> list[tuple[Path, dict]]:
    return [
        (path, json.loads(path.read_text(encoding="utf-8")))
        for path in sorted(DATABASE.glob("**/csg/**/*.json"))
    ]


class CsgContentTests(unittest.TestCase):
    names = _all_records()
    records = _csg_records()

    def test_csg_records_exist_for_both_sides(self) -> None:
        sides = {path.relative_to(DATABASE).parts[-2] for path, _ in self.records}
        self.assertEqual(sides, {"us", "cn"})
        self.assertGreaterEqual(len(self.records), 100)

    def test_names_are_unique_across_the_database(self) -> None:
        dupes = {n: [str(p) for p in ps] for n, ps in self.names.items() if len(ps) > 1}
        self.assertEqual(dupes, {})

    def test_every_ref_resolves(self) -> None:
        missing = []
        for path, rec in self.records:
            refs = [rec.get(k) for k in REF_KEYS if rec.get(k)]
            refs += list(rec.get("sensor_refs") or [])
            refs += list((rec.get("default_loadout") or {}).values())
            helo = (rec.get("embarked_air_ops") or {}).get("helo_unit_name")
            refs += [helo] if helo else []
            missing += [(path.name, r) for r in refs if r not in self.names]
        self.assertEqual(missing, [])

    def test_every_record_carries_provenance(self) -> None:
        bad = [p.name for p, r in self.records
               if not (r.get("_provenance") or {}).get("sources")
               or not (r.get("_provenance") or {}).get("parameters")]
        self.assertEqual(bad, [])

    def test_damage_components_route_to_an_axis(self) -> None:
        dead = []
        for path, rec in self.records:
            for hb in (rec.get("damage_model") or {}).get("hitboxes", []) or []:
                for comp in hb.get("components", []) or []:
                    if not any(tok in str(comp.get("system", "")) for tok in ROUTING_TOKENS):
                        dead.append((path.name, comp.get("name"), comp.get("system")))
        self.assertEqual(dead, [])

    def test_spawnable_records_have_hitboxes(self) -> None:
        bad = [p.name for p, r in self.records
               if r.get("type") in SPAWNABLE and not (r.get("damage_model") or {}).get("hitboxes")]
        self.assertEqual(bad, [])

    def test_vls_sam_mounts_hold_sam_rounds_only(self) -> None:
        for path, rec in self.records:
            mounts = [m for m in (rec.get("naval_weapon_system") or {}).get("mounts", [])
                      if m.get("weapon_type") == "vls_sam"]
            if rec.get("type") == "Submarine":
                self.assertEqual(mounts, [], path.name)
                continue
            if not mounts:
                continue
            sam_load = sum(
                int(w.get("representative_load") or w.get("count") or 0)
                for w in (rec.get("_real_world") or {}).get("weapon_inventory", [])
                if any(t in str(w.get("weapon_ref") or w.get("weapon")) for t in SAM_TOKENS)
            )
            self.assertEqual(sum(m["ready_count"] for m in mounts), sam_load, path.name)

    def test_each_sensor_is_listed_once(self) -> None:
        bad = [p.name for p, r in self.records
               if r.get("sensor_ref") and r["sensor_ref"] in (r.get("sensor_refs") or [])]
        self.assertEqual(bad, [])

    def test_every_platform_record_spawns(self) -> None:
        kernel = ef_py.SimulationKernel()
        kernel.reset(1)
        self.assertTrue(kernel.load_database(str(DATABASE)))
        failed = []
        for path, rec in self.records:
            kind = rec.get("type")
            if kind not in SPAWNABLE:
                continue
            z = 3000.0 if kind in {"Aircraft", "C2Node"} else (-60.0 if kind == "Submarine" else 0.0)
            eid = int(kernel.spawn_unit(ef_py.Side.Blue, rec["name"], 0.0, 0.0, z,
                                        0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
            if eid <= 0:
                failed.append(rec["name"])
        self.assertEqual(failed, [])


if __name__ == "__main__":
    unittest.main()
