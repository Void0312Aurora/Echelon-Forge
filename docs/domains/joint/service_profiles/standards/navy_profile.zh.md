# US Navy Profile

Language:
- English canonical: [navy_profile.md](navy_profile.md)
- Chinese companion: `navy_profile.zh.md`

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/domains/joint/service_profiles/standards/navy_profile.md`
Owner: `domains/joint/service-profiles`
Last verified: `2026-08-08`

状态：`2026-08-08`，Navy 军种画像归口的权威标准。

本文档定义项目在海战与海上行动建模时使用的 Navy service profile。

它不再是早期占位文档。它的职责是说明 Navy 如何解释共享的 Joint common-core
合同，以及应在何处移交给专门的 naval specialization。它不拥有海上领域执行语义。

## 1. 现实基础

Navy 公开资料显示，海军战术组织是任务编组化的，通常会以 `Task Force`、`Task Group`、`Task Unit` 和 `Composite Warfare Commander (CWC)` 体系来表达。

当前公开依据：

- [U.S. 7th Fleet, CTF 71 establishment](https://www.c7f.navy.mil/Media/News/Display/Article/2641477/ctf-71-establishment-enhances-readiness-in-7th-fleet/)
- [TTGP Warfare Commanders Conference I](https://www.ttgp.navy.mil/OFRP-Syllabus/Warfare-Commanders-Conference-I/)
- [NAVIFOR, IW Has a Seat at the Table](https://www.navifor.usff.navy.mil/Press-Room/News-Stories/Article/2395110/iw-has-a-seat-at-the-table/)
- [COMPHIBRON 5 About](https://www.surfpac.navy.mil/Ships/Amphibious-Squadron-COMPHIBRON-5/About/)

这些来源支持三个结论：

- `Task Force / Task Group / Task Unit` 都是现实存在的海军任务组织层级。
- 海军控制以 warfare commander 角色为中心，而不是空军式 `lead / wingman` 配对。
- `Officer in Tactical Command` 是舰队与编队场景中的现实指挥权概念。

## 2. 层级边界

### 2.1 Joint common core

`common` 应保留所有军种可共享的骨架：

- `service_profile`
- `task_family`
- `task_group_id`
- `command_relationship`
- `authority_scope`
- `coordination_mode`
- `supported_node_id / supporting_node_id`
- `recovery_site_id`
- `tactical_unit_type`

对 Navy 来说，这些字段仍保持共享形状，但其含义由海军组织口径解释，而不是空战术语解释。

### 2.2 Navy Service-profile 解释

Navy service profile 负责说明 Navy 对共享骨架的专属读法：

- `task_group` / `task_unit` 层级
- `officer_in_tactical_command`
- `warfare_role_code`
- Navy 在 runtime planning 和任务封装中真正依赖的 common 锚点

这一层应该定义所有权与语义，不应定义执行细节。

### 2.3 海上领域特化

`naval` 是 tight-loop 海上运行时语义的专层：

- `screen / support / station / recover`
- 舰艇与编队任务行为
- 驻站、回收与海上角色几何
- naval execution 与 reporting specialization

这一层不应重新声明共享合同字段，除非是在澄清它们的海军含义。

## 3. 最小解释集

Navy profile 拥有以下军种层解释：

- `task_group`
- `task_unit`
- `warfare_role_code`
- `officer_in_tactical_command`

下列执行语义归 naval owner，而不归本画像：

- `screen`
- `support`
- `station`
- `recover`

这些共同构成当前海军任务计划与 runtime bridge 所需的最小军种/领域术语集，
但两层之间的所有权保持分离。

### 3.1 术语含义

- `task_group`：主要海军任务编组。
- `task_unit`：编组内的下级战术单元。
- `warfare_role_code`：单位或指挥官承担的战斗职能。
- `officer_in_tactical_command`：拥有战术指挥权的责任节点。
- `screen`：围绕高价值编队进行保护性位置部署。
- `support`：护航、保障或支援关系。
- `station`：需要保持或恢复的相对站位。
- `recover`：回收或返回控制语义，包括舰载航空器回收等场景。

## 4. 对当前任务计划的含义

对当前任务计划来说，Navy profile 的推进顺序应是：

1. 保持 common 合同稳定。
2. 用 `task_group / task_unit` 与 `officer_in_tactical_command` 绑定 Navy 的任务规划。
3. 要求 naval owner 把 `screen / support / station / recover` 定义为最小海军控制词汇。
4. 再往下扩展更深的舰艇或编队行为。

这样可以避免把空军优先的假设写入 naval runtime。

## 5. 所有权与桥接职责

Navy service profile 负责说明：

- Navy 依赖哪些 common 字段
- 这些字段由哪一层解释
- 哪些海军角色与任务层级拥有战术控制权

它不负责定义平台级执行命令、传感器行为或武器逻辑。

专门的 naval owner 在 common 骨架就位后拥有这些运行时语义。

## 相关文档

- [军种画像总览](../README.zh.md)
- [海军标准总览](../../../../domains/naval/README.zh.md)
- [联合指挥与建模基线](../../standards/command_and_modeling_baseline.zh.md)
- [联合命令链与汇报基线](../../standards/command_link_and_reporting_baseline.zh.md)
- [场景配置指南](../../../../standards/bridge/scenario_guide.zh.md)
