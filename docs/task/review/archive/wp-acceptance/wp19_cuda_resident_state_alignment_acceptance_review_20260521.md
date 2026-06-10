# WP19 CUDA And Resident-State Mainline Alignment Acceptance Review

Status: `2026-05-21` accepted / implementation mergeable.

Language:

- English canonical:
  `wp19_cuda_resident_state_alignment_acceptance_review_20260521.md`
- Chinese companion:
  [wp19_cuda_resident_state_alignment_acceptance_review_20260521.zh.md](wp19_cuda_resident_state_alignment_acceptance_review_20260521.zh.md)

Inputs:

- [WP19 CUDA And Resident-State Mainline Alignment](../simulation_architecture/wp19_cuda_resident_state_alignment/cuda_resident_state_alignment_wp19_20260521.md)
- [WP19-A CUDA / Resident-State Fact Ledger](../simulation_architecture/wp19_cuda_resident_state_alignment/wp19_cuda_resident_state_fact_ledger_cluster_20260521.md)
- [WP19-B Device-Resident Output Contract Pre-Gate](../simulation_architecture/wp19_cuda_resident_state_alignment/wp19_device_resident_output_contract_cluster_20260521.md)
- [WP19-C GPU Helper Diagnostics Boundary](../simulation_architecture/wp19_cuda_resident_state_alignment/wp19_gpu_helper_diagnostics_boundary_cluster_20260521.md)
- [WP19-D Resident-State Sync And Shard Contract](../simulation_architecture/wp19_cuda_resident_state_alignment/wp19_resident_state_sync_shard_contract_cluster_20260521.md)
- [WP19-E First CUDA Alignment Slice](../simulation_architecture/wp19_cuda_resident_state_alignment/wp19_first_cuda_alignment_slice_cluster_20260521.md)
- [WP19-F Integration And Handoff](../simulation_architecture/wp19_cuda_resident_state_alignment/wp19_integration_handoff_cluster_20260521.md)
- [WP19 dispatch queue](../simulation_architecture/wp19_cuda_resident_state_alignment/wp19_subagent_dispatch_queue_20260521.md)

## 1. Verdict

WP19 is accepted as a bounded CUDA / resident-state mainline alignment
increment. It closes the handoff between existing CUDA helpers,
device-resident output metadata, and resident-state sync vocabulary without
promoting exact GPU world-step execution or maintained resident-state
ownership.

The accepted boundary is intentionally narrow:

- exact GPU, resident-state, shadow, and device-observation support remain
  fail-closed;
- `DeviceResidentOutputDescriptor` stays a standalone export-only DTO;
- `WorldBatchRuntime` broadphase remains a host-owned, evidence-only helper
  slice;
- `gpu_helpers.diagnostics_only` remains diagnostics/export-only and does not
  become maintained capability evidence.

## 2. Gate Verdicts

| Gate | Verdict | Evidence |
|------|---------|----------|
| `WP19-A CUDA / Resident-State Fact Ledger` | pass | The fact ledger freezes helper/probe/capability call sites, keeps support flags fail-closed, and records the current host-owned versus export-only surface split. |
| `WP19-B Device-Resident Output Contract Pre-Gate` | pass | The pre-gate defines the additive export-only `DeviceResidentOutputDescriptor` seam, and `WP19-B2` implements it as a standalone DTO with bindings and focused tests without attaching it to maintained packets or capability projection. |
| `WP19-C GPU Helper Diagnostics Boundary` | pass | Helper/probe availability remains diagnostics/export-only, and helper timing or device-pointer facts do not promote maintained support flags. |
| `WP19-D Resident-State Sync And Shard Contract` | pass | The shard and barrier vocabulary stays host-owned or export-only, while resident-state remains a blocked candidate rather than a maintained surface. |
| `WP19-E First CUDA Alignment Slice` | pass | The selected `WorldBatchRuntime` broadphase candidate-list slice remains host-owned, and `WP19-E1` confirms `use_gpu=True` preserves host filtering semantics and fail-closed capabilities. |
| `WP19-F Integration And Handoff` | pass | The closure lane integrates A-E/B2/E1 results, records validation and residuals, syncs README/review indexes, and creates this acceptance review only after the gates pass. |

## 3. Validation Commands

Recorded main-thread validation from the closure handoff:

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/runtime_facade
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/test_gpu_runtime_bindings.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/runtime_facade/test_runtime_dto_contracts.py -k "device_resident or packet"
cmake --build build-workshop --target ef_py -j4
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/runtime_facade/test_runtime_dto_contracts.py -k "device_resident or packet"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "candidate or gpu or broadphase or visual or comm or sensor"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/test_gpu_runtime_bindings.py
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP19 --summary
```

Observed outcomes:

- `git diff --check`: passed.
- Runtime facade layering: `22 passed`.
- GPU runtime bindings: `12 passed`.
- Runtime DTO contracts batch1 preflight: `2 passed, 4 deselected`.
- `cmake --build build-workshop --target ef_py -j4`: passed.
- Runtime binding DTO surface: `20 passed`.
- Runtime DTO contracts batch1 implementation slice: `3 passed, 4 deselected`.
- World-batch runtime candidate/broadphase slice: `4 passed, 17 deselected`.
- GPU runtime bindings revalidation: `12 passed`.
- `python3 tools/maintenance/wp_doc_closure_audit.py --wp WP19 --summary`: passed, with required Chinese companions present.

## 4. Runtime Surface Summary

- `RuntimeFacade::capabilities()` remains fail-closed for
  `supports_exact_gpu_backend`, `supports_resident_state`,
  `supports_shadow_compare`, and `supports_device_observation_view`.
- `DeviceResidentOutputDescriptor` is a standalone export-only DTO. It does
  not widen maintained packet DTOs or capability projection.
- `WorldBatchRuntime` broadphase candidate-list handling remains host-owned
  helper logic. `use_gpu=True` toggles accelerator candidate-bitset
  production, but host decode, filtering, and sort remain the semantic owner.
- Helper and probe outputs remain diagnostics/export-only evidence. A device
  pointer, CUDA build success, or benchmark speedup does not imply maintained
  promotion.

## 5. Residuals And Next Plan

Residuals intentionally carried forward:

- no maintained device-resident consumer contract or host reconstruction rule
  exists yet;
- helper-level overflow and superset behavior remains a GPU diagnostics
  concern, not a promotion signal;
- exact GPU world-step promotion, maintained resident-state promotion, shadow
  promotion, and public capability-platform composition remain outside WP19;
- future device-resident wiring, if any, must start from a maintained profile
  and a declared reconstruction/export barrier.

WP19 is therefore accepted as a bounded alignment increment, not a broad GPU
promotion or resident-state ownership transfer.
