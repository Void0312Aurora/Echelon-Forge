# TG-P7-R5 Damage-Event Trace Results

Status: `2026-06-14` pass as targeted split-receiver damage-event trace.
All `8` TG-P7 split receivers are observable in the opt-in proxy database
through runtime component event names, while the default database observes none
of those split receiver names.

Chinese canonical:
[target_geometry_damage_event_trace_results_20260614.zh.md](target_geometry_damage_event_trace_results_20260614.zh.md).

## What Ran

```bash
PYTHONPATH=build-workshop:. python tools/geometry/target_geometry_damage_event_trace.py --output docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611/target_geometry_damage_event_trace_20260614.json
PYTHONPATH=build-workshop:. pytest -q tests/tools/test_target_geometry_damage_event_trace.py
```

Generated artifact:

- [target_geometry_damage_event_trace_20260614.json](review_packets/f16c_20260611/target_geometry_damage_event_trace_20260614.json)

## Acceptance Result

| Gate | Result |
| --- | ---: |
| Default F-16 component count | `26` |
| Proxy F-16 component count | `32` |
| Proxy split receiver component count | `8` |
| Proxy observed split receiver count in event names | `8` |
| Default observed split receiver count in event names | `0` |
| Proxy retired parent rows observed | `0` |
| Duplicate proxy component names | `0` |
| Trace cases passed | `8 / 8` |

Observed proxy split receivers:

- `engine_core_afterburner_segment`
- `engine_core_hot_section_segment`
- `engine_core_forward_compressor_segment`
- `wing_spar_center_left_inner_wing_segment`
- `wing_spar_center_left_root_segment`
- `wing_spar_center_carrythrough_segment`
- `wing_spar_center_right_root_segment`
- `wing_spar_center_right_inner_wing_segment`

## Interpretation

R5 proves the TG-P7 opt-in proxy is not only parseable and trainable; the split
receiver identities also reach the runtime `effects_event`,
`component_load_events`, and, when sampled by the fixed seed,
`component_damage_events` surfaces. This closes the targeted trace gap left by
R4.

The trace uses `debug_apply_profiled_local_proximity_hit_with_velocity` with a
synthetic blast-fragmentation profile. It is a geometry/event-surface
acceptance probe, not a real AIM-120 Pk, deterministic fuze, true F-16 internal
layout, or default-path activation claim.

## Next Step

The current model has now completed the next maintained opt-in training slice
as a 32k proxy/baseline comparison:
[target_geometry_training_probe_32k_results_20260614.md](target_geometry_training_probe_32k_results_20260614.md).
Default runtime replacement remains a separate acceptance decision and should
wait for downstream policy/reward diagnostics.
