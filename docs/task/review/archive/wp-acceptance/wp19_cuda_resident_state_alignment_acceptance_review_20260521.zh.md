# WP19 CUDA 与 Resident-State 主线对齐 验收审查

状态：`2026-05-21` accepted / implementation mergeable。

语言版本：

- 英文主文：
  [wp19_cuda_resident_state_alignment_acceptance_review_20260521.md](wp19_cuda_resident_state_alignment_acceptance_review_20260521.md)
- 中文辅文：
  `wp19_cuda_resident_state_alignment_acceptance_review_20260521.zh.md`

输入：

- [WP19 CUDA 与 Resident-State 主线对齐](../simulation_architecture/wp19_cuda_resident_state_alignment/cuda_resident_state_alignment_wp19_20260521.zh.md)
- [WP19-A CUDA / Resident-State Fact Ledger](../simulation_architecture/wp19_cuda_resident_state_alignment/wp19_cuda_resident_state_fact_ledger_cluster_20260521.zh.md)
- [WP19-B Device-Resident Output Contract Pre-Gate](../simulation_architecture/wp19_cuda_resident_state_alignment/wp19_device_resident_output_contract_cluster_20260521.zh.md)
- [WP19-C GPU Helper Diagnostics Boundary](../simulation_architecture/wp19_cuda_resident_state_alignment/wp19_gpu_helper_diagnostics_boundary_cluster_20260521.zh.md)
- [WP19-D Resident-State Sync And Shard Contract](../simulation_architecture/wp19_cuda_resident_state_alignment/wp19_resident_state_sync_shard_contract_cluster_20260521.zh.md)
- [WP19-E First CUDA Alignment Slice](../simulation_architecture/wp19_cuda_resident_state_alignment/wp19_first_cuda_alignment_slice_cluster_20260521.zh.md)
- [WP19-F Integration And Handoff](../simulation_architecture/wp19_cuda_resident_state_alignment/wp19_integration_handoff_cluster_20260521.zh.md)
- [WP19 dispatch queue](../simulation_architecture/wp19_cuda_resident_state_alignment/wp19_subagent_dispatch_queue_20260521.zh.md)

## 1. 结论

WP19 已作为一个有边界的 CUDA / resident-state 主线对齐增量验收。
它收束了现有 CUDA helpers、device-resident 输出元数据与 resident-state
sync 词汇之间的交接，但并没有把 exact GPU world-step execution 或
maintained resident-state ownership 晋级。

本次验收边界刻意保持很窄：

- exact GPU、resident-state、shadow 与 device-observation support 仍然
  fail-closed；
- `DeviceResidentOutputDescriptor` 仍然只是独立的 export-only DTO；
- `WorldBatchRuntime` broadphase 仍然只是 host-owned、evidence-only 的
  helper slice；
- `gpu_helpers.diagnostics_only` 仍然只是 diagnostics/export-only，
  不是 maintained capability evidence。

## 2. Gate 结论

| Gate | 结论 | 证据 |
|------|------|------|
| `WP19-A CUDA / Resident-State Fact Ledger` | pass | fact ledger 冻结了 helper/probe/capability call sites，继续保持 support flags fail-closed，并记录当前 host-owned 与 export-only 的 surface 切分。 |
| `WP19-B Device-Resident Output Contract Pre-Gate` | pass | pre-gate 定义了 additive export-only 的 `DeviceResidentOutputDescriptor` seam；`WP19-B2` 将其实现为独立 DTO，并配有 bindings 与聚焦测试，但没有接入 maintained packets 或 capability projection。 |
| `WP19-C GPU Helper Diagnostics Boundary` | pass | helper/probe availability 仍是 diagnostics/export-only，helper timing 或 device-pointer 事实不会晋级 maintained support flags。 |
| `WP19-D Resident-State Sync And Shard Contract` | pass | shard 和 barrier 词汇仍然保持 host-owned 或 export-only，resident-state 依旧是 blocked candidate，而不是 maintained surface。 |
| `WP19-E First CUDA Alignment Slice` | pass | 选中的 `WorldBatchRuntime` broadphase candidate-list slice 仍然是 host-owned；`WP19-E1` 证明 `use_gpu=True` 仍然保持 host filtering semantics 和 fail-closed capabilities。 |
| `WP19-F Integration And Handoff` | pass | closure lane 已整合 A-E/B2/E1 结果，记录 validation 与 residuals，同步 README/review 索引，并且只在 gates 通过后创建本验收审查。 |

## 3. 验证命令

closure handoff 中记录的主线程验证如下：

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/runtime_facade/test_layering.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/test_gpu_runtime_bindings.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/test_runtime_dto_contracts_batch1.py -k "device_resident or packet"
cmake --build build-workshop --target ef_py -j4
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/test_runtime_dto_contracts_batch1.py -k "device_resident or packet"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "candidate or gpu or broadphase or visual or comm or sensor"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/test_gpu_runtime_bindings.py
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP19 --summary
```

观察结果：

- `git diff --check`：通过。
- Runtime facade layering：`22 passed`。
- GPU runtime bindings：`12 passed`。
- Runtime DTO contracts batch1 预检：`2 passed, 4 deselected`。
- `cmake --build build-workshop --target ef_py -j4`：通过。
- Runtime binding DTO surface：`20 passed`。
- Runtime DTO contracts batch1 实现切片：`3 passed, 4 deselected`。
- World-batch runtime candidate/broadphase 切片：`4 passed, 17 deselected`。
- GPU runtime bindings 复检：`12 passed`。
- `python3 tools/maintenance/wp_doc_closure_audit.py --wp WP19 --summary`：通过，且所需中文辅文都已存在。

## 4. Runtime Surface 摘要

- `RuntimeFacade::capabilities()` 继续对 `supports_exact_gpu_backend`、
  `supports_resident_state`、`supports_shadow_compare` 与
  `supports_device_observation_view` 保持 fail-closed。
- `DeviceResidentOutputDescriptor` 是独立的 export-only DTO，不会扩大
  maintained packet DTO 或 capability projection。
- `WorldBatchRuntime` broadphase candidate-list 处理仍然是 host-owned
  helper logic。`use_gpu=True` 只是切换 accelerator candidate-bitset
  生产；host decode、filtering 与 sort 仍然是语义 owner。
- helper 与 probe 输出仍然只是 diagnostics/export-only evidence。
  device pointer、CUDA build success 或 benchmark speedup 都不等于
  maintained promotion。

## 5. Residuals 与下一步

有意保留的 residuals：

- 目前还没有 maintained 的 device-resident consumer contract 或 host
  reconstruction rule；
- helper-level overflow 与 superset behavior 仍然只是 GPU diagnostics
  议题，不是晋级信号；
- exact GPU world-step promotion、maintained resident-state promotion、
  shadow promotion 与 public capability-platform composition 都不在 WP19；
- 任何后续 device-resident wiring 若要继续，必须先有 maintained profile
  与明确的 reconstruction/export barrier。

因此，WP19 只是一个有边界的对齐增量，不是 broad GPU promotion 或
resident-state ownership transfer。
