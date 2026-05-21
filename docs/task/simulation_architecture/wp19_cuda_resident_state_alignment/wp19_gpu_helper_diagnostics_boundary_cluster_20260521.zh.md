# WP19-C GPU Helper Diagnostics Boundary

状态：`2026-05-21` pass / diagnostics non-promotion accepted。

语言版本：

- 英文主文：[wp19_gpu_helper_diagnostics_boundary_cluster_20260521.md](wp19_gpu_helper_diagnostics_boundary_cluster_20260521.md)
- 中文辅文：`wp19_gpu_helper_diagnostics_boundary_cluster_20260521.zh.md`

输入：

- [WP19 主计划](cuda_resident_state_alignment_wp19_20260521.zh.md)
- [WP13 backend fidelity expansion](../wp13_backend_fidelity_expansion/backend_fidelity_expansion_wp13_20260520.zh.md)
- [WP18 facade contract hardening](../wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_facade_contract_hardening_cluster_20260521.zh.md)

## 目的

让 CUDA helper availability 与 probe output 继续有用，同时防止它们意外变成
maintained capability evidence。

## 范围

范围内：

- architecture/runtime tests，证明 helper/probe availability 在 backend profile evidence
  晋级前仍是 diagnostics 或 export-only；
- 盘点可能被误读成 support 的 build flags 与 probe outputs；
- 为 runtime capability projection 与 bindings 给出 guard 建议。

范围外：

- resident-state sync/shard semantics，由 WP19-D 负责；
- device output contract design，由 WP19-B 负责；
- exact GPU promotion。

## 任务项

| ID | 任务 | 验收 |
|----|------|------|
| `C1` | Non-promotion tests | 现有或新增测试证明 GPU helper/probe availability 不会翻转 maintained support flags。 |
| `C2` | Diagnostics labels | Probe/helper outputs 除非被 maintained profile 晋级，否则被分类为 diagnostics/export-only。 |
| `C3` | Runtime projection guard | Capability projection 仍可由 maintained profiles 与 probeable deployment facts 解释。 |
| `C4` | Misuse inventory | 任何有风险的 helper/probe wording 或 API shape 都路由到 B/D/E。 |

## 第一波 Guard Notes

- `probe_gpu_device()` 暴露的 CUDA build presence、runtime availability、
  device count、compute capability、memory totals、device name 等事实，都只
  是 deployment diagnostics，不能授权 exact GPU、resident-state、
  device-observation-view、shadow 或 multi-fidelity support。
- `last_visual_experiment_stats()`、
  `last_execution_observation_stats()`、
  `last_flight_shaping_stats()` 以及其中的 `used_cuda`/timing 字段，都只是
  experiment/probe evidence，不是 maintained parity evidence，也不能被投射为
  support flags。
- `EF_ENABLE_CUDA_EXPERIMENTS` 与 device-resident export handles 可以放宽
  helper execution 或 export path，但 `RuntimeFacade.capabilities()` 在投射
  maintained support 时不得读取这些信号。
- diagnostics-only backend profile `gpu_helpers.diagnostics_only` 必须继续保持
  `export-only`，保持 host truth ownership，把 helper/probe state 描述为不会提交
  committed state 的 diagnostics，并且显式保持 exact GPU、resident-state、
  shadow、device observation support 为 false。

## Misuse Inventory

- build success 或 `EF_ENABLE_CUDA_EXPERIMENTS` enablement 可能被误读成 exact GPU
  readiness。WP19-C 只把它视为 non-promotion signal；任何未来晋级证明都属于
  WP19-B/D/E 加 maintained profile gate。
- helper bindings 暴露的 device-view export 可能被误读成 maintained
  resident-state 或 device-observation support。WP19-C 只在
  diagnostics/export-only tests 中保留它，并把 consumer contract 问题路由给
  WP19-B。
- probe summaries 与 helper timings 可能被误读成 parity evidence 或
  multi-fidelity readiness。WP19-C 把它们保留为 diagnostics-only facts，并把
  parity/sync obligations 路由到 WP19-D，把未来 runtime slice 路由到 WP19-E。

## Preflight Outcome

- 该 stream 的首选实现形态是 tests 加 guard notes。
- 这轮 boundary hardening 不需要修改 CUDA helper implementation。
- resident-state sync/shard semantics 保持不变，并明确继续由 WP19-D 负责。

## 建议验证

```bash
git diff --check
python -m pytest -q tests/test_gpu_runtime_bindings.py
python -m pytest -q tests/architecture/test_runtime_facade_layering.py
```

## 交付

返回 guard/test changes、helper/probe risk list、B/D/E residuals，以及当前是否存在会误投射 support 的代码路径。

## Closure Outcome

WP19-C 在 WP19 范围内以 diagnostics non-promotion boundary 通过验收。CUDA build
presence、probe facts、helper timing、device pointers 与
`EF_ENABLE_CUDA_EXPERIMENTS` 仍只是 deployment diagnostics 或 export-only
evidence，不能晋级 exact GPU、resident-state、shadow 或 device observation
support。
