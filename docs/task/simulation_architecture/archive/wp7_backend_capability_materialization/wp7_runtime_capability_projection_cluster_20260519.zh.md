# WP7-B Runtime Capability Projection

状态：`2026-05-19` WP7 第二波 implementation-ready 准备。

语言版本：

- 英文主文：[wp7_runtime_capability_projection_cluster_20260519.md](wp7_runtime_capability_projection_cluster_20260519.md)
- 中文辅文：`wp7_runtime_capability_projection_cluster_20260519.zh.md`
- 实现说明：[wp7_runtime_capability_projection_notes_20260519.zh.md](wp7_runtime_capability_projection_notes_20260519.zh.md)

输入：

- [WP7 后端能力物化](backend_capability_materialization_wp7_20260519.zh.md)
- [WP7-A registry materialization](wp7_registry_materialization_cluster_20260519.zh.md)
- [WP7-A registry materialization notes](wp7_registry_materialization_notes_20260519.zh.md)
- [WP6-C1 resident-state 边界规则](wp6_resident_state_boundary_rules_20260519.zh.md)
- 当前 `src/runtime/facade/runtime_facade_types.h`
- 当前 `tests/runtime/facade/test_runtime_facade.py`
- 当前 `tests/test_gpu_runtime_bindings.py`
- 当前 `tests/architecture/runtime_facade`

## 1. 目的

WP7-B 定义让 `RuntimeCapabilities` 成为“已声明 backend profile metadata 加可探测部署事实”的投影所需的实现路线。它必须保留 WP6 规则：GPU helper/probe
是否存在不能晋级 exact GPU、resident-state、device observation 或 shadow support。

这是新的 post-WP6 `WP7-B` 活线。它不能复用旧评审中“`WP7` 等于 backend profile
policy”的历史别名；该策略线已经作为 `WP6` 验收并关闭。

实现说明是第二波的规范交接产物。它定义当前 projection matrix、deployment facts
分离规则，以及让 facade/core 独立于 GPU helper 或 probe implementation 细节的
layering guard。

## 2. 必需工作项

| 流 | 必需产出 | 写入范围 | 预算 |
|----|----------|----------|------|
| `WP7-B1 Projection Source Boundary` | 文档化或实现 registry metadata 进入 runtime facade projection path 的位置。 | runtime/facade 文档，可选 C++ projection helper。 | 高。 |
| `WP7-B2 Deployment Fact Separation` | 保持 GPU helper/probe data 与维护中 capability claim 分离。 | 测试与文档；避免 facade/core 链接 GPU。 | 高。 |
| `WP7-B3 Capability Default Guard` | 保留 exact GPU、device observation、resident-state 与 shadow support 当前 false default。 | `tests/runtime/facade/`、`tests/test_gpu_runtime_bindings.py`。 | 中高。 |
| `WP7-B4 Layering Guard` | 确保 facade/core 不调用或链接 GPU helper/probe implementation 来投影 capability。 | `tests/architecture/runtime_facade`。 | 中高。 |

## 3. 投影规则

runtime projection path 必须遵守：

1. 维护中 capability claim 需要维护中的 profile row。Projection 必须先消费 WP7-A
   materialized registry shape 中的 `maintained_status` 与
   `projection_eligibility`。
2. deployment fact 可以解释可用或不可用，但不能覆盖 profile class、parity budget、
   sync policy 或 validation gate。
3. diagnostics-only row 只能投影 report-only affordance，不能投影维护中真值。
4. candidate row 在 promotion evidence 通过前都投影 false support。
5. facade/core 层不能依赖 GPU helper 或 probe implementation 细节，因为
   `ef_gpu_experiments` 已经依赖 `ef_core`。

计划中的 projection adapter 只能在 registry gate 产出保守 capability truth 之后，
再叠加 deployment facts。GPU helper/probe binding 是否存在是 deployment fact，
不是 promotion evidence。

## 4. 当前必需投影

当前维护中投影保持为：

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

这些值是当前必需 support claim，不是对未来 promotion 的预测。它们保持 false，
直到未来 maintained profile revision 与 gate 显式更新 `maintained_status`、
`projection_eligibility`、`validation_gate` 以及配对 parity budget 的
`acceptance_gate`。

## 5. 实现说明交接

见
[wp7_runtime_capability_projection_notes_20260519.zh.md](wp7_runtime_capability_projection_notes_20260519.zh.md)
中的 implementation-ready contract。该说明要求 runtime projection：

1. 以 `maintained_status` 加 `projection_eligibility` 作为 capability source
   boundary。
2. 只把 deployment facts 叠加为 availability 或 diagnostics explanation。
3. 对当前 support claim 保持 GPU helper/probe binding report-only。
4. 通过避免依赖 GPU helper implementation symbol 来保持 facade/core layering。
5. 如果修改测试，只添加 narrow guard，并避免因为未来 hand-maintained YAML seed
   尚不存在而失败。

## 6. 非目标

- 不启用 exact GPU、resident-state、device observation 或 shadow support。
- 不添加 backend selection。
- 不让 `RuntimeCapabilities` 成为真值源。
- 不让 facade/core 链接 GPU helper code。
- 不删除 diagnostics helper binding。

## 7. 验收门槛

本任务簇在以下条件满足时验收：

1. projection 可以由 registry metadata 与 deployment facts 解释。
2. 当前 false capability claim 在测试中保持 false。
3. GPU helper/probe binding 可以存在，但不会晋级维护中 support。
4. facade/core layering tests 防止 GPU helper dependency inversion。
5. 任何新增 projection field 都引用自己的 registry source 与 validation gate。
6. 英文与中文 WP7-B cluster/notes 文档互链，并保持大致相同结构。

## 8. 验证命令

```bash
git diff --check
rg -n "RuntimeCapabilities|maintained_status|projection_eligibility|deployment facts|supports_exact_gpu_backend|supports_resident_state|supports_shadow_compare|GPU helper|probe" docs/task/simulation_architecture/wp7_runtime_capability_projection*20260519*.md
```

如果测试有改动，运行对应的 narrow pytest target。如果测试未改动，现有 guard 仍是计划覆盖：
`tests/runtime/facade/test_runtime_facade.py`、`tests/test_gpu_runtime_bindings.py`
以及 `tests/architecture/runtime_facade`。
