# WP19-A CUDA / Resident-State Fact Ledger

状态：`2026-05-21` verified / authoritative facts ledger。

语言版本：

- 英文主文：
  [wp19_cuda_resident_state_fact_ledger_cluster_20260521.md](wp19_cuda_resident_state_fact_ledger_cluster_20260521.md)
- 中文辅文：`wp19_cuda_resident_state_fact_ledger_cluster_20260521.zh.md`

输入：

- [WP19 主计划](cuda_resident_state_alignment_wp19_20260521.zh.md)
- [WP18 验收审查](../../review/wp18_runtime_ownership_cxx_hot_path_consolidation_acceptance_review_20260521.zh.md)
- [架构与性能路线进一步调研](../../../plan/architecture/architecture_and_performance_research_followup.zh.md)
- [Simulation system architecture design](../../../plan/architecture/simulation_system_architecture_design.zh.md)
- [WP6 resident-state boundary rules](../wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.zh.md)
- [WP18 ownership fact ledger](../wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.zh.md)

## 目的

在任何 contract 或 runtime 变更落地前，冻结当前 CUDA / resident-state 事实。
该账本只记录当前代码与测试已经证明的内容，并把 WP19-E 保持在 preflight，
直到存在安全 slice 为止。

## 证据窗口

- `src/runtime/contracts/backend_profile_contracts.h:13-20, 24-46, 98-130,
  186-205, 256-339, 391-723`
- `src/runtime/facade/runtime_facade_types.h:17-41`
- `src/runtime/facade/runtime_facade.cpp:1044-1065`
- `src/core/engine/world_batch_runtime.cpp:115-180, 703-900`
- `src/gpu/gpu_visual_runtime.{h,cpp}`
- `src/gpu/gpu_execution_observation_runtime.{h,cpp}`
- `src/gpu/gpu_flight_shaping_runtime.{h,cpp}`
- `src/gpu/gpu_interaction_broadphase_runtime.{h,cpp}`
- `src/gpu/*_cuda.cu`
- `src/tools/experimental/gpu_phase0/README.md`
- `src/tools/experimental/gpu_phase0/*.cpp`
- `tests/test_gpu_runtime_bindings.py:20-260, 543-590`
- `tests/runtime/facade/test_runtime_facade.py:524-554`
- `tests/architecture/runtime_facade/test_scenario_setup_facade_boundary.py`
- `tests/world_batch/test_world_batch_runtime.py:1131-1320`
- `tests/world_batch/test_world_batch_vec_env.py:681-728`

## 分类说明

- `maintained owner`：当前 maintained truth 或 capability projection 的 owner。
- `host-owned helper`：host 侧 helper / orchestration 路径，语义 owner 仍在 host，
  只是使用 accelerator-backed helper。
- `diagnostics-export-only`：只读、probe-only、或 DLPack/export-only surface，
  不能授权 maintained support。
- `candidate`：明确通过 opt-in 或 fallback boundary 使用的 accelerator path，
  但不是 maintained truth path。
- `blocked-unknown`：当前证据不足，不能进入 maintained promotion。

## Surface 账本

| Surface | 分类 | 当前事实 | 证据 |
|---|---|---|---|
| `src/runtime/contracts/backend_profile_contracts.h` + `src/runtime/facade/runtime_facade.{h,cpp}` | maintained owner | maintained capability projection 是 fail-closed。`cpu_exact.reference` 是唯一 maintained profile，`gpu_helpers.diagnostics_only` 只用于 report-only，`supports_resident_state`、`supports_exact_gpu_backend`、`supports_shadow_compare`、`supports_device_observation_view` 都保持 `false`。 | `src/runtime/contracts/backend_profile_contracts.h:13-20, 24-46, 98-130, 186-205, 256-339, 391-723`; `src/runtime/facade/runtime_facade.cpp:1044-1065`; `src/runtime/facade/runtime_facade_types.h:17-41` |
| `src/gpu/gpu_visual_runtime.{h,cpp}` reference helpers (`render_visual_reference_cpu*`, `estimate_visual_tensor_footprint`) | host-owned helper | 这些函数生成 host 侧 reference output 或 size estimate。它们服务于 parity check 与 host orchestration，但不拥有 maintained world truth。 | `src/gpu/gpu_visual_runtime.cpp:47-179` |
| `src/gpu/gpu_visual_runtime.{h,cpp}` experiment / device-resident helpers (`render_visual_experiment*`, `render_visual_experiment_batch_device_resident`) | candidate | GPU path 明确通过 `EF_ENABLE_CUDA_EXPERIMENTS` 选择，必要时回退到 CPU，属于 accelerator/parity candidate，不是 maintained semantic owner。 | `src/gpu/gpu_visual_runtime.cpp:12-43, 185-288`; `src/gpu/gpu_visual_runtime_cuda.cu` |
| `src/gpu/gpu_visual_runtime.{h,cpp}` diagnostics hooks (`last_visual_experiment_stats`, `last_visual_output_device_ptr`, `last_visual_output_float_count`, `probe_device`) | diagnostics-export-only | 这些 hook 暴露 availability、timing 和 device pointer，仅供 report / DLPack export，不会翻转 support flag。 | `src/gpu/gpu_visual_runtime.cpp:115-133` |
| `src/gpu/gpu_execution_observation_runtime.{h,cpp}` reference helpers (`compute_execution_observation_reference_cpu_batch`, `execution_observation_output_float_count`) | host-owned helper | host reference path 负责 observable output shape 和 parity baseline。 | `src/gpu/gpu_execution_observation_runtime.cpp:139-291` |
| `src/gpu/gpu_execution_observation_runtime.{h,cpp}` experiment / device-resident helpers (`compute_execution_observation_experiment_batch*`) | candidate | CUDA path 可选、可与 reference 比较、并可回退到 CPU，不声称 maintained device-observation support。 | `src/gpu/gpu_execution_observation_runtime.cpp:12-31, 270-307`; `src/gpu/gpu_execution_observation_runtime_cuda.cu` |
| `src/gpu/gpu_execution_observation_runtime.{h,cpp}` diagnostics hooks (`last_execution_observation_stats`, `last_execution_observation_output_device_ptr`, `last_execution_observation_output_float_count`) | diagnostics-export-only | 这些 hook 只暴露 device state 供 diagnostics / export 使用。 | `src/gpu/gpu_execution_observation_runtime.cpp:167-185` |
| `src/gpu/gpu_flight_shaping_runtime.{h,cpp}` reference helpers (`compute_flight_shaping_reference_cpu_batch`) | host-owned helper | CPU reference helper 仍是 flight-shaping terms 的 host baseline。 | `src/gpu/gpu_flight_shaping_runtime.cpp:87-110` |
| `src/gpu/gpu_flight_shaping_runtime.{h,cpp}` experiment / device-resident helpers (`compute_flight_shaping_experiment_batch*`) | candidate | GPU path 可选；若 experiment path 不可用或输出为空，会回退到 CPU reference path。 | `src/gpu/gpu_flight_shaping_runtime.cpp:8-19, 101-123`; `src/gpu/gpu_flight_shaping_runtime_cuda.cu` |
| `src/gpu/gpu_flight_shaping_runtime.{h,cpp}` diagnostics hooks (`last_flight_shaping_stats`, `last_flight_shaping_output_device_ptr`, `last_flight_shaping_output_float_count`) | diagnostics-export-only | 这些 hook 仅用于验证 timing 和 device pointer。 | `src/gpu/gpu_flight_shaping_runtime.cpp:63-81` |
| `src/gpu/gpu_interaction_broadphase_runtime.{h,cpp}` reference helpers (`build_interaction_broadphase_reference_cpu_batch`, `interaction_broadphase_word_count`) | host-owned helper | host reference path 负责 bitset 语义和验证。 | `src/gpu/gpu_interaction_broadphase_runtime.cpp:33-112` |
| `src/gpu/gpu_interaction_broadphase_runtime.{h,cpp}` experiment / device-resident helpers (`build_interaction_broadphase_experiment_batch*`) | candidate | GPU path 显式可选，必要时回退到 host reference。 | `src/gpu/gpu_interaction_broadphase_runtime.cpp:7-25, 118-140`; `src/gpu/gpu_interaction_broadphase_runtime_cuda.cu` |
| `src/gpu/gpu_interaction_broadphase_runtime.{h,cpp}` diagnostics hooks (`last_interaction_broadphase_stats`, `last_interaction_broadphase_output_device_ptr`, `last_interaction_broadphase_output_word_count`) | diagnostics-export-only | 这些 hook 只暴露 performance 与 output placement 事实。 | `src/gpu/gpu_interaction_broadphase_runtime.cpp:58-76` |
| `src/tools/experimental/gpu_phase0/*` | diagnostics-export-only | phase-0 probes 是独立 binary，用于 measurement 和 parity reporting。README 明确禁止它们成为默认 runtime backend，或被 facade / core runtime 依赖。 | `src/tools/experimental/gpu_phase0/README.md:3-21`; `src/tools/experimental/gpu_phase0/*.cpp` |
| `WorldBatchRuntime` GPU candidate-ID 调用点 (`get_sensor_candidate_ids_batch`, `get_visual_candidate_ids_batch`, `get_comm_candidate_ids_batch`) | host-owned helper | runtime 负责最终过滤与排序。GPU broadphase 只在显式 `use_gpu` flag 下提供 candidate bitset。 | `src/core/engine/world_batch_runtime.cpp:703-900` |
| `src/gpu/*_cuda.cu` device kernels | blocked-unknown | kernel 内部只通过受保护的 experimental wrapper 间接访问。这里还没有证据支持其成为 maintained surface。 | `src/gpu/*_cuda.cu` |
| `tests/test_gpu_runtime_bindings.py`, `tests/runtime/facade/test_runtime_facade.py`, `tests/architecture/runtime_facade` | diagnostics-export-only | 这些测试把 capability flag 固定为 `false`，检查 helper binding 存在，并阻止 `RuntimeFacade` 或 core runtime 依赖 GPU helper 实现细节。 | `tests/test_gpu_runtime_bindings.py:20-260, 543-590`; `tests/runtime/facade/test_runtime_facade.py:524-554`; `tests/architecture/runtime_facade/test_scenario_setup_facade_boundary.py` |

## Capability Facts

- `RuntimeCapabilities` 的 GPU / resident / shadow flag 默认都是 `false`。
- `RuntimeFacade::capabilities()` 继续保持这些 flag 为 `false`，只发布当前
  candidate profile 的 metadata 字符串。
- `tests/test_gpu_runtime_bindings.py` 证明 helper/probe 的可用性不能推出
  maintained support。
- `tests/runtime/facade/test_runtime_facade.py` 将 facade 结果锁定为
  `supports_resident_state == false`、`supports_exact_gpu_backend == false`、
  `supports_shadow_compare == false`。
- `tests/architecture/runtime_facade` 禁止 `RuntimeFacade`
  引入或调用 GPU helper/probe 代码，也禁止 core runtime 投影 GPU / resident /
  shadow capability support。

## WorldBatchRuntime 事实

- `WorldBatchRuntime` 在 sensor / visual / comm candidate-ID 路径里使用
  `gpu::build_interaction_broadphase_experiment_batch(...)` 和
  `..._device_resident(...)`。
- host 侧 decode、filter、sort 仍然留在 `WorldBatchRuntime`；GPU output 只是一组
  candidate bitset。
- `tests/world_batch/test_world_batch_runtime.py` 用显式 `use_gpu=True` 路径验证候选
  helper 的行为。
- `tests/world_batch/test_world_batch_vec_env.py` 将 compiled visual batch 路径与 legacy
  路径对齐，这仍然属于 parity mode，而不是 support-promotion mode。

## WP19-E 建议

状态：`preflight-only`。

现有证据支持的是受控 helper boundary，而不是 resident-state promotion slice。
如果后续 WP19-B、WP19-C、WP19-D 先产出安全的 bounded helper slice，那么第一个
implementation 候选应当是一个 host-owned 的 `WorldBatchRuntime` candidate-list path，
并带显式 host post-filtering，优先从 interaction broadphase 开始。当前阶段不要修改
runtime 行为。
