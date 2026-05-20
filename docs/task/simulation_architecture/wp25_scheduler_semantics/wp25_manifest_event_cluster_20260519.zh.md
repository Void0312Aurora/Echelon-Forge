# WP2.5-F + WP2.5-A 规范分发表：StageNodeManifest Schema 与 Event Ordering

状态：`2026-05-19` 规范分发表。

语言版本：

- 英文主文：[wp25_manifest_event_cluster_20260519.md](wp25_manifest_event_cluster_20260519.md)
- 中文辅文：`wp25_manifest_event_cluster_20260519.zh.md`

输入：

- [WP2.5 调度语义冻结](scheduler_semantics_wp25_20260519.zh.md)
- [WP2.5-B + WP2.5-C 状态/barrier 任务簇](wp25_state_barrier_cluster_20260519.zh.md)
- [仿真系统架构设计](../../plan/architecture/simulation_system_architecture_design.zh.md)
- [WP2 契约冻结](contract_freeze_wp2_20260519.zh.md)
- [架构计划评审响应](../review/architecture_plan_review_20260519.zh.md)

规范语言：

- `MUST` 表示维护中文档与后续实现都必须遵守的 WP2.5 行为。
- `MUST NOT` 表示不能定义维护中 scheduler truth 的行为。
- `SHOULD` 表示默认规则；偏离时需要显式后续任务或评审说明。
- `MAY` 表示允许的兼容或文档路径。

## 1. 目的

本分发表把 `WP2.5-F StageNodeManifest Schema` 与 `WP2.5-A Event Ordering
and ID Rules` 转成规范任务项。它是文档/规格任务，不是 runtime
implementation 任务。

后续 scheduler、facade 与 replay 工作必须能引用本表，而不需要重新发明
manifest 词汇、event priority 分层、producer label 或 deterministic identity
规则。

## 2. 规范范围

本表冻结：

- `StageNodeManifest` 字段集合及每个字段的出现分类；
- snapshot read、commit/write visibility、facade visibility、兼容标签与
  producer category 的 manifest 枚举词汇；
- 按 `(timestamp, priority, event_id)` 的 event ordering；
- 确定性的 `event_id` 生成规则；
- 按 event priority band 划定的 producer allowlist；
- 维护中 event 与 facade-visible packet 的 diagnostics 最低要求；
- 用于细化或验收这些规则的 subagent 任务边界。

本表不实现 scheduler，不生成机器可读 schema，也不重开 WP3/WP4 行为。

## 3. 分发交付物

| 流程 | 必需输出 | owner 类型 | 思考预算 |
|------|----------|------------|----------|
| `WP2.5-F1` | manifest 字段分类表与标准示例。 | Schema worker。 | 高。 |
| `WP2.5-F2` | 枚举词汇表与兼容标签规则。 | 与 `F1` 相同 owner。 | 高。 |
| `WP2.5-A1` | event priority 表与确定性排序说明。 | Event semantics worker。 | 中高。 |
| `WP2.5-A2` | 按 priority band 的 producer allowlist matrix。 | 与 `F1/F2` 协调的 event semantics worker。 | 如果 producer 跨 facade 或兼容边界，则为高。 |
| `WP2.5-A3` | diagnostics 最低要求与开放问题清理。 | 与 state/barrier owner 协调的 event semantics worker。 | 中高。 |
| 任务簇集成 | 中英文节结构对齐与 `git diff --check`。 | Integration owner。 | 中。 |

## 4. StageNodeManifest 字段分类

出现分类：

- `Required`：每个维护中的 stage-node manifest 都必须出现该字段。只有在
  下方规则明确允许时，字段值才能是空列表。
- `Conditional`：条件成立时必须出现；否则 manifest 应省略该字段，或按说明
  设置为空/false。
- `Optional`：可为了文档清晰而出现，但除非后续 schema freeze 将其提升，
  否则后续实现不得依赖它。

| 字段 | 分类 | 值形态 | 规范规则 | 示例 |
|------|------|--------|----------|------|
| `node_id` | Required | 稳定字符串 id。 | 必须在 manifest registry 内全局稳定，并且维护中 stage-node event 必须用它作为 `producing_node_id`。 | `p7.fire_control_launch.v1` |
| `semantic_stage` | Required | 非空 `P0-P10` stage 名称列表。 | 必须命名该 node 管辖的语义生命周期阶段。 | `[P7 FireControlLaunch]` |
| `owner_module` | Required | source module、adapter、model family 或 facade surface。 | 必须标明负责 event emission 与 diagnostics 的维护 owner。 | `src/core/engine/simulation_kernel_weapon_api.cpp` |
| `input_packets` | Required | packet/request 名称列表；setup-only node 允许为空。 | 必须枚举消费的 contract packet 或 request。 | `[LaunchRequest, TrackPacket]` |
| `output_packets` | Required | packet/report/export 名称列表；只有 internal state-only node 允许为空。 | 必须枚举产出的 packet、report 或 facade export。 | `[LaunchEvent, DiagnosticsTrace]` |
| `read_state_shards` | Required | shard 名称列表，或 shard/policy 对。 | 必须列出该 node 读取的每个 committed 或 same-window state shard version。 | `[track, engagement, command]` |
| `write_state_shards` | Required | shard 名称列表；pure export/diagnostic node 允许为空。 | 必须列出该 node mutation 或 commit 的每个 shard。 | `[engagement]` |
| `read_snapshot_policy` | Required | 第 5.1 节枚举值之一。 | 必须描述该 node 可以观察到的最新 snapshot 类别。 | `post_injection` |
| `write_commit_policy` | Required | 第 5.2 节枚举值之一。 | 必须描述写入何时在 node 外部可见。 | `window_commit` |
| `clock_domain` | Required | cadence、slot、event condition 或 facade export rule。 | 必须命名 clock-domain merge 与 replay 工作要消费的 trigger domain。 | `event_driven_or_fire_control_cadence` |
| `latency_policy` | Required | 文本策略，或后续冻结的枚举值。 | 必须说明 output 是 same-window、next-window、delayed、link-latency controlled 还是 backend-sync controlled。 | `same_window_after_request_barrier` |
| `sync_policy` | Required | 文本策略，或后续冻结的枚举值。 | 必须说明 state 是 host-owned、backend-owned、partially synced、observation-only 还是 explicitly exported。 | `host_owned` |
| `allowed_same_window_edges` | Conditional | 下游 node id 或 stage family 列表。 | 当 `write_commit_policy = stage_publish` 或声明 same-window output visibility 时必须出现且非空；否则应为空。 | `[p8.munition_lifecycle.*]` |
| `required_barriers` | Required | 来自 `input_injection`、`stage_publish`、`window_commit`、`export` 的列表。 | 必须列出该 node 的运行或可见性所需的前置、后置或 gating barrier。 | `[input_injection, window_commit]` |
| `event_families_emitted` | Required | priority-band family 名称列表；只有 non-emitting internal node 允许为空。 | 必须列出该 node 发出的每个维护中 event family。 | `[fire_control_and_launch]` |
| `diagnostic_trace_obligations` | Required | 必需 trace 字段或 ancestry link 列表。 | 必须覆盖第 8 节的通用 diagnostics 最低要求，并加入 family-specific 字段。 | `[launch_request_id, launch_event_id, input_track_snapshot_version]` |
| `facade_visibility` | Required | 第 5.3 节枚举值之一。 | 必须说明 output 是 internal、维护中 facade-visible、compatibility-only 还是 diagnostics-only。 | `maintained_facade_export` |
| `compatibility_adapter_allowed` | Conditional | boolean 或 compatibility label object。 | 当允许 legacy/raw-runtime access，或 `facade_visibility = compatibility_adapter` 时必须出现；否则应为 `false`。 | `legacy_fire_missile: compatibility_diagnostics_only` |

WP2.5 不新增 `allowed_producers` manifest 字段。producer allowlist 的规范来源是
第 7 节，后续可以再生成 registry。

## 5. Manifest 枚举词汇

### 5.1 `read_snapshot_policy`

| 值 | 含义 | 允许的可见性来源 |
|----|------|------------------|
| `pre_window` | 读取当前 scheduling window 开始前已提交的 snapshot。 | 前一个 `window_commit`。 |
| `post_injection` | 读取 pre-window snapshot 加上在 `input_injection` 接收的 injected input。 | `input_injection`。 |
| `same_window` | 读取上游 manifest edge 显式发布的 same-window output。 | `stage_publish` 加声明的 `allowed_same_window_edges`。 |
| `committed` | 只读取已提交 shard version。 | 依据 node 位置读取当前或前一个 `window_commit`。 |
| `diagnostic_only` | 读取不属于 scheduler truth 的 view。 | 只允许声明的 diagnostics/export slot。 |

### 5.2 `write_commit_policy`

| 值 | 含义 | 可见性规则 |
|----|------|------------|
| `stage_publish` | output 对声明的 same-window consumer 可见。 | 需要非空 `allowed_same_window_edges` 与 `stage_publish` barrier。 |
| `window_commit` | output 在 window DAG 完成后成为 committed state shard 或 future event insert。 | `window_commit` 后可见。 |
| `delayed_event` | output 成为未来 window 或声明 event time 的 timestamped event。 | 当 timestamp 进入维护中的 window 时消费。 |
| `export_only` | output 只是基于 committed state 的 observation/facade export。 | 在 `export` 可见；不改变 scheduler truth。 |
| `diagnostic_only` | output 只用于 debug/test/inspection。 | 不得定义维护中 scheduler truth 或 policy/training truth。 |

### 5.3 `facade_visibility`

| 值 | 含义 | 维护状态 |
|----|------|----------|
| `internal` | Node output 不对 facade 可见。 | 若满足其他 manifest 规则，则为维护中。 |
| `maintained_facade_surface` | Node 消费或暴露维护中的 request surface。 | 维护中；需要 source metadata 与 diagnostics。 |
| `maintained_facade_export` | Node 发出维护中的 observation/export packet。 | 维护中；需要 committed `SnapshotVersion` ancestry。 |
| `compatibility_adapter` | Node 可通过 legacy/raw-runtime adapter 访问。 | 除非被维护 producer 包装，否则不是维护中 event truth。 |
| `diagnostics_only` | Node output 仅用于 inspection、test 或 debug export。 | 不是维护中 scheduler truth。 |

### 5.4 Compatibility Labels

| 标签 | 含义 | 写入权限 |
|------|------|----------|
| `maintained_stage_node` | Event 由 manifest-declared stage node 发出。 | 可以为声明的 family 写入维护中 event queue。 |
| `maintained_facade_surface` | Event/request 通过带 source metadata 的维护中 facade surface。 | 可以产生 priority `100` injection event；其他情况下作为 stage-node event 的 source ancestry。 |
| `external_injection` | Policy、orchestration、human 或 external source 通过 `input_injection`。 | 只能产生 priority `100` injection event。 |
| `compatibility_diagnostics_only` | Legacy/raw-runtime 路径尚未被维护语义包装。 | 只能写 diagnostics/export channel。 |
| `diagnostics_only` | 用于 inspection、test 或 debug export 的 helper。 | 只能写 diagnostics/export channel。 |

### 5.5 Producer Categories

| Producer category | 必需标签 | 维护中 event 角色 | 必需 metadata |
|-------------------|----------|-------------------|---------------|
| `stage_node` | `maintained_stage_node` | 当 manifest 声明 family 时，作为 `000`、`200-900` 的主要维护 producer。 | `node_id`、`world_id`、`event_family`、`local_sequence`、source snapshots。 |
| `runtime_facade` | `maintained_facade_surface` | 只作为显式 injection/reset surface 的维护 producer；其他情况下作为 source ancestry。 | `source_id`、`input_snapshot_version`、`effective_time`、`valid_until`、`merge_policy`。 |
| `external_injection` | `external_injection` | 作为 priority `100` 的已到达外部意图 producer。 | `source_id`、`effective_time`、`merge_policy`、authority/validity metadata。 |
| `compatibility_adapter` | `compatibility_diagnostics_only` | 只作为兼容桥接。 | legacy source ref、存在时的 wrapper id、diagnostic reason。 |
| `diagnostic_helper` | `diagnostics_only` | 只用于 inspection/test/debug。 | test/debug id、可获得时的 source snapshot、diagnostic reason。 |

## 6. Event Ordering 与 Deterministic IDs

维护中的 event 行为必须按以下 key 排序：

```text
(timestamp, priority, event_id)
```

`timestamp` 是仿真时间。`priority` 由 event family 固定。`event_id` 必须确定性
生成。插入顺序、墙钟时间、指针身份、entity allocation accident 与非确定性容器
遍历不得成为语义 tie-breaker。

Priority 分层：

| Priority | Event family | 典型维护 producer |
|----------|--------------|-------------------|
| `000` | setup and reset events | `P1 WorldSetup` 或维护中的 reset surface。 |
| `100` | external intent injection | facade、policy、orchestration、human 或声明的 injection adapter。 |
| `200` | tasking and command delivery | `P2 TaskingIntent`、`P3 CommandDelivery`。 |
| `300` | platform control handoff | `P4 PlatformControl`。 |
| `400` | physics/contact candidates | `P5 PhysicsStep`。 |
| `500` | sensing, track, and link updates | `P6 SenseTrackLink`。 |
| `600` | fire-control and launch | `P7 FireControlLaunch`。 |
| `700` | munition lifecycle | `P8 MunitionLifecycle`。 |
| `800` | effects and damage | `P9 EffectsDamage`。 |
| `900` | observation, diagnostics, and export | `P10 ObservationExport`。 |

确定性的 `event_id` 规则保持不变：

```text
event_id = stable_hash(run_seed, world_id, producing_node_id, event_family, local_sequence)
```

要求：

1. 对 stage-node event，`producing_node_id` 必须来自
   `StageNodeManifest.node_id`；对 priority `100` injection event，可来自维护中
   facade/external source id。
2. `local_sequence` 必须在单个 producing node 或维护 source、单个 event
   family、单个 scheduling window 与单个 world 内计数。
3. 并行 producer 不得从共享 mutable counter 分配 event id，除非 counter 顺序
   本身由确定性 node order 推导。
4. 无法产生 deterministic id 的兼容路径必须标为
   `compatibility_diagnostics_only` 或 `diagnostics_only`。

## 7. 按 Priority Band 的 Producer Allowlist

下表是 WP2.5 producer allowlist。后续实现可以把它编码为 registry，但 WP2.5
不新增 runtime registry 或 manifest 字段。

| Priority | Event family | 维护中 producer category | 条件性或兼容 producer | 明确禁止作为维护中 truth 的来源 |
|----------|--------------|--------------------------|-----------------------|----------------------------------|
| `000` | setup and reset events | `stage_node`；`runtime_facade` 仅限声明的维护中 reset/setup surface。 | `compatibility_adapter` 可为 legacy setup/reset 导出 diagnostics。 | `diagnostic_helper` 与未包装的 compatibility path。 |
| `100` | external intent injection | `runtime_facade`；`external_injection`；声明的 injection `stage_node`。 | `compatibility_adapter` 只能作为 `compatibility_diagnostics_only`。 | 缺少 `source_id`、`effective_time` 与 `merge_policy` 的 raw helper call。 |
| `200` | tasking and command delivery | `stage_node`。 | `runtime_facade` 与 `external_injection` 可通过 priority `100` 作为 ancestry source，但不能直接作为 producer。 | 直接写入 command/tasking 维护队列的 facade。 |
| `300` | platform control handoff | `stage_node`。 | Compatibility adapter 只能镜像 diagnostics。 | 绕过 tasking 或 command delivery 的 human/policy helper。 |
| `400` | physics/contact candidates | `stage_node`。 | Backend compatibility export 在 backend profile 声明 deterministic merge/order 前只能是 diagnostics-only。 | Backend thread completion order 或 raw physics callback order。 |
| `500` | sensing, track, and link updates | `stage_node`。 | External sensor/link adapter 必须由维护中的 node 包装，或走 priority `100` injection path。 | 直接写维护中 track queue 的 diagnostic sensor。 |
| `600` | fire-control and launch | `stage_node`。 | Facade launch request 是 ancestry input；legacy fire-missile adapter 在包装前是 `compatibility_diagnostics_only`。 | 直接写 launch event queue 的 facade 或 compatibility path。 |
| `700` | munition lifecycle | `stage_node`。 | Backend/legacy munition helper 只能导出 diagnostics。 | 没有 deterministic ordering 的 raw resident-state callback。 |
| `800` | effects and damage | `stage_node`。 | Compatibility damage calculator 在包装前只能发 diagnostics。 | 缺少 shard version 与 barrier ancestry 的直接 mutation report。 |
| `900` | observation, diagnostics, and export | `stage_node`；`runtime_facade` 可用于维护中 export surface。 | `diagnostic_helper` 与 `compatibility_adapter` 可以写 diagnostics/export channel，但不能写 scheduler truth。 | 被用作 policy/training truth 的 diagnostics-only material。 |

## 8. Diagnostics 最低要求

本任务簇涉及的每个维护中 event 或 facade-visible packet 都必须记录：

- event identity：`event_id`、`event_family`、`timestamp`、`priority`；
- producer identity：`producing_node_id` 或 external `source_id`；
- ordering scope：`world_id`、scheduling window 与 `local_sequence`；
- source versions：相关 `SnapshotVersion` 或 input snapshot 字段；
- barrier ancestry：至少记录 event 或 packet 从哪个 barrier 后开始可见；
- ancestry links：可获得时记录 request id、parent event id、entity ref、report
  id 或 observation packet version；
- 当来源不是维护中 stage node 时，记录 compatibility label。

Family-specific diagnostics 可以增加必需字段，但不得移除上述通用最低要求。

## 9. 标准 Manifest 示例

下面的示例 registry 是 `P0-P10` 的规范起始覆盖。每条示例都刻意保持紧凑，
但仍必须使用已经冻结的 `StageNodeManifest` 词汇，这样后续 scheduler、facade、
replay 与 validation 工作都能引用同一套 registry 形状。

维护中的 `P0 ContentCompile` 示例：

```yaml
node_id: p0.content_compile.v1
semantic_stage: [P0 ContentCompile]
owner_module: content/ and scenario compiler adapters
input_packets: [ScenarioDefinition, BackendProfileRequest]
output_packets: [WorldSetupPacket, ContentIdSet]
read_state_shards: [setup]
write_state_shards: [setup]
read_snapshot_policy: pre_window
write_commit_policy: window_commit
clock_domain: setup_only
latency_policy: same_window_setup
sync_policy: host_owned
allowed_same_window_edges: []
required_barriers: [window_commit]
event_families_emitted: [setup_and_reset]
diagnostic_trace_obligations: [content_id_set, setup_commit_id]
facade_visibility: maintained_facade_surface
compatibility_adapter_allowed: false
```

维护中的 `P1 WorldSetup` 示例：

```yaml
node_id: p1.world_setup.v1
semantic_stage: [P1 WorldSetup]
owner_module: src/runtime/facade/runtime_facade.cpp
input_packets: [WorldSetupPacket, BatchResetRequest]
output_packets: [WorldBatchPacket, EntityRefPacket]
read_state_shards: [setup]
write_state_shards: [setup]
read_snapshot_policy: post_injection
write_commit_policy: window_commit
clock_domain: reset_or_setup_request
latency_policy: same_window_after_request_barrier
sync_policy: host_owned
allowed_same_window_edges: []
required_barriers: [input_injection, window_commit]
event_families_emitted: [setup_and_reset]
diagnostic_trace_obligations: [setup_commit_id, world_id]
facade_visibility: maintained_facade_surface
compatibility_adapter_allowed: false
```

维护中的 `P2 TaskingIntent` 示例：

```yaml
node_id: p2.tasking_intent.v1
semantic_stage: [P2 TaskingIntent]
owner_module: components/tasking and core/mission
input_packets: [TaskOrder, LeaderIntent]
output_packets: [TaskingStatePacket, AuthorityStatePacket]
read_state_shards: [tasking, command]
write_state_shards: [tasking]
read_snapshot_policy: post_injection
write_commit_policy: window_commit
clock_domain: tasking_update_slot
latency_policy: same_window_after_request_barrier
sync_policy: host_owned
allowed_same_window_edges: []
required_barriers: [input_injection, window_commit]
event_families_emitted: [tasking_and_command_delivery]
diagnostic_trace_obligations: [source_id, input_snapshot_version]
facade_visibility: maintained_facade_surface
compatibility_adapter_allowed: false
```

维护中的 `P3 CommandDelivery` 示例：

```yaml
node_id: p3.command_delivery.v1
semantic_stage: [P3 CommandDelivery]
owner_module: command-link systems
input_packets: [MissionCommand, CoordinationIntentPacket]
output_packets: [DeliveredCommandPacket, CommandDeliveryReport]
read_state_shards: [tasking, command]
write_state_shards: [command]
read_snapshot_policy: post_injection
write_commit_policy: window_commit
clock_domain: command_link_tick
latency_policy: link_latency_controlled
sync_policy: host_owned
allowed_same_window_edges: []
required_barriers: [input_injection, window_commit]
event_families_emitted: [tasking_and_command_delivery]
diagnostic_trace_obligations: [source_id, command_report_id]
facade_visibility: internal
compatibility_adapter_allowed: false
```

维护中的 `P4 PlatformControl` 示例：

```yaml
node_id: p4.platform_control.v1
semantic_stage: [P4 PlatformControl]
owner_module: control models and platform systems
input_packets: [DeliveredCommandPacket, ActionIntentPacket]
output_packets: [ControlInputPacket, ActionValidityReport]
read_state_shards: [command, control, physics]
write_state_shards: [control]
read_snapshot_policy: committed
write_commit_policy: stage_publish
clock_domain: control_rate_slot
latency_policy: same_window_after_request_barrier
sync_policy: host_owned
allowed_same_window_edges: [p5.physics_step.v1]
required_barriers: [input_injection, stage_publish, window_commit]
event_families_emitted: [platform_control_handoff]
diagnostic_trace_obligations: [source_id, control_validity_report_id]
facade_visibility: internal
compatibility_adapter_allowed: false
```

维护中的 `P5 PhysicsStep` 示例：

```yaml
node_id: p5.physics_step.v1
semantic_stage: [P5 PhysicsStep]
owner_module: physics systems and backends
input_packets: [ControlInputPacket, EnvironmentPacket]
output_packets: [TruthStatePacket, PhysicsTracePacket]
read_state_shards: [control, physics]
write_state_shards: [physics]
read_snapshot_policy: same_window
write_commit_policy: window_commit
clock_domain: physics.fixed_tick
latency_policy: same_window_after_control_publish
sync_policy: host_owned
allowed_same_window_edges: []
required_barriers: [stage_publish, window_commit]
event_families_emitted: [physics_contact_candidates]
diagnostic_trace_obligations: [source_shard_versions, resulting_snapshot_version]
facade_visibility: internal
compatibility_adapter_allowed: false
```

维护中的 `P6 SenseTrackLink` 示例：

```yaml
node_id: p6.sense_track_link.v1
semantic_stage: [P6 SenseTrackLink]
owner_module: sensor, EW, track, and data-link systems
input_packets: [TruthStatePacket, LinkStatePacket]
output_packets: [TrackPacket, DetectionPacket, SharedTrackReport]
read_state_shards: [physics, track, command]
write_state_shards: [track]
read_snapshot_policy: committed
write_commit_policy: window_commit
clock_domain: sensor.scan_slot
latency_policy: next_window_after_scan
sync_policy: host_owned
allowed_same_window_edges: []
required_barriers: [window_commit]
event_families_emitted: [sensing_track_and_link_updates]
diagnostic_trace_obligations: [source_time, source_shard_versions, track_snapshot_version]
facade_visibility: maintained_facade_export
compatibility_adapter_allowed: false
```

维护中的 `P7 FireControlLaunch` 示例：

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
allowed_same_window_edges: []
required_barriers: [input_injection, window_commit]
event_families_emitted: [fire_control_and_launch]
diagnostic_trace_obligations:
  - launch_request_id
  - launch_event_id
  - input_track_snapshot_version
facade_visibility: maintained_facade_export
compatibility_adapter_allowed:
  legacy_fire_missile: compatibility_diagnostics_only
```

维护中的 `P8 MunitionLifecycle` 示例：

```yaml
node_id: p8.munition_lifecycle.v1
semantic_stage: [P8 MunitionLifecycle]
owner_module: guidance, seeker, and fuze systems
input_packets: [LaunchEvent, TrackPacket]
output_packets: [MunitionLifecyclePacket, DiagnosticsTrace]
read_state_shards: [engagement, track, physics]
write_state_shards: [engagement]
read_snapshot_policy: committed
write_commit_policy: window_commit
clock_domain: munition_guidance_slot
latency_policy: same_window_after_launch
sync_policy: host_owned
allowed_same_window_edges: []
required_barriers: [window_commit]
event_families_emitted: [munition_lifecycle]
diagnostic_trace_obligations: [launch_event_id, munition_id, source_shard_versions]
facade_visibility: maintained_facade_export
compatibility_adapter_allowed: false
```

维护中的 `P9 EffectsDamage` 示例：

```yaml
node_id: p9.effects_damage.v1
semantic_stage: [P9 EffectsDamage]
owner_module: effects models and damage systems
input_packets: [MunitionLifecyclePacket, EffectsTriggerCandidate]
output_packets: [EffectsEvent, DamageReport, DiagnosticsTrace]
read_state_shards: [engagement, damage, physics]
write_state_shards: [damage]
read_snapshot_policy: committed
write_commit_policy: window_commit
clock_domain: event_driven_effects_resolution
latency_policy: delayed_event
sync_policy: host_owned
allowed_same_window_edges: []
required_barriers: [window_commit]
event_families_emitted: [effects_and_damage]
diagnostic_trace_obligations: [launch_event_id, effects_event_id, damage_report_id]
facade_visibility: maintained_facade_export
compatibility_adapter_allowed: false
```

维护中的 `P10 ObservationExport` 示例：

```yaml
node_id: p10.observation_export.v1
semantic_stage: [P10 ObservationExport]
owner_module: src/core/engine/simulation_observation_api.cpp
input_packets: [CommittedSnapshot, DiagnosticsTrace]
output_packets: [ObservationPacket, DiagnosticsTraceBatchPacket]
read_state_shards: [setup, tasking, command, control, physics, track, engagement, damage, observation]
write_state_shards: [observation]
read_snapshot_policy: committed
write_commit_policy: export_only
clock_domain: export_slot_after_window_commit
latency_policy: post_commit_export
sync_policy: explicit_export
allowed_same_window_edges: []
required_barriers: [window_commit, export]
event_families_emitted: [observation_diagnostics_and_export]
diagnostic_trace_obligations:
  - observation_packet_version
  - committed_snapshot_version
  - source_shard_versions
facade_visibility: maintained_facade_export
compatibility_adapter_allowed: false
```

## 10. 分发计划

1. `WP2.5-F1/F2` 必须先落地，因为 manifest 词汇约束 event producer、
   diagnostics、state/barrier reference 与 replay input。
2. 字段名与 priority-band 名称稳定后，`WP2.5-A1` 可以并行推进。
3. `WP2.5-A2/A3` 在收口 same-window visibility 或 diagnostics 文案前，必须
   与 state/barrier 任务簇协调。
4. 任务簇集成必须保持英文主文与中文辅文按章节对齐。
5. 任务簇集成应运行：

```bash
git diff --check -- docs/task/simulation_architecture/wp25_manifest_event_cluster_20260519.md docs/task/simulation_architecture/wp25_manifest_event_cluster_20260519.zh.md
```

## 11. 验收标准

1. WP2.5 冻结中的每个 `StageNodeManifest` 字段都有
   required/conditional/optional 分类。
2. `read_snapshot_policy`、`write_commit_policy`、`facade_visibility`、兼容标签
   与 producer categories 都有枚举表。
3. Event ordering 保持为 `(timestamp, priority, event_id)`。
4. 确定性 `event_id` 公式保持为
   `stable_hash(run_seed, world_id, producing_node_id, event_family, local_sequence)`。
5. Producer allowlist matrix 覆盖从 `000` 到 `900` 的每个 priority band。
6. Diagnostics 最低要求已明确，compatibility-only producer 不能定义维护中
   scheduler truth。
7. Runtime implementation、generated registry 与两份 owned task sheet 外的编辑
   均保持 out of scope。
8. 英文与中文文档保持章节对齐。

## 12. 非目标

- 不实现 runtime scheduler。
- 不重开 WP3 或 WP4。
- 不实现 backend parity 或 replay harness。
- 不生成 machine-readable registry。
- 不新增 public facade API。
- 不编辑这两份任务单之外的文件。

## 13. 开放问题

1. `stable_hash` 是否应在 WP2.5 阶段命名具体算法，还是在输入 tuple 已冻结的
   前提下继续推迟到实现阶段选择？
2. 后续 schema 工作是否应把 `maintained_facade_surface` 与
   `maintained_facade_export` 拆成独立 producer registry，还是继续作为一个
   facade-governance family？

从草案中关闭的问题：

- `allowed_producers` 在 WP2.5 中不是一级 manifest 字段；规范来源是第 7 节
  producer matrix。
- Diagnostics 采用一个通用最低要求；family-specific 字段只能在其上追加。
- Diagnostics-only 与 compatibility-only adapter 不得写入维护中 event queue。
