# A2 MLF-3 Current Status

Status: `2026-06-09` MLF-3B/3E focused pass. The third phase has its own subproject; the MLF-3A read-only inventory is accepted, and MLF-3B standard-event writers plus MLF-3E diagnostics standard-event priority have focused validation. MLF-3 as a whole is not complete.

Chinese main text: [missile_lethality_warhead_effects_current_status_20260609.zh.md](missile_lethality_warhead_effects_current_status_20260609.zh.md)

## Maturity Matrix

| Area | Status | Evidence | What This Does Not Prove |
| --- | --- | --- | --- |
| MLF-2 input | accepted / archived | [MLF-2 pointer](../missile_lethality_geometry_fuze/README.md) | Warhead effects are not high-fidelity yet |
| MLF-3A inventory | accepted | [Inventory acceptance record](missile_lethality_warhead_effects_inventory_20260609.md) | Does not prove all writers or diagnostics are complete |
| Standard event structs | writer focused pass | `WarheadMechanismEvent`, `SpatialCoverageEvent`, and `ComponentLoadEvent` exist in contracts, bindings, and event-store writers | Parameters are not calibrated |
| Current effects model | active scaffold | `default_effects_model`, `default_effects_warhead_detail.inc`, `default_effects_spatial_projection_detail.inc` | Stage boundaries are not standardized and parameters are not calibrated |
| Diagnostics projection | standard-event priority / focused pass | Process probe now reads standard warhead / spatial / component-load events first, with old `EffectsEvent` as same-chain fallback | Broader live geometry gates are not complete |
| Research data rule | boundary fixed | Only generic, uncalibrated, replaceable data and methods are allowed in this phase | Does not prove type-specific parameter truth |
| Third-phase subproject | dispatched | README, status, task clusters, dispatch queue, and archive index; `MLF-3A-X1` is dispatched | MLF-3 implementation is not complete |

## Current Conclusion

The second phase is archived. The third phase is not another fuze-radius adjustment and not a direct crash rule; it must turn post-detonation effects into inspectable load facts.

Current code already has reusable scaffolding: warhead profiles, spatial projection, mechanism-load fields, component-load fields, and historical Phase 3 tests. This round projects post-detonation load facts from old `EffectsEvent` into standard warhead / spatial / component-load events; ordinary debug hits with no component rows do not invent component events.

This phase follows the research data rule: use only generic blast/fragment methods, engineering-order values, proxy-source category hints, and synthetic test values. Every default must label source category, evidence level, scope, unit, uncertainty, and replacement rule.

## Near-Term Tasks

1. Add broader `MLF-3B` live geometry/fuze gates proving real launch detonation paths emit standard events and no-detonation paths do not.
2. Continue into `MLF-3C/3D`: generic blast/fragment loads and spatial/component projection parameter surfaces.
3. Keep all parameter work under the generic research data rule; do not claim type-specific truth.

## Retained Boundaries

- No continuous-rod cutting.
- No structural breakup, fragments, wreck/debris, or entity deletion.
- No real AIM-120C/MQ-9 case lethality claim.
- No conversion from mechanism load to training win/loss facts.
- No writing generic research parameters as type-specific truth.
