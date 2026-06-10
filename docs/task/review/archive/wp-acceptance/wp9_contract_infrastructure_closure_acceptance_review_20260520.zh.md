# WP9 Contract And Infrastructure Closure 验收审查

状态：`2026-05-20` accepted，并保留一个已跟踪残余项。

语言版本：

- 英文主文：[wp9_contract_infrastructure_closure_acceptance_review_20260520.md](wp9_contract_infrastructure_closure_acceptance_review_20260520.md)
- 中文辅文：`wp9_contract_infrastructure_closure_acceptance_review_20260520.zh.md`

输入：

- [WP9 Contract And Infrastructure Closure](../simulation_architecture/wp9_contract_infrastructure_closure/contract_infrastructure_closure_wp9_20260520.zh.md)
- [WP9-A DTO Promotion Batch 1](../simulation_architecture/wp9_contract_infrastructure_closure/wp9_dto_promotion_batch1_cluster_20260520.zh.md)
- [WP9-B DTO Promotion Batch 2](../simulation_architecture/wp9_contract_infrastructure_closure/wp9_dto_promotion_batch2_cluster_20260520.zh.md)
- [WP9-C Infrastructure Closure](../simulation_architecture/wp9_contract_infrastructure_closure/wp9_infrastructure_closure_cluster_20260520.zh.md)
- [WP9-D Guard Enforcement](../simulation_architecture/wp9_contract_infrastructure_closure/wp9_guard_enforcement_cluster_20260520.zh.md)
- [WP9-E Integration And Index Sync](../simulation_architecture/wp9_contract_infrastructure_closure/wp9_integration_and_index_sync_cluster_20260520.zh.md)
- [WP9 guard allowlist evidence](../simulation_architecture/wp9_contract_infrastructure_closure/wp9_guard_allowlist_evidence_20260520.md)

## 1. 结论

WP9 通过验收。DTO promotion、diagnostics facade 暴露、guard enforcement、
manifest completion、capability-trigger wording、facade split governance 与
index sync 均已完成，并有测试证据支撑。

保留一个显式残余项：

- `INF-6` real missile terminal effects capture 仍阻塞给后续 owner，因为
  `src/systems/combat/damage_system.h` 尚无窄的 maintained kernel recorder
  seam。WP9 已在 WP3 任务族记录该 handoff，并保持当前 debug/synthetic
  recorder path 可见。

## 2. Gate 结论

| Gate | 结论 | 证据 |
|------|------|------|
| `WP9-A DTO Promotion Batch 1` | pass | `runtime_dto_contracts.h`、facade result fields、Python bindings 与 DTO/facade tests 覆盖 `RewardReport`、`TerminationSpec`、observation metadata 与 `ObservationViewSpec`。 |
| `WP9-B DTO Promotion Batch 2` | pass | `policy_contracts.h`、Python bindings、agent-shim alignment 与 policy/belief tests 覆盖 `ActionIntentPacket`、`CoordinationIntentPacket`、`AgentRole` 与 `DecisionBelief`。 |
| `WP9-C Infrastructure Closure` | pass with tracked residual | INF-1 至 INF-5 以及 INF-7 已关闭；INF-6 作为带 owner context 和测试可见证据的 blocked handoff 保留。 |
| `WP9-D Guard Enforcement` | pass | `test_wp9_guard_enforcement.py` 与 `wp9_guard_allowlist_evidence_20260520.md` 执行带标签的 `sim.*` 例外；binding smoke 覆盖 empty engagement packet shell defaults。 |
| `WP9-E Integration And Index Sync` | pass | 仿真架构 README、WP9 docs、review index 与本双语验收包已同步。 |

## 3. DTO 证据

| ID | 结论 | 证据 |
|----|------|------|
| DTO-1 `RewardReport` | pass | `src/runtime/contracts/runtime_dto_contracts.h`；`ExecutionBatchStepResult.reward_reports`；`ef_py.RewardReport`；`tests/runtime/facade/test_runtime_dto_promotion_batch1.py`。 |
| DTO-2 `TerminationSpec` | pass | `src/runtime/contracts/runtime_dto_contracts.h`；`ExecutionBatchStepResult.termination_specs`；`ef_py.TerminationSpec`；batch-1 DTO tests。 |
| DTO-3 `ObservationBatchPacket` metadata | pass | `ObservationBatchPacket` 上的 `snapshot_version`、`barrier_id` 与 `source_time_s`；binding 与 trace-replay tests。 |
| DTO-4 `ObservationViewSpec` | pass | Typed view spec、compatibility report 与 `evaluate_observation_view_checkpoint_compatibility`。 |
| DTO-5 `ActionIntentPacket` | pass | `src/runtime/contracts/policy_contracts.h`；`ef_py.ActionIntentPacket`；policy surface tests。 |
| DTO-6 `CoordinationIntentPacket` | pass | `src/runtime/contracts/policy_contracts.h`；`ef_py.CoordinationIntentPacket`；policy surface tests。 |
| DTO-7 `AgentRole` | pass | C++ `AgentRole`、binding surface 与 Python shim compatibility alignment。 |
| DTO-8 `DecisionBelief` | pass | C++ `DecisionBelief`、binding surface，以及保持 truth/raw ECS path 为 diagnostics-only 的 architecture tests。 |

## 4. Infrastructure 证据

| ID | 结论 | 证据 |
|----|------|------|
| INF-1 `clock_merge_policy` naming | pass | Architecture 与 WP2.5 docs 把 `clock_merge_policy` 保留给 scheduler semantics，把 `merge_policy` 保留给 cross-layer intent request。 |
| INF-2 diagnostics facade surface | pass | `RuntimeFacade::export_diagnostics_traces`、Python binding、facade 与 engagement tests。 |
| INF-3 `RuntimeCapabilities` trigger | pass | WP6、WP7 与 architecture docs 声明 richer projection 需等待 maintained non-reference backend profile。 |
| INF-4 `StageNodeManifest` registry completion | pass | WP2.5 manifest cluster 包含 P0-P10 示例；architecture doc test 检查中英文覆盖。 |
| INF-5 facade split threshold | pass | Architecture doc 与 facade README 记录约 40-method split rule 和目标分组。 |
| INF-6 terminal effects capture | tracked residual | WP3 task docs 记录 blocked handoff；WP9 没有强行进行大范围 damage-system rewrite。 |
| INF-7 recent-event storage strategy | pass | Recent-event capture 被形式化为 monotonic id、export sorted recent window，与 event-order evidence 对齐。 |

## 5. Guard 证据

| ID | 结论 | 证据 |
|----|------|------|
| GUA-1 `sim.*` AST guard | pass | `tests/architecture/compatibility_quarantine/test_guard_enforcement.py` 执行带标签 direct-sim access allowlist。 |
| GUA-2 binding surface smoke promotion | pass | `tests/runtime/bindings/test_bindings_engagement_surface.py` 覆盖默认 `world_index=0` 的 empty engagement packet shell。 |

## 6. 验证命令

已通过：

```bash
git diff --check
cmake --build build --target ef_py -j2
CMO_BUILD_DIR=/home/void0312/Workshop/CMO/build pytest -q tests/architecture/runtime_facade/test_dto_contracts_batch1.py tests/architecture/policy_execution/test_belief_and_read_side_boundaries.py tests/architecture/compatibility_quarantine/test_guard_enforcement.py tests/architecture/governance/test_infrastructure_closure_docs.py tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/bindings/test_bindings_policy_surface.py tests/runtime/bindings/test_bindings_engagement_surface.py tests/runtime/facade/test_runtime_dto_promotion_batch1.py tests/runtime/facade/test_runtime_facade.py tests/runtime/engagement/test_facade_engagement_export.py tests/runtime/engagement/test_live_engagement_event_capture.py tests/runtime/engagement/test_trace_replay_gates.py tests/runtime/test_agent_shim.py tests/runtime/mission/test_policy_contract_shape.py
```

聚焦 integration test 命令通过，结果为 `89 passed`。

发布后最终验证已通过：

```bash
CMO_BUILD_DIR=/home/void0312/Workshop/CMO/build pytest -q tests/architecture tests/runtime/bindings tests/runtime/engagement tests/runtime/facade
rg -n "WP9|Contract And Infrastructure Closure|RewardReport|TerminationSpec|ObservationViewSpec|ActionIntentPacket|CoordinationIntentPacket|AgentRole|DecisionBelief|DiagnosticsTrace|StageNodeManifest|sim\\.\\*" docs/task/simulation_architecture docs/task/review docs/plan/architecture src tests
```

最终 scoped validation 命令通过，结果为 `121 passed`。

## 7. 残余风险

- `INF-6` 作为命名 follow-up 保持 open。下一 owner 应先围绕 guidance/effects
  terminal hit resolution 添加窄的 maintained recorder seam，再把 recent-event
  DTO capture 从 debug/synthetic proximity-hit path 迁出。
- 本审查未运行全仓 pytest；已检查的 focused 与 final scoped 命令覆盖
  WP9 architecture、bindings、engagement、facade、DTO、guard 与 integration
  surfaces。

## 8. 双语对齐

WP9 任务族、五个 cluster 文档、guard allowlist evidence、仿真架构 README
以及本验收审查均按项目约定提供中英文入口。
