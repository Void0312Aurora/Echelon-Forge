# A8-W1 Shot Record Contract

Status: `2026-06-07` W1 contract note for `A8-DEC-C Shot Effect Record`.

## Boundary

W1 freezes the smallest inspectable shot record without adding new public event
fields. The record shape is the linked trio already exported by the runtime:

```text
EffectsEvent
-> DamageReport where source_event_id == EffectsEvent.event_id
-> DiagnosticsTrace linking effects_event_id and damage_report_id
```

This is a record contract, not a lethality claim. It does not add aerodynamic,
control, or flight-consumer behavior; it does not add a direct crash rule; and
it does not claim probability-of-kill, deterministic fuze truth, or stock
AIM-120C authority.

## Minimum Stages

The W1 shot record explains these stages:

| Stage | Public fields |
| --- | --- |
| Fuze result | `trigger_type`, `outcome_state`, `fuze_type`, `fuze_trigger_radius_m`, `fuze_delay_s`, `fuze_reliability`, `fuze_effective_reliability`, contact-fuze fields when applicable |
| Detonation geometry | `detonation_time_s`, `nearest_approach_time_s`, `miss_distance_m`, `detonation_local_*`, `detonation_*_deg`, `closure_mps`, `missile_axis_*` |
| Warhead action | `effect_family`, `warhead_*`, `mechanism_*`, `warhead_spatial_*`, `warhead_orientation_*` |
| Affected part | `component_primary_*`, `component_hit_count`, `component_mechanism_load_rows` |
| Damage-mode entry | mechanism vector plus `component_failure_probability*` on the event and matching component row |
| Consequence hook | `DamageReport.source_event_id`, `platform_damage_state_delta`, kill/status booleans, and `DiagnosticsTrace.effects_event_id` / `damage_report_id` |

`component_failure_probability*` is only the W1 damage-mode entry point. The
concrete physical vocabulary such as cut, puncture, deformation, leak, pressure
loss, data loss, fire source, or structural weakening belongs to A8-W2.

## Negative Case

For `fuze_no_detonation` or equivalent non-detonating outcomes, the record still
keeps fuze and geometry evidence, but it must not fabricate component rows,
mechanism loads, warhead spatial samples, or damage-report deltas.

## Integration Notes

- W2 should attach concrete damage vocabulary after this shape, preferably from
  component rows or a compatible extension of the component result surface.
- W3 validation fixtures should assert the linked record rather than only final
  health, alive/dead state, or an isolated missile smoke result.
- Later consumer integration remains held for A8-DEC-E.
