# WP4-I Compatibility Guard 笔记

状态：`2026-05-19` guard review 已作为 WP4 evidence 验收；WP5 handoff 已完成。

输入：

- [WP4-I compatibility guard 任务簇](wp4_compat_guard_cluster_20260519.zh.md)
- [WP4 第一波验收审查](../review/wp4_first_wave_acceptance_review_20260519.zh.md)
- [WP4-A surface inventory 初稿](wp4_surface_inventory_wp4a_20260519.zh.md)
- [WP4-D/E policy-binding 对齐笔记](wp4_policy_binding_alignment_notes_20260519.zh.md)
- `tests/architecture/test_runtime_facade_layering.py`

本文记录当前 compatibility-only 路径的 guard 覆盖情况。本文不移除
compatibility adapter，也不实现 facade/runtime 变更。

## 1. Guard 结论

现有 architecture guard 有用，但还不完整。

它已经覆盖维护中 batch facade 路径里风险最高的回归：raw
`WorldBatchRuntime` 与 `RuntimeFacade::runtime()` 访问必须留在
`world_batch_vec_env` 和 `leader_world_batch_runtime` 的显式 adapter surface 中。

它还不能阻止所有 direct `sim.*` policy input，因为当前仓库仍有大量 legacy
Gym、scenario-loader、reward、teacher、oracle 和 test 路径有意使用 direct
`sim.*`，这些路径在 WP4-A/D/E 中被分类为 `compatibility_adapter` 或
`diagnostics_only`。现在做全局 grep/AST 禁止会产生误报，并阻塞迁移工作。

## 2. 现有 Guard 覆盖

| Guard area | 当前覆盖 | 评估 |
|------------|----------|------|
| `world_batch_vec_env.py` 中的 `RuntimeFacade::runtime()` 使用 | AST test 只允许 `_RuntimeFacadeAdapter` 内调用 `runtime()`。 | 对当前 batch facade adapter 边界足够。 |
| `world_batch_vec_env.py` 中的 `ef_py.WorldBatchRuntime` fallback | AST test 只允许 `_RuntimeFacadeAdapter` 内构造。 | 对当前 fallback 位置足够。 |
| 主 `WorldBatchVecEnv` class 的 raw-runtime coupling | 字符串 guard 阻止 `_runtime_facade`、`_batch_runtime` 与 `.compat_runtime` 出现在主 class 中。 | 对维护中的 batch env path 是有效回归 guard。 |
| `leader_world_batch_runtime.py` raw world handle | Tests 禁止 raw `batch_runtime.world(...)`、`world_vec.batch_runtime.world(...)`、direct batch getter/action/step call 和 `runtime()`。 | 对 leader batch runtime path 是有效 guard。 |
| `RuntimeFacade::runtime()` 文档化 | Test 检查 C++ header 和 facade README 是否说明 compatibility-only 用途。 | 对 escape hatch 的文档 gate 足够。 |
| Runtime contract/facade type header layering | Tests 防止 contract/facade type header include `core/engine/*`。 | 是有效 compile-layering guard。 |
| `RuntimeFacade` public header ownership boundary | Test 确认 engine owner storage 仍通过 forward declaration 隐藏。 | 是有效 C++ facade boundary guard。 |

## 3. 已知缺口

| 缺口 | 为什么暂时 pending | 后续必要 guard |
|------|-------------------|----------------|
| Legacy Gym/scenario 路径里的 direct `sim.*` policy input。 | 现有 single-world 与 scenario-loader 路径仍使用 direct `sim.get_agent_observation`、`sim.get_instrument_state`、`sim.set_pilot_action`、visual helper、reward helper 与 teacher/oracle utility。它们在 WP4-A/D/E 中被分类为 compatibility 或 diagnostics。 | WP4-H 命名 maintained shim 后，增加 allowlist-based AST guard，禁止 registered compatibility module 之外的 direct `sim.*`。 |
| Raw `WorldBatchRuntime` Python binding 仍暴露。 | 该 binding 有意保留给兼容、测试和低层 diagnostics。 | 增加 binding-level 文档或测试，防止新文档把它宣传为 maintained frontend path。 |
| `ObservationPacket` provenance 尚未 runtime-enforced。 | 当前 `ObservationBatchPacket` 缺少完整 `SnapshotVersion`、barrier 与 `ObservationViewSpec` metadata。 | runtime metadata 存在后，WP5 information/belief gate 应拒绝无法命名 observation provenance 的 maintained policy path。 |
| `DecisionBelief` 与 `AgentRole` 还不是 runtime DTO。 | WP4-A 已分类；WP4-D/H 仍需创建 shim 或 contract sketch。 | `AgentRole` 与 belief label 存在后，添加 policy shim tests。 |
| `DiagnosticsTrace` 是 piggyback evidence，不是 dedicated diagnostics facade。 | 第一波验收有意保持 diagnostics-only，并 piggyback on engagement export。 | WP5 trace conformance 决定是否需要 dedicated diagnostics query。 |

## 4. Direct `sim.*` Policy Input 审查

当前 direct `sim.*` 使用可以分为四类：

1. Legacy single-world Gym 路径，例如 `gym_envs/universal_env.py` 和
   `gym_envs/universal_env_parts/*`。
2. Scenario-loader behavior、navigation、command-chain、reward、shaping 与
   step-evaluation helper。
3. Teacher、oracle、diagnostics 与 test-support utility。
4. 有意测试低层 simulation 行为的 runtime tests。

这些路径今天不应被标记为 maintained WP4 frontend path。除非它们消费带声明 provenance 的 facade-exported `ObservationPacket` 数据，否则保持
`compatibility_adapter`；当它们依赖 privileged oracle/truth material 时，标记为
`diagnostics_only`。

## 5. 推荐低风险 Guard 计划

现在不要添加全局禁止。采用分阶段 guard 计划：

1. 保留现有 `_RuntimeFacadeAdapter`、`WorldBatchVecEnv` 与
   `leader_world_batch_runtime.py` architecture tests。
2. 在 WP4-H 中为 `AgentRole`、`ActionIntent`、`CoordinationIntent`、
   observation provenance 与 oracle path 增加显式 Python-side label 或 shim。
3. 这些 label 存在后，添加 AST guard 扫描 maintained policy packages，只允许小型 registered compatibility list 中的 direct `sim.*`。
4. 在 WP5 中，把该 guard 提升为 information/belief leakage tests，用于区分 maintained `ObservationPacket` 或声明过的 `DecisionBelief` input，以及
   `WorldTruth` 和 diagnostics-only oracle input。

## 6. 索引状态

已检查索引：

- `docs/task/simulation_architecture/README.md`
- `docs/task/simulation_architecture/README.zh.md`
- `docs/task/review/README.md`
- `docs/task/review/README.zh.md`

当前状态：

- WP4 第一波与第二波验收审查已索引。
- WP4-A surface inventory、WP4-B/C notes、WP4-D/E notes 已索引。
- WP4-G、WP4-H 与 WP4-I 第二波任务簇已索引。
- WP4-F 集成交接与最终验收审查已从 simulation architecture 与 review 记录索引。

本文不需要在 review index 中增加重复条目。

## 7. WP5 Handoff

WP5 可以立即验证：

- 维护中的 batch facade path 没有新增 raw runtime handle 逃逸；
- `RuntimeFacade::runtime()` 仍被记录为 compatibility-only；
- contract/facade type header 不 include engine owner；
- engagement diagnostics 可以作为 piggyback evidence 检查；
- 第一波 surface classification 可以作为 validation label 使用。

WP5 应等待后续 runtime/provenance metadata 后再强制：

- 对所有 policy path 的 direct `sim.*` ban；
- `ObservationViewSpec` schema compatibility；
- `ObservationPacket` source `SnapshotVersion` 与 barrier metadata；
- `DecisionBelief` provenance；
- `AgentRole` authority 与 action-interface metadata；
- dedicated diagnostics-facade 要求。
