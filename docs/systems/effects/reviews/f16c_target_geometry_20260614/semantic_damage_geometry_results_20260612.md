# TG-P6-R12 Semantic Damage Geometry Implementation

Status: `2026-06-12` applied / parse-ready candidate / active runtime
activation held. Chinese canonical:
[semantic_damage_geometry_results_20260612.zh.md](semantic_damage_geometry_results_20260612.zh.md).

This round starts converting the semantic outer shell into damage-model component
geometry instead of leaving it as a visual-only overlay.

## Implemented

| Slice | Implementation | Boundary |
| --- | --- | --- |
| Semantic volume candidates | Added [semantic_damage_geometry_candidate_20260611.json](review_packets/f16c_20260611/semantic_damage_geometry_candidate_20260611.json) and [semantic_damage_geometry_candidate_20260611.csv](review_packets/f16c_20260611/semantic_damage_geometry_candidate_20260611.csv). The packet now has `14` semantic outer-shell volume components: radome, forward fuselage skin, canopy, center fuselage skin, intake, aft engine bay skin, nozzle, both wings, both wing-root fairings, both horizontal tails, and vertical tail. | Candidate geometry only; `runtime_active_component_count=0`. |
| Isolated semantic views | Retired intermediate semantic views. Each semantic volume had its own top/side/front page with the volume proxy and linked receiver component boxes. | Review-only visual evidence; not a collision mesh. |
| Runtime component schema | Extended `DamageComponent` with `geometry_primitive`, source refs, OBB axes/half-extents, thin-prism metadata, and vertices. The unit loader parses the nested `geometry` object emitted by the candidate packet. | Backward-compatible: old components still default to `aabb`. |
| Runtime component geometry use | Component direct-hit and spatial-projection distance/exposure helpers now read OBB/thin-prism support geometry, and use convex-hull vertices as an axis-aligned support envelope until a closed audited hull exists. | Does not claim true 3D hull/path intersection or real F-16 engineering geometry. |

## Packet Summary

- Semantic volume components: `14`.
- Runtime parse-ready component candidates: `14`.
- Active runtime semantic components: `0`.
- Geometry primitive mix: `convex_hull`, `obb`, and `thin_prism`.
- Cross-region handoff held count: `8`, from `engine_core` and
  `wing_spar_center` receiver ownership.

## Remaining Boundary

- The current F-16 unit file still has `26` active runtime components. The R12
  semantic volumes are emitted as `runtime_component_json_candidate` records for
  controlled activation, not silently injected into live lethality behavior.
- `engine_core` remains a cross-region boundary candidate across intake, aft
  engine bay, and nozzle semantics.
- `wing_spar_center` remains a cross-region structural semantic hold across
  center fuselage, wing roots, and wing skins.
- `convex_hull` currently means simplified mesh-proxy support vertices. It is
  not yet a closed collision hull or swept path intersection target.

## Verification

```bash
python tools/geometry/airframe_geometry_review.py --out docs/systems/effects/reviews/f16c_target_geometry_20260614/review_packets/f16c_20260611
pytest -q tests/tools/test_airframe_geometry_review.py
cmake --build build-workshop --target ef_test -j2
./build-workshop/ef_test --test-suite=components_basic
pytest -q tests/architecture/damage_model
```

Focused results: `2 passed`; `ef_test --test-suite=components_basic` passed
`23` cases; architecture damage-model suite passed `177` tests.
