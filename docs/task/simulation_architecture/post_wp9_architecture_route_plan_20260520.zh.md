# Post-WP9 Architecture Route Plan

状态：`2026-05-21` 路线选择规划；Phase 1 已作为 `WP10` 验收，Phase 2 已作为
`WP11` 验收，Phase 3 已作为 `WP12` 验收，Phase 4 已作为 `WP13` 验收，
Phase 5 已开启为 planned / dispatch-ready `WP14`。

语言版本：

- 英文主文：[post_wp9_architecture_route_plan_20260520.md](post_wp9_architecture_route_plan_20260520.md)
- 中文辅文：`post_wp9_architecture_route_plan_20260520.zh.md`

输入：

- [仿真系统架构设计](../../plan/architecture/simulation_system_architecture_design.zh.md)
- [仿真架构任务索引](README.zh.md)
- [剩余工作整合与后续路线图](../review/consolidated_remaining_work_and_roadmap_20260520.zh.md)
- [Post-WP9 gap analysis](../review/post_wp9_gap_analysis_20260520.zh.md)
- [WP9 contract and infrastructure closure](wp9_contract_infrastructure_closure/contract_infrastructure_closure_wp9_20260520.zh.md)
- [WP14 capability composition](wp14_capability_composition/capability_composition_wp14_20260521.zh.md)
- [WP closure lane policy](../../standards/governance/wp_closure_lane_policy.zh.md)

## 1. 目的

WP0-WP9 已经闭合架构基线、contract vocabulary、facade guardrails、
backend-profile policy、learning-face vocabulary，以及延后的 DTO/infrastructure
项目。下一阶段不应再形成一个 documentation-only wave，而应选择一条实现路线，
把已验收架构规则变成 runtime facts。

本文固定路线顺序，把 Phase 1 锚定为 `WP10`，Phase 2 锚定为 `WP11`，把
Phase 3 锚定为 `WP12`，将 Phase 4 验收为 `WP13`，并把 Phase 5 开启为
planned / dispatch-ready `WP14`。它不会给当前已开启阶段之后的方向预先分配
WP 编号；它定义哪个方向必须先做、哪些方向应等待，以及什么证据才算真正的架构推进。

## 2. 路线决策

post-WP9 路线是：

```text
causal runtime foundation
  -> facade vertical slice
  -> information and agency enforcement
  -> backend/fidelity expansion
  -> capability composition
  -> counterfactual and experiment generation
```

该顺序有明确原因：

1. runtime causality 必须先变成可机器检查的事实，否则 backend、fidelity、
   counterfactual 或 experiment-generation 工作都不可信。
2. 窄的 facade-visible vertical slice 应先证明地基，而不是一次性重写全部 scheduler。
3. information 与 agency 规则必须先变成可执行边界，否则 backend/fidelity 对比不能被信任为 maintained decision evidence。
4. backend 与 fidelity 工作必须留在 profile/capability contracts 后面，不能变成第二条语义路径。
5. capability composition 是语义升级，应在 runtime 能暴露稳定 state/event/evidence
   边界后再推进。
6. counterfactual 与 experiment generation 需要 deterministic replay、snapshot/restore
   和 evidence ancestry，因此应成为较后的消费者。

## 3. 有序架构轨道

| 顺序 | 轨道 | 第一个具体产物 | 依赖 | 应等待 |
|------|------|----------------|------|--------|
| 1 | Causal runtime foundation | 机器可读 `StageNodeManifest` registry，以及最小 scheduling-window loop：收集 facade requests、注入 graph inputs、运行 manifest 派生的无环窗口、通过 barriers commit、导出有序 evidence。 | WP2.5、WP5、WP9、GAP-2/GAP-3 | 完整 multi-rate scheduler |
| 2 | Facade vertical slice | 一条维护中链路，优先 engagement/observation，证明 `manifest -> event order -> diagnostics trace -> facade export -> tests`，同时补后续 policy cadence 需要的 `ActionHoldPolicy` 与 information-state provenance labels。 | track 1 seed、GAP-1/GAP-4 | 大范围 scheduler rewrite |
| 3 | Information and agency enforcement | Law 14 read-side guards、`AgentRole` authority validation、information-transformation evidence 与 authorized intent injection 变成有测试支撑的边界。 | WP10、WP11、GAP-5/GAP-6/GAP-7 | 完整 Agency Graph runtime |
| 4 | Backend/fidelity expansion | `RuntimeCapabilities` 与 model-provider/fidelity profiles 变成可查询、可拒绝、可测试。 | WP6、WP7、tracks 1-3 | maintained causal/evidence boundary |
| 5 | Capability composition | 通过 resolved spawn plans 与 additive setup DTOs，让 type-name spawning 走向 typed `Capability` / `CapabilityBundle` composition，同时不破坏兼容。 | WP2、WP9、tracks 1-4、`Capability` / `CapabilityBundle` DTOs | 稳定 setup/content contract |
| 6 | Counterfactual and experiment generation | 可分支 worldline、deterministic replay envelope、scenario/adversary generation 与 capability profiling evidence。 | WP8、tracks 1-5 | snapshot/restore 与 replay proof |

### 3.1 Post-WP9 阶段粗分

路线被划分为不超过六个实现阶段。Phase 1-5 现已分配给 `WP10` 到 `WP14`。
Phase 6 仍只是顺序锚点，在前置 gate 达到 mergeable 之前不创建已开启任务文件夹。

| Phase | 工作标签 | 范围 | 候选 WP 归属 | 开启条件 | 暂不声明 |
|-------|----------|------|--------------|----------|----------|
| 1 | Causal runtime foundation | 为 engagement/observation slice 物化第一组 code-owned `StageNodeManifest` registry、最小 scheduling-window loop、cross-layer request injection、same-window edge validation 与 event/snapshot evidence。 | `WP10` | WP9 closure 与 post-WP9 route 已验收。 | 完整 multi-rate scheduling、严格 clock-domain enforcement、Law 14 read-side enforcement。 |
| 2 | Facade vertical slice and provenance | 添加 `ActionHoldPolicy`、information-state provenance labels，并在 Phase 1 runtime seam 上证明一条 facade/binding-visible chain。 | `WP11` | Phase 1 registry、barriers 与 event/snapshot evidence 已验收。 | broad facade rewrite，以及超出 demonstrated slice 的 policy/control/physics cadence support。 |
| 3 | Information and agency enforcement | 把延期的 `GAP-5`、`GAP-6` 与 `GAP-7` 转成可执行的 read-side、role/authority 与 transformation-surfacing gates。 | `WP12` | provenance labels、consumer pre-gates 与 facade slice 稳定。 | 完整 Agency Graph runtime 或 backend/fidelity promotion。 |
| 4 | Backend/fidelity expansion | 在 causal boundary 后，让 `RuntimeCapabilities`、model-provider profiles、fidelity profiles 与 parity budgets 变成可查询、可拒绝、可证据化。 | `WP13` | Phase 1-3 的 evidence boundary 足够稳定，可用于比较 backend。 | 无 gate 晋升 exact GPU、resident-state、shadow 或 multi-fidelity。 |
| 5 | Capability composition | 在保持 type-name compatibility 的同时，把有边界 setup/content path 推向 typed `Capability` / `CapabilityBundle` composition。 | `WP14` | runtime/facade/backend contracts 能命名稳定 capability effects 与 evidence。 | big-bang spawn rewrite、强制 public `spawn_platform` 或 scenario-schema replacement。 |
| 6 | Counterfactual and experiment generation | 添加 branchable worldlines、deterministic replay envelopes、scenario/adversary generation 与 experiment evidence ancestry。 | 后续 WP | snapshot/restore、replay、capability evidence 与 facade provenance 稳定。 | 在 deterministic replay 与 snapshot boundaries 存在前进行 worldline branching。 |

## 4. Gap Analysis Incorporation

post-WP9 gap analysis 认可五轨顺序，但收紧 Track 1 与 Track 2。以下项目现在属于路线定义，
不是可选装饰：

| Gap | 路线决策 |
|-----|----------|
| `GAP-1 ActionHoldPolicy` | 加入 Track 2，作为声明 policy/control/physics cadence 前的必需 DTO。第一个 engagement/observation slice 可以先暴露 DTO，而不证明完整 cadence。 |
| `GAP-2 Scheduling window loop` | 加入 Track 1，作为连接 `StateStore`、`EventQueue`、`Barrier` 与 `StageNodeManifest` 的最小 loop skeleton。 |
| `GAP-3 Cross-layer request injection` | 加入 Track 1，在声明的 window boundary 定义 input-injection semantics。Track 2 可展示 facade-visible effects。 |
| `GAP-4 Information-state provenance labels` | 加入 Track 2，落在 observation/facade packets 上，为后续 Law 14 enforcement 提供稳定词汇。 |
| `GAP-8 Same-window edge derivation` | 加入 Track 1，作为 schedule-construction validation，而不是每 tick runtime discovery。 |
| `GAP-9 Clock-domain enforcement` | 严格 enforcement 延后到 window-loop skeleton 可工作之后；第一个 Track 1 slice 中 manifest 的 advisory clock-domain declaration 可接受。 |

Phase 3 gates 已作为 `WP12` 验收：

- `GAP-5` Architecture Law 14 read-side enforcement 现在以 WP11 provenance
  labels 与 consumer pre-gates 作为起始边界。
- `GAP-6` Agency Graph runtime enforcement 从 role/authority boundary
  validation 开始，而不是完整 Agency Graph dispatch。
- `GAP-7` 五条 information-state transformation rules 现在为 selected slice
  转成可机器检查的 vocabulary/evidence。

### 4.1 缺口驱动的工作内容

gap analysis 应按以下顺序转成实现 backlog。这些项目属于第一个实现型 WP 及其
直接 follow-on 的工作内容，不是新的 documentation-only 阶段。

| ID | 轨道 | 工作内容 | 必需证据 | 明确非范围 |
|----|------|----------|----------|------------|
| `POST9-T1-A Manifest Registry Seed` | Track 1 | 为选定的 engagement/observation slice 物化 code-owned `StageNodeManifest` registry。必需字段包括稳定 `node_id`、semantic stage、read/write state shards、advisory clock domain、latency/sync/read-snapshot/write-commit policy，以及 declared same-window publish intent。 | architecture test 能枚举 registry，并拒绝 maintained nodes 缺少必需字段。 | 暂不完整盘点每个 runtime system。 |
| `POST9-T1-B Scheduling Window Loop Skeleton` | Track 1 | 添加连接 primitives 的最小 loop：collect facade requests、跨过 `input_injection` barrier、运行 manifest-derived acyclic window、跨过 `window_commit`，并暴露 `export` barrier。 | runtime 或 architecture test 证明 barrier sequence，并为该 slice 记录稳定 window id / barrier id。 | 不实现完整 multi-rate scheduler，也不替换全局 scheduler。 |
| `POST9-T1-C Cross-Layer Request Injection` | Track 1 | 用 `source_layer`、`source_id`、`input_snapshot_version`、`effective_time`、`valid_until` 与 `merge_policy` 排队 facade-compatible graph inputs，并让 accepted requests 只在声明的 injection barrier 后可见。 | 测试覆盖该 slice 上的 accepted、future-window 与 expired requests。 | `ActionHoldPolicy` 存在前，不声明广义 policy/control/physics cadence。 |
| `POST9-T1-D Same-Window Edge Validation` | Track 1 | 在 schedule construction 阶段验证 same-window edges：consumer read set 必须与 producer write set 相交，且 producer 必须声明向该 consumer/stage family 发布 same-window output。 | 对选定 slice 提供 passing fixture，并为 undeclared 或 data-disjoint edge 提供 failing fixture。 | 不做 per-tick edge discovery，也不允许 wildcard same-window visibility。 |
| `POST9-T1-E Event And Snapshot Evidence` | Track 1 | 把 ordered events、snapshot version、barrier id、source time 与 diagnostics ancestry 绑定到 facade-visible engagement/observation export path。 | facade/binding-visible test 证明 deterministic event ordering 与 exported metadata presence。 | 不声明 counterfactual branching 或 snapshot/restore。 |
| `POST9-T2-A ActionHoldPolicy Contract` | Track 2 | 添加 typed `ActionHoldPolicy` contract，包含 hold-last、interpolate、expiry、drop semantics，以及 validity duration 和 refresh cadence 字段。 | DTO shape、serialization/binding surface 与 guard tests 证明 contract 存在，但不声明 runtime cadence support。 | Track 1 证明 loop 且后续 cadence slice 消费该 DTO 前，不声明 maintained policy/control/physics multi-rate runtime。 |
| `POST9-T2-B Information Provenance Labels` | Track 2 | 给 `ObservationPacket` 与 `DecisionBelief` export metadata 添加稳定 information-state provenance labels，使 maintained packets 声明数据来自 World Truth、Sensed State、Track State、Shared Tactical Picture、Agent Observation 或 Decision Belief。 | 测试拒绝 unlabeled maintained facade exports，并证明 labels 能保留到 Python/binding-facing packets。 | 暂不做 Law 14 read-side enforcement。 |
| `POST9-T2-C Facade Vertical Slice Proof` | Track 2 | 证明一条 maintained chain：从 manifest registry 到 event order、diagnostics trace、facade export，再到 Python binding smoke。 | end-to-end test 在 runtime 与 facade 层引用同一组 node ids / barrier ids / event ancestry。 | 不做 broad facade rewrite。 |

派发规则：`POST9-T1-A` 到 `POST9-T1-E` 应成为第一个实现型 WP 的主线。
`POST9-T2-A` 与 `POST9-T2-B` 只有在 Track 1 seam 已命名后才适合并行推进；
`POST9-T2-C` 应等待 Track 1 skeleton 与 Track 2 metadata contracts 都达到
mergeable。

## 5. 第一个实现候选

第一个实现型 WP 应是 causal runtime materialization slice，而不是大范围 scheduler
重写。

该 seed 现已开启为 [WP10 causal runtime foundation](wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.zh.md)。

推荐 seed：

- 在代码中物化一个小型 `StageNodeManifest` registry，
- 添加最小 scheduling-window loop skeleton：
  collect facade requests -> input-injection barrier -> manifest-derived acyclic
  window -> window-commit barrier -> export barrier，
- 把稳定 node id 与 semantic stage 接到 engagement/observation 路径，
- 对所选 slice 在 schedule construction 阶段验证 same-window edges，
- 在 facade 已经返回 packet 的地方暴露或断言 snapshot version、barrier id、
  source time 与 event ordering，
- 让 `DiagnosticsTrace` 与 event ancestry 保持绑定，
- 添加 focused architecture/runtime tests 证明该路径。

优先切片：

```text
P7 FireControlLaunch / P9 EffectsDamage / P10 ObservationExport
  -> recent engagement events
  -> diagnostics traces
  -> RuntimeFacade export APIs
  -> Python binding smoke and architecture checks
```

这条路径合适，是因为 WP3-WP5 和 WP9 已围绕 engagement、diagnostics、observation
与 facade exports 建立了 guardrails、contracts 和 tests。

Track 2 follow-on seed：

- 添加 `ActionHoldPolicy` typed contract，再声明 policy/control/physics cadence support，
- 给 observation/facade packets 添加 information-state provenance labels，
- 证明 facade exports 可以携带 provenance，同时不让 policy code 访问 `World Truth`。

该 follow-on seed 现已开启为
[WP11 facade vertical slice and provenance](wp11_facade_vertical_slice_provenance/facade_vertical_slice_provenance_wp11_20260520.zh.md)。

Phase 3 enforcement seed：

- 把 WP11 consumer pre-gates 晋升为 focused Law 14 read-side enforcement，
- 在 maintained outputs 被授权前，校验 `AgentRole` authority、information source、
  decision-model reference 与 action interface，
- 为 selected packet/belief chain 暴露 information transformation evidence，
- 通过 facade-compatible injection 守护 `DecisionBelief -> ActionIntentPacket` /
  `CoordinationIntentPacket` 路径，
- 保持完整 Agency Graph runtime、backend/fidelity、capability composition 与
  counterfactual work 不在范围内。

该 enforcement seed 现已验收为
[WP12 information and agency enforcement](wp12_information_agency_enforcement/information_agency_enforcement_wp12_20260520.zh.md)。

Phase 4 backend/fidelity seed：

- 让 `RuntimeCapabilities` 暴露保守 query metadata 与稳定 rejection reasons，而不从
  GPU helper/probe availability 推断 support，
- 从已验收 WP6/WP7 registries 物化 code-owned backend profile records 与 parity
  budget evidence gates，
- 把 fidelity profile labels 作为绑定 profile ids、budget refs、model-family scope、
  validation gate 与 facade evidence 的 requests 来 admission，
- 通过 maintained facade 与 Python binding surfaces 证明 query 与 rejection 行为，
- 在各自 gate 存在前，保持 exact GPU、resident-state、shadow、adaptive fidelity、
  learned `ModelProvider` 与 maintained multi-fidelity support 不在范围内。

该 backend/fidelity seed 现已验收为
[WP13 backend fidelity expansion](wp13_backend_fidelity_expansion/backend_fidelity_expansion_wp13_20260520.zh.md)。

Phase 5 capability-composition seed：

- 定义 platform-semantic `Capability`、`CapabilityBundle`、capability-family
  vocabulary 与 resolved-plan evidence，同时不复用 backend `RuntimeCapabilities`；
- 引入内部兼容链路：
  `type_name -> CapabilityBundle template -> ResolvedPlatformSpawnPlan ->
  materialization evidence`；
- 让既有 spawn 路径在 materialization 前先走 resolution，同时保持
  `spawn_unit(type_name)` 与 `WorldSpawnRequest.type_name`；
- 为未来 typed platform spawn requests 添加 additive facade/setup DTO vocabulary，
  但不让它成为强制入口；
- 把 capability families 绑定到现有 ECS/component materialization evidence 与
  unsupported-effect reasons，同时不添加新战术行为；
- 在各自 gate 存在前，保持 public `spawn_platform({capabilities...})` 晋级、
  scenario-schema migration、backend/fidelity promotion 与 broad spawn rewrites
  不在范围内。

该 capability-composition seed 现已开启但尚未验收为
[WP14 capability composition](wp14_capability_composition/capability_composition_wp14_20260521.zh.md)。

## 6. 第一个实现型 WP 的非目标

- 不重写整个 scheduler。
- 在 window-loop skeleton 证明前，不声明严格 clock-domain enforcement。
- 不把 exact GPU、resident-state 或 multi-fidelity execution 晋升为 maintained。
- 不把所有 platform spawning 迁到 capability composition。
- WP14 compatibility bridge 与 additive facade/setup DTO gates 通过前，不让 typed
  capability spawning 成为强制入口。
- 第一个 causal slice 不声明 Law 14 read-side enforcement 或 Agency Graph runtime enforcement。
- 在 deterministic replay 和 snapshot 边界存在前，不启动 counterfactual/worldline branching。
- 不让文档 closure 阻塞实现 `Mergeable` 状态；README、acceptance、archive 与
  bilingual sync 交给 closure lane。

## 7. 证据标准

WP9 之后，主线架构 WP 若没有 runtime artifacts，就不能算完成。

实现型 WP 的最低证据：

- code-owned contract 或 runtime surface，
- focused runtime 或 architecture tests，
- 精确验证命令和结果，
- 若影响 frontend consumer，至少一个 facade-visible 或 binding-visible proof，
- 若某 track 声明 scheduler semantics，则必须有 schedule-construction 或 runtime
  test 证明相应 edge/barrier/event rule，
- 命名 residual，而不是隐藏 TODO。

documentation-only output 仍可能有价值，但应归类为 planning 或 closure-lane work，
不应算作主实现结果。

## 8. Subagent 路由

采用以下拆分：

- 主实现 worker 负责一个有边界 track 或 slice 的代码、测试和英文 canonical handoff notes。
- closure subagent 在 stream 到达 `Mergeable` 后负责 README/review/index/archive/bilingual 同步。
- explorer 可以在派发任务前检查候选 implementation seam，但不能替代 runtime materialization。

对于 `WP14`，思考预算最高的是 compatibility-preserving composition seam：决定
capability contracts、content/factory lowering、spawn resolution、facade setup DTOs
与 materialization evidence 附着在哪里，同时避免创造第二套 spawn lifecycle 或强迫 callers
离开 type-name compatibility。
