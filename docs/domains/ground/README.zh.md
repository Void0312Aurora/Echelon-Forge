# 地面任务域

语言：[英文规范页](README.md)；本页为中文配套。

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/domains/ground/README.md`
Owner: `domains/ground`
Last verified: `2026-10-01`

Ground owner 定义陆上领域特化语义，但不把 Army 军种条令变成一条私有 runtime
栈。它拥有 Ground 专属平台身份和静态 task/status 词汇。Joint 关系、Army
service-profile 解释以及跨域 runtime 架构仍由各自 owner 负责。

## 当前权威

- [Ground 特化基线](standards/specialization_baseline.zh.md)：规范 Ground 身份、
  owner 边界、已接受实现表面和仍保持 held 的 runtime 声明。
- [Ground 最小任务结构](standards/minimal_task_structure.zh.md)：维护中的
  `TASK_MOVE`、`TASK_OCCUPY` 和 `TASK_SUPPORT` 静态 task/status 合同。

## 当前已实现表面

- `army`、`ground`、`land` 和 `ServiceProfile.Army` 均路由到维护中的
  `ground` tasking profile。
- `Ground_Platoon_MVP` 是 runtime 可加载的原生 `UnitType::Ground` 内容定义，
  用于静态 schema 与 scenario-loader 证据。
- Ground 自有 component slice 通过 `TaskOrder`、`LeaderIntent`、`PilotReport`
  和 `MissionCommand` 兼容 shell 传递静态 command/task/status 字段。
- 维护中的 tasking cadence 基线是 `1 Hz`。
- `Ground_Infantry_Soldier_MVP` 是原生的单兵 Ground fixture。
  `GroundInfantryMovement` 系统消费已准入的 `MoveStatic` 命令，通过共享
  `IEnvironmentModel` 应用确定性的地表、坡度与植被速度代价，并推进一个受限的水平
  运动学步；kernel 还向 native training probe 暴露同一 owner 计算出的 movement-effect
  倍率。这是单兵移动原语，不是 route following、passability、formation 或完整陆战动力学。
  准入记录见
  [Ground Infantry Movement v1](reviews/ground_infantry_movement_v1_20260924/README.zh.md)。
- 默认环境 provider 可以显式加载已验证的 Arnis 连续高程/地表覆盖栅格对，维护中的
  kernel 也向训练 adapter 暴露有界地形和 movement-effect 观测 tuple。树线/聚落语义、一般通行性以及
  track/sensor observation export 仍保持 held；河流/桥面地表采样已有限准入。
- `GroundWeaponState` 与 `SimulationKernel.fire_ground_weapon` 已为单兵 fixture
  准入一个有界原生直射切片：必须有敌方 Ground 目标的接触记录，并满足步枪射程、弹药、
  冷却与共享 effects/damage bridge 条件。这是确定性的近距离代理，不宣称视线、掩体、
  压制、弹道、间接火力或完整火控模型。
- `src/systems/domains/ground/damage_system_ground.h` 注册 `GroundDamageStateUpdate` 为默认
  组合 stage 30 的 `domain = ground` 系统。它**能匹配到**已生成的 ground 实体并推进
  ground 自有的 `GroundPlatformDamageState`，而且通往该 state 的 effects 路由可达：组件 id
  在组合路径里按 world 解析一次，因此一次结构命中会给出 ground 后果，而不是 placeholder
  兜底的"全零并被摧毁"。`2026-09-22` 实测，记录见
  [DM-G1 修复包](reviews/ground_damage_effects_route_repair_20260922/README.md)。
  [地面域系统归属准入](reviews/ground_systems_owner_admission_20260921/README.zh.md)
  包已收口该放置位置并被接受。
- `src/systems/domains/ground/` 拥有受限的单兵 movement 与 damage response，
  weapon release 则通过显式 core service seam；但这里仍不是完整的 Ground
  runtime-system owner。Route movement、passability、sensing、间接火力、共享
  damage bridge 之外的 effects、suppression、logistics 和 Ground observation
  export 仍作为**能力**保持 held。
- Ground 在中立的 `DecisionModelRegistry` 后注册了一个脚本决策模型：
  `ground.infantry.objective_occupy_scripted`（`adapter`，角色
  `ground_infantry_controller`，位于 `python/tasking_contracts/ground/`）。它以
  `MoveStatic` 航向/速度/姿态把一名步兵移动到任务给定的目标点，随后以 `OccupyStatic`
  或 `SupportStatic` 保持位置。只有当指挥员已在其自身 mission command 上指派目标并授权开火时，
  它才发出开火请求；放行权仍属于原生 `fire_ground_weapon_from_mission_command` 闸门。
  其逐能力标签位于 `python/tasking_contracts/ground/capability.py`：单兵移动、静态保持、
  局部地形交互和受限直射请求为 `admitted_bounded`；路线规划、一般通行性、视线/掩体/隐蔽、
  感知与航迹导出、观测导出、effects/damage 后果、间接火力、压制、后勤和多单位编队为
  `held`，请求其中任何一项都会 fail closed。推导出的 Ground 脚本标签是
  `bounded_adapter`，不是 `playable`。

目录位置不会扩大上述声明。当前证据证明的是原生身份和静态 task/status 链，
而不是完整 land-combat runtime。

## 当前相关路由

- [环境系统](../../systems/environment/README.zh.md)：跨域 substrate contract 与保留的
  G0/Arnis 验收边界。
- [Ground 缺陷清单](reviews/ground_domain_defect_inventory_20260522.zh.md)：带日期的
  review 快照；开放项需要按当前状态重新核验。
- [Ground 单兵移动 v1](reviews/ground_infantry_movement_v1_20260924/README.zh.md)与
  [Ground Arnis 原生地形 v1](reviews/ground_arnis_native_terrain_v1_20260924/README.zh.md)：
  于 `2026-09-24` 接受，作为带日期的 review 记录保留；其长期事实已并入
  [Ground 特化基线](standards/specialization_baseline.zh.md)。

当前已授权的地面工作面曾是
[地面域系统归属准入](reviews/ground_systems_owner_admission_20260921/README.zh.md)，
现为一份已接受的 review 记录：它把 `src/systems/domains/ground/` 准入为地面域的每 tick
系统归属目录。其声明收口簇改完了本页与专业化基线，因此损伤机制的 effects 路由可达性状态
是**写明的**，而不是以 placeholder 措辞暗示的。该记录中的每一处读数都是定位成因时的
**修复前**测量；该路由现在是可达的。归档记录可以提供 provenance，但不得重新定义以上标准。

超出该准入记录、仍然开放的工作，在此重述以免只存在于记录内部：`DM-G1` 修复已随自己的包落地，并于 `2026-09-29` 验收、作为带日期的 review 记录保留；
它留下的 mobility 期望已于 `2026-09-28` 决定在目前所有已上线 Ground 单位使用的合成 bootstrap
表面上撤回并钉住现状，原因是该表面上 Ground 的弹头机理载荷估算尚未准入，任何弹头类型都到不了
底盘 mobility 分支。`2026-09-29` 的范围澄清记录了另一处已知暴露：若 authored 的 Ground
`damage_model` 声明了 `engine`/`fuel` 系统，会经由一个既有的通用系统名系数到达 mobility，
而非 Ground 自身机制。仍开放的是该包记录的按部件推导机动
损失的后续议题；`ground_p2_stage_node` 包（地面域唯一声明的 stage 没有注册节点）；以及已退役
`docs/task/ground/` 记录的归档登记，归文档治理所有。

## 相关 Owner

- [Joint 任务域](../joint/README.zh.md)：共享授权与 common-core command
  relationship。
- [美国陆军 service profile](../joint/service_profiles/standards/army_profile.zh.md)：
  Army 组织和军种级解释。
- [Runtime workflow 与合同基线](../../architecture/standards/runtime_workflow_and_contract_baseline.zh.md)：
  共享 stage 与 runtime 边界。
