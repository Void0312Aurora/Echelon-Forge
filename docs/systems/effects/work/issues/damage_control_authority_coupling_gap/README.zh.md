# Damage 到操控权限的传递缺口

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/systems/effects/work/issues/damage_control_authority_coupling_gap/README.md`
Owner: `systems/effects`
Last verified: `2026-08-08`

状态：`2026-06-15` 保留跟踪 / 暂存。这个问题是真实的行为建模缺口，但不是当前发射窗口或杀伤链分析的核心工作项。

首次观察：`2026-06-15`，检查飞行员、飞控、指挥/导航、通信或数据链部件失效之后，飞机是否真的失去后续操控能力时。

问题类别：部件 damage、整机 kill 标志、控制指令、指挥链路和数据链之间的传递缺口。

## 摘要

当前 damage 链可以把飞行员/乘员、飞控、推进、任务系统等损伤写入飞机和平台状态。
但这些状态不一定会真正切断后续操控链路。

说人话就是：报告里可能已经写着飞行员失效、`crew_kill=true`，或者通信/数据链相关部件受损，但模拟器仍可能继续接受 `PilotAction`、`MissionCommand`、`CommandLink` 或 `DataLink` 行为，好像操控权限仍然可用。

这个问题需要保留，因为它会让功能性击杀看起来偏弱，也可能让已经失去操控或通信能力的目标在后续步骤里继续机动或通信。不过它不应塞进当前 fire-window sweep，除非当前工作明确扩展到控制权限后果。

## 当前证据

- [damage_air.h](../../../../../../src/components/domains/air/combat/damage_air.h)
  会把 `flight_control_kill` 或 `propulsion_kill` 转成机动能力归零，把
  `crew_kill` 转成任务能力归零。
- [damage_system_common.h](../../../../../../src/systems/combat/damage_system_common.h)
  会把平台 damage 值转成 `mission_kill`、`mobility_kill`、`sensor_kill`
  和 `loss_state`。
- [default_control_model.cpp](../../../../../../src/models/domains/air/default_control_model.cpp)
  仍然从 `PilotAction`、激活的 `MissionCommand` 或滞后的控制状态选择控制来源；
  没有按 `crew_kill`、`pilot_effectiveness`、`mission_kill` 或 `mobility_kill`
  关闭这些来源。
- [control_input_resolution.h](../../../../../../src/components/domains/air/command/control_input_resolution.h)
  根据 active 标志解析 `PilotAction`、`MissionCommandControlState` 和 legacy command，
  没有读取 damage 状态。
- [command_link_system.h](../../../../../../src/systems/systems/command_link_system.h)
  通过 `CommandLink` 的时间状态投递 pending movement/action/mission command，
  没有 damage gate。
- [data_link_system.h](../../../../../../src/systems/systems/data_link_system.h)
  使用 `DataLink.active`、网络 id、距离、地平线和阵营匹配；目前看不到因为通信或
  航电部件受损而停用链路行为的逻辑。

## 影响

- 飞行员或乘员被杀伤后，报告可能已经记录失效，但人工或脚本控制仍能继续输入。
- 飞控失效会降低飞行性能，但控制器仍可能继续尝试操纵飞机。
- 通信或数据链损伤可能只扣任务/航电能力，而没有禁用命令投递、航迹共享或消息交换。
- 如果训练和评估只看 destroyed，或者目标在控制权限失效后仍继续行动，就会低估功能性击杀。

## 不能宣称

- 这不代表当前 damage-chain 概率工作无效。
- 这不授权立刻重写整条指挥/控制链。
- 这不要求把轨迹随机性加入当前发射时机分析。
- 这不表示每次飞行员或通信命中都必须直接摧毁目标。

## 后续行动门槛

1. 区分有人机、无人机、导弹和自主平台的后果规则。
2. 明确 `crew_kill`、`flight_control_kill`、`mission_kill` 或通信/数据链部件失效后应该发生什么：禁用输入、保持上一条命令、降低控制权限、强制返航，还是标记失控。
3. 在控制输入解析、指挥链投递和数据链共享中加入明确 gate，而不是只依赖报告字段。
4. 增加测试，证明飞行员/乘员杀伤、飞控杀伤、数据链杀伤都会按预期改变后续行为。
5. 在发射窗口和杀伤链诊断里，把功能性击杀和物理摧毁分开报告。

## 闭合标准

- 功能性 kill 有明确行为后果，而不只是报告标志。
- 飞行员/乘员、飞控、指挥/导航、通信、数据链失效至少有 smoke 级运行时测试。
- 训练/评估诊断能区分 destroyed、mission kill、mobility kill、crew kill 和控制权限丧失。
- 后续修复不能静默削弱现有 damage report 或合法性 gate。
