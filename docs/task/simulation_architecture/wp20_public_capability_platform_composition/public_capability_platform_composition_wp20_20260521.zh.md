# WP20 Public Capability-Platform Composition

状态：`2026-05-21` complete / accepted。

语言版本：

- 英文主文：[public_capability_platform_composition_wp20_20260521.md](public_capability_platform_composition_wp20_20260521.md)
- 中文辅文：`public_capability_platform_composition_wp20_20260521.zh.md`

输入：

- [WP14 capability composition](../wp14_capability_composition/capability_composition_wp14_20260521.zh.md)
- [WP14 验收审查](../../review/wp14_capability_composition_acceptance_review_20260521.zh.md)
- [WP17 capability spawn runtime promotion](../wp17_stage3_runtime_materialization_cleanup/wp17_capability_spawn_runtime_cluster_20260521.zh.md)
- [WP18 runtime ownership and C++ hot-path consolidation](../wp18_runtime_ownership_cxx_hot_path_consolidation/runtime_ownership_cxx_hot_path_consolidation_wp18_20260521.zh.md)
- [WP19 CUDA and resident-state alignment](../wp19_cuda_resident_state_alignment/cuda_resident_state_alignment_wp19_20260521.zh.md)
- [仿真系统架构设计](../../../plan/architecture/simulation_system_architecture_design.zh.md)
- [Subagent 使用规范](../../../standards/governance/subagent_usage_policy.zh.md)
- [WP Closure Lane Policy](../../../standards/governance/wp_closure_lane_policy.md)

命名与提交信息说明：

- `WP20` 只是 public capability-platform composition 的任务索引标签。
- 实现提交应使用结果语言，例如 `Promote typed platform spawn admission`
  或 `Consume typed platform setup requests through validated plans`，避免在
  commit message 中使用内部任务标签。

## 1. 目的

WP14 已建立 platform capability vocabulary 与 additive typed setup DTO。
WP17 已让 `DefaultUnitFactory::spawn()` 内部通过 `ResolvedPlatformSpawnPlan`
证据后再 materialize，同时保持 type-name 兼容。WP20 的目标是把这条链公开为
maintained、validated setup entry，而不是强制 scenario schema 迁移或移除
`spawn_unit(type_name)`。

目标链：

```text
typed platform spawn request
  -> validated CapabilityBundle and ResolvedPlatformSpawnPlan
  -> compatibility-preserving type_name materialization bridge
  -> facade/world-batch setup result evidence
  -> public contract and binding guards
```

WP20 是实现阶段。仅有计划文档不能通过 gate。

## 2. 范围边界

WP20 可以：

- 冻结 platform capability contracts、typed setup DTO、internal resolved
  spawn plans 与 public gap 的当前代码事实。
- 添加 public admission/result contract，覆盖 request id、entity id、admission
  state、rejection reason 与 evidence refs。
- 仅在 validation 通过后消费 `BatchWorldSetupRequest.typed_platform_spawn_requests`，
  且必须通过 compatibility-preserving resolved-plan bridge。
- 通过 facade 与 Python bindings 暴露公开 setup/admission surface。
- 把 WP14 的 "not auto-materialized" guard 替换为 WP20 的 validation-first
  publicization guards。
- 保留 `spawn_unit(type_name)`、`WorldSpawnRequest.type_name`、现有 scenario setup
  与 world-batch setup 行为。

WP20 不能：

- 删除或废弃 type-name spawning。
- 强制 scenario JSON、examples 或 Python callers 迁移到 typed platform spawn。
- 在没有 preserved compatibility `source_type_name` 与 admitted resolved plan 时
  materialize 任意 capability bundle。
- 把 platform composition semantics 混入 backend `RuntimeCapabilities`。
- 添加新战术行为、武器/传感器 realism、平台族或 backend/fidelity claim。
- 打开 full counterfactual / experiment runtime；那属于 WP21。

## 3. 当前代码事实待验证

| 区域 | 当前事实 | WP20 含义 |
|------|----------|-----------|
| Platform capability contracts | `platform_capability_contracts.h` 已定义 `Capability`、`CapabilityBundle`、`ResolvedPlatformSpawnPlan`、validation helpers、family vocabulary 与 request kind。 | WP20 复用这些词汇，不新建平行 schema。 |
| Typed setup DTO | `world_batch_contracts.h` 已定义 `TypedPlatformSpawnRequest`、validation helpers 与 `BatchWorldSetupRequest.typed_platform_spawn_requests`。 | 缺失的是 admitted consumption 与 result evidence，而不是又一轮 DTO-only。 |
| Internal spawn path | `DefaultUnitFactory::spawn()` 已在 materialization 前解析 type-name 到 resolved spawn plan。 | WP20 可通过保留 compatibility type-name bridge 来公开 typed requests。 |
| Runtime/facade gap | `RuntimeFacade::apply_world_setup()` 会归一化 typed request world index，但 setup 执行仍只 materialize `WorldSpawnRequest`。 | WP20 必须选择显式 consume path 与 result ordering。 |
| WP14 guard state | WP14 guard 刻意禁止 typed request auto-materialization。 | WP20 需要改成 validation-first publicization guard。 |
| Backend/fidelity boundary | `RuntimeCapabilities` 仍是 backend/fidelity projection。 | Platform composition 必须留在 platform/setup contracts。 |

## 4. 工作包

| 工作包 | 状态 | 关注点 | 目标 | 产出 |
|--------|------|--------|------|------|
| `WP20-A Public Capability Fact Ledger` | pass | source facts and entry gate | 冻结 public capability-platform composition 的真实代码/测试事实，并识别最小安全公开 seam。 | [fact ledger](wp20_public_capability_fact_ledger_cluster_20260521.zh.md) |
| `WP20-B Public Typed Platform Spawn Contract` | focused pass | request/admission/result DTOs | 定义并实现 typed platform spawn 的 public admission/result contract，且不使其成为强制路径。 | [public spawn contract](wp20_public_typed_platform_spawn_contract_cluster_20260521.zh.md) |
| `WP20-C Runtime Setup Consume Bridge` | accepted / focused pass | runtime materialization bridge | 通过 existing compatibility-preserving resolved-plan bridge 消费 validated typed requests，并返回稳定 result evidence。 | [runtime setup consume bridge](wp20_runtime_setup_consume_bridge_cluster_20260521.zh.md) |
| `WP20-D Facade And Binding Public Surface` | accepted / focused pass | public API exposure | 通过 facade 与 Python bindings 暴露 admitted typed setup path，同时保留 legacy setup surfaces。 | [facade and binding surface](wp20_facade_binding_public_surface_cluster_20260521.zh.md) |
| `WP20-E Compatibility And Schema Guard` | pass | anti-regression guard | 把 WP14 "not materialized" guard 替换为 WP20 validation-first guard，并阻止 schema migration、backend naming drift 与行为变化。 | [compatibility/schema guard](wp20_compatibility_schema_guard_cluster_20260521.zh.md) |
| `WP20-F Integration And Handoff` | complete / accepted | closure lane | 集成 worker 结果、运行验证、记录 residuals、同步索引，并且只在实现证据存在后准备验收。 | [integration handoff](wp20_integration_handoff_cluster_20260521.zh.md) |

## 5. 并行规则

- `WP20-A`、`WP20-B` 与 `WP20-E` 可以作为第一轮并行流，只要写入范围互不重叠。
- `WP20-C` 已在 B contract 后返回，并通过 focused validation。
- `WP20-D` 已返回并通过 focused validation。
- `WP20-F` 已关闭为串行 closure lane。

## 6. Gate Rules

| Gate | 所需证据 | 失败条件 |
|------|----------|----------|
| `WP20-A` | platform contracts、typed DTO、internal resolution、public gaps 与 WP14/WP17/WP18/WP19 residuals 的 source/test ledger。 | 从过时假设推进，或重开 WP14 vocabulary。 |
| `WP20-B` | additive public admission/result contract，带 fail-closed rejection reasons 与稳定 result ordering。 | typed request 成为强制路径，或缺少 request/result evidence。 |
| `WP20-C` | runtime setup 只通过 validated/admitted typed requests 与 preserved `source_type_name` compatibility materialization。 | 任意 capability bundle 绕过 validation 或 type-name compatibility 被 materialize。 |
| `WP20-D` | facade/binding tests 证明 public visibility 与 fail-closed 行为，同时 legacy setup calls 保持兼容。 | public API 静默忽略 typed requests 或绕过 validation。 |
| `WP20-E` | guards 阻止 scenario-schema migration、backend `RuntimeCapabilities` 混用、行为变化与 type-name 兼容删除。 | WP20 改变 tactical behavior 或强制 caller 迁移。 |
| `WP20-F` | validation rollup、residual map、README/index sync、bilingual docs 与验收审查。 | 只凭计划文档创建验收。 |

## 7. 建议验证

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/test_wp14_*.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "spawn or world_setup"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "world_setup or capability or spawn"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/bindings/test_wp14_additive_platform_spawn_bindings.py
```

## 8. 非目标

- Big-bang spawn rewrite。
- 删除 type-name compatibility。
- 强制 public `spawn_platform` schema migration。
- Backend/fidelity capability promotion。
- 新战术行为、新平台族或新传感器/武器 realism。
- Full counterfactual / experiment runtime。
