# WP2.5 调度语义验收审查

状态：`2026-05-19` 已验收。

语言版本：

- 英文主文：[wp25_scheduler_semantics_acceptance_review_20260519.md](wp25_scheduler_semantics_acceptance_review_20260519.md)
- 中文辅文：`wp25_scheduler_semantics_acceptance_review_20260519.zh.md`

范围：

- [WP2.5 调度语义冻结](../simulation_architecture/scheduler_semantics_wp25_20260519.zh.md)
- [WP2.5-F + WP2.5-A manifest/event 任务簇](../simulation_architecture/wp25_manifest_event_cluster_20260519.zh.md)
- [WP2.5-B + WP2.5-C state/barrier 任务簇](../simulation_architecture/wp25_state_barrier_cluster_20260519.zh.md)
- [WP2.5-D + WP2.5-E clock/replay 任务簇](../simulation_architecture/wp25_clock_replay_cluster_20260519.zh.md)

## 一、结论

WP2.5 作为文档/规格冻结已通过验收。

它关闭了架构评审中指出的关键缺口：`StateStore`、`EventQueue`、
`ClockDomain`、`Barrier` 与 `StageNodeManifest` 在 WP4 facade hardening 和
WP5 validation work 之前需要可执行语义。

本验收仅针对文档规格。它不声称 runtime scheduler、replay harness、机器可读
manifest registry 或 backend parity implementation 已经存在。

## 二、证据

| 领域 | 证据 | 结果 |
|------|------|------|
| Stage-node manifest | `WP2.5-F + WP2.5-A` 定义了必填/条件字段、枚举词汇、兼容标签、producer category、规范示例与 diagnostics 最低要求。 | 通过。 |
| Event ordering | Event order 保持为 `(timestamp, priority, event_id)`，且 `event_id = stable_hash(run_seed, world_id, producing_node_id, event_family, local_sequence)`。Producer allowlist 覆盖 `000-900` priority bands。 | 通过。 |
| State shard versioning | `WP2.5-B + WP2.5-C` 定义 shard ownership、commit trigger、increment rule、diagnostics obligation 与 `SnapshotVersion` 命名。 | 通过。 |
| Barrier visibility | 同一任务单定义了 `input_injection`、`stage_publish`、`window_commit` 与 `export` 的前后可见性，并把 same-window 合法性绑定到 producer publish intent 与 consumer manifest read set。 | 通过。 |
| Clock-domain merge | `WP2.5-D + WP2.5-E` 冻结全部六个 merge policy，并把 independent clock domain 分为 maintained、rejected 或 diagnostics-only。未新增 merge-policy 取值。 | 通过。 |
| Deterministic replay | Replay input envelope、forbidden nondeterminism、parity-budget template 与 diagnostics chain 已文档化。 | 作为未来实现契约通过。 |
| WP3 边界 | 所有 WP2.5 文档都保持 WP3 已验收状态，没有重新 scope engagement behavior。 | 通过。 |

## 三、已解决裁决

1. WP2.5 不增加 runtime code。
2. `allowed_producers` 在 WP2.5 中不是一级 manifest 字段；规范来源是 producer
   allowlist matrix。
3. Diagnostics-only 与 compatibility-only adapter 不得写入维护中的 event queue，
   也不得定义 scheduler truth。
4. `observation` 是 export packet version 的 maintained shard，但 diagnostics-only
   pre-commit view 不递增它。
5. `barrier_id` 只限四个冻结 barrier；细分标签放入 `barrier_detail`。
6. Same-window 合法性必须同时满足 producer publish intent 与 consumer declared
   read set。
7. `interpolate` 在 WP2.5 中只作为派生 consumer view 维护，不提交 producer shard
   version。
8. `parity_budget` 是 backend profile block，不是单个标量。
9. 如果 ordering ambiguity 会影响 scheduler truth，`reject_on_ambiguous_order`
   是唯一维护中的结果。

## 四、剩余风险

这些不是 WP2.5 验收阻塞项，但必须由后续工作处理：

1. `stable_hash` 在实现前仍需选择具体算法。
2. 后续机器可读 registry 可能需要规范化 `clock_domain_id`、backend profile id、
   `barrier_detail` 与 manifest enum values。
3. WP5 需要决定每个 diagnostics-only fallback 是否都必须有完整 trace graph，或在
   没有 replay assertion 消费该 fallback 时允许 compact records。
4. 实现测试需要决定 facade export 是否总是记录完整 shard map，还是只记录
   replay-sensitive subset。

## 五、移交

WP4 可以把 WP2.5 作为 scheduler-semantics 输入继续推进。WP4 不应在 facade
alignment 内临时发明新的 scheduler rules。如果 facade 工作需要 WP2.5 未覆盖的
field、producer、barrier、merge policy 或 replay rule，应开启有范围的 contract
amendment，而不是把规则藏进 runtime 或 facade code。

WP5 应在实现 surface 存在后，把 WP2.5 normative dispatch sheets 转化为
architecture tests、manifest checks、replay-envelope tests 或 smoke validation。

## 六、验收状态

已验收产物：

- [调度语义冻结](../simulation_architecture/scheduler_semantics_wp25_20260519.zh.md)
- [manifest/event 规范任务单](../simulation_architecture/wp25_manifest_event_cluster_20260519.zh.md)
- [state/barrier 规范任务单](../simulation_architecture/wp25_state_barrier_cluster_20260519.zh.md)
- [clock/replay 规范任务单](../simulation_architecture/wp25_clock_replay_cluster_20260519.zh.md)

已执行验证：

```bash
git diff --check -- docs/task/simulation_architecture/scheduler_semantics_wp25_20260519.md docs/task/simulation_architecture/scheduler_semantics_wp25_20260519.zh.md docs/task/simulation_architecture/wp25_manifest_event_cluster_20260519.md docs/task/simulation_architecture/wp25_manifest_event_cluster_20260519.zh.md docs/task/simulation_architecture/wp25_state_barrier_cluster_20260519.md docs/task/simulation_architecture/wp25_state_barrier_cluster_20260519.zh.md docs/task/simulation_architecture/wp25_clock_replay_cluster_20260519.md docs/task/simulation_architecture/wp25_clock_replay_cluster_20260519.zh.md docs/task/simulation_architecture/README.md docs/task/simulation_architecture/README.zh.md
```

由于 WP2.5 仅为文档/规格冻结，不要求 runtime 测试。
