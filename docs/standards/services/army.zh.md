# 美国陆军画像

Language:
- English canonical: `army.md`
- Chinese companion: [army.zh.md](army.zh.md)

状态：`2026-05-18`，Army 军种画像层权威版本。

本文档定义仓库在未来进入地面特化之前，应如何解释美国陆军的组织层级与指挥关系。

它刻意比完整陆军条令摘要更窄，目标是防止 air-first 的 runtime 假设继续渗入未来的陆战建模。

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

### `services/army`

陆军画像层负责给这套骨架赋予陆军口径：

- 以梯队为核心的单位组织
- 机动、火力、保障与支援关系
- 哪些层级可视为战术 runtime 单位
- 哪些层级应继续保留在作战或战役元数据层

这一层定义的是解释权，而不是平台执行细节。

### 未来地面特化

未来如果建立 ground specialization，应由其负责当前仓库尚未维护的执行词汇：

- maneuver geometry
- frontage、bounds、routes、battle positions
- 直接火力与间接火力执行接口
- 保障与机动控制细节
- 领域专属 observation、action、reporting 扩展

在那之前，`services/army` 应继续扮演边界文档，而不是假想 runtime API。

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
- 哪些内容必须等 dedicated ground specialization 落地后再定义

## 与当前仓库合同的关系

当前仓库还没有维护中的 Army 执行层。因此，陆军画像目前主要是面向未来设计的标准化护栏：

- 共享 tasking/reporting 流应保持 `TaskOrder -> LeaderIntent -> MissionCommand -> Report`
- common 字段应持续保持对陆战可移植
- air-specific 的命令细节不应被提升为 Army 基线

也正因如此，即便 ground runtime 尚未存在，`services/army` 仍然必须先写清楚。

## 相关文档

- [军种画像总览](README.md)
- [联合指挥与建模基线](../joint/command_and_modeling_baseline.md)
- [联合命令链与汇报基线](../joint/command_link_and_reporting_baseline.md)
- [仿真约定](../foundation/conventions.md)
- [运行时工作流与合同基线](../bridge/runtime_workflow_and_contract_baseline.md)
