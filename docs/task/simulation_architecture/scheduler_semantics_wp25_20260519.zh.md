# WP2.5 调度语义冻结

状态：`2026-05-19` 调度语义冻结完成。

语言版本：

- 英文主文：[scheduler_semantics_wp25_20260519.md](scheduler_semantics_wp25_20260519.md)
- 中文辅文：`scheduler_semantics_wp25_20260519.zh.md`

输入：

- [仿真系统架构设计](../../plan/architecture/simulation_system_architecture_design.zh.md)
- [WP2 契约冻结](contract_freeze_wp2_20260519.zh.md)
- [架构计划评审](../review/architecture_plan_review_20260519.zh.md)
- [临时评审源论述](../review/temp-01.zh.md)
- [WP2.5 调度语义验收审查](../review/wp25_scheduler_semantics_acceptance_review_20260519.zh.md)

WP2.5 是插入在 `WP2 Contract Freeze` 与 `WP4 Facade Alignment` 之间的
文档级语义冻结。它不重开已经验收的 `WP3 Engagement Pilot`，也不实现
scheduler。它的职责是把架构概念 `StateStore`、`EventQueue`、
`ClockDomain`、`Barrier` 与 `StageNodeManifest` 转化为后续实现可以验证的
规则。

## 1. 冻结定位

架构基线已经说明 `P0-P10` 是语义生命周期，真实执行是多率 temporal
DAG。评审指出的问题是，若干调度概念方向正确，但仍然过于隐式：

1. event family priority 已被命名，但没有表格；
2. deterministic `event_id` 生成规则尚未钉住；
3. state shard version 没有递增规则；
4. barrier visibility 没有说明 read 观察 pre-commit 还是 post-commit；
5. independent clock domain 缺少 merge rule；
6. stage-node declaration 尚未固化为 manifest。

WP2.5 冻结 facade hardening 与 validation harness 依赖前所需的最小调度语义。

验收备注：WP2.5 已在
[WP2.5 调度语义验收审查](../review/wp25_scheduler_semantics_acceptance_review_20260519.zh.md)
中作为文档/规格冻结通过验收。

非目标：

- 不重写 runtime scheduler；
- 不迁移 Flecs pipeline；
- 不实现 GPU 或 resident-state；
- 不改变已经验收的 WP3 交战试点；
- 不新增 public facade API，除非后续 WP4 任务明确需要。

## 2. 交付物

| 交付物 | 在本文冻结的内容 | 后续实现目标 |
|--------|------------------|--------------|
| `event_family_priority_table.md` | Event ordering table 与 deterministic `event_id` 规则。 | 机器可读 event family registry。 |
| `state_shard_versioning_rules.md` | Shard 词汇、递增策略与 snapshot 命名。 | State-store 或 backend sync 实现。 |
| `barrier_visibility_rules.md` | Injection、stage、commit、export barrier 的读写可见性。 | Scheduler tests 与 observation/export guards。 |
| `clock_domain_merge_rules.md` | Nested triggering 默认规则与 independent domain merge rules。 | 多率 scheduler 实现。 |
| `deterministic_replay_contract.md` | Replay log 输入、排序 key 与禁止依赖的非确定性来源。 | WP5 或后续 replay harness。 |
| `stage_node_manifest_schema.md` | Stage-node governance 所需的 manifest 字段。 | Markdown-to-schema registry、lint 或 generated manifests。 |

如果后续实现量变大，这些名称可以拆成独立文件。当前冻结阶段将规范性内容集中在本文，以保持语义面紧凑。

## 3. Event Family Priority

维护中的 event 行为必须按以下 key 排序：

```text
(timestamp, priority, event_id)
```

`timestamp` 是仿真时间，`priority` 由 event family 固定，`event_id` 必须确定性生成。插入顺序不是维护行为的 tie-breaker。

初始优先级表：

| Priority | Event family | 典型 producer | 可见性意图 |
|----------|--------------|---------------|------------|
| `000` | setup and reset events | `P1 WorldSetup` | 在 runtime event 前建立初始状态。 |
| `100` | external intent injection | facade、policy、orchestration、human、diagnostic adapters | 让已到达的跨层请求在 scheduled node 运行前可见。 |
| `200` | tasking and command delivery | `P2 TaskingIntent`、`P3 CommandDelivery` | 物化 tasking、link latency、command arrival 与 drop events。 |
| `300` | platform control handoff | `P4 PlatformControl` | 记录 resolved control intent 与 validity outcomes。 |
| `400` | physics/contact candidates | `P5 PhysicsStep` | 发布已提交物理状态或 contact candidate event。 |
| `500` | sensing, track, and link updates | `P6 SenseTrackLink` | 发布 track snapshot、link report 与 detection/fusion events。 |
| `600` | fire-control and launch | `P7 FireControlLaunch` | 记录 accepted/rejected launch decision 与 munition spawn ancestry。 |
| `700` | munition lifecycle | `P8 MunitionLifecycle` | 记录 seeker、guidance、fuze-arm、terminal、miss 或 effects trigger candidate。 |
| `800` | effects and damage | `P9 EffectsDamage` | 应用 effects、damage report、kill/loss transition 与 capability delta。 |
| `900` | observation, diagnostics, and export | `P10 ObservationExport` | 导出 committed snapshot、diagnostics trace 与 facade packet。 |

Deterministic `event_id` 规则：

```text
event_id = stable_hash(run_seed, world_id, producing_node_id, event_family, local_sequence)
```

要求：

1. `producing_node_id` 来自 `StageNodeManifest.node_id`。
2. `local_sequence` 在单个 producing node、event family、scheduling window 与 world 内计数。
3. 并行 producer 不得从共享 mutable counter 分配 event id，除非 counter 顺序本身由确定性 node order 推导。
4. 无法产出 deterministic id 的兼容路径必须把 export 标记为 diagnostics-only，直到由维护中的 event producer 包装。

## 4. State Shard Versioning

早期 CPU-only 执行可以暴露单一 global snapshot version，但维护中的 scheduler 语义必须为 shard 做好准备。

初始 shard 词汇：

| Shard | Owned stages | 包含内容 | 最小 version 递增规则 |
|-------|--------------|----------|-----------------------|
| `setup` | `P0`、`P1` | content id、world setup、initial entity ref、static environment ref | setup/reset commit 时递增。 |
| `tasking` | `P2` | task order、authority state、已进入 DAG 的 coordination intent | tasking state commit 时递增。 |
| `command` | `P3` | delivered command、pending queue、link state、command report | delivery state 或 queue commit 时递增。 |
| `control` | `P4` | resolved action/control state、actuator intent、validity report | control input commit 时递增。 |
| `physics` | `P5` | truth position/velocity/orientation、contact、physical environment state | physics integration window commit 时递增。 |
| `track` | `P6` | detection、fused track、link report、shared situation snapshot | track/link snapshot commit 时递增。 |
| `engagement` | `P7`、`P8` | launch event、munition ref、munition lifecycle state、fuze/effects trigger candidate | launch 或 munition lifecycle state commit 时递增。 |
| `damage` | `P9` | damage report、platform damage state、capability degradation、kill/loss state | damage 或 capability effect commit 时递增。 |
| `observation` | `P10` | observation packet version、diagnostics trace export、mirrored episode status | 产生可导出的 observation snapshot 时递增。 |

Snapshot 命名：

```text
SnapshotVersion = {
  global_version,
  shard_versions: map<state_shard, version>,
  source_time,
  barrier_id
}
```

规则：

1. 写入只在 commit barrier 递增目标 shard，不因内部临时 mutation 每次递增。
2. 任一维护 shard commit 时，`global_version` 递增。
3. 同时读取多个 shard 的 stage node 在发出 event 或 facade-visible packet 时，必须在 diagnostics 中记录所有 source shard versions。
4. Observation packet 必须声明读取的是哪个 committed snapshot。
5. Damage-to-capability feedback 必须写 `damage`，并在 capability state 改变时写受影响的 capability-bearing shard。Fire-control 或 sensor node 只能在声明的 barrier 后观察该变化。

## 5. Barrier Visibility

维护中的 scheduling window 有四个语义 barrier：

| Barrier | 位置 | 开始可见的写入 | 必要 reader |
|---------|------|----------------|-------------|
| `input_injection` | scheduled stage node 运行前。 | 已到达的 facade、policy、orchestration、human 与 diagnostic request。 | manifest read set 包含 injected input 的 `P2`、`P3`、`P4` 或后续 node。 |
| `stage_publish` | same-window DAG node 之间。 | Producing node 显式标记 same-window visible 的写入。 | 具有 data-derived same-window edge 的下游 node。 |
| `window_commit` | 无环 window DAG 完成后。 | 已提交 state shard version 与 future event-queue insert。 | 下一窗口 node 与 replay log。 |
| `export` | commit 后或声明的 diagnostics/export slot。 | facade packet、observation view、diagnostics trace 与 mirrored status。 | frontend、test、policy consumer 与 replay validator。 |

默认可见性策略：

1. Stage-local 临时写入在 producing node 外不可见。
2. Same-window read 只有在 producer manifest 声明 same-window output，且 consumer manifest 声明相应 read 时合法。
3. Cross-window feedback 只能读取 committed `SnapshotVersion`。
4. `P10 ObservationExport` 默认读取 post-`window_commit` snapshot。Pre-commit diagnostic view 只有在明确标记为 diagnostics 且排除在 policy/training truth 外时才允许。
5. 如果 facade action 不应影响当前 window，它必须携带后续 window 的 `effective_time`，而不是依赖隐藏调用顺序。

## 6. Clock Domain Merge

默认规则：

```text
one outer scheduling window owns deterministic order;
lower-rate domains run as declared nested triggers inside that window.
```

典型 merge 行为：

| Clock domain 关系 | 维护规则 |
|-------------------|----------|
| base tick 的整数倍 | 按声明 slot number 运行；除非明确可跳过，否则 missed slot 是 replay error。 |
| 低频 policy 或 control | 使用 `ActionHoldPolicy` 或等价 validity window，让一个 producer output 被多个 control/physics tick 消费。 |
| Event-driven damage 或 fuze | 入队 timestamped events；当 timestamp 进入当前 window 后消费。 |
| Sensor/track scans | 产出带 source time 与 shard version 的 snapshot；consumer 不得假设与 physics tick 等频。 |
| 独立 backend 或 resident-state clock | 在 backend profile 声明 sync barrier、event export order 与 parity budget 前，不进入维护路径。 |

Merge policy 值：

| 值 | 含义 |
|----|------|
| `nested_slot` | Producer 在 outer window 的确定性 slot 中运行。 |
| `hold_last` | 最近的有效 producer output 在过期前被复用。 |
| `interpolate` | Consumer 从两个 versioned producer output 推导中间值。 |
| `enqueue_event` | Producer output 变为 timestamped event。 |
| `defer_to_next_window` | Producer output 到下一 window 才可见。 |
| `reject_on_ambiguous_order` | 若无法证明确定性顺序，scheduler 或 adapter 拒绝输入。 |

## 7. Deterministic Replay Contract

维护中的 replay 必须能由以下信息重建：

1. static content ids 与 scenario setup；
2. run seed 与 deterministic backend profile；
3. 带 `source_id`、`input_snapshot_version`、`effective_time`、
   `valid_until`、`merge_policy` 的 facade 与 external producer request；
4. `StageNodeManifest` registry；
5. 按 `(timestamp, priority, event_id)` 排序的 event stream；
6. 已提交的 `SnapshotVersion` 序列；
7. 连接 source request、event、report 与 observation export 的 diagnostics trace。

维护路径禁止依赖：

- 来自非确定性容器遍历的 event insertion order；
- wall-clock timing 作为 tie-breaker；
- raw pointer address 或 entity allocation accident 作为 semantic id；
- 未体现在 facade request metadata 里的 Python helper call order；
- 没有 deterministic merge rule 的 backend-specific thread completion order。

Replay tolerance：

1. CPU exact path 是参考。
2. Accelerated 或 approximate backend 必须先声明 parity budget，才能成为维护中的 replay source。
3. Diagnostics-only compatibility export 可以做结构性比较，但不定义 scheduler truth。

## 8. StageNodeManifest Schema

每个维护中的 stage node 都应能用以下 manifest schema 描述：

| 字段 | 要求 |
|------|------|
| `node_id` | 稳定唯一 id，用于 docs、tests、event ids 与 diagnostics。 |
| `semantic_stage` | 一个或多个 `P0-P10` 阶段。 |
| `owner_module` | 所属 source module、adapter、model family 或 facade surface。 |
| `input_packets` | 消费的 contract packet 或 request。 |
| `output_packets` | 产出的 contract packet、report 或 facade export。 |
| `read_state_shards` | node 读取的 state shard 与 snapshot policy。 |
| `write_state_shards` | node 改变或提交的 state shard。 |
| `read_snapshot_policy` | `pre_window`、`post_injection`、`same_window`、`committed` 或 `diagnostic_only`。 |
| `write_commit_policy` | `stage_publish`、`window_commit`、`delayed_event`、`export_only` 或 `diagnostic_only`。 |
| `clock_domain` | 触发 cadence、event condition 或 facade-requested export rule。 |
| `latency_policy` | Same-window、next-window、delayed、link-latency controlled 或 backend-sync controlled。 |
| `sync_policy` | Host-owned、backend-owned、partial sync、observation-only sync 或 explicit export。 |
| `allowed_same_window_edges` | 允许读取 same-window output 的 downstream node id 或 stage family。 |
| `required_barriers` | node 运行前后必须存在的 barrier 名称。 |
| `event_families_emitted` | 该 node 产出的 event family 与 priority。 |
| `diagnostic_trace_obligations` | 必须记录的 trace id、ancestry id 或 source snapshot version。 |
| `facade_visibility` | Maintained facade surface、compatibility adapter、diagnostics-only 或 internal。 |
| `compatibility_adapter_allowed` | legacy/raw-runtime access 是否可包装该 node，以及必须使用什么标签。 |

最小 markdown 示例：

```yaml
node_id: p7.fire_control_launch.v1
semantic_stage: [P7 FireControlLaunch]
owner_module: src/core/engine/simulation_kernel_weapon_api.cpp
input_packets: [LaunchRequest, TrackPacket]
output_packets: [LaunchEvent, DiagnosticsTrace]
read_state_shards: [track, engagement, command]
write_state_shards: [engagement]
read_snapshot_policy: post_injection
write_commit_policy: window_commit
clock_domain: event_driven_or_fire_control_cadence
latency_policy: same_window_after_request_barrier
sync_policy: host_owned
allowed_same_window_edges: [p8.munition_lifecycle.*]
required_barriers: [input_injection, window_commit]
event_families_emitted: [fire_control_and_launch]
diagnostic_trace_obligations:
  - launch_request_id
  - launch_event_id
  - input_track_snapshot_version
facade_visibility: maintained_facade_export
compatibility_adapter_allowed: true_for_legacy_fire_missile_only
```

## 9. 工作流地图

WP2.5 虽然是冻结文档，但后续工作应该按有边界的流来组织，并明确依赖关系与所有权边界。

| 工作流 | 关注点 | 依赖 | 并行性 | 思考预算 | 退出产物 |
|--------|--------|------|--------|----------|----------|
| `WP2.5-F StageNodeManifest Schema` | 定义 manifest 字段、示例、ownership tag 与兼容标签。 | 架构基线文档、评审结论。 | 先启动；在 node 词汇稳定后可与 A-C 并行。 | 高。 | 供其他工作流引用的 manifest schema 草案。 |
| `WP2.5-A Event Ordering and ID Rules` | 固化 event family、priority、deterministic id 与允许的 producer。 | `StageNodeManifest` 的 node id、评审结论。 | 在共享命名稳定后，可与 B/C/F 并行。 | 中。 | 可供实现测试使用的 event ordering 表。 |
| `WP2.5-B State Shard Versioning` | 定义 shard 词汇、commit 边界、版本递增与 snapshot 命名。 | 基础状态模型、manifest schema。 | 可与 A/C/F 并行。 | 中。 | 供后续 scheduler 测试使用的 shard/version 规则集。 |
| `WP2.5-C Barrier Visibility` | 定义 injection、stage_publish、window_commit、export 的可见性，以及 same-window 合法性。 | manifest 的 read/write 字段、event ordering。 | 可与 A/B/F 并行。 | 中。 | 明确 pre/post commit 可见性的 barrier 规则集。 |
| `WP2.5-D Clock-Domain Merge` | 定义 nested triggering 默认规则与 independent domain merge policy。 | A、C、F。 | 等 A/C/F 稳定后再开始。 | 高。 | clock-domain contract 与 merge-policy 矩阵。 |
| `WP2.5-E Deterministic Replay Contract` | 定义 replay 输入、禁止的非确定性来源、parity budget 与 diagnostics 义务。 | A-D 加 F。 | 需在 A-D 后串行收敛。 | 高。 | 可供 WP5 harness 使用的 replay contract。 |
| `WP2.5-G Integration and Index Sync` | 同步 README、架构基线、WP2 handoff 与验证说明。 | 上述全部。 | 串行集成 owner。 | 中。 | 对齐后的文档索引，供 WP4/WP5 使用。 |

分发产物：

- [WP2.5-F + WP2.5-A manifest/event 任务簇](wp25_manifest_event_cluster_20260519.zh.md)
- [WP2.5-B + WP2.5-C state/barrier 任务簇](wp25_state_barrier_cluster_20260519.zh.md)
- [WP2.5-D + WP2.5-E clock/replay 任务簇](wp25_clock_replay_cluster_20260519.zh.md)

建议执行顺序：

1. 先做 `WP2.5-F`，让其他工作流共享同一组 node 词汇。
2. 再并行推进 `WP2.5-A`、`WP2.5-B`、`WP2.5-C`。
3. 然后做 `WP2.5-D`，因为它依赖 event ordering、barrier 语义与 manifest。
4. 接着做 `WP2.5-E`，因为 replay 依赖已冻结的语义。
5. 最后做 `WP2.5-G`，作为串行集成与发布步骤。

推荐思考预算：

- 高：`WP2.5-D` 和 `WP2.5-E`。
- 中：其他工作流。

## 10. WP2.5 验收门槛

WP2.5 退出条件：

1. 任务树从 `README.md`、`README.zh.md` 和 WP2 handoff 链接到本文。
2. 架构基线把 WP2.5 命名为 scheduler semantics 的冻结计划。
3. Event ordering、state shard versioning、barrier visibility、clock-domain
   merge、replay 与 `StageNodeManifest` schema 都已有显式规则。
4. 已验收的 WP3 pilot 继续标为 complete，且不被重新 scope。
5. WP4 与 WP5 可以引用本文，而不是在 facade 或 validation 工作中临时发明 scheduler semantics。

建议在 WP5 中补充的后续验证：

```powershell
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\architecture
.\tools\maintenance\cmo_env.ps1 python tools\runners\run_pytest_suite.py --suite tests\smoke\ci_smoke_suite.json
```

未来实现可以增加解析本文或机器可读 manifest registry 的架构测试，但这不属于 WP2.5 文档冻结范围。
