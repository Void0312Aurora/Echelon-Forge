# A2 Proximity Fuze Realism Dispatch Queue

Status: `2026-06-16` PF-R5 validation dispatch and PF-R6 closeout complete for
[README.md](README.md).

Chinese companion:
[missile_lethality_proximity_fuze_realism_dispatch_queue_20260616.zh.md](missile_lethality_proximity_fuze_realism_dispatch_queue_20260616.zh.md).

## Queue

| Dispatch | Cluster | Owner | Goal | Write set | Validation | Closure |
| --- | --- | --- | --- | --- | --- | --- |
| `PF-R1` | `PF-P1` | main thread | Write public-source mechanism note with admitted/rejected claims. | `public_mechanism_source_note_20260616.md`; `public_mechanism_source_note_20260616.zh.md` | Source admission inspection, no parameter claims | pass as source-bound planning note |
| `PF-R2` | `PF-P2` | main thread | Write current-runtime gap audit. | `current_runtime_gap_audit_20260616.md`; `current_runtime_gap_audit_20260616.zh.md` | Read-only code/test scan, no runtime diff | pass as gap table |
| `PF-R3` | `PF-P3` | main thread | Write surrogate contract and focused validation plan. | `proximity_fuze_surrogate_contract_20260616.md`; `proximity_fuze_surrogate_contract_20260616.zh.md` | Contract inspection and link check | pass as implementation-ready plan |
| `PF-R4` | `PF-P4` | main thread | Implement accepted surrogate. | Runtime contracts, damage system, Python bindings, diagnostics, focused tests | `ef_py` build; focused runtime, diagnostics, training, binding tests | pass as focused implementation |
| `PF-R5` | `PF-P5` | main thread | Generate focused mechanism comparison matrices. | `validation/pf_r5_proximity_fuze_validation.py`; CSV/JSON/heatmap/summary | Matrix artifacts and summary | pass_with_residuals |
| `PF-R6` | `PF-P6` | main thread | Acceptance closeout. | README/status/acceptance/parent A2 docs | Link check, `git diff --check`, validation summary | pass |

## Dispatch Rules

- `PF-R1` to `PF-R3` are complete.
- `PF-R4` is complete as a focused implementation slice after explicit
  continuation.
- `PF-R5` is complete as a focused surrogate-validation slice; later work may
  not broaden scope from this queue alone.
- A worker must report whether it touched any implementation file. For `PF-R1`
  to `PF-R3`, the expected answer is `no`.
- Any unexpected code diff stops the queue and requires review.

## Held Implementation Trigger

`PF-R4` was opened only after:

- `PF-R1` and `PF-R2` pass; complete on `2026-06-16`;
- `PF-R3` names exact fields, tests, write sets, and expected behavior changes; complete on `2026-06-16`;
- the user explicitly authorized continuation into implementation.

`PF-R5` was opened only for PF-R4 surrogate evidence behavior across trigger
radius, initial lateral/vertical offset, and mechanism family. It did not add
reward tuning, Pk claims, or real fuze calibration. `PF-R6` records the closeout
boundary and keeps the residual live-guidance symmetry note attached.
