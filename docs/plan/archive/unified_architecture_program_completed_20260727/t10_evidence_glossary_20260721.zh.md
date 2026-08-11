# T10 证据词汇表（2026-07-21）

语言：
- 英文正本：[t10_evidence_glossary_20260721.md](t10_evidence_glossary_20260721.md)
- 中文伴随：`t10_evidence_glossary_20260721.zh.md`

文档种类：`reference`
生命周期：`maintained`
正本：`docs/plan/archive/unified_architecture_program_completed_20260727/t10_evidence_glossary_20260721.md`
所有者：`unified architecture program workline`
最后核验：`2026-07-21`
基线提交：`1d25c4d1`

状态：面向[统一架构计划](README.zh.md)的 T10 第二切片叠加式证据词汇表，执行
[T10 证据脊柱普查](t10_evidence_spine_census_20260721.zh.md)第 3 节所记切片顺序的第 2 步
（"叠加式证据词典。一份 schema 单源的 id/版本词典（VA-1、VA-2、VA-3），映射 `uint64` 与
`string` id 空间及两个版本概念——文档 + schema 元数据，不改字段"）。本文件是描述性
`reference` 登记，非独立评审：它是证据 id 空间与两个版本概念的**权威逐字段词汇表**，每条
事实均在基线 `1d25c4d1` 上对源码重新核实（普查在 `8bd21d86` 上核验；该面未变，且每一行都
自带 `file:line` 指针）。它不改变任何行为、不改任何字段、不改动 `src/**`/`python/**` 代码。
词汇以
[Simulation System Architecture Design](../../../architecture/standards/simulation_system_architecture_design.zh.md)
的 SCAL Evidence Graph 面为准（第 2 节，Evidence Graph："Trace ids, packet ancestry,
snapshot versions, event order, and validation verdicts"）。

## 0. 方法与范围

- 在基线 `1d25c4d1` 上重读维护面（`src/**` 只读、`python/**`、
  `tools/maintenance/dto_schema/**`、`tests/**`）。下文每条词汇行均标注其核实所依据的
  `file:line`；当某事实是生产者行为（而非声明）时，一并标注生产者 `file:line`。声明行号
  由机械方式从签入源码重新提取（非手工誊抄）并做了抽验。
- schema 单源的 DTO 字段列表位于 `src/runtime/contracts/detail/` 与
  `src/runtime/facade/detail/` 下的 X-macro `.inc` 片段，由
  `tools/maintenance/dto_schema/schemas/*.py` 生成。这些字段的行号指向签入的 `.inc` 片段
  （即 ABI/序列化面）。`src/runtime/contracts/counterfactual_replay_contract_types.h` 中的
  counterfactual/replay 契约类型是手写 struct；行号指向该头文件。
- **取值来源图例（适用于全部表格）。** 全文保持两组显式区分：(a) *声明默认值*
  （`.inc`/头文件声明所初始化的值，即默认构造的 DTO 携带的值）与*生产路径实际值*
  （kernel/facade 在导出/experiment 路径上实际写入的值）——若干字段两者不同；
  (b) *可由调用方直接构造*（该 DTO 是契约类型，调用方与 WP15 测试 fixture 可直接填写）与
  *facade/kernel 生产*（有生产代码路径为该字段赋值）。"生产者"列记录生产路径赋值，并显式
  标注可由调用方构造的面。
- 本词汇表映射普查的 VA-1（id 类型分裂）、VA-2（snapshot 版本名/型，当前无单调计数）、
  VA-3（版本概念混用）。VA-4/VA-5/VA-6/VA-7/VA-8 在其涉及某 id/版本字段处被引用，但其对齐
  工作留待普查的后续切片。
- 零代码变更。可选的 schema 元数据子任务已评估并放弃；理由（无语义合适的既有通道；扩展
  model 属生成器代码变更、超出本切片红线）记录于第 6 节。

## 1. 证据 id 空间

证据面以两种不相交的表示携带身份，当前没有任何单一类型化字段桥接它们（VA-1）：
trace/engagement/packet 面为 `std::uint64_t` 空间，worldline/replay/experiment 面为
`std::string` 空间。（不存在类型化转换；跨越是把数字文本化嵌入字符串——非穷举示例：
worldline-id 默认值嵌入 `world_index`/`entity_id` 数字，restore-boundary 的
`snapshot_version_ref` 嵌入 `uint64` `snapshot_version`，adapter 的
`input_snapshot_version` 默认值嵌入 `world_index`/`entity_id`
（`python/rl/runtime/world_batch/adapter.py:448`），packet-provenance 的 id/版本字符串
嵌入数值 `snapshot_version`（`runtime_facade_packet.cpp:204-211`、`:317-320`、
`:331-334`）；见第 3 节。）

### 1.1 `uint64` 身份字段

语义图例：**epoch-单调** = 在单个 event-store epoch 内递增，但 `clear()` / event-clock
回退时重置为 `1`；**batch-局部** = 在单次导出/批次内赋值，跨导出不稳定；**copy/ref** =
从另一字段的值复制或引用而来。

| 字段 | DTO — `file:line` | 类型 | 生产者（`file:line`） | 消费者 / 测试钉扎 | 语义 | VA |
|------|-------------------|------|-----------------------|-------------------|------|----|
| `trace_id` | `DiagnosticsTrace` — `diagnostics_trace.inc:6` | `std::uint64_t` | Kernel store 铸造 `trace.trace_id = next_engagement_event_id_++`（`simulation_kernel_engagement_event_store.cpp:364` launch、`:750` effects）；facade observation-export trace 则携带从 `request.trace_ids` 循环取出的调用方标签（`runtime_facade_packet.cpp:734`、`:828-831`），进入 `diagnostics_trace_from_track_packet`（`:368`） | `test_trace_replay_gates.py:196`（`trace_id > 0`、可重放排序） | kernel 铸造值在共享 engagement-event id 空间内 epoch-单调；observation-export 值是调用方标签（维护 adapter 占位 `[1]`），故不唯一 | VA-1, VA-8 |
| `parent_trace_id` | `DiagnosticsTrace` — `diagnostics_trace.inc:7` | `std::uint64_t` | facade observation-export 字面量硬编码 `0`（`runtime_facade_packet.cpp:369`）；kernel store 路径保留声明默认 `0` | `test_diagnostics_trace_contract.py:202`（`parent_trace_id == 0`） | 当前恒 `0`，故 trace ancestry 仅单层 | VA-8 |
| `chain_id` | `DiagnosticsTrace` — `diagnostics_trace.inc:8` | `std::uint64_t` | kernel launch：`= event_id`（`simulation_kernel_engagement_event_store.cpp:365`）；kernel effects：`= launch_event_id`，回退到 `effects_event_id`（`:761`）；observation export：`= trace_id`，即同一调用方标签（`runtime_facade_packet.cpp:370`） | `test_trace_replay_gates.py:197`（`chain_id == launch.event_id`） | kernel 路径上把 trace 归组到其起源事件；observation export 上等于请求标签 | VA-1, VA-8 |
| `track_id` | `DiagnosticsTrace` — `diagnostics_trace.inc:9` | `std::uint64_t` | observation export 复制 `= track.track_id`（`runtime_facade_packet.cpp:371`）；kernel launch 路径的 trace 保留声明默认 `0`（`simulation_kernel_engagement_event_store.cpp:363-368` 未设 `track_id`） | — | 存在时为 `TrackPacket` 身份的复制 | copy/ref |
| `launch_request_id` | `DiagnosticsTrace` — `diagnostics_trace.inc:10` | `std::uint64_t` | `= event.request_id`（`simulation_kernel_engagement_event_store.cpp:366`）；legacy launch 路径上 `request_id` 本身是铸造的 `event_id` 的复制（`:348`） | `test_trace_replay_gates.py:198` | 引用某 `LaunchEvent.request_id`（event-store id 空间） | copy/ref |
| `launch_event_id` | `DiagnosticsTrace` — `diagnostics_trace.inc:11` | `std::uint64_t` | `= event_id`（`simulation_kernel_engagement_event_store.cpp:367`） | `test_trace_replay_gates.py:194`（链接） | 引用某 `LaunchEvent.event_id`（event-store id 空间） | copy/ref |
| `effects_event_id` | `DiagnosticsTrace` — `diagnostics_trace.inc:13` | `std::uint64_t` | `next_engagement_event_id_++`（`simulation_kernel_engagement_event_store.cpp:747`） | — | effects id，取自 event-store 分配器 | VA-8 |
| `damage_report_id` | `DiagnosticsTrace` — `diagnostics_trace.inc:14` | `std::uint64_t` | `next_engagement_event_id_++`（`simulation_kernel_engagement_event_store.cpp:748`） | — | damage-report id，取自 event-store 分配器 | VA-8 |
| `track_id` | `TrackPacket` — `track_packet.inc:6` | `std::uint64_t` | `track_packet_from_observation_contact` 中 `= contact.id`（`runtime_facade_packet.cpp:343`）——observation contact 的实体 id，**并非** event-store 分配器 | `test_trace_replay_gates.py:202`（`track_id > 0`） | 观测路径上的传感器 contact 身份 | VA-1 |
| `entity_id` | `RuntimeCounterfactualSnapshot` — `runtime_counterfactual_snapshot.inc:11` | `std::uint64_t` | `counterfactual_snapshot_from_runtime` 中 `= ref.entity_id`（`runtime_facade_counterfactual.cpp:83`）；作为 worldline-id 默认字符串的组成（`:460-461`）与 `deterministic_seed` 默认值（`:466-467`） | `test_runtime_facade_counterfactual.py` | ECS 实体 id；其数字被嵌入 string worldline-id 空间的那个 `uint64` | VA-1 |
| `trace_ids` | `EngagementEventPacket` — `engagement_event_packet.inc:15` | `std::vector<std::uint64_t>` | 请求上由调用方提供；window coordinator 对空列表默认填 `[index + 1]`（`runtime_window_coordinator_selection_helpers.h:89-93`）；facade 把请求列表复制到 packet（`runtime_facade_packet.cpp:778`）并循环用于给 trace 打标（`:734`、`:828-831`）；维护 adapter 设 `[1]`（`python/rl/runtime/world_batch/adapter.py:436`） | `test_trace_replay_gates.py`（window 路径） | 请求侧打标列表；维护路径上为占位 `[1]` | VA-8 |
| `barrier_sequence` | `EngagementEventPacket` — `engagement_event_packet.inc:8` | `std::uint64_t` | 声明默认 `0`；导出路径写入常量 `kExportBarrierSequence = 1`（`runtime_facade_internal.h:55`；经 `apply_export_packet_metadata` `runtime_facade_packet.cpp:198` 与 `export_engagement_event_packet` `:780` 应用） | `test_trace_replay_gates.py:241` 仅钉扎默认构造的 `0` | 声明默认 `0` vs 生产路径实际值 `1`；固定导出常量，与任何分配器无关 | VA-7 |
| `barrier_sequence` | `ReplayBarrierRef` — `counterfactual_replay_contract_types.h:19` | `std::uint64_t` | 可由调用方构造（WP15 fixture）；experiment 信封设 `1`（`runtime_facade_counterfactual.cpp:127`）；restore boundary 设 `= snapshot.snapshot_version`（`:381`） | `test_replay_envelope_contracts.py`（WP15） | replay barrier 序号 | VA-7 |

**分配器范围。** `next_engagement_event_id_` 计数属于 kernel engagement event
store：从 `1` 起（`simulation_kernel_engagement_event_store.h:63`），被 `clear()` 重置为
`1`（`:1073`），且帧计数回退时 `reset_if_event_clock_rewound` 会再次调用 `clear()`
（`:274-279`）。它为 store 记录的**每一个** kernel 事件族铸造 event id：launch
（`simulation_kernel_engagement_event_store.cpp:345`；`request_id` 于 `:348` 从它复制）、
nearest-approach（`:385`）、fuze-evaluation（`:441`）、warhead-mechanism（`:508`）、
spatial-coverage（`:531`）、component-load（`:554`）、component-damage（`:576`）、
structural-breakup（`:599`）、platform-consequence（`:640`）、lifecycle-transition
（`:705`）——lethality-chain 事件族把这些 id 落在 `LethalityChainHeader.event_id`
（`lethality_chain_header.inc:8`，如 `:399`）——外加 store 铸造的 launch-trace
`trace_id`（`:364`）与 effects-damage 路径在 `:747-750` 连续铸造的
`effects_event_id`/`damage_report_id`/`platform_consequence_event_id`/`trace_id`
四元组。以上全部共享这一个可重置计数，跨重置可能碰撞。store 之外：
`TrackPacket.track_id` 来自 observation contact（`contact.id`）、packet `trace_ids` 是
调用方标签（window 默认 `[index + 1]`）、`barrier_sequence` 是固定导出常量——它们都不从
event-store 分配器取值。

### 1.2 `string` 身份字段

| 字段 | DTO — `file:line` | 类型 | 生产者（`file:line`） | 消费者 / 测试钉扎 | 语义 | VA |
|------|-------------------|------|-----------------------|-------------------|------|----|
| `source_node_id` | `DiagnosticsTrace` — `diagnostics_trace.inc:20` | `std::string` | kernel store 保留声明默认 `{}`；observation-export 字面量设 `kObservationExportNodeId` = `"observation_export.v1"`（`runtime_facade_packet.cpp:377`；常量 `runtime_facade_internal.h:50`）；recent/kernel trace 经 `apply_export_trace_metadata` 得到匹配的 stage 节点（`:225-227`，manifest 门控），调用点传入 launch/effects/observation 节点 id（`:497`、`:514-515`、`:520-521`、`:266-306`） | `test_trace_replay_gates.py:232`（字段存在） | stage 节点标签（注册的节点 id），非 run 唯一身份 | VA-1 |
| `export_node_id` | `DiagnosticsTrace` — `diagnostics_trace.inc:21` | `std::string` | kernel store 保留 `{}`；observation-export 字面量设 `"observation_export.v1"`（`runtime_facade_packet.cpp:378`）；`apply_export_trace_metadata` 将其设为 `kObservationExportNodeId`（manifest 门控，`:228-230`） | `test_trace_replay_gates.py:233`（字段存在） | 导出 stage 节点标签 | VA-1 |
| `worldline_id` | `RuntimeCounterfactualSnapshot` — `runtime_counterfactual_snapshot.inc:7` | `std::string` | 为空时 facade 默认 `"worldline:runtime:<world_index>:<entity_id>"`（`runtime_facade_counterfactual.cpp:460-461`）；experiment 路径默认 `"worldline:baseline"`/`"worldline:branch"`（`:645`、`:656`）；否则调用方手写 | `test_runtime_facade_counterfactual.py` | 为空时 facade 生成；无跨 run 方案 | VA-1 |
| `parent_worldline_id` | `RuntimeCounterfactualSnapshot` — `runtime_counterfactual_snapshot.inc:8` | `std::string` | 为空时默认 `= worldline_id`（`runtime_facade_counterfactual.cpp:463`） | `test_runtime_facade_counterfactual.py` | 默认单层谱系 | VA-1 |
| `fidelity_profile_id` | `RuntimeCounterfactualSnapshot` — `runtime_counterfactual_snapshot.inc:23` | `std::string` | `= fidelity_admission.backend_profile_id`（`runtime_facade_counterfactual.cpp:95`）——注意它由 admission 的 **backend** profile id 填充 | `test_runtime_facade_counterfactual.py` | 快照上的 fidelity/backend profile 标签 | VA-1 |
| `selected_stage_node_id` | `RuntimeCounterfactualSnapshot` — `runtime_counterfactual_snapshot.inc:25` | `std::string` | `= fidelity_admission.selected_stage_node_id`（`runtime_facade_counterfactual.cpp:97`）；非空时被复用为 restore-boundary 的 event-order `producer_node_id`（`:390-392`） | `test_runtime_facade_counterfactual.py` | fidelity admission 选定的 stage 节点标签 | VA-1 |
| `comparison_id` | `RuntimeWorldlineComparison` — `runtime_worldline_comparison.inc:8` | `std::string` | `"counterfactual:selected_slice"` 或加 `":<branch_point_id>"` 后缀（`runtime_facade_counterfactual.cpp:334-336`） | `test_runtime_facade_counterfactual.py` | 每次 branch 调用生成 | VA-1 |
| `parent_worldline_id` | `RuntimeWorldlineComparison` — `runtime_worldline_comparison.inc:9` | `std::string` | `= parent.worldline_id`（`runtime_facade_counterfactual.cpp:337`） | — | snapshot id 的复制 | copy/ref |
| `branch_worldline_id` | `RuntimeWorldlineComparison` — `runtime_worldline_comparison.inc:10` | `std::string` | `= branch.worldline_id`（`runtime_facade_counterfactual.cpp:338`） | — | snapshot id 的复制 | copy/ref |
| `replay_envelope_id` | `ReplayEnvelope` — `counterfactual_replay_contract_types.h:38` | `std::string` | 可由调用方构造；experiment 信封透传 `branch_request.replay_envelope_id`（`runtime_facade_counterfactual.cpp:109`）；restore boundary 合成 `"replay:facade:<worldline_id>"`（`:365-367`） | `test_replay_envelope_contracts.py`（WP15） | 调用方手写或 facade 合成；非从真实 run 构造 | VA-1 |
| `run_id` | `ReplayEnvelope` — `counterfactual_replay_contract_types.h:39` | `std::string` | 可由调用方构造；experiment 信封：`request.experiment_run_id` 或默认 `"run:counterfactual_experiment"`（`runtime_facade_counterfactual.cpp:110-111`）；restore boundary：`snapshot.worldline_id` 或 `"run:facade"`（`:368`） | `test_replay_envelope_contracts.py` | run 身份字符串 | VA-1 |
| `episode_id` | `ReplayEnvelope` — `counterfactual_replay_contract_types.h:40` | `std::string` | 可由调用方构造；experiment 信封：`request.setup_ref` 或默认 `"episode:counterfactual_experiment"`（`runtime_facade_counterfactual.cpp:112-113`）；restore boundary：`snapshot.barrier_id` 或 `"episode:facade"`（`:369`） | `test_replay_envelope_contracts.py` | episode 身份字符串 | VA-1 |
| `event_id` | `ReplayEventOrderRef` — `counterfactual_replay_contract_types.h:25` | `std::string` | 可由调用方构造；experiment 信封设 `= branch_request.branch_point_id`（`runtime_facade_counterfactual.cpp:135`）；restore boundary 设 `"event:<worldline_id>"` 或 `"event:facade"`（`:388-389`） | `test_replay_envelope_contracts.py` | **此处 `event_id` 为 `std::string`，而 kernel 中为 `std::uint64_t`**；experiment 路径上它实际携带的是 branch-point id | VA-1 |
| `producer_node_id` | `ReplayEventOrderRef` — `counterfactual_replay_contract_types.h:26` | `std::string` | 可由调用方构造；experiment 信封设固定 `"observation_export.v1"`（`runtime_facade_counterfactual.cpp:136`）；restore boundary 设 `snapshot.selected_stage_node_id` 或同一默认（`:390-392`） | `test_replay_envelope_contracts.py` | 生产者节点标签 | VA-1 |
| `branch_point_id` | `BranchPoint` — `counterfactual_replay_contract_types.h:54` | `std::string` | 请求上由调用方提供（如 `"replay:wp17f:0001"`）；experiment branch-point 构造器复制 `request.branch_request.branch_point_id`（`runtime_facade_counterfactual.cpp:152`）；admission 从它派生自己的 `request_id`（`:246-248`） | `test_replay_envelope_contracts.py`（`make_branch_point_identity`） | 调用方手写；字符串相等身份 | VA-1, VA-5 |
| `replay_envelope_id` | `BranchPoint` — `counterfactual_replay_contract_types.h:55` | `std::string` | 可由调用方构造；experiment 构造器复制 `branch_request.replay_envelope_id`（`runtime_facade_counterfactual.cpp:153`） | `test_replay_envelope_contracts.py` | 交叉引用某 `ReplayEnvelope.replay_envelope_id`（字符串相等） | VA-1, VA-5 |
| `baseline_worldline_id` | `WorldlineBranchMetadata` — `counterfactual_replay_contract_types.h:65` | `std::string` | 仅可由调用方构造；`src/**` 中只有验证器、无 facade 生产者构造该 struct | `test_worldline_branch_metadata.py` | 仅元数据的 branch 记录 | VA-1 |
| `parent_worldline_id` | `WorldlineBranchMetadata` — `counterfactual_replay_contract_types.h:66` | `std::string` | 仅可由调用方构造（验证器，无 facade 生产者） | `test_worldline_branch_metadata.py` | 仅元数据的 branch 记录 | VA-1 |
| `child_worldline_id` | `WorldlineBranchMetadata` — `counterfactual_replay_contract_types.h:67` | `std::string` | 仅可由调用方构造（验证器，无 facade 生产者） | `test_worldline_branch_metadata.py` | 仅元数据的 branch 记录 | VA-1 |
| `request_id` | `CounterfactualExperimentRequest` — `counterfactual_replay_contract_types.h:87` | `std::string` | 仅可由调用方构造；facade experiment 路径接收 `RuntimeExperimentRequest` 并直接构造 admission（`runtime_facade_counterfactual.cpp:240-270`） | `test_counterfactual_admission.py` | experiment 请求身份 | VA-1 |
| `baseline_worldline_id` | `CounterfactualExperimentRequest` — `counterfactual_replay_contract_types.h:88` | `std::string` | 仅可由调用方构造（见上一行）；admission 的 baseline 来自 `branch_request.parent_worldline_id`（`runtime_facade_counterfactual.cpp:249`） | `test_counterfactual_admission.py` | experiment 基线身份 | VA-1 |
| `experiment_run_id` | `ExperimentEvidenceBridgeRecord` — `counterfactual_replay_contract_types.h:215` | `std::string` | 由 `make_experiment_evidence_bridge_record` 生产（`counterfactual_replay_experiment_validation.h:641`）；facade 传入 `request.experiment_run_id` 或默认 `"experiment_run:runtime_facade.counterfactual"`（`runtime_facade_counterfactual.cpp:857-858`）；也可由调用方构造 | `test_experiment_evidence_bridge.py` | bridge experiment-run 身份 | VA-1 |
| `comparison_id` | `ExperimentEvidenceBridgeRecord` — `counterfactual_replay_contract_types.h:216` | `std::string` | 于 `counterfactual_replay_experiment_validation.h:642` 生产；facade 传入 `request.comparison_id` 或 branch comparison 的 id（`runtime_facade_counterfactual.cpp:859-860`） | `test_experiment_evidence_bridge.py` | 交叉引用某 `RuntimeWorldlineComparison.comparison_id` | VA-1 |
| `replay_run_id` | `ExperimentEvidenceBridgeRecord` — `counterfactual_replay_contract_types.h:217` | `std::string` | `= replay_envelope.run_id`（`counterfactual_replay_experiment_validation.h:643`） | `test_experiment_evidence_bridge.py` | bridge replay-run 身份 | VA-1 |
| `baseline_worldline_id` | `ExperimentEvidenceBridgeRecord` — `counterfactual_replay_contract_types.h:218` | `std::string` | `= admission.baseline_worldline_id`（`counterfactual_replay_experiment_validation.h:644`），facade 从 `branch_request.parent_worldline_id` 填充（`runtime_facade_counterfactual.cpp:249`） | `test_experiment_evidence_bridge.py` | bridge 基线身份 | VA-1 |
| `variant_worldline_id` | `ExperimentEvidenceBridgeRecord` — `counterfactual_replay_contract_types.h:219` | `std::string` | `= admission.child_worldline_id`（`counterfactual_replay_experiment_validation.h:645`），从 `branch_request.branch_worldline_id` 填充（`runtime_facade_counterfactual.cpp:250`） | `test_experiment_evidence_bridge.py` | bridge 变体身份 | VA-1 |
| `request_id` | `ScenarioGenerationRequestMetadata` — `counterfactual_replay_contract_types.h:183` | `std::string` | facade experiment 路径生产：`generated_input_ref`/`generation_ref` 或默认 `"scenario-gen:runtime_facade.counterfactual"`（`runtime_facade_counterfactual.cpp:187-191`）；也可由调用方构造（平行 Python 面 `python/scenario/compiler/generation_request.py`） | `python/scenario/compiler/generation_request.py` | 生成请求身份 | VA-1, VA-6 |

### 1.3 无类型 ancestry 引用（`*_ref`）

`RuntimeExperimentAncestry`
（`src/runtime/facade/detail/runtime_experiment_ancestry.inc`）把全部谱系作为自由
`std::string` ref 携带，与其所指的 `_id` 无类型化链接（匹配靠字符串相等）。它们是序列化
形式，在此列出以便后续切片叠加式新增一份"ref → id-kind"注册表（VA-5）。

| 字段 | `file:line` | 类型 | 所指 id-kind | VA |
|------|-------------|------|--------------|----|
| `counterfactual_request_ref` | `runtime_experiment_ancestry.inc:11` | `std::string` | `CounterfactualExperimentRequest.request_id` | VA-5 |
| `counterfactual_admission_ref` | `runtime_experiment_ancestry.inc:12` | `std::string` | `CounterfactualAdmissionResult.request_id` | VA-5 |
| `setup_ref` | `runtime_experiment_ancestry.inc:13` | `std::string` | setup 身份 | VA-5 |
| `generation_ref` | `runtime_experiment_ancestry.inc:14` | `std::string` | generation 身份 | VA-5 |
| `replay_envelope_ref` | `runtime_experiment_ancestry.inc:15` | `std::string` | `ReplayEnvelope.replay_envelope_id` | VA-5 |
| `branch_point_ref` | `runtime_experiment_ancestry.inc:16` | `std::string` | `BranchPoint.branch_point_id` | VA-5 |
| `generated_input_ref` | `runtime_experiment_ancestry.inc:17` | `std::string` | generated-input 身份 | VA-5 |
| `backend_profile_ref` | `runtime_experiment_ancestry.inc:18` | `std::string` | backend-profile 身份 | VA-5 |
| `fidelity_profile_ref` | `runtime_experiment_ancestry.inc:19` | `std::string` | fidelity-profile 身份 | VA-5 |

## 2. 版本概念

两个不同概念都用 `version` 后缀（VA-3）：**状态切片版本**（packet/trace 对应哪一切片的已产
出状态）与**格式/schema 版本**（payload 遵循哪个契约/格式）。二者不得混用。

### 2.1 状态切片版本字段（VA-2）

生产者说明：`next_snapshot_version(index)` 作为纯函数返回 `index + 1`
（`runtime_facade_packet.cpp:574`、`runtime_facade_execution.cpp:27`）。它用于 observation/
tasking packet 顶层版本（`= next_snapshot_version(refs.size() - 1) = refs.size()`；
`runtime_facade_packet.cpp:865`、`:896`）与逐 step 版本
（`= next_snapshot_version(step_index)`；`runtime_facade_execution.cpp:164`）。逐
`TrackPacket` 版本来自一个**独立的局部计数器**，在单次导出内从 `1` 起、按 ref 递增
（`runtime_facade_packet.cpp:728-732`、`:817-821`）。**当前不存在 run 全局单调 snapshot
计数。**

| 字段 | DTO — `file:line` | 类型 | 生产者 / 取值 | 唯一性 / 单调性 | VA |
|------|-------------------|------|---------------|-----------------|----|
| `snapshot_version` | `TrackPacket` — `track_packet.inc:19` | `std::uint64_t` | 从 `1` 起的逐 ref 局部计数（`runtime_facade_packet.cpp:732`、`:821`）；声明默认 `0` | batch-局部；每次导出重置为 `1`；非单调 | VA-2 |
| `snapshot_version` | `ObservationBatchPacket` — `observation_batch_packet.inc:7` | `std::uint64_t` | `= refs.size()`（`runtime_facade_packet.cpp:865`）；声明默认 `0` | 等于批次 ref 数；非单调 | VA-2 |
| `snapshot_version` | `EngagementEventPacket` — `engagement_event_packet.inc:6` | `std::uint64_t` | `resolve_engagement_snapshot_version` = track/trace 版本之 max，否则 `refs.size()`（`runtime_facade_packet.cpp:641-654`；经 `apply_export_packet_metadata` `:196` 应用，调用点 `:808-809`、`:840-841`） | 每次导出派生；非单调 | VA-2 |
| `snapshot_version` | `RuntimeCounterfactualSnapshot` — `runtime_counterfactual_snapshot.inc:21` | `std::uint64_t` | 固定常量 `kRuntimeCounterfactualSelectedSliceSnapshotVersion = 1`（`runtime_facade_internal.h:89`；应用于 `runtime_facade_counterfactual.cpp:93`）；声明默认 `0` | 生产路径上恒 `1` | VA-2 |
| `snapshot_version` | `TerminationSpec` — `termination_spec.inc:8` | `std::uint64_t` | `termination_spec_from_step_result` 设置（`runtime_facade_execution.cpp:104`），值取逐 step 的 `next_snapshot_version(step_index)`（`:164`，使用于 `:176`） | 逐 step 切片标记；随 step 索引重置 | VA-2 |
| `observation_packet_version` | `DiagnosticsTrace` — `diagnostics_trace.inc:15` | `std::uint64_t` | 作为逐 ref 快照版本传入导出 trace 字面量（`runtime_facade_packet.cpp:372`） | batch-局部 | VA-2 |
| `source_snapshot_version` | `DiagnosticsTrace` — `diagnostics_trace.inc:16` | `std::uint64_t` | observation export 上 `= track.snapshot_version`（`runtime_facade_packet.cpp:373`）；recent/kernel trace 由 `apply_export_trace_metadata` 重新盖章（`:221`） | batch-局部 | VA-2 |
| `source_snapshot_version` | `RuntimeWindowNodeExecutionRecord` — `runtime_window_node_execution_record.inc:17` | `std::string` | window coordinator 复制 action request 的 `clock_domain_metadata.source_snapshot_version`，回退到其 `input_snapshot_version`（`runtime_window_coordinator_helpers.h:87-93`；应用如 `runtime_window_coordinator_execution_helpers.h:77-78`）；export 记录经 `runtime_window_export_snapshot_evidence`（`runtime_window_coordinator.h:345`） | **类型分裂：此处 `std::string`，而 `DiagnosticsTrace` 中为 `std::uint64_t`** | VA-2 |
| `fact_snapshot_version` | `RewardReport` — `reward_report.inc:8` | `std::uint64_t` | `reward_report_from_step_result` 设置（`runtime_facade_execution.cpp:46`），值取逐 step 版本（`:164`，使用于 `:180`） | 逐 step reward 切片标记 | VA-2 |
| `snapshot_version_ref` | `ReplaySnapshotRef` — `counterfactual_replay_contract_types.h:14` | `std::string` | 可由调用方构造；experiment 信封：`request.setup_ref` 或 `"snapshot:counterfactual_experiment"`（`runtime_facade_counterfactual.cpp:120-122`）；restore boundary：`"snapshot:" + std::to_string(snapshot.snapshot_version)`（`:376`）——嵌入固定的 `uint64` 值 `1` | 字符串 ref；类型上未绑定任何产出的 `uint64` 版本 | VA-2, VA-5 |
| `snapshot_version_ref` | `BranchPoint` — `counterfactual_replay_contract_types.h:56` | `std::string` | 可由调用方构造；experiment branch-point 构造器复制信封的 ref（`runtime_facade_counterfactual.cpp:154`） | 字符串 ref；类型上未绑定任何产出的 `uint64` 版本 | VA-2, VA-5 |
| `input_snapshot_version` | `RuntimeWindowActionRequest` — `runtime_facade_types.h:192`（Python 参数 `python/rl/runtime/world_batch/adapter.py:322`、`:400`） | `std::string` / `str` | adapter 默认 `"obs:{world}:{entity}"`（`adapter.py:448`）；流入 `source_observation_versions = [str(...)]`（`:361`）并经 `runtime_window_input_source_snapshot_version` 进入 window 记录（`runtime_window_coordinator_helpers.h:87-93`） | 合成字符串；非产出版本 | VA-2 |

### 2.2 格式 / schema 版本字段（VA-3）

| 字段 | DTO / 所有者 — `file:line` | 类型 | 取值 | VA |
|------|----------------------------|------|------|----|
| `schema_version` | `ObservationViewSpec` — `observation_view_spec.inc:7` | `std::string` | `"1.0"`；由 `parse_observation_schema_version` 按 `major.minor` 解析（`runtime_dto_contracts.h:40`） | VA-3 |
| `schema_version` | `LethalityChainHeader` — `lethality_chain_header.inc:6` | `std::uint32_t` | 默认 `kLethalityChainContractSchemaVersion` = `1`（常量位于 `engagement_contracts.h:10`） | VA-3 |
| `schema_version` | `KillChainRuntimeFacade` — `kill_chain_runtime_facade.inc:7` | `std::uint32_t` | 默认 `1` | VA-3 |
| `vulnerability_evidence_schema_version` | `EffectsEvent` — `effects_event_fields.inc:127`；`EffectsResult` 上的同名字段 — `effects_model.h:77` | `std::string` | 从采样的 `VulnerabilityAdjustment.evidence_schema_version` 复制（`default_effects_result_detail.inc:195-196`） | VA-3 |
| `evidence_schema_version` | `AircraftVulnerabilityProfile` — `damage_air.h:72`；`VulnerabilityAdjustment` — `default_effects_warhead_detail.inc:104` | `std::string` | loader 从内容 descriptor 的 `schema_version` 填充 profile（`unit_definition_loader.cpp:754`）；复制链 profile → adjustment（`default_effects_warhead_detail.inc:1063`）→ result（`default_effects_result_detail.inc:195-196`） | VA-3 |
| `request_version` | `ScenarioGenerationRequestMetadata` — `counterfactual_replay_contract_types.h:184` | `std::string` | `"1"`（声明值；facade experiment 路径亦写 `"1"`，`runtime_facade_counterfactual.cpp:192`） | VA-3 |
| `contract_version` | `ScenarioGenerationRequestMetadata` — `counterfactual_replay_contract_types.h:185` | `std::string` | `kScenarioGenerationContractVersionRequestV1`（声明值；facade 重新盖章，`runtime_facade_counterfactual.cpp:193`） | VA-3 |
| `envelope_schema_version` | 报告信封 — `python/experiment/report_envelope.py:45`（`ENVELOPE_SCHEMA_VERSION`），发出于 `:113` | `str` | `"1"` | VA-3 |

### 2.3 概念 → 表示 映射（VA-2、VA-3）

| 概念 | 表示（名 @ 型） | 当前单调？ | 备注 |
|------|-----------------|------------|------|
| 状态切片版本（哪一产出切片） | `snapshot_version` @ `uint64`；`observation_packet_version` @ `uint64`；`source_snapshot_version` @ `uint64`（`DiagnosticsTrace`）/ `std::string`（`RuntimeWindowNodeExecutionRecord`）；`fact_snapshot_version` @ `uint64`；`snapshot_version_ref` @ `string`；`input_snapshot_version` @ `string` | 否 | ≥5 名、2 型；按导出/batch-局部或固定 `1`；无 run 全局单调计数 |
| 格式 / schema 版本（哪个契约/格式） | `schema_version` @ `string` `"1.0"`（`ObservationViewSpec`）/ `uint32`（`LethalityChainHeader`、`KillChainRuntimeFacade`）；`evidence_schema_version`/`vulnerability_evidence_schema_version` @ `string`；`request_version`/`contract_version` @ `string`；`envelope_schema_version` @ `str` | 不适用 | 离散契约标签；`*_schema_version`/`*_contract_version` 表格式，`*_snapshot_version`/`*_packet_version` 表状态切片 |

## 3. id 空间并存与冲突风险（VA-1、VA-3）

- **两种不相交表示，无类型化桥接字段。** "用于重放/诊断的身份"在 trace/engagement/packet
  面为 `std::uint64_t`（第 1.1 节），在 worldline/replay/experiment 面为 `std::string`
  （第 1.2 节）。没有类型化字段在两者间转换；跨越是多处把数字文本化嵌入字符串，例如：
  worldline-id 默认值嵌入 `world_index`/`entity_id`
  （`runtime_facade_counterfactual.cpp:460-461`）、restore-boundary 的
  `snapshot_version_ref` 嵌入 `snapshot_version`（`:376`）、adapter 的
  `input_snapshot_version` 默认值嵌入 `world_index`/`entity_id`
  （`python/rl/runtime/world_batch/adapter.py:448`）、packet-provenance 的
  `observation_packet_ids`/`source_observation_versions` 字符串嵌入数值
  `snapshot_version`（`runtime_facade_packet.cpp:204-211` engagement、`:317-320`
  observation、`:331-334` tasking）。SCAL 命名
  了一个 `source_id`（"用于重放与诊断的稳定生产者 id"），但没有单一类型实现它。后续切片可
  叠加式声明一个桥接 ref 字段或 id-kind 注册表（VA-1、VA-5）；本词汇表只记录该分裂。
- **同名不同型。** `event_id` 在 kernel 中为 `std::uint64_t`
  （`LaunchEvent`/`EffectsEvent`，被 `DiagnosticsTrace.launch_event_id`/`effects_event_id`
  引用），但在 `ReplayEventOrderRef` 中为 `std::string`
  （`counterfactual_replay_contract_types.h:25`）——且 experiment 路径实际存入的是
  branch-point id（`runtime_facade_counterfactual.cpp:135`）。`source_snapshot_version` 在
  `DiagnosticsTrace` 中为 `std::uint64_t`，在 `RuntimeWindowNodeExecutionRecord` 中为
  `std::string`。因此跨面按这些名字连接并不类型安全。
- **kernel event-store id 共享一个可重置分配器。** 在 store 铸造集合内（第 1.1 节：
  store 记录的全部 kernel 事件族的事件 id——launch、nearest-approach、fuze-evaluation、
  warhead-mechanism、spatial-coverage、component-load/damage、structural-breakup、
  platform-consequence、lifecycle-transition、effects/damage——与 store 铸造的
  trace id），全部取值
  来自 `next_engagement_event_id_`，它在 `clear()` / 时钟回退时重置为 `1`。两次 run（或
  一次 run 回退之后）可能铸造出相同的值，故这些 id 跨重置不稳定、不得当作全局唯一。对
  调用方标签 id 冲突风险更直接：维护 adapter 给每个 observation-export trace 打 `[1]`。
- **string id 由 facade 生成或调用方手写。** worldline/comparison id 与 restore-boundary
  ref 在单次裸 facade 调用内由 facade 生成（第 1.2 节）；experiment 路径的信封大多透传
  调用方字段并配固定回退（`run:counterfactual_experiment`、
  `episode:counterfactual_experiment`）；`branch_point_id`、请求的 `replay_envelope_id`
  及 branch-metadata 的 worldline id 仍为调用方手写字符串。无跨 run 稳定 id 方案，故
  string 空间唯一性仅在每次调用/每个作者范围内成立。

## 4. barrier-id 词汇（VA-7）

`barrier_id` 一律为 `std::string`，但其默认值因 DTO 而异；普查把 `"window_commit"` 归于
`barrier_id`，但在基线 `1d25c4d1` 上它是 `ReplayBarrierRef` 的 **`barrier_detail`** 默认——
那里的 `barrier_id` 无默认（见第 5 节普查差异）。导出面上声明默认与生产路径写入一致
（常量 `kExportBarrierId`/`kExportBarrierDetail` 重复声明默认，
`runtime_facade_internal.h:53-54`）。

| 字段 | DTO — `file:line` | 声明默认 | 生产路径写入 |
|------|-------------------|----------|--------------|
| `barrier_id` | `DiagnosticsTrace` — `diagnostics_trace.inc:17` | `"export"` | `kExportBarrierId` = `"export"`（`runtime_facade_packet.cpp:222`、`:374`） |
| `barrier_id` | `ObservationBatchPacket` — `observation_batch_packet.inc:8` | `"export"` | `"export"`（`runtime_facade_packet.cpp:852`） |
| `barrier_id` | `EngagementEventPacket` — `engagement_event_packet.inc:7` | `"export"` | `kExportBarrierId`（`runtime_facade_packet.cpp:197`、`:779`） |
| `barrier_id` | `RuntimeCounterfactualSnapshot` — `runtime_counterfactual_snapshot.inc:22` | `"counterfactual_selected_slice"` | `kRuntimeCounterfactualSelectedSliceBarrierId`（`runtime_facade_internal.h:87-88`；应用于 `runtime_facade_counterfactual.cpp:94`） |
| `barrier_id` | `RuntimeWorldlineComparison` — `runtime_worldline_comparison.inc:11` | `"counterfactual_selected_slice"` | 同一常量（`runtime_facade_counterfactual.cpp:339`） |
| `barrier_id` | `ReplayBarrierRef` — `counterfactual_replay_contract_types.h:18` | 无（空） | experiment：`branch_request.restore_barrier_id`（`runtime_facade_counterfactual.cpp:126`）；restore boundary：`snapshot.barrier_id`（`:380`） |
| `barrier_detail` | `ReplayBarrierRef` — `counterfactual_replay_contract_types.h:20` | `"window_commit"` | experiment：`cadence_reason` 或 `"maintained_facade_export"`（`runtime_facade_counterfactual.cpp:128-130`）；restore boundary 类似（`:382-383`） |
| `barrier_detail` | `DiagnosticsTrace` / `EngagementEventPacket` — `diagnostics_trace.inc:18` / `engagement_event_packet.inc:9` | `"maintained_facade_export"` | `kExportBarrierDetail`（`runtime_facade_packet.cpp:223` / `:199`、`:781`） |

## 5. 普查差异（供协调者裁定）

普查（`t10_evidence_spine_census_20260721.md`）作为不可变历史记录保留；本词汇表不编辑它。
重新核实时发现两处微小不精确，在此记录供协调者裁定：

1. **`RuntimeExperimentAncestry` 字段名。** 普查 §1(ii) 把 evidence-bridge 字段写作
   `evidence_bridge_valid`/`fail_closed`/`rejection_reason`/`errors`。实际字段名带
   `evidence_bridge_` 前缀：`evidence_bridge_valid`（`runtime_experiment_ancestry.inc:7`）、
   `evidence_bridge_fail_closed`（`:8`）、`evidence_bridge_rejection_reason`（`:9`）、
   `evidence_bridge_errors`（`:10`）。
2. **`ReplayBarrierRef` 的 `"window_commit"`。** 普查 §2 VA-7 把 `"window_commit"` 默认归于
   `barrier_id`。在 `1d25c4d1` 上 `ReplayBarrierRef.barrier_id` 无默认；`"window_commit"` 是
   `barrier_detail` 的默认（`counterfactual_replay_contract_types.h:20`）。

两者均不影响普查结论；本词汇表已正确记录（第 1.2、4 节）。

## 6. 非目标

- **零代码变更；零字段变更。** 本切片仅文档。它不新增字段、不改名、不改型、不触及任何
  `src/**`、`python/**`、`examples/**` 或既有测试。
- **可选 schema 元数据子任务已放弃。** 普查切片允许一个可选的仅文档 schema 注解。经评估后
  基于范围裁定放弃：当前 `Field` 模型
  （`tools/maintenance/dto_schema/model.py:19-31`，`frozen=True, slots=True` dataclass）
  没有语义上适合承载证据词汇的既有通道——自由文本 `comment` 会被渲染进生成的 `.inc` 产物
  （`tools/maintenance/dto_schema/generate.py:58-63`），从而改变签入产物；保留键属于
  binding/序列化元数据（`readonly` 会改变生成的 Python builder，
  `python_builder.py:100-102`；`python_name`/`hidden`/`json_key` 携带 binding/codec 语义）。
  新增一个专用注解属性（例如 `evidence_role`）本身可以做到不影响生成输出，但它需要修改
  model/生成器代码（固定的 dataclass 属性集会对未知关键字抛 `TypeError`），属于生成器
  代码变更、超出本切片"零代码变更"红线。故该子任务仅以文档交付；后续切片可连同其
  freshness 门证据一起新增该属性。
- **additive-only 红线**（照抄普查 §3，未改）：
  - 任何现有证据字段不得改名、改型、删除或重排。成员顺序是 ABI；JSON codec 别名与保留产物
    哈希钉扎序列化形状；普查第 1 节的测试钉扎该面。
  - 新证据以新字段 / 新 DTO / 新生产者到来，配重生成 freshness 门
    （`tools/maintenance/dto_schema/generate.py --check`）；行为可能漂移处配内嵌参照 parity；
    兼容壳保留至 T7 最终残余审计有意退役。
  - 词汇对齐以文档加新叠加字段交付，绝不对被钉扎面做原地编辑。

## 7. 覆盖总数

- `uint64` 身份字段：13（第 1.1 节）。
- `string` 身份字段：27（第 1.2 节）。
- 无类型 ancestry ref：9（第 1.3 节）。
- 状态切片版本字段：12（第 2.1 节）。
- 格式/schema 版本字段：8（第 2.2 节）。
- **文档化 id/ref/版本字段总数：69。**

## 相关权威

- [统一架构计划](README.zh.md)（T10 轨道定义与风险）
- [T10 证据脊柱普查（2026-07-21）](t10_evidence_spine_census_20260721.zh.md)（切片 1；VA-1..VA-8 与叠加红线）
- [Simulation System Architecture Design](../../../architecture/standards/simulation_system_architecture_design.zh.md)（SCAL Evidence Graph 面）
- [SCAL 一致性普查（2026-07-20）](scal_conformance_census_20260720.zh.md)（普查格式先例）
- [T6 残差台账（2026-07-20）](t6_residual_ledger.zh.md)
- [仓库整合计划](../repository_consolidation_completed_20260729/README.zh.md)（迭代台账与协议）
