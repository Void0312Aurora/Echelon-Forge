# A2 MLF-3 Current Status

Status: `2026-06-10` MLF-3 standard load chain focused accepted. The third phase has its own subproject; the MLF-3A read-only inventory is accepted, real detonation paths export standard warhead/spatial/component-load events, no-detonation paths no longer emit standard load events, and range/direction/family/spatial coverage now have standard-load variation gates. Real-weapon calibration, structural breakup, debris/wreck, and Pk are not complete.

Chinese main text: [missile_lethality_warhead_effects_current_status_20260609.zh.md](missile_lethality_warhead_effects_current_status_20260609.zh.md)

## Maturity Matrix

| Area | Status | Evidence | What This Does Not Prove |
| --- | --- | --- | --- |
| MLF-2 input | accepted / archived | [MLF-2 pointer](../../../missile_lethality_geometry_fuze/README.md) | Warhead effects are not high-fidelity yet |
| MLF-3A inventory | accepted | [Inventory acceptance record](missile_lethality_warhead_effects_inventory_20260609.md) | Does not prove all writers or diagnostics are complete |
| Standard event structs | live gate focused pass | `WarheadMechanismEvent`, `SpatialCoverageEvent`, and `ComponentLoadEvent` exist in contracts, bindings, event-store writers, and real detonation-path tests | Parameters are not calibrated |
| Current effects model | generic load-shape focused pass | `default_effects_model`, `default_effects_warhead_detail.inc`, `default_effects_spatial_projection_detail.inc`; 3C focused tests prove range / direction / family change standard load facts | Stage boundaries are not standardized and parameters are not calibrated |
| Spatial/component projection | focused pass | Euclid read-only audit confirmed the minimum entry point; `test_warhead_spatial_component_projection.py` proves spatial coverage / local projection changes standard `ComponentLoadEvent` component, distance, effect scale, fragment density, and blast overpressure | Component failure probability, structural breakup, debris/wreck, Pk, and type-specific calibration are not complete |
| Diagnostics projection | standard-event priority / focused pass | Process probe now reads standard warhead / spatial / component-load events first, with old `EffectsEvent` as same-chain fallback; other chains can still fall back | Target vulnerability and structural failure are not complete |
| Runtime handoff gate | no-detonation focused pass | `fuze_no_detonation` and `fuze_no_terminal_track` do not promote into standard warhead/spatial/component-load events | Target vulnerability and structural failure are not complete |
| Research data rule | boundary fixed | Only generic, uncalibrated, replaceable data and methods are allowed in this phase | Does not prove type-specific parameter truth |
| Third-phase subproject | focused accepted | README, status, task clusters, dispatch queue, acceptance record, and archive index are synced to `MLF-3G` | The whole high-fidelity lethality model is not complete |

## Current Conclusion

The second phase is archived. The third phase is not another fuze-radius adjustment and not a direct crash rule; it must turn post-detonation effects into inspectable load facts.

Current code already has reusable scaffolding: warhead profiles, spatial projection, mechanism-load fields, component-load fields, and historical Phase 3 tests. This round projects post-detonation load facts from old `EffectsEvent` into standard warhead / spatial / component-load events; ordinary debug hits with no component rows do not invent component events; no-detonation `EffectsEvent` rows still preserve diagnostics facts but no longer promote into standard load events.

This 3C pass added no runtime fields or default parameters. It uses synthetic profile fixtures to pin the existing generic engineering-assumption load surface: miss distance / range, direction/aspect, and warhead family change fragment energy, areal density, blast overpressure, impulse, and component loads in standard events. The read-only audit confirmed that DTOs still lack per-default source category / scope / unit / uncertainty / replacement-rule metadata, so these constants remain generic research assumptions only.

This 3D pass changed no core effects model or standard event fields. Euclid confirmed the existing spatial projection path already generates component candidates and component-load source rows, while Fermat's focused test proves right-side near/far and mirrored local projection change standard component-load facts. This only proves that component load can be read from standard events; it does not prove component failure, crash, or entity deletion.

This phase follows the research data rule: use only generic blast/fragment methods, engineering-order values, proxy-source category hints, and synthetic test values. Every default must label source category, evidence level, scope, unit, uncertainty, and replacement rule.

## Near-Term Tasks

1. Future MLF-4/5/6/8/9 work should consume MLF-3 standard load facts, not treat them as direct kill conclusions.
2. Keep all parameter work under the generic research data rule; do not claim type-specific truth.
3. Structural breakup, debris/wreck, Pk, type-specific calibration, and full per-default metadata remain held.

## Retained Boundaries

- No continuous-rod cutting.
- No structural breakup, fragments, wreck/debris, or entity deletion.
- No real AIM-120C/MQ-9 case lethality claim.
- No conversion from mechanism load to training win/loss facts.
- No writing generic research parameters as type-specific truth.
