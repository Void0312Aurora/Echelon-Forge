# WP19-E First CUDA Alignment Slice

Status: `2026-05-21` evidence-only pass / host-owned broadphase slice verified.

Language:

- English canonical: `wp19_first_cuda_alignment_slice_cluster_20260521.md`
- Chinese companion:
  [wp19_first_cuda_alignment_slice_cluster_20260521.zh.md](wp19_first_cuda_alignment_slice_cluster_20260521.zh.md)

Inputs:

- [WP19 main plan](cuda_resident_state_alignment_wp19_20260521.md)
- [WP19-A fact ledger](wp19_cuda_resident_state_fact_ledger_cluster_20260521.md)
- [WP19-B device output contract](wp19_device_resident_output_contract_cluster_20260521.md)
- [WP19-C diagnostics boundary](wp19_gpu_helper_diagnostics_boundary_cluster_20260521.md)
- [WP19-D sync and shard contract](wp19_resident_state_sync_shard_contract_cluster_20260521.md)

## Purpose

Implement one safe CUDA/helper alignment slice only after the first-wave
preflight identifies a bounded path that does not promote exact GPU or
maintained resident-state support.

## Selected Slice

Selected path: `WorldBatchRuntime` interaction broadphase candidate-list
queries for sensor, visual, and comm candidate IDs.

Why this path is safe after A/C/D:

- WP19-A already classifies the `WorldBatchRuntime` candidate-list path as a
  `host-owned helper`: the GPU helper provides candidate bitsets, while host
  code owns decode and final list semantics.
- WP19-C requires helper/probe availability to remain diagnostics-only and to
  avoid promoting maintained capability support.
- WP19-D keeps resident-state and sync ownership fail-closed, which means this
  slice must stay outside any maintained backend-owned state claim.

Rejected alternatives for this stream:

- helper/device-resident output promotion;
- any capability-flag or facade projection change;
- any CUDA helper implementation rewrite;
- any resident-state ownership or sync promotion.

## Scope

In scope:

- one helper/output path selected by A-D, likely visual/observation,
  broadphase metadata, or probe diagnostics;
- additive metadata, guard, or evidence wiring that stays host-owned,
  diagnostics-only, export-only, or observation-only;
- focused tests proving support flags remain false unless maintained evidence
  exists.

Out of scope:

- exact GPU world-step rewrite;
- broad device-resident runtime migration;
- request build/consume migration unless A-D explicitly select a tiny safe seam.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `E1` | Slice selection | A-D evidence selects one bounded helper/output path and rejects unsafe alternatives. |
| `E2` | Implementation | The selected path gains additive metadata, guard, or evidence wiring without changing maintained truth ownership. |
| `E3` | Focused tests | Tests prove behavior and capability non-promotion. |
| `E4` | Residual routing | Broader CUDA, exact GPU, and resident-state ownership residuals are routed forward. |

## Implementation Outcome

Result: no `WorldBatchRuntime` C++ implementation change was required for this
slice.

Current source already satisfies the selected host-owned boundary:

- `run_interaction_broadphase_candidate_ids(...)` chooses CPU vs GPU helper
  bitset production only.
- `decode_broadphase_candidate_ids(...)` reconstructs candidate IDs on the
  host after helper output returns.
- `get_sensor_candidate_ids_batch(...)` and
  `get_visual_candidate_ids_batch(...)` apply host-owned self-exclusion and
  sorting after decode.
- `get_comm_candidate_ids_batch(...)` applies host-owned self-exclusion,
  alliance/network semantic filtering, and sorting after decode.

This means `use_gpu=True` stays an accelerator/helper toggle, not a transfer of
semantic ownership.

## Focused Evidence

Evidence landed in `tests/world_batch/test_world_batch_runtime.py` only.

Locked behavior:

- the selected live candidate-helper scenario now runs with both
  `use_gpu=False` and `use_gpu=True`;
- sensor and visual candidate lists remain identical on the safe bounded case;
- comm candidate lists remain identical on the safe bounded case;
- all three paths still enforce host-owned sorting and self-exclusion;
- comm candidate results still enforce host-owned semantic filtering
  (same-side/same-network friend admitted, foe rejected);
- `RuntimeFacade.capabilities()` remains fail-closed after helper-backed
  candidate queries, including
  `supports_device_observation_view == false`,
  `supports_resident_state == false`,
  `supports_exact_gpu_backend == false`, and
  `device_observation_view_candidate_profile_id ==
  gpu_helpers.diagnostics_only`.

The tests intentionally do not widen the contract to claim that every raw GPU
broadphase bitset must match the CPU reference exactly. That would conflict
with the existing helper-level overflow/superset diagnostics boundary. The
slice contract stays at the `WorldBatchRuntime` host-owned candidate-list
surface.

## Residuals

Residuals explicitly left for later streams:

1. helper-level overflow and superset behavior remains a GPU diagnostics/runtime
   helper concern, not a WP19-E capability or resident-state promotion signal;
2. no device-resident output DTO or export contract is introduced here; that
   remains WP19-B scope;
3. no resident-state sync/barrier ownership is introduced here; that remains
   WP19-D scope;
4. broader exact-GPU, shadow, or maintained backend-profile promotion remains
   blocked.

## Suggested Validation

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "candidate or gpu or broadphase or visual or comm or sensor"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/test_gpu_runtime_bindings.py
```

## Handoff

Return the selected host-owned broadphase slice, evidence that no runtime
ownership changed, focused test results, capability non-promotion evidence, and
residual routing for WP19-F integration.
