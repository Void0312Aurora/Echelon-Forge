# T7 I89 Residual Disposition (2026-07-27)

Language:
- English canonical: `t7_i89_residual_disposition_20260727.md`
- Chinese companion: [t7_i89_residual_disposition_20260727.zh.md](t7_i89_residual_disposition_20260727.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/plan/unified_architecture_program/t7_i89_residual_disposition_20260727.md`
Owner: `unified architecture program workline`
Last verified: `2026-07-27`
Baseline commit: `b2cec611`

Status: classification component of the I89 narrow repair pack for findings
from the I88 final-residual-audit pass. The same I89 pack also owns the
`sensor_refs` parity repair and the T8/T9 maintained-document corrections;
this note neither promotes a held surface nor authorizes cleanup. The note
itself changes no runtime behavior, generated artifact, worktree, or Git
metadata.

## 1. Classification Rules

- **Fixed** means the narrow defect has an existing repair owner and evidence;
  this document does not reimplement or absorb that repair.
- **Intentional** means two surfaces remain distinct because they serve
  different contracts and a gate prevents accidental drift.
- **Held** means the repository lacks a named semantic decision, domain
  authority, performance result, or destructive-operation approval. A held
  item is not permission to delete, normalize, or silently broaden it.
- **Uneconomic** means a safe convergence exists in principle but its current
  maintenance risk is lower than the churn and compatibility cost.

## 2. Program-Surface Dispositions

| ID | Surface and evidence | Disposition | Owner | Missing authority or evidence | Next gate |
|---|---|---|---|---|---|
| D-01 | T1 GPU packed views remain handwritten: `src/gpu/gpu_execution_observation_runtime.h` (`InstrumentPacked`/`MissionPacked`), `gpu_interaction_broadphase_runtime.h`, and `gpu_visual_runtime.h`. They are not registered in `tools/maintenance/dto_schema`. | **Held** | T1 DTO schema workline jointly with the exact-runtime/GPU backend owner | A maintained GPU layout/ABI authority and an accepted projection contract. Current GPU helpers are not canonical simulation truth. | Reopen only after the exact-runtime line accepts a maintained GPU layout, then generate the packed views from the same schema groups as their CPU descriptions with ABI/byte parity and freshness gates. |
| D-02 | T2 I83 extracted only the measured observation/evidence seam into `WorldBatchCore`; single, leader, and cooperative callers retain mode-specific episode, leader, shared-memory, and compatibility behavior in `python/rl/runtime/{single_world_batch_runtime.py,leader_world_batch_runtime.py,cooperative_world_batch_vec_env.py}`. | **Held** | T2 runtime-substrate owner with the T4 exact-runtime owner | Representative parity and performance evidence for moving the remaining mode-specific ownership without breaking active callers or monkeypatch seams. | Reopen with a measured duplicate slice and a shrink-only caller inventory after the WP4 controller/default decision; no speculative plugin methods. |
| D-03 | T5 naval active configs under `examples/config/training/active/naval/` are N4 entry/runtime smoke gates, not general training-matrix products, and therefore are not in the air-combat/cooperative `Experiment` generators. | **Held** | Naval N4 domain owner and T5 experiment-space owner | Domain acceptance that freezes a naval evaluation protocol and authorizes these smoke gates to become typed experiment products. | A naval Experiment slice must preserve the three paths byte-for-byte, add a registry/freshness gate, and retain the N4 no-weapon/no-damage claim boundary. |
| D-04 | T5 repeats `MATRIX_DIR` once as a module API and once as the `MatrixEntryBase` subclass contract in each of `air_combat_matrix.py` and `cooperative_flight_matrix.py`. Construction/freshness gates fail if the values diverge. | **Intentional / uneconomic** | T5 experiment-space owner | None. The two names serve distinct extension/API contracts; replacing four pinned literals would buy negligible maintenance value. | Revisit only if a third matrix demonstrates real drift or if `MatrixEntryBase` gains one canonical path owner without changing public imports or output bytes. |
| D-05 | T6 weapon-guidance residuals: 33 unique governed nodes (including mixed-subtest `expectedFailure` cases), seven I97 focused calibration assertions, and the diagnostics top-level script-governance strict xfail. Conditional toolchain/GPU skips are capability-scoped. | **Intentional governance; product expectations held** | T6 test-infrastructure owner; damage/calibration owners for product changes | Authoritative calibration or an accepted product-semantics change. Passing unrelated structural assertions must remain active. | Repair one product expectation at a time; strict xfails must XPASS on recovery, and `--runxfail` must still expose the exact residual assertions. Conditional skips may clear only when their declared dependency exists. |
| D-06 | T8 stale candidate/review wording identified by I88 is corrected in this I89 pack: the authoritative inventory now records I87 as accepted/landed. Remaining declared-but-open truth readers are already explicit semantic deferrals, not safe mechanical moves. | **Fixed where textual; remaining semantics held** | T8 information-state owner | For held readers, a typed view with correct empty-list/provenance semantics and domain parity. | Keep the I87 status pinned to the queue/register; migrate each remaining reader only with its own view declaration, raw-read ban, and behavior parity. |
| D-07 | T9 representation review found no valid mapping between echelon authority and action-interface authority. I89 refreshes the stale adapter source pointers; the no-mapping verdict remains unchanged and behavioral convergence cannot start from name similarity. | **Evidence-pointer drift fixed; behavioral slice held** | T9 agency/doctrine owner | Domain evidence for an explicit registered mapping, delegation, and arbitration rule. | Reopen only through the registered authority owner with domain review and a load-bearing mapping gate; otherwise preserve the no-mapping verdict. |
| D-08 | I96 already repaired malformed capability-bundle flags. I89 additionally matches the bounded Python derivation to the C++ loader's `sensor_refs` key-present-and-array branch: an empty array suppresses inline sensor, a non-array falls through, non-string array elements are ignored like the loader, and a non-empty string array emits `sensor_refs`. | **Fixed** | T11 content-compilation owner | None for the audited edge. Broader family expansion remains outside the bounded pilot. | Keep the three-shape plus ignored-element parity test active; any future loader-chain change must update the mirror and reference-path parity together. |
| D-09 | The T11 rollback guard scans the maintained roots selected by the pilot but omits root entry points and `scripts/`; widening it could classify diagnostic/launcher references as default-path wiring. | **Held** | T11 rollback-shell owner | A maintained-caller taxonomy for root entry points and `scripts/`, including explicit diagnostic/tool exemptions. | Extend the scan only together with a positive default-path inventory and injected-offender tests; do not broaden an allowlist merely to keep the gate green. |

## 3. Source TODO Dispositions

The only three source `TODO` comments found by I88 are co-located in
`src/systems/systems/logistics_system.h`. None is a safe textual cleanup.

| ID | TODO | Disposition | Owner | Missing authority or evidence | Next gate |
|---|---|---|---|---|---|
| D-10 | Line 49: set a flag or disable `ActionCommand` when fuel state blocks an action. | **Held** | Logistics behavior owner plus command/tasking contract owner | A decision about which owner records fuel-blocked intent, whether commands are rejected or held, and what diagnostic/event is public. | Add a typed rejection/hold contract and end-to-end command behavior tests before changing command state. |
| D-11 | Line 68: iterate `default_loadout` when replenishing stores. | **Held** | Logistics/store owner plus T11 content owner | Accepted loadout replenishment semantics, magazine capacity rules, and compatibility with the held int-keyed `default_loadout` codec. | Freeze a typed replenishment request/result and fixture parity over authored loadouts before iteration logic. |
| D-12 | Line 92: reduce drag after external-store jettison if drag is tracked. | **Held** | Logistics owner plus aero/flight-model owner | A single drag-state owner and validated external-store drag model; current code cannot infer an authoritative coefficient change from the TODO. | Land a model-owned jettison/drag contract with before/after flight-model parity and domain evidence. |

## 4. Workspace And Git-State Dispositions

| ID | Surface | Disposition | Owner | Missing authority or evidence | Next gate |
|---|---|---|---|---|---|
| D-13 | The main worktree contains 857 untracked entries under 58 `.tmp*`/`.pytest*` directories from I83/I87 runs (11,745 filesystem files, 198.93 MiB). They are generated test artifacts, but the audit did not establish retention or consumer state. | **Held** | Main-worktree operator / artifact producer | Confirmation that each artifact is disposable or reproducible, and approval for deletion or relocation. | Inventory exact producers and recovery route; remove only under explicit cleanup authority. |
| D-14 | Six non-target worktrees are dirty and not byte-identical to the I88 head: Ground (20 modified + 1 untracked), i61 repair (4 staged + 5 unstaged), w14 lineage (10 modified + 1 untracked), w17 botfix (3 modified), w18 botfix (5 modified), and w3 flightshaping (10 modified + 2 untracked). | **Held** | Each worktree/branch owner | Per-worktree ownership, publish/abandon decision, and destructive cleanup approval. | Record HEAD, branch/detached state, status, unique commits, and recovery ref for each; then obtain explicit cleanup direction. Do not prune, reset, move, or delete from this document. |
| D-15 | `git count-objects -vH` reports the empty `.git/worktrees/EF-w24-i88/refs` directory as garbage. That report alone does not authorize shared-metadata mutation or prove the linked worktree is orphaned. | **Held** | Repository/worktree administrator | Approval to mutate shared Git metadata after validating the live I88 worktree's gitdir mapping. | Revalidate with `git worktree list --porcelain` and path/gitdir checks; use an approved Git-native repair only after dirty-worktree reconciliation. |

## 5. Closeout Consequence

I88 is **not a clean pass** because the audit found surfaces that required this
explicit disposition and separately owned narrow repairs. This document closes
only the classification gap: it does not claim that held items are complete or
that I90 may ignore them. I90 must verify the fixed items on its exact checkout
and reproduce every held/intentional classification against current callers,
gates, worktree state, and owner authority.

## 6. Related Authority

- [Unified Architecture Program](README.md)
- [I72+ Iteration Queue](iteration_queue_i72_plus_20260726.md)
- [T6 Residual Ledger](t6_residual_ledger.md)
- [Repository Consolidation Plan](../repository_consolidation/README.md)
- [Exact Runtime Refactor Plan](../exact_runtime/cpp_exact_runtime_refactor_plan.md)
- [Simulation System Architecture Design](../architecture/simulation_system_architecture_design.md)
