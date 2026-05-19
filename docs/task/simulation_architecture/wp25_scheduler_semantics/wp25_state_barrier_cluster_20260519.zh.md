# WP2.5-B + WP2.5-C 状态分片版本与 Barrier 可见性任务单

状态：`2026-05-19`，WP2.5 执行用规范分发任务单。

语言：

- 英文主文：`wp25_state_barrier_cluster_20260519.md`
- 中文辅文：[wp25_state_barrier_cluster_20260519.zh.md](wp25_state_barrier_cluster_20260519.zh.md)

输入：

- [WP2.5 调度语义冻结](scheduler_semantics_wp25_20260519.zh.md)
- [WP2.5-F + WP2.5-A Manifest/Event 任务簇](wp25_manifest_event_cluster_20260519.zh.md)
- [仿真系统架构设计](../../plan/architecture/simulation_system_architecture_design.zh.md)
- [架构评审](../review/architecture_plan_review_20260519.md)
- [临时评审源文档](../review/temp-01.md)

## 1. 目的

本任务单把 WP2.5 state/barrier 草案转换为规范性任务包。它面向后续负责
审查或实现调度语义的 subagent，避免后续实现自行发明额外规则。

规范用语：

- `MUST` 与 `MUST NOT` 表示 WP2.5 必须遵守的行为。
- `SHOULD` 表示默认优先规则，除非后续评审记录了明确例外理由。
- `MAY` 表示允许但非强制的 diagnostics 或文档选择。

## 2. 范围与非目标

范围内：

- 状态分片词汇、owner stage、commit 触发条件与版本递增规则；
- `SnapshotVersion` 结构、示例与命名规则；
- `input_injection`、`stage_publish`、`window_commit`、`export` 前后的
  barrier 可见性；
- 基于 producer 发布意图与 consumer 声明 read set 的 same-window 合法性；
- replay、facade export 与 `StageNodeManifest` 声明需要消费的 diagnostics
  义务；
- manifest 字段：
  `read_state_shards`、`write_state_shards`、`read_snapshot_policy`、
  `write_commit_policy`、`allowed_same_window_edges`、`required_barriers`、
  `diagnostic_trace_obligations` 与 `facade_visibility`。

非目标：

- 实现或重构运行时 scheduler；
- 重做 event ordering；
- 定义 clock-domain merge policy，除非只是引用已提交 snapshot version；
- 实现 replay harness；
- 扩展 facade API；
- 重新开启 WP3；
- 机器可读 manifest registry 或生成式 schema。

## 3. 分发切片

| 切片 | 关注点 | 必需输出 | 思考预算 |
|------|--------|----------|----------|
| `B1` | Shard 所有权与递增策略。 | 完整 shard/version 表与例外说明。 | 中 |
| `B2` | Snapshot 命名与 diagnostics 义务。 | `SnapshotVersion` 示例、命名规则与 export diagnostics 清单。 | 中 |
| `C1` | Barrier 矩阵与 same-window 合法性。 | 前后可见性矩阵与合法性规则。 | 高 |
| `C2` | 验收示例与 manifest 对齐。 | Manifest 字段映射、验收标准、已解决/未解决问题列表。 | 中 |

并行规则：

1. 如果 shard 名称仍在移动，`B1` 与 `B2` SHOULD 由同一 owner 负责。
2. shard 名称稳定后，`C1` MAY 并行推进。
3. 不应让两个 worker 同时编辑同一份 barrier 矩阵或 snapshot 示例。
4. 修改 same-window 合法性的 worker MUST 同步复查本任务单中的 diagnostics
   与 manifest 对齐。

## 4. Shard 与版本规则

即使早期 CPU-only 路径只暴露一个 global snapshot version，维护中的 scheduler
语义也 MUST 具备 shard-ready 能力。

| Shard | Owner stages | 已提交内容 | Commit 触发条件 | 递增规则 | Diagnostics 义务 |
|-------|--------------|------------|-----------------|----------|------------------|
| `setup` | `P0`, `P1` | 场景 content id、world setup、初始 entity ref、静态环境 ref。 | runtime window 前的 setup/reset commit。 | 每次被接受的 setup/reset commit 递增一次；只读 content lookup 不递增。 | 记录 content id 集合、setup manifest id、`barrier_id` 与结果 `setup` version。 |
| `tasking` | `P2` | 被接受的 task order、authority state、进入 DAG 的 coordination intent。 | `window_commit` 上的 tasking state commit，或声明的 delayed task event commit。 | accepted tasking state 改变时递增；reject 或 diagnostics-only input 不递增。 | 记录 source request id、input snapshot version、accepted/rejected 状态与目标 `effective_time`。 |
| `command` | `P3` | delivered command、pending command queue、link-delivery state、command report。 | command delivery 或 queue mutation commit。 | delivered command state 或 pending queue 改变时递增；纯 inspection 不递增。 | 记录 command id、link/report ancestry、delivery timestamp，以及消费的 source `tasking`/`track` version。 |
| `control` | `P4` | resolved action/control state、actuator intent、validity report。 | control handoff commit。 | resolved control input 或 validity state 改变时递增。 | 记录 controlling request/event id、validity window、消费的 `command` version，以及非 maintained 时的 rejection reason。 |
| `physics` | `P5` | truth pose、velocity、orientation、contact、物理环境状态。 | physics integration window commit。 | 每个会改变 physical state 的已提交 integration window 递增一次；same-window temporary integration state 不递增。 | 记录 integration window、source `control` version、先前 `physics` version 与 deterministic backend profile。 |
| `track` | `P6` | detection、fused track、link report、shared situation snapshot。 | track/link snapshot commit。 | maintained detection、fusion 或 link snapshot 提交时递增。 | 记录 source time、source `physics` version、sensor/link producer id，以及任何 hold/interpolate 的 source version。 |
| `engagement` | `P7`, `P8` | launch decision、munition ref、munition lifecycle state、seeker/fuze/effects trigger candidate。 | fire-control launch 或 munition lifecycle commit。 | launch acceptance、munition state、seeker/fuze state 或 trigger candidate state 改变时递增。 | 记录 parent request/event id、munition/entity ref、消费的 `track`/`physics`/`control` version 与 emitted event id。 |
| `damage` | `P9` | damage report、platform damage state、capability degradation、kill/loss state。 | effects/damage commit。 | damage、capability 或 kill/loss state 改变时递增。若另一个 capability-bearing shard 也变化，该 shard 在同一 `window_commit` 递增。 | 记录 effects event id、affected entity ref、前后 capability state、source `engagement`/`physics` version 与任何 coupled shard increment。 |
| `observation` | `P10` | observation packet version、diagnostics trace export、mirrored episode/status view。 | 已提交 source snapshot 之后，在 `export` 处产生 exportable observation snapshot。 | maintained facade/observation packet version 产生时递增。diagnostics-only pre-commit view MUST NOT 递增 maintained `observation` shard。 | 记录 exported packet id、source `SnapshotVersion`、export barrier detail、facade visibility label 与适用时的 diagnostics-only flag。 |

附加规则：

1. 写入 MUST 只在其声明的 commit trigger 处递增目标 shard。
2. 任一 maintained shard version 递增时，`global_version` MUST 递增。
3. 同一个 `window_commit` 中的多个 shard increment 共享结果 committed snapshot
   的同一个 `global_version`。
4. Stage-local temporary write MUST NOT 改变 shard version。
5. Same-window published output MUST NOT 改变 shard version，直到其所属写入
   commit。
6. Rejected、diagnostics-only 或 compatibility-only observation MUST NOT 定义
   maintained shard truth。

## 5. SnapshotVersion 契约

规范形态：

```yaml
SnapshotVersion:
  name: sv.world_alpha.g000042.window_commit.000017
  world_id: world_alpha
  global_version: 42
  shard_versions:
    setup: 1
    tasking: 8
    command: 11
    control: 21
    physics: 42
    track: 17
    engagement: 6
    damage: 3
    observation: 15
  source_time: 12.500s
  barrier_id: window_commit
  barrier_sequence: 17
  barrier_detail: physics_tick_250
```

命名规则：

1. `name` SHOULD 使用
   `sv.<world_id>.g<global_version>.<barrier_id>.<barrier_sequence>`。
2. `world_id` MUST 在 replay scope 内稳定，且 MUST NOT 依赖内存地址或分配顺序。
3. 诊断名称中的 `global_version` MUST 为可读性做 zero-padding，但数值比较
   MUST 使用整数字段，而不是词典序。
4. `barrier_id` MUST 是 `input_injection`、`stage_publish`、
   `window_commit` 或 `export` 之一。
5. 更细的标签 MAY 记录在 `barrier_detail`；它们 MUST NOT 替代冻结的
   `barrier_id`。
6. `source_time` 是模拟时间。Wall-clock time MUST NOT 用作 snapshot 排序键。
7. `shard_versions` MUST 精确使用第 4 节中的 shard key。
8. Facade-visible packet MUST 标明自己读取或导出的 `SnapshotVersion`。
9. 从读取 state 的 stage 发出的 maintained event MUST 记录相关 source
   `SnapshotVersion` 或 source shard version。

## 6. Barrier 可见性矩阵

| Barrier | 前置可见性 | 后置可见性 | Barrier 后的合法 reader | 明确排除 |
|---------|------------|------------|--------------------------|----------|
| `input_injection` | 外部/facade/policy/human request 可以存在于 ingress buffer，但 scheduled stage node 不能把它们作为 maintained input 消费。State shard 仍停留在先前 committed snapshot。 | `effective_time` 进入当前 window 且 source metadata 有效的 accepted request，作为 injected input 可见。 | Manifest 声明匹配 `input_packets`、`read_snapshot_policy: post_injection` 与 required `input_injection` barrier 的 node。 | 不暴露 state write。Late、invalid 或 future-effective request 会被 reject 或 defer，并且对当前 window maintained logic 不可见。 |
| `stage_publish` | Producer 的 stage-local write 与 draft output 对 producing node 外不可见。 | Producer 显式标记为 same-window visible 的 output，对声明过的 downstream consumer 可见。 | `allowed_same_window_edges` 命名的 consumer，且其 manifest 声明 `read_snapshot_policy: same_window` 与匹配的 read set。 | 不提交 shard version，不创建通用 read-after-write channel，也不允许 undeclared consumer。 |
| `window_commit` | 合法 downstream node 可能已经消费 same-window published output，但 shard version 在 commit 前仍表示先前 committed snapshot。 | Maintained write 成为 committed shard version；future event-queue insert 对 replay 可见；结果 `SnapshotVersion` 可供 next-window node 与默认 `P10` export 使用。 | Next-window node、replay log construction、post-commit diagnostics，以及默认的 `P10 ObservationExport`。 | Pre-commit diagnostic view 不能成为 policy/training truth。Failed 或 diagnostics-only write 不 commit。 |
| `export` | Frontend、policy consumer、test 与 replay validator 只能依赖先前 exported maintained packet 或 committed snapshot。 | Facade packet、observation view、diagnostics trace 与 mirrored status 带着 source snapshot 和 barrier metadata 可见。 | Frontend、test、policy consumer、replay validator 与 diagnostics tool，具体由 `facade_visibility` 决定。 | Diagnostics-only pre-commit export 必须标记，并从 maintained truth、policy training truth 与 replay parity assertion 中排除。 |

可见性规则：

1. Maintained stage logic 的默认 read snapshot 是该 stage 声明 barrier 上可用的
   最新 committed `SnapshotVersion`。
2. `input_injection` 改变 input 可用性，不改变 committed state shard version。
3. `stage_publish` 是 intra-window visibility edge，不是 commit。
4. `window_commit` 是本任务簇中唯一提交 maintained state shard version 的
   barrier。
5. `export` 默认发布 committed snapshot 上的 view，除非 packet 被明确标记为
   diagnostics-only。

## 7. Same-Window 合法性

Same-window read 只有在 producer intent 与 consumer declaration 同时允许该
edge 时才合法。

Producer 必需条件：

1. Producer manifest MUST 声明对应 output packet 或 state-derived output。
2. 被 same-window 消费的 output，其 `write_commit_policy` MUST 是
   `stage_publish`。
3. `allowed_same_window_edges` MUST 包含 consumer node id 或允许的 downstream
   stage family。
4. Producer MUST 命名 published shard 或 packet，并保留指向最终 committed
   shard version 或 event id 的 diagnostic link。
5. 该 publish 必须适配 acyclic deterministic window DAG。

Consumer 必需条件：

1. Consumer manifest MUST 声明 `read_snapshot_policy: same_window`。
2. Consumer 的 `read_state_shards` 或 `input_packets` MUST 包含 producer 发布的
   精确 shard/packet。
3. Consumer 的 `required_barriers` MUST 包含 `stage_publish`。
4. Consumer diagnostics MUST 记录 producer node id、producer output id、
   commit 前 source shard version 与当前 scheduling window。

合法性表：

| Producer 发布意图 | Consumer 声明 read set | Same-window 结果 |
|-------------------|------------------------|------------------|
| `stage_publish` 且 consumer 被列入 `allowed_same_window_edges`。 | 匹配 `read_snapshot_policy: same_window`，且匹配 shard/packet。 | `stage_publish` 后允许；直到 `window_commit` 前不递增 shard version。 |
| `stage_publish`，但 consumer 未被命名或 DAG 顺序含糊。 | 任意 read set。 | 作为 maintained behavior 禁止；reject 或 diagnostics-only。 |
| 仅 `window_commit`。 | 请求 `same_window` read。 | 禁止；consumer 必须等待下一个 committed `SnapshotVersion`。 |
| `delayed_event` 或未来 `effective_time`。 | 任意当前 window read set。 | 当前 window 禁止；等 event 进入声明 window 时再消费。 |
| `export_only` 或 `diagnostic_only`。 | Maintained stage read set。 | 禁止作为 scheduler truth；只能通过 diagnostics/export 路径可见。 |
| `stage_publish`。 | Consumer 的 `read_state_shards` 或 `input_packets` 缺少匹配 shard/packet。 | 禁止；manifest read set 是权威来源。 |

## 8. Diagnostics 清单

任何使用本任务单的 maintained event、committed state mutation 或 facade-visible
packet，MUST 记录足够信息来重建其 barrier 与 snapshot 上下文。

最小字段：

- `world_id`；
- scheduling window id 或 simulated time window；
- `barrier_id` 与可选 `barrier_detail`；
- producer `node_id` 或 external `source_id`；
- same-window edge 的 consumer `node_id`；
- source `SnapshotVersion` 或精确 source shard version；
- committed 或 exported output 的 resulting `SnapshotVersion`；
- 产生 event/export 时的 event id 或 packet id；
- output 不是 maintained truth 时的 diagnostics-only 或 compatibility label。

Export 专用规则：

1. Maintained facade/observation packet MUST 记录自己读取的 committed
   `SnapshotVersion`。
2. Diagnostics-only pre-commit view MUST 记录 pre-commit barrier context，并且
   MUST NOT 被当作 policy/training truth 消费。
3. Same-window diagnostic trace MUST 同时记录 pre-commit source shard version
   与该写入 commit 后的 committed version，如果该写入最终 commit。

## 9. Manifest 对齐

| Manifest 字段 | 本任务簇要求的对齐方式 |
|---------------|------------------------|
| `read_state_shards` | 必须使用第 4 节 shard 名称。Same-window consumer 必须包含自己读取的精确 shard。 |
| `write_state_shards` | 必须列出所有可能在 commit 时递增的 maintained shard。Coupled `damage` capability update 必须列出所有受影响 shard。 |
| `read_snapshot_policy` | 必须是 `pre_window`、`post_injection`、`same_window`、`committed` 或 `diagnostic_only`；same-window read 必须满足第 7 节。 |
| `write_commit_policy` | 必须区分 `stage_publish`、`window_commit`、`delayed_event`、`export_only` 与 `diagnostic_only`。 |
| `allowed_same_window_edges` | 必须为空或显式列出；wildcard same-window visibility 不属于 maintained 语义。 |
| `required_barriers` | 必须命名 node 运行前/后需要的 barrier。 |
| `diagnostic_trace_obligations` | 必须包含第 5、7、8 节需要的 snapshot、shard、barrier、producer 与 consumer 字段。 |
| `facade_visibility` | 必须区分 maintained facade surface、compatibility output 与 diagnostics-only output。 |

## 10. 验收标准

本任务簇在满足以下条件时验收：

1. 每个 shard 都有 owner-stage 集合、已提交内容、commit 触发条件、递增规则与
   diagnostics 义务；
2. `SnapshotVersion` 有具体示例与稳定命名规则；
3. 每个 barrier 都有明确的前置/后置可见性；
4. same-window 合法性同时依赖 producer publish intent 与 consumer declared
   read set；
5. state commit、same-window edge 与 export 的 diagnostics 义务明确；
6. 运行时 scheduler 实现保持在范围外；
7. 英文与中文任务单章节对齐。

## 11. 已解决决策与遗留问题

已解决决策：

1. `observation` 保留为 export packet version 的 maintained shard，但
   diagnostics-only pre-commit view 不递增它。
2. `barrier_id` 只限四个冻结 barrier 名称；更细标签使用 `barrier_detail`。
3. Maintained export 记录 source `SnapshotVersion`；same-window 与
   replay-sensitive path 记录精确 source shard version。
4. Same-window 合法性由 producer publish intent 与 consumer declared read set
   共同决定。
5. Pre-commit diagnostic view 仅允许作为 diagnostics-only path，并从
   policy/training truth 中排除。

后续遗留问题：

1. 未来 machine-readable manifest registry 是否应规范化 `barrier_detail` 取值。
2. 实现测试是否要求所有 export 都记录完整 shard map，或在 replay assertion
   不依赖被省略 shard 时允许 compact source-shard subset。
