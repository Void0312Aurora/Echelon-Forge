# WP12-C Information Transformation Surface

状态：`2026-05-20` accepted / implementation mergeable。

语言版本：

- 英文主文：[wp12_information_transformation_surface_cluster_20260520.md](wp12_information_transformation_surface_cluster_20260520.md)
- 中文辅文：`wp12_information_transformation_surface_cluster_20260520.zh.md`

输入：

- [WP12 information and agency enforcement](information_agency_enforcement_wp12_20260520.zh.md)
- [Post-WP9 gap analysis](../../review/post_wp9_gap_analysis_20260520.zh.md)
- [仿真系统架构设计](../../../plan/architecture/simulation_system_architecture_design.zh.md)

## 1. 目的

`WP12-C` 让架构中的 information-state transformations 在第一个 maintained
slice 中变成可机器检查。目标不是重写每个 producer，而是暴露一个稳定的
transformation vocabulary 和 evidence surface，供后续 producer 逐步接入。

必需 transformation chain：

```text
World Truth -> Sensed State
Sensed State -> Track State
Track State -> Shared Tactical Picture
Shared Tactical Picture -> Agent Observation
Agent Observation -> Decision Belief
Decision Belief -> ActionIntentPacket
```

## 2. 范围

范围内：

- 添加 canonical transformation-name vocabulary 或 registry；
- 为每个 transformation 关联 source layer、target layer 与 evidence
  requirements；
- 要求 selected slice 中的 maintained packet/belief fixtures 命名自己的
  transformation step；
- 添加 architecture 或 runtime tests，拒绝缺失或非法 transformation
  declarations；
- 将 diagnostics-only truth paths 保持为显式 diagnostics-only。

范围外：

- 完整 sensor model rewrite；
- 完整 track fusion 或 data-link implementation；
- 完整 Shared Tactical Picture producer；
- 一次性改变所有 observation schemas；
- backend/fidelity 或 capability-composition work。

## 3. 候选实现接缝

编辑前检查：

- `src/runtime/contracts/policy_contracts.h`
- `src/runtime/facade/runtime_facade_types.h`
- `src/runtime/facade/runtime_facade.cpp`
- `src/interfaces/python/bindings_runtime.cpp`
- `tests/runtime/facade/test_runtime_facade.py`
- `tests/runtime/bindings/test_bindings_runtime_dto_surface.py`
- `tests/architecture/test_policy_belief_boundaries.py`

优先方式：

- 尽量复用 `InformationStateSource` 与 WP11 provenance vocabulary；
- 把 transformation evidence 建模为 contract metadata 或 helper validation，
  而不是大范围 runtime rewrite；
- 至少在 focused maintained path 证明 `Shared Tactical Picture -> Agent Observation`
  与 `Agent Observation -> Decision Belief`。

## 4. Gate 规则

| Boundary | 必需行为 |
|----------|----------|
| Known transformation | 声明 source layer、target layer、stable name 与 evidence requirement。 |
| Maintained packet/belief | 命名合法 transformation step 与 source version/provenance。 |
| Illegal direct jump | 除非显式 diagnostics-only，否则拒绝。 |
| Unknown transformation | 在 focused tests 中 fail closed。 |
| Diagnostics transformation | 只有标记为 diagnostics-only 且不作为 maintained decision evidence 时允许。 |

## 5. 验收测试

最低测试：

- canonical transformation vocabulary 对测试可见；
- maintained packet 或 belief 命名合法 transformation step；
- 缺失 transformation metadata 时失败；
- 非法 `World Truth -> ActionIntentPacket` maintained shortcut 失败；
- diagnostics-only shortcut 保持显式；
- tests 不声明所有 producer 已迁移。

## 6. 交付契约

返回：

- touched transformation vocabulary/registry/helper files；
- touched packet/belief metadata fields 或 validators；
- 新增或更新的 tests；
- 精确 commands run 与 outcomes；
- 更广 producer adoption 的 blockers 和 residuals；
- 给 `WP12-D` 与 `WP12-E` 的 integration notes。
