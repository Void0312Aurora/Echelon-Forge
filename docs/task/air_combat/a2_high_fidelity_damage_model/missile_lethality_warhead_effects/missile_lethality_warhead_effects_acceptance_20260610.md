# A2 MLF-3 Closeout Acceptance Record

Status: `2026-06-10` closeout accepted / focused load-chain accepted. This record accepts the MLF-3A-G standard load-fact chain; it does not claim the whole missile lethality model is high-fidelity.

Chinese main text: [missile_lethality_warhead_effects_acceptance_20260610.zh.md](missile_lethality_warhead_effects_acceptance_20260610.zh.md)

## Acceptance Result

Pass: MLF-3 can now explain what load a detonated warhead applied, where it was spatially projected, and which components received component-load facts. No-detonation paths do not emit standard warhead-load events.

Held: real weapon calibration, continuous rod, component failure probability, structural breakup, debris/wreck objects, entity deletion, Pk, and training win/loss projection. Current data remains generic, uncalibrated, replaceable research data.

## Accepted Slices

| Slice | Result | Evidence | Boundary |
| --- | --- | --- | --- |
| `MLF-3A` | accepted | Inventory record confirms current warhead / spatial / component fields and writer gaps | Does not prove runtime completion |
| `MLF-3B` | focused pass | Event-store writers, live detonation-path test, and engagement capture tests | Does not calibrate parameters |
| `MLF-3C` | focused pass | `test_mlf3_generic_blast_fragmentation_loads.py` proves range / direction / family change standard load facts | Does not introduce real AIM-120C parameters |
| `MLF-3D` | focused pass | Euclid read-only audit and `test_mlf3_spatial_component_projection.py` prove spatial coverage / local projection changes standard component-load facts | Does not claim component failure or crash |
| `MLF-3E` | focused pass | Process probe prefers standard warhead / spatial / component events, with same-chain old events as fallback only | Does not change reward or win/loss semantics |
| `MLF-3F` | focused pass | No-detonation gate test proves no-detonation paths have no standard load events | Future no-detonation outcomes must keep the gate |
| `MLF-3G` | focused pass | Closeout record, README, status, task clusters, dispatch queue, and archive index state the accepted/held boundary consistently | Does not close later high-fidelity phases |

## Revalidation Commands

```bash
cmake --build build-workshop --target ef_py -j2
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest \
  tests/runtime/air_combat/test_mlf3_spatial_component_projection.py \
  tests/runtime/air_combat/test_mlf3_generic_blast_fragmentation_loads.py \
  tests/runtime/air_combat/test_mlf3_live_detonation_standard_events.py \
  tests/runtime/air_combat/test_mlf3_no_detonation_handoff_gate.py \
  tests/runtime/engagement/test_live_engagement_event_capture.py \
  tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q
```

Result: `37 passed`. The build passed in the revalidation run.

## Held Items

- Standard `ComponentLoadEvent` does not yet expose per-component spatial weight explicitly; spatial influence is read through `effect_scale` and mechanism loads.
- Default constants still lack per-default source category / scope / unit / uncertainty / replacement-rule runtime metadata.
- Structural breakup, debris/wreck, Pk, real weapon parameters, and the AIM-120C/MQ-9 case remain future phases.

## Next Step

Future phases should create separate MLF-4/5/6/8/9 subprojects for continuous rod, component failure probability, structural breakup, debris/wreck, and Pk. MLF-3 outputs are only standard load-fact inputs for those phases.
