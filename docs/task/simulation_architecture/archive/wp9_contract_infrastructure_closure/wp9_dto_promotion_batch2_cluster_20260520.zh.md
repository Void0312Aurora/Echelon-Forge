# WP9-B DTO Promotion Batch 2

状态：`2026-05-20` complete / accepted WP9 并行流。

语言版本：

- 英文主文：[wp9_dto_promotion_batch2_cluster_20260520.md](wp9_dto_promotion_batch2_cluster_20260520.md)
- 中文辅文：`wp9_dto_promotion_batch2_cluster_20260520.zh.md`

输入：

- [WP9 contract and infrastructure closure](contract_infrastructure_closure_wp9_20260520.zh.md)
- [仿真系统架构设计](../../../plan/architecture/simulation_system_architecture_design.zh.md)
- [WP4 facade 对齐验收](../../review/archive/wp-acceptance/wp4_facade_alignment_acceptance_review_20260519.zh.md)
- [WP5 information/belief 审查](../../review/archive/wp-superseded/wp5_information_belief_acceptance_review_20260519.zh.md)
- [WP8 学习面](../wp8_learning_face/learning_face_wp8_20260520.zh.md)

## 1. 目的

WP9-B 晋升第二批 policy、coordination、role 与 belief 边界 DTO。这些 DTO 让 agentic 侧显式化，但不允许 raw ECS 或 hidden truth mutation。

本流覆盖：

- DTO-5 `ActionIntentPacket`
- DTO-6 `CoordinationIntentPacket`
- DTO-7 `AgentRole`
- DTO-8 `DecisionBelief`

## 2. 必需 DTO 形状

| DTO | 必需字段 | Ownership 规则 |
|-----|----------|----------------|
| `ActionIntentPacket` | `source_id`、`effective_time_s`、`valid_until_s`、`target`、`action_family`、`merge_policy`、action-interface discriminator | Policy 产出 intent；runtime/facade 在 command/control injection point 翻译它。 |
| `CoordinationIntentPacket` | `source_type`、`source_id`、`target_roster`、`update_clock`、`merge_policy`、produced tasking/leader-intent references | Scripted、learned 与 human director 只通过 tasking/command facade path 进入。 |
| `AgentRole` | `role`、`authority_scope`、`information_state_source`、`decision_model_ref`、`action_interface` | Policy model 本身不是 agent；它挂在 typed role boundary 上。 |
| `DecisionBelief` | `belief_id`、`source_observation_versions`、`memory_or_estimator_ref`、`confidence_shape`、`maintained_status`、diagnostics reason | Maintained belief 必须来自声明过的 observation 或 memory/estimator state。Truth/raw ECS 使用只能是 diagnostics-only。 |

## 3. 实施路线

推荐路线：

1. 在 policy/intent/decision contract header 中添加 typed C++ contract structs。
2. 保持 DTO 为 passive 和 serializable；不要直接 mutate runtime state。
3. 添加 Python bindings 与 focused shape/default tests。
4. 添加 architecture checks，证明 `DecisionBelief` 与 `ObservationPacket` 保持分离。
5. 为仍保留的 Python shim labels 添加 compatibility notes。

推荐写入范围：

- `src/runtime/contracts/*`
- `src/runtime/facade/runtime_facade_types.h`
- `src/interfaces/python/bindings_runtime.cpp`
- `python/rl/runtime/*` 仅用于 compatibility label alignment
- `tests/runtime/bindings/*`
- `tests/runtime/test_agent_shim.py`
- `tests/architecture/*`

冲突提示：

- 与 WP9-A 共享的 binding glue 必须协调。如果两路同时活跃，WP9-B 应优先添加 C++ contracts 与 tests，然后把共享 Python module wiring 留给 WP9-E，除非被指定为 integration owner。

## 4. 工作项

| 流 | 必需产出 | 预算 |
|----|----------|------|
| `WP9-B1 ActionIntentPacket` | 带 validity window、action family 与 cross-layer `merge_policy` 的 typed action intent。 | High. |
| `WP9-B2 CoordinationIntentPacket` | 带 roster、source、clock 与 merge semantics 的 typed coordination/director intent。 | High. |
| `WP9-B3 AgentRole` | 把五元素 role schema 从 passive labels 晋升为 typed contract。 | High. |
| `WP9-B4 DecisionBelief` | 带 maintained/diagnostics-only status 与 observation provenance 的 typed belief boundary。 | Xhigh. |

## 5. 非目标

- 不实现完整 policy engine。
- 不让 intent DTO 绕过 command/tasking facade path。
- 不把 learned latent state 当作 world truth。
- 除非 compatibility tests 同步更新，否则不删除现有 Python shims。
- 不把 policy `merge_policy` 命名与 WP2.5 clock merge semantics 混同。

## 6. 验收 Gate

WP9-B 满足以下条件后可进入 WP9-E：

1. DTO-5 至 DTO-8 都有 typed fields 与 defaults。
2. Python surface 暴露 typed fields，或记录准确 binding blocker。
3. Tests 证明 intent DTO 是 passive contracts，而不是 direct mutation handles。
4. Tests 或 docs 证明 `DecisionBelief` 与 `World Truth` 保持分离。
5. 剩余 shared binding/index work 已明确交给 WP9-E。

## 7. 验证命令

```bash
git diff --check
pytest tests/runtime/bindings tests/runtime/test_agent_shim.py tests/architecture
rg -n "ActionIntentPacket|CoordinationIntentPacket|AgentRole|DecisionBelief|merge_policy|World Truth" src python tests docs/task/simulation_architecture/wp9_contract_infrastructure_closure
```
