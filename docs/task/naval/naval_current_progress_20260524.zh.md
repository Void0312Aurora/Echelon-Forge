# 海军当前进展追踪

状态：`2026-05-27` 工作区抽样复核版，纳入 N4 bridge 验收与 N4 RL
action/observation surface 修复。

本文档是 `docs/task/naval/` 的当前活跃追踪入口，用来承接
`2026-05-17` 海军进度检查点之后的状态。它重点追踪三件事：

1. 基础设施：数据、组件、系统、合同和 facade/runtime 通路是否已经稳定。
2. 域特性：舰艇、海况、传感器、武器、毁伤、后勤和屏护行为已经真实到哪一步。
3. RL 对接：海军任务语义是否能通过现有训练/runtime 框架进入 policy 面。

本文档不把当前状态描述成完整高保真海战。当前更准确的定位仍是：

- 最小现实海上屏护接触场景已经稳定。
- 海军域已经拥有可运行的战术原型骨架。
- RL/tasking 对接已具备 profile、合同和 batch-sync 通道。
- 专门面向海军的训练任务已有 N4 smoke/probe entry gates；海军 reward、curriculum、
  evaluation gates 和 learned-policy acceptance 仍待后续完成。
- `n5_rl_action_surface_split/` 包已经作为 N4 pre-fire training-entry repair
  落地：`naval_station3` 与 `naval_screen_station_v1` 是 active surface，但 N5
  武器交战仍保持在独立 launch/reject package 之后。

## 一、当前结论

海军线已经从 `2026-05-17` 的“第三波主体完成，但武器命令链仍有红点”
推进到更靠近主线 runtime/facade 的状态：

- `DDG-51` 屏护 `T-AKE-1` 的 contact-report 与 closing-contact 两个场景都存在。
- 最近通过距离、HVU 盲区、共享航迹和报告链已有 contract 守门。
- `screen-hold` 已有扰动恢复和后段振荡守门。
- 旧检查点中提到的主炮直调和 `MissionCommand -> CIWS` 两个定向红点，在当前抽样复核中已转绿。
- 海军 tasking profile 已进入 Python RL/tasking bridge，并能投影到 maintained TaskOrder/MissionCommand/LeaderIntent/PilotReport 合同面。
- world-batch 和 cooperative vec env 的 command-chain sync 已通过 maintained assignment 投影海军字段，而不是只依赖旧 whole-shell 口径。
- `ddg51_take1_screen_threat_roe_v1` N4 bridge 已作为开火前场景扩展接受，
  具备 maintained threat/ROE 和 assigned-target provenance。

当前主要剩余风险不在“最小链路是否存在”，而在：

- 多数海军域能力仍是工程近似和 token 级 MVP。
- 海军 RL 还没有独立训练 curriculum、奖励面和评估套件。
- loader 侧仍保留部分 raw `SimulationKernel` compatibility quarantine seam，后续应继续迁到 facade-owned surface。

## 二、域真实性梯度临界点

海军域真实性应按“场景复杂度实际用到的能力”分层验收，而不是按代码里是否已经存在某个系统来笼统打勾。当前原则是：

- 简单巡航或站位场景，只要求巡航/站位所需的真实性。
- 接触报告场景，必须额外要求传感器、航迹共享和报告链真实性。
- 进入交火场景后，必须先补齐武器、火控、授权、毁伤和终止条件的真实性临界点。
- 没有被当前场景使用的域能力可以保持 MVP，但不能被拿来支撑更高复杂度场景的“现实性”声明。

建议采用以下梯度临界点：

| 梯度 | 场景复杂度入口 | 最低真实性要求 | 当前状态 |
| --- | --- | --- | --- |
| `N0` 平台/身份 | 只加载舰艇、展示编组或做静态几何 | 真实公开舰型、角色、基础尺寸/速度/传感器族；明确工程近似参数来源 | 已具备 |
| `N1` 巡航/航渡 | 舰艇按航向/速度移动，做简单巡航或跟随 | 水面速度上限、加减速、转向速率、低速舵效、海况入口、基础质量/库存不破坏运行 | 已具备 MVP；可支撑简单巡航和屏护站位 |
| `N2` 接触/报告 | 发现目标、共享航迹、生成报告 | 雷达地平线/海况损失/LOS、数据链节流、航迹来源、报告消息语义、HVU 本舰盲区守门 | 当前 screen/contact 场景已通过合同 |
| `N3` 屏护/C2 | 护航、站位保持、受扰恢复 | `TASK_SCREEN/TASK_SUPPORT`、海军角色、站位半径/方位、reference entity、扰动恢复和振荡守门 | 当前单 DDG/HVU 屏护已具备；不是完整舰队 C2 |
| `N4` 受威胁机动/ROE | 目标逼近、威胁排序、授权开火前态势 | ROE 状态、交战授权、目标分配、威胁优先级、传感器质量对决策的影响 | `ddg51_take1_screen_threat_roe_v1` 开火前 bridge 已接受；仍不是完整战术指挥官 |
| `N5` 交火/武器 | VLS、舰炮、CIWS 或导弹交战成为场景目标 | 火控前置条件、有效航迹、射程/射界/冷却/库存、发射事件、拒绝原因、命中/拦截证据 | 有最小骨架并通过定向测试；若作为交火场景核心仍需扩 gate |
| `N6` 命中/毁伤/终止 | 命中后继续演化或以战损判胜负 | mission kill/mobility kill/sensor kill、持续火灾/进水 proxy、能力退化、终止条件与奖励绑定 | 有 proxy；不够支撑高保真抗毁声明 |
| `N7` ASW/舰载机/后勤 | 声纳、潜艇、舰载机、UNREP 成为核心玩法 | 水声传播、接触置信度、舰载机 sortie/回收约束、UNREP 窗口和库存转移 | token/MVP；适合链路验证，不适合作为高保真主任务 |
| `N8` 多舰队/学习战术 | 多舰、多角色、长期 RL 或作战级 C2 | 多节点通信、指挥关系、协同策略、对抗策略、课程和评估覆盖 | 尚未进入 |

当前海军场景主要落在 `N1-N3`：

- `ddg51_take1_screen_contact_report_v1`：`N2` 接触/报告真实性是主要验收面。
- `ddg51_take1_screen_closing_contact_v1`：在 `N2` 基础上加入接触逼近和 `N3` 屏护几何稳定性。
- `ddg51_take1_screen_threat_roe_v1`：已接受为 `N4` 开火前 bridge，威胁/ROE 状态和
  assigned-target provenance 可观察，但 weapon release 和 damage 不是验收证明。
- `ddg51_take1_screen_threat_roe_offstation_recovery_v1`：维护态 N4 离站位恢复变体，
  DDG 初始位于名义站位内侧 `1800 m`，用于在固定原始任务奖励参考下守住脚本恢复 gate；
  它仍不等于 learned-policy 验收。
- 武器、CIWS、毁伤、ASW、舰载机和 UNREP 虽有 runtime 测试，但目前主要作为后续扩展的基础设施和局部链路证明，不能自动把现有 screen/contact 场景提升为交火或完整海战场景。

因此，后续每新增一个场景类型，都应先声明它进入了哪个梯度，并把对应临界点变成测试或合同。比如：

- 若只训练 `naval_screen_station_hold`，重点守门应停在 `N1-N3`。
- 若训练 `naval_contact_report`，必须守住 `N2` 的传感器/共享态势/报告链。
- 若扩展到 `naval_surface_engagement`，必须先把 `N4-N6` 的 ROE、火控、发射事件、毁伤和终止条件补成 scenario-level gate。

## 三、基础设施进展

### 3.1 场景和合同

已存在并通过抽样复核：

- 场景：
  - [ddg51_take1_screen_contact_report_v1.json](../../../scenarios/naval/ddg51_take1_screen_contact_report_v1.json)
  - [ddg51_take1_screen_closing_contact_v1.json](../../../scenarios/naval/ddg51_take1_screen_closing_contact_v1.json)
  - [ddg51_take1_screen_threat_roe_v1.json](../../../scenarios/naval/ddg51_take1_screen_threat_roe_v1.json)
  - [ddg51_take1_screen_threat_roe_offstation_recovery_v1.json](../../../scenarios/naval/ddg51_take1_screen_threat_roe_offstation_recovery_v1.json)
- 合同：
  - [naval_screen_contact_report_geometry.json](../../../tests/contracts/unit/naval/naval_screen_contact_report_geometry.json)
  - [naval_screen_closing_contact_geometry.json](../../../tests/contracts/unit/naval/naval_screen_closing_contact_geometry.json)
  - [naval_screen_threat_roe_geometry.json](../../../tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json)
  - [naval_screen_threat_roe_offstation_recovery.json](../../../tests/contracts/unit/naval/naval_screen_threat_roe_offstation_recovery.json)
  - [scenario_loader_naval_common_core_semantics.json](../../../tests/contracts/unit/naval/scenario_loader_naval_common_core_semantics.json)

这些合同证明当前海军场景不再只是静态摆拍。它们至少锁住：

- `DDG` 先获得本舰接触。
- `HVU` 通过共享态势获得航迹和报告。
- closing-contact 变体在指定窗口内保持 HVU 本舰盲区。
- `DDG` 与 `HVU` 的屏护站位距离维持在 contract 约束内。
- `tasking_profile: naval` 能驱动 common-core tasking semantics。

### 3.2 运行时组件和系统

当前海军基础设施已经覆盖以下主要 C++ 组件和系统：

- 舰船平台与运动：
  - [ship_platform.h](../../../src/components/naval/ship_platform.h)
  - [ship_motion_system.h](../../../src/systems/naval/ship_motion_system.h)
- 潜艇平台与运动：
  - [submarine_platform.h](../../../src/components/naval/submarine_platform.h)
  - [submarine_motion_system.h](../../../src/systems/naval/submarine_motion_system.h)
- 舰载机 token 协同：
  - [embarked_air_ops.h](../../../src/components/naval/embarked_air_ops.h)
  - [embarked_air_ops_system.h](../../../src/systems/naval/embarked_air_ops_system.h)
- 海军命令扩展：
  - [mission_command_naval.h](../../../src/components/command/naval/mission_command_naval.h)
  - [task_order_naval.h](../../../src/components/tasking/naval/task_order_naval.h)
- 舰载武器：
  - [naval_weapon_mounts.h](../../../src/models/weapons/naval_weapon_mounts.h)
  - [naval_mission_weapon_release_system.h](../../../src/systems/naval/naval_mission_weapon_release_system.h)
- 后勤和 UNREP：
  - [logistics.h](../../../src/components/systems/logistics.h)
  - [logistics_system.h](../../../src/systems/systems/logistics_system.h)

关键进展是：海军字段不再只是 JSON metadata。它们已经进入 ECS 组件、系统、Python binding、runtime tests 和 world-batch maintained contract 投影。

### 3.3 数据和单位库

当前数据库层已具备：

- 蓝方 `DDG-51` 与 `T-AKE-1` 真实公开舰型基线。
- `Red_Surface_Combatant_Minimal` 替代早期红方物流舰占位。
- `Kilo_Class_MVP` 和 `MH-60R_MVP` 等 ASW/舰载机 MVP 数据。
- `AN/SPS-67(V)`、`AN/SPY-1D`、民用导航雷达、`SLQ-32`、`SQQ-89` MVP 声纳等传感器模块。
- `naval_stores`、`naval_logistics` 和 structured naval weapon mounts。

这些数据多数明确标注为 public fact、engineering calibration 或 community-derived approximation。后续仍应保持这个数据口径，不把工程校准参数写成真实性能硬事实。

## 四、域特性进展

### 4.1 舰船运动和海况

当前已具备：

- 低速舵效和无舵速阈值。
- 船舶加减速和转向速率限制。
- `sea_state / wave_heading_deg / wave_period_s` 平台默认值。
- 全局 maritime state 环境覆盖规则。
- 海况驱动的 roll/pitch proxy。
- 高海况下的波浪增阻和有效最大航速下降。

边界：

- 仍是水面二维运动加姿态 proxy，不是完整舰艇操纵性、推进时滞和波浪响应模型。
- maritime state 当前是全覆盖或无覆盖，不支持字段级 merge。

### 4.2 传感器、ESM、声纳和态势共享

当前已具备：

- 多传感器挂载。
- 海面雷达地平线、海况损失和 ducting 近似。
- ESM bearing-only MVP。
- Sonar / acoustic MVP。
- Track source 中保留 Radar、DataLink、ESM、Sonar 等来源。
- 数据链共享不再是每步全量广播，而是围绕 confirmed/new-significant/refresh 语义收敛。
- 海面 LOS 对近海平面接触有最小 maritime 容错路径。

边界：

- ESM 仍是告警/方位级 MVP。
- 声学模型仍是工程校准近似。
- 海面 LOS 不是完整海面、地形、折射统一模型。

### 4.3 屏护、C2 和任务语义

当前已具备：

- `TASK_SCREEN` / `TASK_SUPPORT` 海军任务语义。
- `ScreenCommander`、`LogisticsCoordinator` 等海军角色默认推断。
- `NavalStationType.Screen / Support`。
- `station_radius_m / station_bearing_deg / reference_entity_id` 驱动的 station-keeping。
- Python `compute_naval_screen_station_hold()` 的动态屏护命令更新。
- 扰动后恢复与后段振荡 runtime 守门。

边界：

- 当前是单屏护舰围绕 HVU 的 station-hold 控制，不是完整舰队编队控制器。
- tasking 语义已经进入 common-core，但海军专门 C2 策略还很薄。

### 4.4 武器、发射和毁伤

当前已具备：

- `DDG-51` structured `VLS / gun / CIWS` mounts。
- `VLS-SAM` 最小发射链，要求有效航迹并消耗库存。
- 主炮直调发射链。
- CIWS 对近距导弹拦截的简化链路。
- `MissionCommand -> CIWS` 命令驱动路径。
- mission kill、mobility kill、sensor kill 等中间毁伤态和持续毁伤传播 proxy。
- naval launch adapter 的 request/event shape 映射测试。

这意味着 `2026-05-17` 检查点中提到的主炮和 `MissionCommand -> CIWS` 两个红点，当前抽样复核已经转绿。

边界：

- 仍不是完整 naval tasking / fire-control AI。
- `VLS-SAM`、主炮、CIWS 都是工程近似，不包含完整火控、弹道、射界、照射/制导通道和电子对抗。
- 毁伤传播仍是标量 proxy，不是舱室、稳性、进水、自由液面和损管高保真模型。

### 4.5 后勤和舰载机

当前已具备：

- `naval_stores` 抽象 fuel/missile/dry cargo 库存。
- `T-AKE` 到 `DDG` 的 UNREP 窗口、连接、转移、完成/退出状态机。
- `LaunchHelo / RecoverHelo / RelayOTHTargeting` token MVP。

边界：

- UNREP 是抽象库存转移，不是补给 doctrine 或真实吞吐率模型。
- `RecoverHelo` 当前仍是 token 级回收。
- 舰载机 sortie、甲板调度、航空燃油/弹药循环还未展开。

## 五、RL 对接进展

### 5.1 已有能力

海军任务语义已经进入 RL/tasking 框架：

- [naval_profile.py](../../../python/rl/profile/naval_profile.py) 负责海军默认推断和 `build_kernel_mission_command()`。
- [naval_adapter.py](../../../python/rl/tasking/naval_adapter.py) 暴露 naval profile 到 tasking bridge。
- [bridge.py](../../../python/rl/tasking/bridge.py) 通过 `tasking_profile: naval` 或 `ServiceProfile.Navy` 解析海军 profile。
- [observations.py](../../../gym_envs/leader_env_parts/decision_runtime/observations.py) 在 leader observation 的 task vector 中消费 profile-specific `task_observation_codes()`。
- [world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py) 和 [cooperative_world_batch_vec_env.py](../../../python/rl/runtime/cooperative_world_batch_vec_env.py) 通过 maintained assignment 投影 MissionCommand / TaskOrder / LeaderIntent / PilotReport。
- [command_chain_cache.py](../../../python/rl/runtime/world_batch/command_chain_cache.py) 覆盖 naval owner slice snapshot 与 maintained contract projection。

这使海军任务字段可以进入：

- scenario-loader command-chain sync。
- leader-env task observation。
- world-batch / cooperative-world-batch command-chain batch sync。
- maintained tasking export 和 task-order contract 面。

### 5.2 当前还不能声称的能力

当前还不应声称：

- 已有完整海军 RL 训练任务。
- 已有海军专属 reward/curriculum/eval 主线。
- policy 已学会屏护、交战、ASW 或 UNREP。
- 海军 C2 决策已从 scripted/token 行为升级为 learned policy。

当前更准确的说法是：

- 海军 RL 对接的语义和运输层已经可用。
- 最小 naval scenarios 可作为 RL 接入候选场景。
- 训练目标、奖励定义、curriculum 和评估 gate 仍待下一轮设计。

N4 RL preflight 已记录在
[naval_n4_rl_task_surface_preflight_20260525.zh.md](archive/n4_threat_roe_bridge/naval_n4_rl_task_surface_preflight_20260525.zh.md)。
已接受的下一步 RL 兼容任务候选是：

- `naval_contact_report_threat_roe_v1`；
- `naval_screen_station_hold_threat_aware_v1`。

三者现在都有 active smoke/probe 入口，位置是
[examples/config/training/active/naval](../../../examples/config/training/active/naval/README.zh.md)。
这些条目是实现 gate，而不是已训练 policy 证据：它们把已接受 N4 场景与 cooperative
单策略槽位 runtime 配对，使用专门的 no-release `naval_station3` 站位指令动作面和
`naval_screen_station_v1` 策略观测面，并把武器释放、毁伤奖励、击杀奖励和 learned-policy
声明排除在范围外。`2026-06-12` compatibility cleanup 之后，`naval_station3` 还会记录
`_naval_station3_command_surface` 作为测试化站位指令真值，中性 `PilotAction` 仅保留为
legacy assignment carrier。同一轮刷新也把 `naval_screen_station_v1` 收束为
`naval_screen_station_v1_maintained_adapter`；active/eval JSON 现在会报告
`surface_gate`，覆盖 action command surface、legacy transport adapter 与 naval
observation adapter。`naval_limited_engagement_v1` 继续被 N5 launch/reject 和非毁伤 gate
阻塞。

## 六、验证记录

本次抽样复核时间：`2026-05-24 21:24 CST`。

已通过：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/naval/test_naval_ship_database.py tests/runtime/naval/test_naval_screen_scenario.py tests/runtime/naval/test_naval_sensor_realism_runtime.py tests/runtime/naval/test_naval_asw_helo_runtime.py tests/runtime/engagement/test_naval_launch_adapter.py tests/leader/test_tasking_profile_contracts.py tests/leader/test_command_field_projection_contracts.py
# 49 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_contact_report_geometry.json
# PASS

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_closing_contact_geometry.json
# PASS

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/scenario_loader_naval_common_core_semantics.json
# PASS

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "naval or task_order or command_chain"
# 5 passed, 22 deselected

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "naval_owner_slice or task_order_naval or command_chain"
# 5 passed, 54 deselected

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/mission/test_mission_command_naval_fields_roundtrip.py tests/runtime/mission/test_naval_mission_command_mapping.py tests/runtime/mission/test_ship_mission_command_authority.py
# 12 passed
```

N4 bridge 验收：

- [N4 RL 任务面预检](archive/n4_threat_roe_bridge/naval_n4_rl_task_surface_preflight_20260525.zh.md)
- [N4 集成验收](archive/n4_threat_roe_bridge/naval_n4_integration_acceptance_20260525.zh.md)
- [N4 闭合](archive/n4_threat_roe_bridge/naval_n4_closure_20260525.zh.md)

文档验证：

```bash
git diff --check -- docs/task/naval
# passed
```

N4 active training-entry gate：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/training/test_naval_training_entry_contracts.py
# 4 passed, 4 subtests passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py --scenario scenarios/naval/ddg51_take1_screen_threat_roe_v1.json --train_config examples/config/training/active/naval/naval_contact_report_threat_roe_smoke_v1.json --output_base /tmp/cmo-naval-train.<tmp> --run_name naval_contact_report_threat_roe_smoke_v1
# Training Complete.

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py --scenario scenarios/naval/ddg51_take1_screen_threat_roe_v1.json --train_config examples/config/training/active/naval/naval_screen_station_hold_threat_aware_smoke_v1.json --output_base /tmp/cmo-naval-train.<tmp> --run_name naval_screen_station_hold_threat_aware_smoke_v1
# Training Complete.

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
# PASS
```

Action 侧 compatibility cleanup 验证（`2026-06-12`）：

```bash
pytest -q tests/runtime/naval/test_naval_station_policy_surface.py
# 19 passed

pytest -q tests/runtime/mission/test_mission_obs_taxonomy.py
# 5 passed

pytest -q tests/eval/test_evaluation_cli_contracts.py -k "NavalStationPolicyEvalTests"
# 8 passed, 5 deselected
```

## 七、下一步建议

建议下一轮按下面顺序推进：

1. 将 N4 视为已闭合，避免为了 engagement 工作重新打开 N4。
   `naval_contact_report_threat_roe_v1`、`naval_screen_station_hold_threat_aware_v1`
   与 `naval_screen_station_recovery_threat_aware_v1` 现在已有 active smoke/probe 条目。
2. Facade 化收口：把 loader-owned raw simulation compatibility seam 中仍承担业务含义的 naval command-chain 同步继续迁到 facade-owned maintained surface。Action 侧 command surface 与 observation adapter 已显式化；`P2-B` 仍需要 command projection guards，之后才能把 `MissionCommand` 从 compatibility shell 进一步收窄。
3. 任务面守门：为 `MissionCommand -> naval weapon`、`screen-hold` 和 `tasking_profile: naval` 增加更少依赖调试 API 的 facade 或 world-batch 级验收。
4. N5 门控：`naval_limited_engagement_v1` 继续阻塞，直到独立 N5 包定义
   launch/reject、range/arc/cooldown/inventory、action masking 和非毁伤验收 gate。
5. 域真实性小步补强：优先补 maritime state 细字段测试、传感器/LOS 联动和武器命令链稳定性，不急于扩成多舰队高保真交战。
6. 在当前 N4 cooperative baseline eval gate 之上，继续扩展完整 curriculum 和
   learned-policy acceptance，再考虑 learned-policy 或更广 cooperative naval training 声明。

当前优先级仍应是“把已存在的海军任务语义稳定接入学习面”，而不是继续横向扩更多海军系统。
