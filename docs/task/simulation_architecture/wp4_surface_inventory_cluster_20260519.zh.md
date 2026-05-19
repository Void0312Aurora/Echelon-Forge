# WP4-A 规范分发表：Facade Surface Inventory

状态：`2026-05-19` 分发表；WP4 第一波任务。

语言版本：

- 英文主文：[wp4_surface_inventory_cluster_20260519.md](wp4_surface_inventory_cluster_20260519.md)
- 中文辅文：`wp4_surface_inventory_cluster_20260519.zh.md`

输入：

- [WP4 facade 对齐](facade_alignment_wp4_20260519.zh.md)
- [WP4 facade 对齐计划审查](../review/wp4_facade_alignment_plan_review_20260519.zh.md)
- [WP2.5 调度语义冻结](scheduler_semantics_wp25_20260519.zh.md)
- [Temp-02 SCAL 架构愿景审查](../review/temp-02_review_20260519.zh.md)
- 当前 `src/runtime/facade/*` 与 `src/interfaces/python/bindings_runtime.cpp`

规范语言：

- `MUST` 表示维护中文档和后续实现必须满足的 WP4 行为。
- `MUST NOT` 表示不能成为维护中 facade truth 的行为。
- `SHOULD` 表示默认规则；偏离需要明确 review note。
- `MAY` 表示允许的兼容或文档路径。

## 一、目的

本表把 `WP4-A Facade Surface Inventory` 变成有边界的任务簇。它是 WP4 后续工作的共享词汇冻结。

WP4-A 必须在 worker 添加或调整 facade 行为前，产出 canonical surface map。它应吸收 WP4 计划审查中的结论：

- `ObservationViewSpec` 是独立的 policy/test-owned surface concept。
- `DecisionBelief` 是从声明过的 observation input 派生出的 policy/agent-side belief layer，而不是 `World Truth`。
- `DiagnosticsTrace` 需要明确 facade/evidence surface 决策，即使首轮实现仍 piggyback 在 engagement export 上。
- 每个 surface 对 WP2.5 调度语义的依赖必须声明。
- 在 public surface 继续增长前，应记录 facade endpoint governance。

## 二、分发交付物

| 流 | 必需输出 | owner 类型 | 思考预算 |
|----|----------|------------|----------|
| `WP4-A1 Surface Catalog` | maintained、compatibility-only、diagnostics-only 与 deferred facade surface 的 canonical table。 | Facade surface worker。 | 高。 |
| `WP4-A2 Observation And Belief Boundary` | `ObservationViewSpec`、`ObservationPacket` 与 `DecisionBelief` provenance 规则。 | Information-state worker。 | 高。 |
| `WP4-A3 Diagnostics Surface Decision` | 判断 `DiagnosticsTrace` 现在是否成为独立 facade surface，或作为 WP4 piggyback 并设置 WP5 promotion gate。 | Diagnostics worker。 | 中高。 |
| `WP4-A4 Endpoint Governance` | per-surface metadata 字段与 `RuntimeFacade` 拆分阈值规则。 | 偏集成的 facade worker。 | 中。 |
| Cluster integration | 中英文段落对齐与 `git diff --check`。 | 主集成 owner。 | 中。 |

## 三、必需 Surface Metadata

每个维护中的 WP4 surface 条目必须声明：

| 字段 | 规则 |
|------|------|
| `surface_name` | 稳定的 C++/Python-facing request、result、packet 或 concept name。 |
| `classification` | `maintained`、`compatibility_adapter`、`diagnostics_only`、`deferred` 之一。 |
| `consumer_group` | `frontend`、`policy`、`orchestration`、`test`、`diagnostics`、`binding` 或 `backend`。 |
| `request_dto` | request/input DTO 名称；pure query/export concept 可为 `none`。 |
| `result_dto` | result/output DTO 名称、packet 名称或声明的 concept output。 |
| `source_layer` | simulation、facade、policy、orchestration、adapter、human 或 diagnostics。 |
| `snapshot_semantics` | Source `SnapshotVersion`、observation version、event ancestry 或 `not_applicable`。 |
| `scheduler_dependency` | WP2.5 依赖，例如 `event_order`、`barrier_visibility`、`clock_domain`、`state_shard_version`、`replay_metadata` 或 `none`。 |
| `information_state_layer` | `WorldTruth`、`SensedState`、`TrackState`、`SharedTacticalPicture`、`AgentObservation`、`DecisionBelief` 或 `not_applicable`。 |
| `compatibility_rule` | legacy/raw access 是否允许，以及携带什么 diagnostics label。 |
| `deprecation_rule` | 移除或收窄 compatibility path 的条件。 |
| `validation_gate` | 证明 surface 安全的 test、architecture gate 或 WP5 tier。 |

## 四、需冻结的 Surface 决策

WP4-A 至少必须分类这些 surface：

| Surface | 默认 WP4-A 决策 |
|---------|-----------------|
| `BatchWorldSetupRequest` / `BatchWorldSetupResult` | 维护中的 setup/reset surface。 |
| `ObservationViewSpec` | 独立 policy/test-owned concept，带 schema version 与 required/optional field 规则。 |
| `ObservationBatchRequest` / `ObservationBatchPacket` | 基于声明 observation provenance 的维护中 facade export。 |
| `DecisionBelief` | 只有来自声明 observation 或 memory/estimator state 时才是 maintained；truth-derived belief 是 diagnostics-only。 |
| `EngagementBatchRequest` / `EngagementEventPacket` | 维护中的 engagement export；producer coverage 必须显式。 |
| `ExecutionBatchStepRequest` / `ExecutionBatchStepResult` | 维护中的 step/result surface。 |
| `ActionIntentPacket` / `ActionHoldPolicy` | Facade-compatible policy action input；依赖 clock domain 与 replay metadata。 |
| `CoordinationIntentPacket` | Facade-compatible coordination input；依赖 external injection 与 merge policy。 |
| `AgentRole` | Agent boundary concept：role、authority、information source、decision model、action interface。 |
| `RewardSpec` / `RewardReport` | 拆分 simulation fact 与 shaping term。 |
| `TerminationSpec` / `EpisodeStatus` | 拆分 semantic termination 与 orchestration truncation。 |
| `EpisodeLifecycleContract` | compiled/facade phase authority，adapter 只 mirror。 |
| `DiagnosticsTrace` | 维护中 diagnostics query/export surface，或记录为 WP4 piggyback 并设置 WP5 promotion gate。 |
| `RuntimeFacade::runtime()` / raw `WorldBatchRuntime` | compatibility-only diagnostics escape hatch。 |
| `RuntimeCapabilities` / backend capability query | 推迟到 backend profile work，除非需要记录既有空 surface。 |

## 五、Observation 与 Belief 规则

WP4-A 必须声明：

1. `ObservationViewSpec` 拥有 schema version、required field、optional field、feature encoding、normalization、masking、stacking 与 checkpoint compatibility behavior。
2. `ObservationPacket` 拥有在声明 barrier 或 snapshot version 上采样的 facade-exported data。
3. `DecisionBelief` 不是 world truth。它必须声明 consumed observation version 或声明过的 memory/estimator state。
4. Truth-derived oracle material 必须标记为 `diagnostics_only`。
5. 任何使用 belief metadata 的维护中 policy 或 orchestration adapter，都必须能说明消费它的 `AgentRole`。

## 六、Facade 拆分阈值

WP4 默认不拆分 `RuntimeFacade`。WP4-A 应记录此规则：

```text
If RuntimeFacade exceeds 40 maintained public methods, plan a split into
RuntimeSessionFacade, WorldSetupFacade, ExecutionStepFacade,
ObservationFacade, EngagementFacade, DiagnosticsFacade, and
BackendCapabilityFacade.
```

该阈值是治理触发器，不是自动重构命令。

## 七、退出标准

本任务簇退出条件：

1. WP4 有一张后续 worker 可以引用的 canonical surface inventory。
2. `ObservationViewSpec`、`DecisionBelief`、`AgentRole` 与 `DiagnosticsTrace` 有明确 WP4 classification。
3. 每个 maintained surface 都声明 scheduler dependency 或写明 `none`。
4. compatibility-only 与 diagnostics-only 路径不会被误认为维护中 policy/training truth。
5. 中文 companion 足够对齐，可用于任务分发。
