# 标准化文档总览

语言版本：

- 英文主文：[README.md](README.md)
- 中文辅文：`README.zh.md`

状态：`2026-06-01`，当前维护中的标准树权威入口。

本目录用于定义项目后续采用的标准化建模基线。它的职责不是重复每一份活跃任务文档，而是回答：

- 哪些概念属于 `joint/common core`
- 哪些概念属于 `service profile`
- 哪些概念属于领域特化
- 哪些跨域 runtime / bridge / foundation 约束必须被所有层遵守
- 当前代码、测试与任务计划应如何对齐到这套分层

## 目录定位

维护中的标准树要同时约束三件事，避免它们彼此漂移：

- 公开可引用的现实条令与参考资料
- 仓库当前 runtime 与测试合同
- `docs/task/` 下的活跃任务规划

因此，标准树是 ownership map，不是任务板。任务计划可以描述当前执行波次，但不应重新定义
`authority_scope`、`task_group_id`、`runway_slot_code` 或 `warfare_role_code`
归谁所有。
任务区的实现成熟度是有用的状态信息，但它不是标准所有权层级。

## 当前结构

从 `2026-03-23` 起，标准化文档不再沿用“空战先行，再尝试泛化”的组织方式，
而改为以下领域所有权主干：

1. `joint/`
2. `services/`
3. `air/`
4. `naval/`
5. `ground/`

这条主干需要与 `foundation/` 和 `bridge/` 下的跨域标准一起阅读，包括 runtime
workflow 与合同基线。这些文档约束所有领域，不构成一条单独的军种或平台栈。

维护中的标准树对应一套明确的分层：

- `joint/` 负责跨军种仍成立的关系、授权、任务下达、汇报和工作流边界。
- `services/` 负责解释空军、陆军、海军、海军陆战队如何读取这些共通对象。
- `air/` 负责空中平台专用语义，例如 sortie phase、runway recovery、takeoff procedure、
  air mission observation。
- `naval/` 负责海军专用语义，例如 task-group、station、screen、support、recover、
  maritime command-role extension。
- `ground/` 负责地面域专用语义，例如以 platoon 为中心的 tasking、
  move/occupy/support 语义、terrain-masked information 假设，以及 land
  command/support extension。

第三域导航必须同时经过这两层：`services/army.md` 负责 Army 军种画像解释，
`ground/` 负责维护中的 ground 特化语义。`army` 与 `land` 作为别名会规范化为
维护名 `ground`，不会形成一条单独的 `army runtime stack`。

## 所有权层级

判断稳定概念应落在哪一层时，按下面层级处理：

1. `foundation/` 与 runtime/bridge 约束负责跨域规则：坐标与时间约定、真实性门槛、
   公开来源准入、场景/runtime 工作流边界、DTO 对齐，以及当前可测试合同。它们约束
   所有军种和领域特化。
2. `joint/` 负责共享语义对象，例如 command relationship、authority scope、
   task/report identifier、support relationship，以及其他必须在跨军种语境中保持同义的命名。
3. `services/` 负责军种画像解释：空军、陆军、海军、海军陆战队如何读取共享对象，
   哪些梯队或单位形态可进入 runtime tight loop，以及军种术语在变成领域机制前应停在哪里。
4. `air/`、`naval/`、`ground/` 负责领域特化。它们可以定义平台、任务、环境和执行语义；
   某一领域先实现了某个概念，不代表这个概念应提升为 common core。

这是一套所有权层级，不是成熟度阶梯。空战或飞行动力学实现更成熟，不会让 air 概念自动变成
项目级 common core。海军或地面 bootstrap 还早，也可以为其 service/profile 与 specialization
概念建立权威归口。runtime 支持缺失或不完整，应作为实现任务追踪，而不是被解释成更低标准层级。

## 推荐阅读顺序

建议按下面顺序进入：

1. [联合标准总览](joint/README.md)
2. [联合指挥与建模基线](joint/command_and_modeling_baseline.md)
3. [联合命令链与汇报基线](joint/command_link_and_reporting_baseline.md)
4. [运行时工作流与合同基线](bridge/runtime_workflow_and_contract_baseline.md)
5. [梯度真实性原则](foundation/gradient_realism_principles.zh.md)
6. [真实性与 Authority 边界规则](foundation/realism_authority_boundary.zh.md)
7. [公开数据来源准入标准](foundation/public_data_source_admission.zh.md)
8. [军种画像总览](services/README.md)
9. [美国空军画像](services/air_force.md)
10. [美国陆军画像](services/army.md)
11. [美国海军画像](services/navy.md)
12. [文档对齐映射](overview/document_alignment_map.md)
13. [场景配置指南](bridge/scenario_guide.md)
14. [空中平台特化总览](air/README.md)
15. [海军标准总览](naval/README.md)
16. [Ground 标准总览](ground/README.zh.md)

## 与活跃任务树的关系

`docs/task/` 当前包含 flight dynamics、air combat、common air/naval split、
naval realism、ground bootstrap、simulation architecture、runtime/performance、
model work，以及跨域 issue tracking 等活跃或近期活跃的执行线。

这种组织方式对执行、backlog 归属和成熟度追踪有用，但它不是标准所有权地图。某条任务线可以
更成熟、较不成熟、已经归档，或刚启动 bootstrap；这些状态都不改变稳定概念归属的标准层级。
特别是：

- `flight_dynamics/flight`、`sensor_situation`、`weapon_guidance` 和 `air_combat`
  主要推动实现真实性与 air specialization；它们不使 air 成为默认 common core。
- `flight_dynamics/c2_command_chain`、`simulation_architecture` 以及跨域
  runtime/performance 工作，经常会产出应落在 `joint/`、`foundation/` 或 `bridge/` 的合同。
- `common_air_naval` 与 naval 任务计划里的概念，可能分属共享语义、`services/navy.md`
  和 `naval/`。
- `ground` 任务计划里的概念，可能分属共享语义、`services/army.md` 和 `ground/`；
  `army` 与 `land` 别名应通过这套分层归口，而不是形成新的 runtime stack。
- model、training、evaluation 与 issue-board 任务可以依赖标准合同，但应引用或推动对应的
  标准归口，而不是定义一套平行层级。
- 标准树应吸收任务文档里已经稳定下来的共享合同，而不是照搬任务目录结构，或照搬各领域当前
  rollout 成熟度。

若任务文档和标准文档在“概念归属”上冲突，以标准树为准。

## 调研与依据

本轮标准化重建采用：

- 官方或官方托管公开资料
- 仓库内当前 runtime/测试代码作为合同依据

当前关键外部来源包括：

- [联合参谋部 doctrine publications](https://www.jcs.mil/Doctrine/Service-Publications/)
- [CJCSM 3150.13C，联合报告结构](https://www.jcs.mil/Portals/36/Documents/Library/Manuals/m315013.pdf)
- [AFDP 3-0.1，指挥与控制](https://www.doctrine.af.mil/Portals/61/documents/AFDP_3-0_1/AFDP3-0.1CommandandControl.pdf)
- [美国第七舰队，CTF 71 建立](https://www.c7f.navy.mil/Media/News/Display/Article/2641477/ctf-71-establishment-enhances-readiness-in-7th-fleet/)
- [TTGP Warfare Commanders Conference I](https://www.ttgp.navy.mil/OFRP-Syllabus/Warfare-Commanders-Conference-I/)
- [NAVIFOR，IW Has a Seat at the Table](https://www.navifor.usff.navy.mil/Press-Room/News-Stories/Article/2395110/iw-has-a-seat-at-the-table/)
- [MCDP 1-0](https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/1323621/mcdp-1-0-w-ch-1-3/)

当前关键仓库内依据包括：

- [docs/task/README.md](../task/README.md)
- [docs/task/flight_dynamics/README.md](../task/flight_dynamics/README.md)
- [docs/task/air_combat/README.md](../task/air_combat/README.md)
- [docs/task/naval/README.md](../task/naval/README.md)
- [docs/task/ground/README.md](../task/ground/README.md)
- [docs/task/simulation_architecture/README.md](../task/simulation_architecture/README.md)
- [docs/task/flight_dynamics/archive/program/realism_program_convergence_plan_20260517.md](../task/flight_dynamics/archive/program/realism_program_convergence_plan_20260517.md)
- [gym_envs/scenario_loader/core.py](../../gym_envs/scenario_loader/core.py)
- [src/core/mission/README.md](../../src/core/mission/README.md)
- [tests/runtime/README.md](../../tests/runtime/README.md)

## 状态分类

维护中的标准树使用三类状态：

- `Authoritative`
  - 当前维护工作的主标准
- `Specialization`
  - 平台或领域特化补充
- `Archived`
  - 仅保留作历史参考的旧路线

这些分类描述文档权威性与特化归属，不表示每个被归口的概念都已经在 runtime、测试、场景、
模型或 UI 表面达到相同实现程度。

当前划分：

- `foundation/*.md`：`Authoritative foundation`
- `joint/*.md`：`Authoritative`
- `services/*.md`：`Authoritative`
- `runtime_workflow_and_contract_baseline.md`：`Authoritative`
- `scenario_guide.md`：`Authoritative bridge`
- `air/*.md`：`Specialization`
- `naval/*.md`：`Specialization`
- `ground/*.md`：`Specialization`
- `docs/Archive/**`：`Archived`
- `docs/task/flight_dynamics/archive/**`：任务历史归档，不是活跃标准来源

额外维护中的补充页：

- [naval/ship_unit_references.md](naval/ship_unit_references.md)
  - 第一批海军单位与公开来源可追溯性的参考基准补充页
- [ground/minimal_task_structure.md](ground/minimal_task_structure.md)
  - 第一批 ground tasking 语汇与架构约束的 G0 基线
- [modularization_plan.md](planning/modularization_plan.md)
  - 面向未来代码结构的活跃规划补充页，不是当前 runtime 合同

## 维护规则

- 英文 `.md` 是 canonical，中文 `.zh.md` 是 companion。
- 维护中的英文主文不应继续保留机器翻译草稿标记。
- 新的共享合同应先落在 `joint/` 或 `bridge/` 下的 workflow bridge 文档，再扩散到任务计划。
- 某一军种或平台当前恰好先实现了，不代表它的术语可以直接提升为全项目 common core。
- 当工作被拆分给多个 subagent 或 worker 时，应遵循
  [Subagent 使用规范](governance/subagent_usage_policy.zh.md)。
- 当 simulation-architecture WP 已完成实现但仍需要发布收口时，使用
  [WP Closure Lane Policy](governance/wp_closure_lane_policy.zh.md)。

## 相关文档

- [双语文档政策](governance/bilingual_documentation_policy.zh.md)
- [双语文档簇](governance/bilingual_document_clusters.zh.md)
- [Subagent 使用规范](governance/subagent_usage_policy.zh.md)
- [WP Closure Lane Policy](governance/wp_closure_lane_policy.zh.md)
- [文档对齐映射](overview/document_alignment_map.zh.md)
- [仿真约定](foundation/conventions.zh.md)
- [梯度真实性原则](foundation/gradient_realism_principles.zh.md)
- [真实性与 Authority 边界规则](foundation/realism_authority_boundary.zh.md)
- [公开数据来源准入标准](foundation/public_data_source_admission.zh.md)
- [场景配置指南](bridge/scenario_guide.zh.md)
- [运行时工作流与合同基线](bridge/runtime_workflow_and_contract_baseline.zh.md)
- [模块化规划](planning/modularization_plan.zh.md)
