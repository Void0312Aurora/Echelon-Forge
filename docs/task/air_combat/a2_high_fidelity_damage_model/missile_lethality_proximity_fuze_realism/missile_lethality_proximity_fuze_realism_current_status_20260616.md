# A2 Proximity Fuze Realism Current Status

Status: `2026-06-16` PF-R5 focused matrix validation complete with residuals.
The subproject has a mechanism note, gap audit, surrogate contract, runtime
explainability implementation, and final validation artifacts.

Chinese companion:
[missile_lethality_proximity_fuze_realism_current_status_20260616.zh.md](missile_lethality_proximity_fuze_realism_current_status_20260616.zh.md).

## Change Since Previous Checkpoint

No previous checkpoint existed before this subproject. This checkpoint now
records the full surrogate pass: PF-R1 public mechanism note, PF-R2 read-only
runtime gap audit, PF-R3 surrogate contract, PF-R4 focused runtime
implementation, and PF-R5 matrix validation.

## Maturity Matrix

| Area | Maturity | Evidence | Next action | Forbidden overclaim |
| --- | --- | --- | --- | --- |
| Subproject boundary | active / validation checkpoint | [README.md](README.md) | Keep PF-R6 closeout synced | Runtime change is limited to the documented surrogate slice. |
| Public-source mechanism | pass / non-authoritative | [public_mechanism_source_note_20260616.md](public_mechanism_source_note_20260616.md) | Review before implementation | Sources do not provide weapon-specific fuze truth. |
| Runtime gap audit | pass / read-only | [current_runtime_gap_audit_20260616.md](current_runtime_gap_audit_20260616.md) | Review before implementation | Current proxy is not a real fuze model. |
| Surrogate contract | pass / implemented design | [proximity_fuze_surrogate_contract_20260616.md](proximity_fuze_surrogate_contract_20260616.md) | Keep authority boundary attached | No real fuze or Pk authority. |
| Implementation | pass / focused runtime evidence | [proximity_fuze_runtime_implementation_20260616.md](proximity_fuze_runtime_implementation_20260616.md) | Keep scope frozen | No deterministic fuze authority or Pk. |
| Validation | pass_with_residuals / focused matrix evidence | [validation/pf_r5_proximity_fuze_validation_20260616.md](validation/pf_r5_proximity_fuze_validation_20260616.md) | Retain final artifacts only | No kill-probability or stock lethality claim. |

## Evidence Links

- Parent A2 pointer: [../README.md](../README.md)
- MLF-2 geometry/fuze pointer:
  [../missile_lethality_geometry_fuze/README.md](../missile_lethality_geometry_fuze/README.md)
- Current implementation surface:
  [../../../../../src/systems/combat/damage_system_common.h](../../../../../src/systems/combat/damage_system_common.h)
- Current focused test entry:
  [../../../../../tests/runtime/air_combat/weapon_guidance_realism/test_launch_guidance_and_dynamics.py](../../../../../tests/runtime/air_combat/weapon_guidance_realism/test_launch_guidance_and_dynamics.py)
- Realism authority boundary:
  [../../../../standards/foundation/realism_authority_boundary.zh.md](../../../../standards/foundation/realism_authority_boundary.zh.md)
- Public mechanism note:
  [public_mechanism_source_note_20260616.md](public_mechanism_source_note_20260616.md)
- Runtime gap audit:
  [current_runtime_gap_audit_20260616.md](current_runtime_gap_audit_20260616.md)
- Surrogate contract:
  [proximity_fuze_surrogate_contract_20260616.md](proximity_fuze_surrogate_contract_20260616.md)
- Runtime implementation result:
  [proximity_fuze_runtime_implementation_20260616.md](proximity_fuze_runtime_implementation_20260616.md)
- PF-R5 validation summary:
  [validation/pf_r5_proximity_fuze_validation_20260616.md](validation/pf_r5_proximity_fuze_validation_20260616.md)
- PF-R5 final heatmap:
  [validation/pf_r5_proximity_fuze_validation_heatmaps_20260616.png](validation/pf_r5_proximity_fuze_validation_heatmaps_20260616.png)

## Residual Register

| Residual | Status | Owner | Resolution path |
| --- | --- | --- | --- |
| Public-source mechanism note missing | closed | main thread | Closed by `PF-P1`. |
| Current runtime gap audit missing | closed | main thread | Closed by `PF-P2`. |
| Future surrogate contract missing | closed | main thread | Closed by `PF-P3`. |
| Implementation approval missing | closed | user/main thread | Closed by explicit continuation into `PF-P4`. |
| Validation matrix not defined | closed_with_residuals | main thread | Closed by PF-R5 CSV/JSON/heatmap/summary artifacts. |
| Initial-offset symmetry not pure | retained residual | future fixed-point harness | Live guidance remains in-loop, so initial launch offsets are not pure detonation-point symmetry tests. |
| Real fuze/Pk authority absent | deferred | future authority package | Separate source-admission and validation package. |

## Recommended Next Actions

1. Retain PF-R5 final CSV, JSON, heatmap, and summaries as the standard
   validation artifact set.
2. Treat initial-offset asymmetry as a live-guidance residual, not as a pure
   fuze-symmetry failure.
3. Keep reward, Pk, and real weapon calibration out of this validation pass.

## Explicitly Refused Claims

- Real AIM-120C or AIM-120C-class deterministic fuze behavior.
- Real Pk, weapon-specific lethality, or stock runtime authority.
- Calibrated target-detecting-device thresholds.
- Treating PF-R4/PF-R5 surrogate evidence as full lethality acceptance.
- Reward or terminal-state tuning as a substitute for fuze-chain realism.
