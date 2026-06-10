# WP6 后端配置文件策略验收审查

状态：`2026-05-19` WP6 验收已完成。

范围：WP6-A backend profile taxonomy 与 registry、WP6-B parity budget 与
comparison rules、WP6-C resident-state 与 capability projection 对齐，以及
WP6-D 发布/index 同步。

相关文档：

- [WP6 后端配置文件策略](../simulation_architecture/backend_profile_policy_wp6_20260519.zh.md)
- [WP6-A 后端配置文件注册表](../simulation_architecture/wp6_backend_profile_registry_20260519.zh.md)
- [WP6-B parity budget 注册表](../simulation_architecture/wp6_parity_budget_registry_20260519.zh.md)
- [WP6-C1 resident-state 边界规则](../simulation_architecture/wp6_resident_state_boundary_rules_20260519.zh.md)
- [WP6-C/D 集成与 index 同步](../simulation_architecture/wp6_integration_and_index_sync_20260519.zh.md)

## 1. 验收决定

WP6 backend profile policy 予以验收。

已验收的 WP6 线定义了 backend profile metadata、profile-owned parity budget、
resident-state ownership 与 sync gate，以及保守的 runtime capability projection。
它没有把 exact GPU execution、resident-state truth、device observation view 或
shadow comparison 提升为维护中支持。

## 2. 已验收产物

已验收的 WP6 产物：

1. `cpu_exact.reference` 是初始 backend profile registry 中唯一维护中的 exact baseline。
2. `gpu_helpers.diagnostics_only`、`gpu_exact.unmaintained_candidate`、
   `resident_state.unmaintained_candidate` 与
   `shadow_compare.unmaintained_candidate` 仍为 diagnostics-only 或 unmaintained candidate。
3. `parity_budget.cpu_exact.reference.v1` 是维护中的 reference budget；GPU helper、
   GPU exact、resident-state 与 shadow budget 仍为 diagnostics-only 或 candidate record。
4. `event_order` 与 `snapshot_versions` 是 exact-only identity domain。
5. Numeric tolerance 必须显式声明 field family、comparator 与 threshold。
6. Observation export 拥有 exact envelope；payload comparison 继承 `numeric_state`。
7. Diagnostics prose 不参与维护中真值。
8. `RuntimeCapabilities` 保持 projection。它不能仅凭 helper/probe availability
   推断 exact GPU、resident-state 或 shadow support。

## 3. 验证

构建命令：

```bash
cmake --build build-workshop --target ef_py -j2
```

结果：通过。

WP6 聚焦命令：

```bash
python -m pytest tests/runtime/facade/test_runtime_facade.py tests/test_gpu_runtime_bindings.py tests/architecture/runtime_facade -q
```

结果：`31 passed`。

文档检查：

```bash
git diff --check
rg -n "backend_profile_id|profile_class|parity_budget_ref|validation_gate" docs/task/simulation_architecture/wp6_backend_profile_registry_20260519*.md
rg -n "budget_id|comparison_domains|sync_barriers|mismatch_policy|acceptance_gate" docs/task/simulation_architecture/wp6_parity_budget_registry_20260519*.md
rg -n "resident_state\\.unmaintained_candidate|supports_resident_state|backend thread completion order|unsynced backend-local state" docs/task/simulation_architecture/wp6_resident_state_boundary_rules_20260519*.md
```

结果：通过。

## 4. Deferred 后续项

以下项目保持可见，但不阻断 WP6 验收：

1. 维护中的 exact GPU backend profile 需要后续 registry revision、exact parity
   budget、replay evidence、ownership/sync declaration 与 validation gate。
2. 维护中的 resident-state profile 需要 backend-owned state scope、host-visible
   reconstruction 或 export rule、sync barrier 与维护中的 parity budget。
3. 维护中的 shadow-compare profile 如果要超过 diagnostics-only reporting，需要
   non-interference rule、diagnostics separation，以及维护中的 comparison budget。
4. 专门的 `BackendCapabilityFacade` 可在后续引入，但它必须消费已声明 registry
   metadata，而不是隐藏 implementation truth。
5. Machine-readable registry generation 可在文档 registry 形态稳定后继续推进。

## 5. 收口

WP6 完成了当前架构线的 backend profile policy 层。后续 backend 工作在修改维护中的
capability projection 前，应先修订 registry，并引用本验收审查。
