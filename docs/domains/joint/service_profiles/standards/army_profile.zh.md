# 美国陆军画像

Language:
- English canonical: [army_profile.md](army_profile.md)
- Chinese companion: `army_profile.zh.md`

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/domains/joint/service_profiles/standards/army_profile.md`
Owner: `domains/joint/service-profiles`
Last verified: `2026-08-08`

状态：`2026-06-01`，Army 军种画像层权威版本。

本文档定义仓库在早期 ground specialization 已经启动之后，应如何解释美国陆军
的组织层级与指挥关系，同时避免把 Army 军种画像误当成执行层。

它刻意比完整陆军条令摘要更窄，目标是防止 air-first 的 runtime 假设继续渗入
当前或未来的陆战建模。

本画像负责解释 Joint common core 在陆军组织和指挥关系中的含义，不拥有地面领域
执行合同。

## 现实基础

陆军官方公开资料仍把地面行动建立在 mission command、command and control
以及分层梯队组织之上，而不是建立在空战式架次包装之上。

官方参考：

- [Mission Command Center of Excellence (MCCoE)](https://usacac.army.mil/Organizations/Centers-of-Excellence-CoE/MCCoE)
- [Mission Command Resources](https://usacac.army.mil/Organizations/Centers-of-Excellence-CoE/MCCoE/Mission-Command-Resources)
- [CADD Command and Control Division](https://usacac.army.mil/Article-Library/View-Content-2/Command-and-Control-Division?ArtMID=437&ArticleID=331)

当前 MCCoE 的公开 mission statement 明确表示其负责 Mission Command Force
Modernization Proponent 与 Command and Control Warfighting Function。Mission
Command Resources 页面直接列出 `ADP 6-0 Mission Command: Command and Control of Army Forces`，
而 Command and Control Division 页面也说明该部门负责产出包括 `ADP 6-0` 在内的关键条令。

对本仓库的标准化工作来说，关键现实锚点就是：

- 陆军组织是梯队化的
- command and control 是一等问题
- 仓库在建模地面单位时，应优先围绕指挥关系与战术梯队，而不是套用空战架次术语

## 层级边界

### `joint/common core`

common 层应保留跨军种共享的骨架：

- `service_profile`
- `task_family`
- `tactical_unit_type`
- `authority_scope`
- `command_relationship`
- `coordination_mode`
- `task_group_id`
- `role_code`
- `supported_node_id`
- `supporting_node_id`
- `recovery_site_id`

这些字段是可移植的，不应被重命名成空军专用或舰队专用术语。

### 陆军 Service-profile 解释

陆军画像层负责给这套骨架赋予陆军口径：

- 以梯队为核心的单位组织
- 机动、火力、保障与支援关系
- 哪些层级可视为战术 runtime 单位
- 哪些层级应继续保留在作战或战役元数据层

这一层定义的是解释权，而不是平台执行细节。

### Ground specialization 边界

专门的 ground specialization 拥有，或应在成熟过程中逐步拥有，不属于 Army 军种
画像层的执行词汇：

- maneuver geometry
- frontage、bounds、routes、battle positions
- 直接火力与间接火力执行接口
- 保障与机动控制细节
- 领域专属 observation、action、reporting 扩展

当前 ground 线已有 tasking/schema 证据，但 movement、terrain、sensing、fires、
damage 与 combat 行为仍保持 held。因此，陆军画像继续扮演边界标准，而不是
假想 runtime API。

## Runtime 边界

### 应留在场景或作战元数据层的层级

当前仓库应把下列梯队保留在 tight-loop runtime 之上：

- corps
- division
- brigade
- battalion 在其主要承担作战层任务管理，而非直接战术控制时

这些层级更适合表达为：

- 场景组织
- 任务分配与授权框架
- 后勤与火力分配元数据
- 作战边界与兵力包装

### 可能适合作为战术 runtime 单位的层级

如果未来扩展陆战建模，最先有价值的 tight-loop 单位大概率是：

- squad / section
- platoon
- company / troop / battery

battalion 级控制仍可存在于场景与 tasking 图景里，但真正的可执行闭环应先在更小的战术编组上稳定下来。

## 对标准设计的直接约束

### 不要把空军词汇当成陆战基线

面向 Army 的标准不应把以下术语视为通用词：

- `wingman`
- `element lead`
- `runway`
- `takeoff`
- `formation slot`
- `recovery approach`

这些都是空中术语，不是陆地 common-core 术语。

### 在 common core 中保留支援关系与梯队锚点

陆军画像进一步强化了以下共享字段的必要性：

- `tactical_unit_type`
- `authority_scope`
- `supported_node_id`
- `supporting_node_id`
- `role_code`
- `coordination_mode`

这些字段比任何 aircraft-centric DTO 形状都更接近军种中立的陆战基线。

### 把军种画像与未来机动 API 分开

本文档不应发明伪造的 ground action surface。它只负责说明：

- 战术梯队边界应落在哪里
- 哪些关系必须在 common core 中存活
- 哪些内容必须等 dedicated ground specialization 明确接受后再定义

## 与当前仓库合同的关系

当前仓库已有早期 ground tasking/profile/schema 证据，但还没有维护中的完整
Army 执行层或 ground-combat runtime。因此，陆军画像仍主要是标准化护栏：

- 已接受的 ground tasking/status 流覆盖
  `TaskOrderGround -> LeaderIntentGround -> PilotReportGround`
- ground profile 会把 G0/G1 static task metadata 投影到
  `MissionCommandGround`；这是 command authoring 与 command-chain sync，
  不是已经释放的动态 command delivery
- formal ground command delivery 仍属于未来 ground-owner release
- common 字段应持续保持对陆战可移植
- air-specific 的命令细节不应被提升为 Army 基线

也正因如此，在更广泛的 ground runtime 行为仍被后续任务 gate 持有时，陆军画像
仍是边界标准。

## 相关文档

- [军种画像总览](../README.zh.md)
- [联合指挥与建模基线](../../standards/command_and_modeling_baseline.zh.md)
- [联合命令链与汇报基线](../../standards/command_link_and_reporting_baseline.zh.md)
- [仿真约定](../../../../standards/foundation/conventions.zh.md)
- [运行时工作流与合同基线](../../../../standards/bridge/runtime_workflow_and_contract_baseline.zh.md)
- [Ground 标准总览](../../../ground/README.zh.md)
