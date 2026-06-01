# 美国海军陆战队画像

Language:
- English canonical: `marine_corps.md`
- Chinese companion: [marine_corps.zh.md](marine_corps.zh.md)

状态：`2026-05-18`，USMC 军种画像层权威版本。

本文档定义仓库应如何把美国海军陆战队解释为一个独立的军种画像。

它的目标不是宣称当前已经存在独立的 Marine runtime，而是规定海军陆战队的兵力包装与指挥关系应如何约束后续标准化工作。

## 现实基础

当前官方海军陆战队条令仍把 Marine operations 视为围绕 Marine air-ground task force
展开的综合性军种与组成力量问题，而不是单域模板问题。

官方参考：

- [MCDP 1-0 w/ CH 1-3](https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/1323621/mcdp-1-0-w-ch-1-3/)

当前官方页面明确写到，该条令聚焦于：

- 海军陆战队组成力量在作战层级的作用
- 作为最大 MAGTF 的 Marine expeditionary force 如何在战术层级组织行动

这已经足以支撑本仓库的标准边界：USMC 不应被建模成 Army、Navy、Air Force 术语的临时拼接，
而应拥有自己的军种画像解释层。

## 层级边界

### `joint/common core`

common 层保留跨军种共享骨架：

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

这些字段保持共享形状，而 Marine profile 负责解释 MAGTF 式兵力包装如何读取它们。

### `services/marine_corps`

USMC 画像层负责 Marine 口径的共享骨架解释：

- MAGTF 式任务包装
- command element 的职责
- ground、aviation、logistics elements 之间的关系
- 一个 Marine 组织层级何时只是兵力包装，何时应被解释为战术 runtime 单位

这一层负责军种解释权，不负责执行细节。

### `air`、`naval` 与 ground specialization

当前各领域执行语义继续放在专门目录中：

- air 执行合同属于 `air/`
- maritime 执行合同属于 `naval/`
- 超出 shared tasking/schema bootstrap 的 land 执行合同属于专门的 ground 层

因此，Marine profile 的职责是通过 shared fields 协调这些层，而不是重写它们的命令面或传感器面。

## Runtime 边界

### 应留在场景或任务包装元数据层的层级

下列概念真实存在且重要，但在当前仓库中应继续保留在 tight-loop runtime 之上：

- Marine component 级作战框架
- MEF / MEB / MEU 作为战役组织时的兵力包装
- 大规模两栖或远征任务组织
- 尚未被现有 air、naval 或 ground 执行合同特化的跨域任务分配

这些内容更适合放在：

- 场景设计
- 兵力包装元数据
- 授权与支援关系
- 作战层级编排

### 可以触及当前可执行边界的层级

今天，Marine 概念只有通过已维护的 shared 或 specialized contract 才能进入可执行边界：

- `joint/common core` 中的共享命令与汇报骨架
- 通过 `air/` 合同进入的 air tactical units
- 通过 `naval/` 合同进入的 naval tactical units

当前并不存在维护中的独立 Marine execution DTO 集。本文档不应暗示相反结论。

## 对标准设计的直接约束

### 不要把 USMC 写成拼接军种包

Marine profile 不应被化约成：

- Army ground structure
- 加上 Navy sea basing
- 再加上 Air Force air support

标准文档必须保留一个事实：Marine task organization 旨在由单一军种画像统一整合这些元素。

### 用 shared fields 表达 MAGTF 关系

Marine 标准化最合适的共享锚点是：

- `task_group_id`
- `authority_scope`
- `command_relationship`
- `supported_node_id`
- `supporting_node_id`
- `coordination_mode`
- `role_code`

这些字段能让军种画像表达多作战单元关系，同时不假装当前 runtime 已经存在专门的 Marine control surface。

### 把执行细节继续下沉到特化层

例如：

- aviation command 语义必须继续通过 `air/`
- ship、screen、recovery 或 sea-based positioning 语义必须继续通过 `naval/`
- 后续 ground maneuver 语义应等待 dedicated ground layer

这样才能让 MAGTF 画像保持诚实，避免 `services/` 里再出现第二套平行命令面。

## 与当前仓库合同的关系

在当前仓库里，Marine profile 主要承担协调边界职责：

- `joint/common` 字段提供共享命令骨架
- Air Force 与 Navy profile 展示了军种执行层如何挂接在该骨架之下
- Marine profile 保证未来远征标准可以组合这些层，而不会重新塌缩回 air-first ontology

也正因此，`services/marine_corps` 必须始终聚焦在所有权与跨域解释上。

## 相关文档

- [军种画像总览](README.md)
- [空中平台特化](../air/README.md)
- [海军特化](../naval/README.md)
- [联合指挥与建模基线](../joint/command_and_modeling_baseline.md)
- [联合命令链与汇报基线](../joint/command_link_and_reporting_baseline.md)
