# WP2.5-D + WP2.5-E 规范分发单：时钟域合并与确定性回放

状态：`2026-05-19` 规范分发单。

语言版本：

- 英文主文：[wp25_clock_replay_cluster_20260519.md](wp25_clock_replay_cluster_20260519.md)
- 中文辅文：`wp25_clock_replay_cluster_20260519.zh.md`

输入：

- [WP2.5 调度语义冻结](scheduler_semantics_wp25_20260519.zh.md)
- [WP2.5-F + WP2.5-A manifest/event 任务簇](wp25_manifest_event_cluster_20260519.zh.md)
- [WP2.5-B + WP2.5-C state/barrier 任务簇](wp25_state_barrier_cluster_20260519.zh.md)
- [仿真系统架构设计](../../plan/architecture/simulation_system_architecture_design.zh.md)
- [架构计划评审](../review/architecture_plan_review_20260519.zh.md)

规范用语：

- `MUST` 表示 WP2.5 文档与后续实现必须遵守的行为。
- `MUST NOT` 表示不能定义维护中 scheduler 或 replay truth 的行为。
- `SHOULD` 表示默认规则；偏离时需要明确的后续任务或评审记录。
- `MAY` 表示允许的兼容或诊断路径。

## 1. 目的

本分发单把 `WP2.5-D Clock-Domain Merge` 与
`WP2.5-E Deterministic Replay Contract` 转成规范任务包。后续负责
scheduler、facade、backend、diagnostics 或 replay 的 subagent 可以引用本文件，
而不需要临时发明新的 clock 或 replay 语义。

分发目标是：

- `WP2.5-D` 冻结 clock domain 如何合并进确定性 scheduling window。
- `WP2.5-E` 冻结 replay input envelope、禁止的非确定性、parity-budget 声明与 diagnostics 义务。

本文件是文档/规范工作，MUST NOT 实现 runtime scheduler 或 replay harness。

## 2. 规范范围与非目标

范围内：

- nested triggering 作为默认 outer-window 规则；
- `nested_slot`、`hold_last`、`interpolate`、`enqueue_event`、
  `defer_to_next_window`、`reject_on_ambiguous_order` 的 merge-policy 矩阵；
- independent clock domain 作为 maintained、rejected 或 diagnostics-only fallback 的处理方式；
- 使用稳定的 `StageNodeManifest`、event、shard、`SnapshotVersion` 与 barrier 词汇定义 replay input envelope；
- 禁止非确定性表；
- accelerated 或 approximate backend 的 parity-budget 模板；
- 连接 request、event、`SnapshotVersion`、barrier、report 与 export 的 diagnostics 义务。

非目标：

- 不实现 runtime scheduler；
- 不实现 replay harness；
- 不实现 backend parity；
- 不生成机器可读 registry；
- 不新增 merge-policy 取值；
- 不新增 public facade API；
- 不重开 WP3，也不改变 WP4 范围。

## 3. 分发切片

| 切片 | 关注点 | 必要产出 | 依赖 | 思考预算 |
|------|--------|----------|------|----------|
| `D1` | Merge-policy 矩阵。 | 六个冻结 merge-policy 取值的规范表。 | Manifest/event 任务簇与 state/barrier 任务簇。 | 高 |
| `D2` | Independent clock-domain 处理。 | Maintained/rejected/diagnostics-only 规则与 required metadata。 | `D1`、架构基线中的 backend profile 词汇。 | 高 |
| `E1` | Replay input envelope。 | Replay 输入与必要 provenance 的有序表。 | `D1/D2`、manifest/event 任务簇、state/barrier 任务簇。 | 高 |
| `E2` | 禁止非确定性与 parity。 | Nondeterminism 表与 parity-budget 模板。 | `E1` 与冻结的 backend-reference 规则。 | 高 |
| `E3` | Diagnostics 义务与验收。 | Trace 义务、验收门槛与 open-question cleanup。 | `D1-D2`、`E1-E2`。 | 中高 |

并行规则：

1. `D1` MUST 先于 `D2` 落地，因为 independent-domain 处理会引用 merge-policy 取值。
2. `E1` MAY 在 `D2` review 时先起草，但在 `D2` 稳定前 MUST NOT 定稿规范性文字。
3. `E2` 与 `E3` MAY 在 `E1` 稳定后并行，但必须有一个 owner 负责最终英文/中文章节对齐。
4. 同一张规范表 MUST NOT 拆给多个作者同时编辑。

## 4. 时钟域基线

默认维护中调度规则是：

```text
one outer scheduling window owns deterministic order;
lower-rate domains run as declared nested triggers inside that window.
```

必要基线规则：

1. 维护中的 stage node MUST 在 `StageNodeManifest` 中声明 `clock_domain`、
   `latency_policy`、`sync_policy`、`required_barriers` 与 emitted event families。
2. 只要 cadence 可以表达为 outer window 内的确定性 slot，lower-rate domain SHOULD 表达为 nested trigger。
3. 无法证明确定性顺序的 domain MUST 使用 `reject_on_ambiguous_order`
   或 diagnostics-only fallback。
4. Independent backend 或 resident-state clock 在声明 sync barrier、event export order、parity budget 与 diagnostics metadata 前，不能成为维护中的 replay source。

## 5. Merge-Policy 矩阵

WP2.5 不引入六个冻结取值之外的 merge-policy。

| Merge policy | 维护中用途 | 必要输入 | 可见性/barrier 规则 | Replay 规则 | 拒绝或诊断规则 |
|--------------|------------|----------|---------------------|-------------|----------------|
| `nested_slot` | Producer 在 outer scheduling window 内的确定性 slot 运行。 | `clock_domain`、slot number 或 cadence rule、`node_id`、`world_id`、source `SnapshotVersion` 与 required barriers。 | Output 按 producer manifest 声明的 `stage_publish`、`window_commit` 或 `export` 可见。 | Replay 在相同 slot 重跑 producer，并按 `(timestamp, priority, event_id)` 排序 event。 | slot 声明缺失或重复是 replay error，除非该 node 是 diagnostics-only。 |
| `hold_last` | Lower-rate producer output 在 `valid_until` 或等价有效期前被复用。 | Producer output id、`effective_time`、`valid_until`、source snapshot、held value version 与 consumer domain。 | Consumer 只能在声明的 injection 或 commit barrier 之后、过期之前读取 held output。 | Replay 必须记录首次 producer event/request，以及依赖 held value 的每个 consumer window。 | 没有有效 held output 时，consumer 必须 reject、defer，或使用声明过的 diagnostics-only fallback。 |
| `interpolate` | Consumer 从两个 versioned producer output 推导中间值。 | 前后两个 producer output id、source time、source shard version、interpolation rule id 与 consumer node id。 | Interpolated value 是派生 consumer view，不提交 producer shard version。 | Replay 必须用相同两个 versioned output 和 rule id 重建相同 interpolation。 | 任一 endpoint 缺失、未版本化、diagnostics-only 或无序时，interpolation 不是维护行为。 |
| `enqueue_event` | Producer output 变成当前或后续 window 的 timestamped event。 | Event family、timestamp、deterministic `event_id`、source request/event id、source snapshot 与 target barrier。 | Event 在 timestamp 进入维护中 window 后消费，并按 `(timestamp, priority, event_id)` 排序。 | Replay 消费排序后的 event stream；插入顺序绝不是 tie-breaker。 | 没有 deterministic id 或 timestamp 的 event 从维护 truth 中拒绝，只能 diagnostics-only。 |
| `defer_to_next_window` | Producer output 被接受，但到下一 scheduling window 才可见。 | Source request id、`effective_time`、prior snapshot、target window id 或 timestamp，以及 deferred reason。 | Output 对当前 window 的维护逻辑不可见，并在下一次 `input_injection` 或声明 barrier 后变成 eligible。 | Replay 必须保留 deferral decision 与 target window。 | 隐式 current-window visibility 被禁止；模糊 deferral 变成 reject 或 diagnostics-only。 |
| `reject_on_ambiguous_order` | 当无法证明确定性顺序时，scheduler 或 adapter 拒绝输入。 | Source id、attempted merge policy、ambiguity reason、input snapshot 与 rejection barrier。 | 不发生维护中的 state shard 或 event queue mutation。Diagnostics 可以导出 rejection。 | Replay 必须用相同 metadata 重现相同 rejection。 | 当顺序歧义会影响 scheduler truth 时，这是唯一维护中的结果。 |

## 6. Independent Clock-Domain 处理

Independent clock domain 包括 external backend、device-resident state、
resident physics substep、asynchronous sensor、service callback，或任何无法自然表达为 outer scheduling window 中 nested slot 的 producer。

| 处理状态 | 规范规则 | 必要 metadata | 允许输出 | 验收门槛 |
|----------|----------|---------------|----------|----------|
| Maintained | 只有在声明了可 replay 的确定性 merge order 时，MAY 成为维护行为。 | `clock_domain_id`、owner node/backend、deterministic backend profile、sync barriers、event export order、merge policy、source time、source `SnapshotVersion` 或 shard versions、`effective_time`、适用时的 `valid_until`、parity-budget reference、diagnostics obligations。 | 按 manifest 与 barrier 规则产生 maintained event、committed shard update 或 facade export。 | 后续 replay 能在不依赖 wall-clock 或 thread completion order 的情况下重建相同 request/event/report/export 顺序。 |
| Rejected | 缺少 deterministic order、required metadata、valid source snapshot 或允许的 merge policy 时，MUST 拒绝。 | Source id、attempted domain id、ambiguity 或 missing-metadata reason、可用时的 input snapshot、rejection barrier。 | 仅 rejection diagnostics；不产生 maintained event 或 shard mutation。 | rejection 本身可 replay，且不改变维护中 scheduler truth。 |
| Diagnostics-only fallback | Source 有检查价值但不是维护行为时，MAY 导出 inspection data。 | Compatibility 或 diagnostics label、source id、best-effort timestamp、可用时的 source snapshot、not-maintained reason、export barrier。 | 仅 diagnostics/export channel。 | Output MUST NOT 定义 scheduler truth、policy/training truth、replay parity truth 或 event-queue truth。 |

额外 independent-domain 规则：

1. Independent domain MUST NOT 使用 backend thread completion order 作为 event order。
2. Independent domain MUST NOT 使用 wall-clock arrival time 作为维护中的 tie-breaker。
3. Missed slot 是 replay error，除非 manifest 或 backend profile 显式声明 skippable semantics，并且 diagnostics 记录每次 skip。
4. Backend profile MUST 在 replay 把它视为维护 source 前，声明自己是 CPU exact、accelerated exact、approximate 还是 diagnostics-only。
5. Maintained output 产生时，independent-domain diagnostics SHOULD 同时记录 pre-merge source snapshot 与 post-merge committed/exported snapshot。

## 7. Replay Input Envelope

维护中的 replay MUST 能由下表中的有序 input envelope 重建。该表使用 manifest/event 与 state/barrier 分发单中的稳定词汇。

| Input block | 必要内容 | 来源词汇 | Replay 用途 | Diagnostics 链接 |
|-------------|----------|----------|-------------|------------------|
| Static content and scenario setup | Content id、scenario setup packet、world setup ref、setup/reset commit id。 | `setup` shard、`P0/P1`、`SnapshotVersion`、setup/reset event。 | 重建初始权威状态。 | Setup manifest id、content id set、setup barrier id。 |
| Run identity | Run seed、world id、deterministic backend profile id、replay format/version id。 | `world_id`、backend profile、`StageNodeManifest` registry。 | 定义 deterministic identity 与 backend 假设。 | Run trace id 与 profile hash 或 stable id。 |
| Stage-node registry | 带有 `node_id`、stage、packet、shard、clock domain、barrier、event family、diagnostics obligation 与 facade visibility 的 `StageNodeManifest`。 | Manifest/event 任务簇字段与 enum 词汇。 | 定义合法 producer、consumer、barrier 与 event family。 | Manifest registry id 或 version。 |
| External and facade requests | `source_id`、request id、input packet type、`input_snapshot_version`、`effective_time`、`valid_until`、`merge_policy`、authority/validity metadata。 | Priority `100` injection event、facade/external producer category。 | Replay accepted、deferred、rejected 与 diagnostics-only injection。 | Request trace id、injection barrier、accepted/rejected reason。 |
| Clock-domain merge records | Domain id、merge policy、slot 或 source time、held/interpolated endpoint、target window、rejection 或 diagnostics reason。 | 第 5 节 merge-policy 矩阵与第 6 节 independent-domain metadata。 | 重建跨 domain 可见性与排序决策。 | Merge trace id、source 与 resulting snapshot。 |
| Event stream | 按 `(timestamp, priority, event_id)` 排序的 event，包含 event family、producer id、local sequence、source request/event id 与 visibility barrier。 | Manifest/event priority table 与 deterministic id rule。 | Replay event 消费顺序。 | Event trace id 与 ancestry link。 |
| Snapshot sequence | 已提交的 `SnapshotVersion`，包含 global version、shard versions、source time、barrier id、barrier sequence 与 barrier detail。 | State/barrier 任务簇的 `SnapshotVersion` contract。 | 重建 committed state visibility。 | Snapshot trace id 与 source shard versions。 |
| Reports and facade exports | Report id、observation/export packet id、source `SnapshotVersion`、facade visibility label、diagnostics-only flag。 | `P10`、`observation` shard、`export` barrier、facade visibility enum。 | Replay 维护中的 export surface，并排除 diagnostics-only truth。 | Export trace id、report ancestry、observation packet version。 |
| Diagnostics trace | Request、event、report、snapshot、barrier、merge、rejection 与 export link。 | Manifest 中的 `diagnostic_trace_obligations` 与本文件。 | 审计 replay 重建与 parity comparison。 | Trace graph root 与每条边的 id。 |

## 8. 禁止非确定性

维护中的 scheduler 或 replay truth MUST NOT 依赖以下来源。

| 禁止来源 | 禁止原因 | 必要替代 | Diagnostics 处理 |
|----------|----------|----------|------------------|
| 非确定性容器遍历顺序 | 它会随运行、编译器或进程改变 event 或 producer order。 | 确定性 node order 加 `(timestamp, priority, event_id)`。 | 记录 ambiguity，并 reject 或标记 diagnostics-only。 |
| Wall-clock timing 作为 tie-breaker | 它不是仿真时间，无法可靠 replay。 | Simulated `timestamp`、`effective_time`、`valid_until` 与 deterministic event id。 | Wall-clock 只能作为非语义 diagnostic metadata。 |
| Raw pointer address | 分配布局会跨运行变化。 | `world_id`、`node_id`、request id、entity semantic id 或 event id 等稳定 id。 | Pointer-like value 不得出现在 maintained event id 中。 |
| Entity allocation accident | 并行或 backend layout 改变时，分配顺序可能变化。 | 记录在 `SnapshotVersion` ancestry 中的 stable entity ref 或 setup-assigned id。 | 仅基于分配的 id 在被包装前是 diagnostics-only。 |
| 隐藏的 Python helper call order | Frontend 调用顺序不是 scheduler truth，除非表达为 facade metadata。 | 带 `source_id`、`input_snapshot_version`、`effective_time`、`valid_until` 与 `merge_policy` 的 facade/external request。 | 未包装的 helper order 仅为 compatibility diagnostics。 |
| Backend thread completion order | Thread scheduling 依赖 host/runtime。 | 带 deterministic sync barrier 与 event export order 的 backend profile。 | 没有 profile 时，backend output 被 reject 或 diagnostics-only。 |
| 没有 budget 的 floating approximate backend drift | Approximate result 可能差异化但看起来合法。 | 在维护 replay 使用前声明 parity budget 与 comparison domain。 | 超出 budget 的 output 失败 parity 或保持 diagnostics-only。 |

## 9. Parity-Budget 模板

Accelerated 或 approximate backend 在被视为维护中的 replay source 前，MUST 声明 parity budget。

```yaml
parity_budget:
  budget_id: backend_profile.cpu_exact.reference
  backend_profile_id: cpu_exact.reference
  status: maintained_reference
  applies_to_clock_domains: [physics.fixed_tick, sensor.scan_slot]
  comparison_reference: cpu_exact
  deterministic_ordering:
    sync_barriers: [input_injection, window_commit, export]
    event_export_order: [timestamp, priority, event_id]
    merge_policies_allowed: [nested_slot, enqueue_event, defer_to_next_window]
  numeric_tolerance:
    position_abs: 0.0
    velocity_abs: 0.0
    time_abs: 0.0
  event_tolerance:
    event_family_set: exact
    event_order: exact
    rejected_inputs: exact
  snapshot_tolerance:
    shard_versions: exact
    committed_barriers: exact
  diagnostics_required:
    - backend_profile_id
    - source_snapshot_version
    - resulting_snapshot_version
    - parity_budget_id
```

模板规则：

1. CPU exact path 是默认参考，SHOULD 使用 exact parity。
2. Accelerated exact path MUST 保持 event order 与 committed shard version exact，除非后续 backend-specific 任务记录了更严格的例外。
3. Approximate path MUST 声明 numeric tolerance、event tolerance、snapshot tolerance 与 affected clock domain。
4. 没有 parity budget 的 backend MUST 对 replay truth 保持 diagnostics-only，即便它能导出有用的 inspection data。

## 10. Diagnostics 义务

Diagnostics MUST 连接完整 scheduler/replay 链：

```text
request -> input_injection -> merge decision -> event/report
  -> window_commit SnapshotVersion -> export -> replay/parity check
```

最小 trace 字段：

- `world_id`；
- scheduling window id 或 simulated time window；
- producer `node_id` 或 external `source_id`；
- 存在 request 时的 request id 与 input packet type；
- `input_snapshot_version` 或精确 source shard versions；
- merge policy 与 clock-domain id；
- barrier id 与可选 barrier detail；
- 产生 event 时的 event id、event family、timestamp、priority 与 local sequence；
- 产生 report/export 时的 report id 或 packet id；
- committed 或 exported output 的 resulting `SnapshotVersion`；
- facade visibility、compatibility label 或 diagnostics-only label；
- 适用时的 rejection reason、deferral target、hold expiry 或 interpolation endpoints；
- 任意 accelerated 或 approximate maintained source 的 parity-budget id。

义务表：

| 链路 | 必要 diagnostics | 不得省略 |
|------|------------------|----------|
| Request/injection | `source_id`、request id、`input_snapshot_version`、`effective_time`、`valid_until`、`merge_policy`、injection barrier。 | replay accepted、rejected 或 deferred input 所需的 source metadata。 |
| Merge decision | Clock-domain id、merge policy、source time、source snapshot、target window 或 barrier，以及 ambiguity/rejection reason。 | Output 变为 visible、deferred、rejected 或 diagnostics-only 的原因。 |
| Event/report | Deterministic event id 或 report id、producer id、priority band、source request/event link。 | `(timestamp, priority, event_id)` 排序字段。 |
| Snapshot/commit | Prior source shard versions、resulting `SnapshotVersion`、barrier id、barrier sequence。 | 被后续 stage 或 export 消费的 committed state ancestry。 |
| Export | Export packet id、source `SnapshotVersion`、facade visibility label、适用时的 diagnostics-only flag。 | Export 是 maintained truth 还是 diagnostics-only。 |
| Replay/parity | Replay input block id、backend profile id、parity-budget id、comparison outcome。 | 用于评估 parity 的 backend 与 budget metadata。 |

## 11. 验收标准

本任务簇在满足以下条件时通过：

1. 默认 nested-triggering 规则已明确；
2. 每个冻结 merge-policy 取值都有规范行，且没有新增取值；
3. independent clock domain 有 maintained、rejected 与 diagnostics-only 处理规则；
4. independent domain 的 required metadata 已明确；
5. replay input envelope 覆盖 setup、run identity、manifest、request、
   merge record、event、snapshot、report/export 与 diagnostics；
6. 禁止非确定性已列表化，并给出确定性替代；
7. parity-budget 模板区分 CPU exact、accelerated exact、approximate 与 diagnostics-only backend status；
8. diagnostics 义务连接 request、event、`SnapshotVersion`、barrier、report、export 与 parity；
9. runtime scheduler 与 replay harness implementation 仍在范围外；
10. 英文与中文文档保持章节对齐。

## 12. 已解决决策与剩余问题

已解决决策：

1. `interpolate` 在 WP2.5 中只作为派生 consumer view 维护；它不提交 producer shard version。
2. `parity_budget` 被视为可命名 affected clock domain 的 backend profile block，而不是单个标量。
3. Maintained independent-domain diagnostics SHOULD 在产生 output 时，同时记录 pre-merge source snapshot 与 post-merge committed/exported snapshot。
4. 当顺序歧义会影响 scheduler truth 时，`reject_on_ambiguous_order` 是唯一维护中的结果。
5. Missed slot 是 replay error，除非 manifest 或 backend profile 显式声明 skippable semantics，并且每次 skip 都被诊断记录。

剩余问题留给后续工作：

1. 未来机器可读 registry 是否应规范化 `clock_domain_id` 与 backend profile id。
2. 实现测试是否应要求每个 diagnostics-only fallback 都有完整 trace graph，或在没有 replay assertion 消费该 fallback 时允许紧凑记录。

## 13. 验证

任务簇集成 SHOULD 运行：

```bash
git diff --check -- docs/task/simulation_architecture/wp25_clock_replay_cluster_20260519.md docs/task/simulation_architecture/wp25_clock_replay_cluster_20260519.zh.md
```
