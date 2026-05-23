# WP19-E First CUDA Alignment Slice

状态：`2026-05-21` evidence-only pass / host-owned broadphase slice 已验证。

语言版本：

- 英文主文：[wp19_first_cuda_alignment_slice_cluster_20260521.md](wp19_first_cuda_alignment_slice_cluster_20260521.md)
- 中文辅文：`wp19_first_cuda_alignment_slice_cluster_20260521.zh.md`

输入：

- [WP19 主计划](cuda_resident_state_alignment_wp19_20260521.zh.md)
- [WP19-A fact ledger](wp19_cuda_resident_state_fact_ledger_cluster_20260521.zh.md)
- [WP19-B device output contract](wp19_device_resident_output_contract_cluster_20260521.zh.md)
- [WP19-C diagnostics boundary](wp19_gpu_helper_diagnostics_boundary_cluster_20260521.zh.md)
- [WP19-D sync and shard contract](wp19_resident_state_sync_shard_contract_cluster_20260521.zh.md)

## 目的

只有在第一轮 preflight 识别出不会晋级 exact GPU 或 maintained resident-state support
的 bounded path 后，才实现一条安全 CUDA/helper alignment slice。

## 已选 Slice

选定路径：`WorldBatchRuntime` 中 interaction broadphase candidate-list 查询，
覆盖 sensor、visual 与 comm candidate ID path。

在 A/C/D 结论下它之所以安全：

- WP19-A 已将 `WorldBatchRuntime` candidate-list path 归类为
  `host-owned helper`：GPU helper 只提供 candidate bitset，decode 与最终列表语义
  仍由 host 代码拥有。
- WP19-C 要求 helper/probe availability 保持 diagnostics-only，不能推动
  maintained capability support。
- WP19-D 保持 resident-state 与 sync ownership fail-closed，因此这条 slice
  不能扩展成任何 maintained backend-owned state claim。

本流明确拒绝的替代项：

- helper/device-resident output promotion；
- capability flag 或 facade projection 变更；
- CUDA helper implementation rewrite；
- resident-state ownership 或 sync promotion。

## 范围

范围内：

- 由 A-D 选出的一条 helper/output path，可能是 visual/observation、broadphase
  metadata 或 probe diagnostics；
- 保持 host-owned、diagnostics-only、export-only 或 observation-only 的 additive
  metadata、guard 或 evidence wiring；
- 聚焦测试证明 support flags 除非有 maintained evidence，否则仍保持 false。

范围外：

- exact GPU world-step rewrite；
- broad device-resident runtime migration；
- request build/consume migration，除非 A-D 明确选出很小且安全的 seam。

## 任务项

| ID | 任务 | 验收 |
|----|------|------|
| `E1` | Slice selection | A-D evidence 选出一条 bounded helper/output path，并拒绝不安全替代项。 |
| `E2` | Implementation | 选定路径增加 additive metadata、guard 或 evidence wiring，但不改变 maintained truth ownership。 |
| `E3` | Focused tests | 测试证明 behavior 与 capability non-promotion。 |
| `E4` | Residual routing | 更宽的 CUDA、exact GPU 与 resident-state ownership residuals 被路由后续。 |

## 实施结论

结果：这条 slice 不需要修改 `WorldBatchRuntime` 的 C++ 实现。

当前源码已经满足选定的 host-owned 边界：

- `run_interaction_broadphase_candidate_ids(...)` 只负责在 CPU/GPU helper
  bitset 生成之间切换；
- `decode_broadphase_candidate_ids(...)` 在 helper 输出返回后，由 host 侧重建
  candidate ID；
- `get_sensor_candidate_ids_batch(...)` 与
  `get_visual_candidate_ids_batch(...)` 在 decode 后继续执行 host-owned 的
  self-exclusion 与 sorting；
- `get_comm_candidate_ids_batch(...)` 在 decode 后继续执行 host-owned 的
  self-exclusion、alliance/network semantic filtering 与 sorting。

因此，`use_gpu=True` 仍然只是 accelerator/helper toggle，而不是语义 ownership
的转移。

## 聚焦证据

本轮只在 `tests/world_batch/test_world_batch_runtime.py` 落证据测试。

锁定的行为：

- 选定的 live candidate-helper 场景同时运行 `use_gpu=False` 与 `use_gpu=True`；
- 在这条安全 bounded case 上，sensor 与 visual candidate list 保持一致；
- 在这条安全 bounded case 上，comm candidate list 保持一致；
- 三条路径都继续执行 host-owned sorting 与 self-exclusion；
- comm candidate result 继续执行 host-owned semantic filtering
  （同 side/同 network 的友军保留，敌方剔除）；
- helper-backed candidate query 之后，
  `RuntimeFacade.capabilities()` 仍保持 fail-closed，包括
  `supports_device_observation_view == false`、
  `supports_resident_state == false`、
  `supports_exact_gpu_backend == false`，以及
  `device_observation_view_candidate_profile_id ==
  gpu_helpers.diagnostics_only`。

这些测试刻意没有把契约扩大成“所有原始 GPU broadphase bitset 都必须与 CPU
reference 完全一致”。那会与现有 helper-level overflow/superset 的
diagnostics boundary 冲突。本 slice 的契约仍停留在
`WorldBatchRuntime` host-owned candidate-list surface。

## Residuals

明确留给后续流的 residual：

1. helper-level overflow 与 superset 行为仍属于 GPU diagnostics/runtime helper
   concern，不是 WP19-E capability 或 resident-state promotion 信号；
2. 本流不引入 device-resident output DTO 或 export contract；这仍属于 WP19-B；
3. 本流不引入 resident-state sync/barrier ownership；这仍属于 WP19-D；
4. 更宽的 exact-GPU、shadow 或 maintained backend-profile promotion 仍保持 blocked。

## 建议验证

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "candidate or gpu or broadphase or visual or comm or sensor"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/test_gpu_runtime_bindings.py
```

## 交付

返回这条 selected host-owned broadphase slice、runtime ownership 未改变的证据、
聚焦测试结果、capability non-promotion 证据，以及供 WP19-F 集成的 residual 路由。
