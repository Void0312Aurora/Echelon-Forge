# WP7-B Runtime Capability Projection 实现说明

状态：`2026-05-19` WP7-B 第二波 implementation-ready notes。

语言版本：

- 英文主文：[wp7_runtime_capability_projection_notes_20260519.md](wp7_runtime_capability_projection_notes_20260519.md)
- 中文辅文：`wp7_runtime_capability_projection_notes_20260519.zh.md`
- 父级 cluster：
  [wp7_runtime_capability_projection_cluster_20260519.zh.md](wp7_runtime_capability_projection_cluster_20260519.zh.md)

输入：

- [WP7 后端能力物化](backend_capability_materialization_wp7_20260519.zh.md)
- [WP7-A registry materialization](wp7_registry_materialization_cluster_20260519.zh.md)
- [WP7-A registry materialization notes](wp7_registry_materialization_notes_20260519.zh.md)
- [WP6-A backend profile registry](wp6_backend_profile_registry_20260519.zh.md)
- [WP6-B parity budget registry](wp6_parity_budget_registry_20260519.zh.md)
- [WP6-C1 resident-state 边界规则](wp6_resident_state_boundary_rules_20260519.zh.md)
- 当前 `src/runtime/facade/runtime_facade_types.h`
- 当前 `src/runtime/facade/runtime_facade.cpp`
- 当前 `tests/runtime/facade/test_runtime_facade.py`
- 当前 `tests/test_gpu_runtime_bindings.py`
- 当前 `tests/architecture/runtime_facade/test_layering.py`

## 1. 投影论点

`RuntimeCapabilities` 是 accepted backend metadata 加可探测 deployment facts
的投影。它不是真值源，也不能从 helper code、build flag、import、device probe
或 runtime experiment 推断 support。

投影顺序是：

1. 在 seed 存在后，从 WP7-A hand-maintained YAML seed shape 读取 profile row
   与配对 parity budget row。
2. 用显式 `maintained_status` 与 `projection_eligibility` gate 维护中 claim。
3. 任何维护中 claim 都要求 profile `validation_gate` 与 parity budget
   `acceptance_gate` 一致。
4. deployment facts 只能在 registry gate 之后叠加，并且只能作为 availability
   或 diagnostics explanation。

在 seed 落地之前，测试必须使用窄的 source/document guard 或当前 runtime
expectation。测试不能只因为未来 YAML seed 尚不存在而失败。

## 2. Source Boundary

未来 projection adapter 应消费 normalized registry row，而不是直接消费 WP6
Markdown 表。WP7-A 已定义第一波 seed vocabulary：`maintained_status`、
`projection_eligibility`、`source_doc_provenance`、profile `validation_gate`
以及 parity budget `acceptance_gate`。

adapter 只能从以下 metadata 计算维护中 support：

| 输入字段 | Projection 用途 |
|----------|-----------------|
| `maintained_status` | 区分 `maintained_exact_baseline`、`diagnostics_only` 与 `unmaintained_candidate`。 |
| `projection_eligibility.maintained_cpu_exact_baseline` | 只允许 `cpu_exact.reference` 成为 CPU exact reference baseline。 |
| `projection_eligibility.exact_gpu_supported` | 控制 `supports_exact_gpu_backend`；当前所有 WP6 row 都是 false。 |
| `projection_eligibility.resident_state_supported` | 控制 `supports_resident_state`；当前所有 WP6 row 都是 false。 |
| `projection_eligibility.shadow_supported` | 控制 `supports_shadow_compare`；当前所有 WP6 row 都是 false。 |
| `projection_eligibility.diagnostics_allowed` | 允许 report-only diagnostics surface，但不改变 support claim。 |
| `validation_gate` 与 `acceptance_gate` | 必须维护中/已验收，才能投影 true 的维护中 support claim。 |

`RuntimeCapabilities` 可以镜像结果，但不能创造新的 capability truth。如果 registry
metadata 缺失或不完整，candidate 或 diagnostics-only claim 的安全输出是 false
support 加 diagnostics text。

## 3. 当前必需 Projection Matrix

当前必需 `RuntimeCapabilities` support matrix 是：

```yaml
supports_batch_runtime: true
supports_compiled_episode_controller: true
supports_compiled_execution_step: true
supports_gpu_visual: false
supports_gpu_observation: false
supports_gpu_flight_shaping: false
supports_device_observation_view: false
supports_resident_state: false
supports_exact_gpu_backend: false
supports_shadow_compare: false
```

三个 true 值是当前 facade/runtime surface。七个 false 值保持 false，除非未来
maintained profile revision 与 promotion gate 更新 registry、parity budget
以及 projection test contract。

当前 WP6/WP7-A row 映射：

| Profile row | `maintained_status` | 相关 `projection_eligibility` | 必需 projection |
|-------------|---------------------|-------------------------------|-----------------|
| `cpu_exact.reference` | `maintained_exact_baseline` | `maintained_cpu_exact_baseline: true` | 可以解释 true 的 CPU-backed facade surface；不隐含 GPU、resident-state、device view 或 shadow support。 |
| `gpu_helpers.diagnostics_only` | `diagnostics_only` | `diagnostics_allowed: true`；所有维护中 support boolean 为 false | GPU helper/probe diagnostics 可以可用，但 support field 保持 false。 |
| `gpu_exact.unmaintained_candidate` | `unmaintained_candidate` | `exact_gpu_supported: false` | `supports_exact_gpu_backend: false`；helper/probe availability 不能晋级它。 |
| `resident_state.unmaintained_candidate` | `unmaintained_candidate` | `resident_state_supported: false` | `supports_resident_state: false`；unsynced backend-local state 保持 diagnostics-only。 |
| `shadow_compare.unmaintained_candidate` | `unmaintained_candidate` | `shadow_supported: false` | `supports_shadow_compare: false`；shadow report 不能影响 committed state 或 fallback control flow。 |

`supports_gpu_visual`、`supports_gpu_observation`、`supports_gpu_flight_shaping`
和 `supports_device_observation_view` 在当前维护中投影中也保持 false。已有 GPU helper
输出是 deployment facts 或 diagnostics export，不是维护中 runtime capability claim。

## 4. Deployment Facts 分离

deployment facts 是关于当前 build 或机器的观察事实。例如 GPU helper binding 是否存在、
`probe_gpu_device()` 是否可调用、CUDA runtime support 是否已构建、是否报告 device
count，或某个 experiment 是否产出 timing/debug stats。

deployment facts 可以解释：

1. 为什么某个 diagnostics surface 可用或不可用。
2. 为什么一个 metadata 已验收的 maintained profile 在特定 deployment 无法运行。
3. 哪个 helper/probe 产出了 report-only artifact。
4. diagnostics 中应显示什么 availability reason。

deployment facts 不可以：

1. 改变 `maintained_status`。
2. 改变 `projection_eligibility`。
3. 满足 `validation_gate` 或 `acceptance_gate`。
4. 晋级 exact GPU、resident-state、device observation view 或 shadow compare
   support。
5. 让 helper/probe binding presence 替代 registry metadata。

这就是为什么 GPU helper/probe binding 存在可以与 `supports_exact_gpu_backend: false`、
`supports_resident_state: false` 和 `supports_shadow_compare: false` 共存。

## 5. Layering 规则

facade/core projection path 不得链接或调用 GPU helper/probe implementation。
`ef_gpu_experiments` already depends on `ef_core`，所以 facade 或 core 反向依赖
GPU helper code 会倒置 dependency direction。

允许的 layering：

1. `RuntimeCapabilities` 可以从 facade metadata 暴露保守 support boolean。
2. GPU helper/probe binding 可以继续作为 diagnostics helper 导出。
3. 测试可以断言 helper/probe binding 存在，同时仍不晋级 support。
4. Architecture guard 可以扫描 facade/core source 中的 GPU helper marker。

禁止的 layering：

1. `src/runtime/facade` include GPU helper header 来计算 capabilities。
2. `src/core` 调用 `probe_gpu_device()` 或 GPU helper stats 来投影维护中 support。
3. deployment probe 翻转 `supports_exact_gpu_backend`、`supports_resident_state`
   或 `supports_shadow_compare`。
4. device-resident pointer 或 helper-local buffer 成为 facade/core truth。

## 6. 测试 Guard 计划

本轮文档工作不需要新增 pytest，因为当前测试集已经有窄 guard：

| 现有 target | 已提供 guard |
|-------------|--------------|
| `tests/runtime/facade/test_runtime_facade.py` | Facade capability expectation 保持当前 false support field 为 false。 |
| `tests/test_gpu_runtime_bindings.py` | GPU helper/probe binding 可以存在，同时 support claim 保持 false。 |
| `tests/architecture/runtime_facade/test_layering.py` | Facade/core source 不得 include 或调用 GPU helper/probe implementation marker。 |

如果后续新增测试，保持测试窄化。它应该只检查上述 contract 之一，并在未来
hand-maintained YAML seed 不存在时 skip 或使用 docs-only expectation。WP7-A seed
落地前，不应把 seed 缺失变成失败。

## 7. Promotion Requirements

未来任何把当前 false support field 置为 true 的改动，都必须同时具备：

1. 更新 `maintained_status` 的 maintained profile revision。
2. 针对该 support claim 更新 `projection_eligibility`。
3. 带已验收 `acceptance_gate` 的 maintained parity budget。
4. 命名该 claim 所需 evidence 的 profile `validation_gate`。
5. 回指 accepted registry 与 review artifact 的 source provenance。
6. 证明 helper/probe availability 单独仍不足以晋级 support 的 projection test。
7. 保持 facade/core 独立于 GPU helper code 的 layering guard。

缺少这些内容时，`RuntimeCapabilities` 必须保持 support field false，并且只能报告
diagnostics/availability explanation。

## 8. 验收门槛

WP7-B 达到 implementation-ready 的条件是：

1. Projection source boundary 记录为 `maintained_status` 加
   `projection_eligibility`。
2. deployment facts 与 capability claim 明确分离。
3. 当前必需 projection 保持 GPU visual、GPU observation、GPU flight shaping、
   device observation view、resident state、exact GPU backend 与 shadow compare
   support 为 false。
4. GPU helper/probe binding presence 只作为 diagnostics/availability evidence。
5. Facade/core layering 排除 GPU helper/probe implementation dependency。
6. 测试指导避免因未来 seed file 尚未落地而失败。
7. 英文与中文 notes 互链，并保持大致相同结构。

## 9. 验证命令

```bash
git diff --check
rg -n "RuntimeCapabilities|maintained_status|projection_eligibility|deployment facts|supports_exact_gpu_backend|supports_resident_state|supports_shadow_compare|GPU helper|probe" docs/task/simulation_architecture/wp7_runtime_capability_projection*20260519*.md
```

只修改这些 WP7-B 文档时，不需要运行 pytest。如果后续编辑测试，运行对应的 narrow
target。
