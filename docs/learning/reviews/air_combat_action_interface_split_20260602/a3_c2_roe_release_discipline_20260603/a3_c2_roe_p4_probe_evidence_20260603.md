# A3 C2/ROE P4 Probe Evidence - 2026-06-03

Status: `2026-06-03` A3-aware process-probe evidence for M1 review.

Language:

- English canonical: `a3_c2_roe_p4_probe_evidence_20260603.md`
- Chinese companion: [a3_c2_roe_p4_probe_evidence_20260603.zh.md](a3_c2_roe_p4_probe_evidence_20260603.zh.md)

## Scope

This record checks whether the new S1 C2/ROE probe can split missile-release
behavior into authorized and violation categories. It is not a learned-policy
acceptance and it does not release M2.

Scenario/config:

- `scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json`
- `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_shaped_world_batch_probe_v1.json`

## Commands

```powershell
.\tools\maintenance\cmo_env.ps1 python tools/diagnostics/air_combat_weapon_employment_process_probe.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_shaped_world_batch_probe_v1.json --mode forced_fire --episodes 1 --seed 20260603 --max_steps 240 --json_out "$env:TEMP\cmo_a3_p4_forced_fire.json" --csv_out "$env:TEMP\cmo_a3_p4_forced_fire.csv"
```

```powershell
.\tools\maintenance\cmo_env.ps1 python tools/diagnostics/air_combat_weapon_employment_process_probe.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_shaped_world_batch_probe_v1.json --mode switch_explore --episodes 1 --seed 20260603 --max_steps 360 --json_out "$env:TEMP\cmo_a3_p4_switch_explore.json" --csv_out "$env:TEMP\cmo_a3_p4_switch_explore.csv"
```

## Results

| Probe | Steps | Fire attempts | Releases | Authorized releases | Violation releases | Invalid fire attempts | Release steps | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `forced_fire` | 240 | 1 | 1 | 1 | 0 | 0 | `[1]` | First effective release occurs under `roe_state=2` and `authorization_to_fire=1`. |
| `switch_explore` | 360 | 90 | 4 | 1 | 3 | 86 | `[13, 52, 81, 99]` | The same C2/ROE contract splits the first release from later violation releases. |

Additional `switch_explore` summary:

- `release_count_by_authorization_state={"authorized":1,"unauthorized":0,"violation":3,"legacy_or_unknown":0}`
- `min_release_interval_steps=18`
- `fire_under_hold_count=0`
- `legacy_roe_fallback_release_count=0`

## M1 Interpretation

A3 changes the interpretation of repeated release evidence. Raw
`release_count > 1` is no longer enough to call the issue a temporal-memory
failure. The same probe surface can now separate:

- authorized first release;
- later violation releases under a single-shot contract;
- invalid fire attempts without release;
- legacy fallback cases, if a legacy scenario is intentionally used.

The current evidence keeps M2 held. It proves that A3 can classify repeated
release behavior, but it does not show that a learned temporal policy has solved
weapon employment under the C2/ROE contract.
