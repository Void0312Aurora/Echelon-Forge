# A2 MLF-5 Target Component Vulnerability And Failure Acceptance

Status: `2026-06-11` accepted / archived.

Chinese main text: [missile_lethality_component_failure_acceptance_20260611.zh.md](missile_lethality_component_failure_acceptance_20260611.zh.md)

## Acceptance Conclusion

MLF-5 is accepted as a target component vulnerability and failure fact chain. It
closes the path from post-detonation component load / cut exposure to component
damage facts:

- Same-chain component load or cut exposure can produce standard component
  damage facts.
- Component damage facts include component name, system, redundancy group,
  failure probability, random sample, failure mode, severity, and before/after
  integrity.
- Positive probability is not recorded as failure by itself; component damage
  events are exported only when the sample triggers and state is written.
- No-detonation, no component load, no positive load, and untriggered samples do
  not create false component failure.
- Component state changes are written into the existing damage state so
  maintained flight-dynamics, propulsion, sensor, and system models propagate
  consequences.
- Diagnostics explain component damage without promoting it to crash,
  structural breakup, debris/wreck, Pk, or training win/loss.

## Accepted Evidence

- Main evidence package: [README.md](README.md)
- Read-only inventory: [missile_lethality_component_failure_inventory_20260611.md](missile_lethality_component_failure_inventory_20260611.md)
- Current status: [missile_lethality_component_failure_current_status_20260611.md](missile_lethality_component_failure_current_status_20260611.md)
- Task-cluster boundary: [missile_lethality_component_failure_task_clusters_20260611.md](missile_lethality_component_failure_task_clusters_20260611.md)
- Dispatch record: [missile_lethality_component_failure_dispatch_queue_20260611.md](missile_lethality_component_failure_dispatch_queue_20260611.md)
- Expanded aspect/distance matrix: [missile_lethality_component_failure_expanded_matrix_20260611.md](missile_lethality_component_failure_expanded_matrix_20260611.md)

## Test Evidence

- [test_component_damage_event_surface.py](../../../../../../../tests/runtime/air_combat/test_component_damage_event_surface.py): standard component damage event surface, sample-trigger gate, before/after integrity, and Python binding.
- [test_component_failure_probability_surface.py](../../../../../../../tests/runtime/air_combat/test_component_failure_probability_surface.py): generic failure probability varies with load, cut exposure, proximity fragment/blast loading, redundancy, prior damage, and authorized evidence rows.
- [test_warhead_spatial_component_projection.py](../../../../../../../tests/runtime/air_combat/test_warhead_spatial_component_projection.py): upstream warhead/spatial/component load fact projection.
- [test_live_detonation_event_surface.py](../../../../../../../tests/runtime/air_combat/test_live_detonation_event_surface.py): live detonation event-surface regression.
- [test_diagnostics_probe_contracts.py](../../../../../../../tests/runtime/air_combat/test_diagnostics_probe_contracts.py): diagnostics schema v2, `component_damage` stage, standard-event priority, and untriggered-sample guard.

Closeout verification commands:

```bash
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat/test_diagnostics_probe_contracts.py tests/runtime/air_combat/test_component_damage_event_surface.py tests/runtime/air_combat/test_component_failure_probability_surface.py tests/runtime/air_combat/test_warhead_spatial_component_projection.py tests/runtime/air_combat/test_live_detonation_event_surface.py -q
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat -q -k "component_damage or vulnerability or component_failure"
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_component_failure docs/task/air_combat/a2_high_fidelity_damage_model/README.md docs/task/air_combat/a2_high_fidelity_damage_model/README.zh.md docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_continuous_rod/README.md docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_continuous_rod/README.zh.md tools/diagnostics/air_combat_weapon_employment_process_probe.py tests/runtime/air_combat/test_diagnostics_probe_contracts.py
```

Latest recorded result after the binding-default cleanup, generic
proximity-miss probability retune, and debug-hit sampling seed repair:
diagnostics `26 passed`; combined regression `42 passed`; broad selected run
`41 passed, 282 deselected, 7 subtests passed`. The distance/aspect probe
confirms that, with a 35 m radius setting, blast/fragmentation leaves projection
after about 15.75 m and continuous rod after about 11 m; with good beam-side
exposure, continuous rod y=6 m theoretical probability is `0.347818` and the
256-seed any-component trigger rate is `0.527344`, while y=12 m edge trigger
rate drops to `0.015625` and y=16 m has no projection. The expanded matrix also
covers nose, tail, top, bottom, and diagonal aspects and confirms that aspect
changes the result. The previous nanobind
shutdown leak warning was traced to binding/test helper default objects and no
longer appears in the collect-only or runtime closeout reruns.

## Explicitly Not Accepted

- Structural breakup, airframe rupture, or airborne fragmentation are not
  accepted. They belong in MLF-6.
- Debris/wreck or fragment object lifecycle is not accepted. It belongs in
  MLF-8.
- Pk, training win/loss, entity deletion, or mission-cycle closure is not
  accepted.
- Real AIM-120C/MQ-9 or any weapon/target-specific lethality conclusion is not
  accepted.
- No shortcut rule such as "if this component fails, crash immediately" is
  accepted.

## Follow-On Entry

MLF-5 is closed and has no further dispatch. Later work that turns component
failure into airframe rupture, wreck/debris lifecycle, Pk, or weapon-specific
calibration should create a separate `docs/agent` subproject and consume this
package's component damage facts instead of adding more rules inside MLF-5.
