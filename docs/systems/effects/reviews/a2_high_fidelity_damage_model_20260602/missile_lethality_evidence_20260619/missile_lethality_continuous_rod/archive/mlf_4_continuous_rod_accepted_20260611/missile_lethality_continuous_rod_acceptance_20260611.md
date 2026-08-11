# A2 MLF-4 Continuous-Rod Cutting Acceptance

Status: `2026-06-11` accepted / archived.

Chinese main text: [missile_lethality_continuous_rod_acceptance_20260611.zh.md](missile_lethality_continuous_rod_acceptance_20260611.zh.md)

## Acceptance Conclusion

MLF-4 is accepted as a continuous-rod/cutting exposure fact chain. It closes the
path from post-detonation mechanism facts to diagnosable cut exposure:

- `continuous_rod` detonations produce same-chain positive rod/cut facts.
- Non-rod warheads do not produce positive rod/cut facts.
- No-detonation paths are not backfilled into false warhead, spatial coverage,
  or component cut rows.
- Cut facts vary with range, side/aspect, orientation, and component projection.
- Component-load rows expose cut exposure but do not claim component failure,
  airframe breakup, crash, or entity deletion.
- Diagnostic snapshots carry both mechanism-level and component-level
  `rod_cut_margin` for later consumers.

## Accepted Evidence

- Inventory evidence: [missile_lethality_continuous_rod_inventory_20260610.md](missile_lethality_continuous_rod_inventory_20260610.md)
- Current status: [missile_lethality_continuous_rod_current_status_20260610.md](missile_lethality_continuous_rod_current_status_20260610.md)
- Dispatch record: [missile_lethality_continuous_rod_dispatch_queue_20260610.md](missile_lethality_continuous_rod_dispatch_queue_20260610.md)
- Task-cluster boundary: [missile_lethality_continuous_rod_task_clusters_20260610.md](missile_lethality_continuous_rod_task_clusters_20260610.md)
- Main evidence package: [README.md](README.md)

## Test Evidence

- `test_continuous_rod_event_surface.py`: standard rod/cut event surface.
- `test_continuous_rod_geometry_response.py`: range, side/aspect, and orientation response.
- `test_continuous_rod_component_cut_projection.py`: component cut exposure projection.
- `test_continuous_rod_diagnostic_projection.py`: diagnostic explanation, non-rod zero cut, and no-detonation no false rod rows.
- `test_diagnostics_probe_contracts.py`: diagnostic field contract regression.

Closeout verification commands:

```bash
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat/test_continuous_rod_diagnostic_projection.py tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat -q -k "mlf4 or continuous_rod or rod_cut"
git diff --check -- docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_continuous_rod tools/diagnostics/air_combat_weapon_employment_process_probe.py tests/runtime/air_combat/test_continuous_rod_diagnostic_projection.py
```

## Explicitly Not Accepted

- Component failure probability is not accepted. It belongs in MLF-5.
- Structural breakup, airframe slicing, or airborne fragmentation is not
  accepted. It belongs in MLF-6.
- Debris/wreck object lifecycle is not accepted. It belongs in MLF-8.
- Pk or statistical kill probability is not accepted. It belongs in MLF-9.
- Real AIM-120C/MQ-9 or any weapon/target-specific lethality conclusion is not
  accepted.

## Follow-On Entry

MLF-4 is closed and has no further dispatch. If later work should turn cut
exposure into actual damage, create MLF-5 as a separate `docs/agent`
subproject and let its component-failure model consume the rod/cut facts from
this package instead of adding rules inside MLF-4.
