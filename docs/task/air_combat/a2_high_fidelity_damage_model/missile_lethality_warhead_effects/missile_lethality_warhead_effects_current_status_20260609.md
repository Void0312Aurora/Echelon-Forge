# A2 MLF-3 Current Status

Status: `2026-06-10` MLF-3B live gate, MLF-3C generic load-shape, MLF-3E diagnostics guard, and MLF-3F no-detonation gate focused pass. The third phase has its own subproject; the MLF-3A read-only inventory is accepted, real detonation paths export standard warhead/spatial/component-load events, no-detonation paths no longer emit standard load events, and range/direction/family now have a standard-load variation gate. MLF-3 as a whole is not complete.

Chinese main text: [missile_lethality_warhead_effects_current_status_20260609.zh.md](missile_lethality_warhead_effects_current_status_20260609.zh.md)

## Maturity Matrix

| Area | Status | Evidence | What This Does Not Prove |
| --- | --- | --- | --- |
| MLF-2 input | accepted / archived | [MLF-2 pointer](../missile_lethality_geometry_fuze/README.md) | Warhead effects are not high-fidelity yet |
| MLF-3A inventory | accepted | [Inventory acceptance record](missile_lethality_warhead_effects_inventory_20260609.md) | Does not prove all writers or diagnostics are complete |
| Standard event structs | live gate focused pass | `WarheadMechanismEvent`, `SpatialCoverageEvent`, and `ComponentLoadEvent` exist in contracts, bindings, event-store writers, and real detonation-path tests | Parameters are not calibrated |
| Current effects model | generic load-shape focused pass | `default_effects_model`, `default_effects_warhead_detail.inc`, `default_effects_spatial_projection_detail.inc`; 3C focused tests prove range / direction / family change standard load facts | Stage boundaries are not standardized and parameters are not calibrated |
| Diagnostics projection | standard-event priority / focused pass | Process probe now reads standard warhead / spatial / component-load events first, with old `EffectsEvent` as same-chain fallback; other chains can still fall back | MLF-3D spatial/component projection parameter surfaces are not complete |
| Runtime handoff gate | no-detonation focused pass | `fuze_no_detonation` and `fuze_no_terminal_track` do not promote into standard warhead/spatial/component-load events | Target vulnerability and structural failure are not complete |
| Research data rule | boundary fixed | Only generic, uncalibrated, replaceable data and methods are allowed in this phase | Does not prove type-specific parameter truth |
| Third-phase subproject | dispatched | README, status, task clusters, dispatch queue, and archive index; `MLF-3A-X1` is dispatched | MLF-3 implementation is not complete |

## Current Conclusion

The second phase is archived. The third phase is not another fuze-radius adjustment and not a direct crash rule; it must turn post-detonation effects into inspectable load facts.

Current code already has reusable scaffolding: warhead profiles, spatial projection, mechanism-load fields, component-load fields, and historical Phase 3 tests. This round projects post-detonation load facts from old `EffectsEvent` into standard warhead / spatial / component-load events; ordinary debug hits with no component rows do not invent component events; no-detonation `EffectsEvent` rows still preserve diagnostics facts but no longer promote into standard load events.

This 3C pass added no runtime fields or default parameters. It uses synthetic profile fixtures to pin the existing generic engineering-assumption load surface: miss distance / range, direction/aspect, and warhead family change fragment energy, areal density, blast overpressure, impulse, and component loads in standard events. The read-only audit confirmed that DTOs still lack per-default source category / scope / unit / uncertainty / replacement-rule metadata, so these constants remain generic research assumptions only.

This phase follows the research data rule: use only generic blast/fragment methods, engineering-order values, proxy-source category hints, and synthetic test values. Every default must label source category, evidence level, scope, unit, uncertainty, and replacement rule.

## Near-Term Tasks

1. Continue into `MLF-3D`: spatial/component projection parameter surfaces on top of the 3C load surface.
2. Keep all parameter work under the generic research data rule; do not claim type-specific truth.
3. Run `MLF-3G` closeout only after 3D returns; do not mark MLF-3 accepted early.

## Retained Boundaries

- No continuous-rod cutting.
- No structural breakup, fragments, wreck/debris, or entity deletion.
- No real AIM-120C/MQ-9 case lethality claim.
- No conversion from mechanism load to training win/loss facts.
- No writing generic research parameters as type-specific truth.
