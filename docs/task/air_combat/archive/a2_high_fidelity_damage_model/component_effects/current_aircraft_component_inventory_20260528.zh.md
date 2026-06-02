# 当前 Aircraft Component Inventory 概览

状态：`2026-05-28` 只读 inventory 概览。本文依据当前 aircraft JSON 组件样例、`DamageComponent`/`ComponentDamageState`/`AircraftDamageState` 字段和既有 A2 文档整理；不新增 authoritative 平台数据。

## 运行时结构面

当前组件级 structured-aircraft 路径的核心数据面如下：

- `Hitbox`：保存局部机体系几何盒、装甲厚度、protected systems 和 `DamageComponent` 列表。
- `DamageComponent`：保存组件 `name`、`system`、`redundancy_group_id`、局部几何、装甲、阈值尺度、mechanism-specific threshold、critical 标志、冗余权重和 `dependencies`。
- `ComponentDamageState`：保存运行时组件完整性、组件到冗余组映射、冗余权重、冗余组可用性、组成员数和失败数。
- `AircraftDamageState`：保存 aircraft overlay 后果状态，包括结构、飞控、液压、三轴控制、控制不对称、推进、燃油、航电、机组、飞行员、任务机组、指挥/导航、火灾、燃油泄漏、结构过载、颤振暴露和 kill/forced landing 标志。
- `PlatformDamageState`：保存平台级 mission/mobility/sensor/survivability capability 和 loss state，作为旧接口与新 overlay 的桥接面。
- `EffectsEvent`/`DamageReport`：保存 warhead/fuze/geometry/mechanism/component/redundancy/vulnerability evidence 等审计字段，供诊断、训练消费层和验收测试读取。

## 当前代表平台覆盖

| 平台 | hitbox 数 | component 数 | 主要系统覆盖 | 冗余组数 | 依赖边数 | 当前定位 |
|---|---:|---:|---|---:|---:|---|
| `F-16C_Block50` | 4 | 22 | radar、cockpit、fuel、avionics、engine、flight_control、hydraulic、navigation、data_link、wings | 18 | 26 | 单发战斗机代表样例 |
| `Su-35S_Flanker-E` | 5 | 23 | radar、cockpit、sensor_payload、fuel、avionics、data_link、双发 engine、flight_control、navigation、wings | 16 | 26 | 双发战斗机/推力矢量代表样例 |
| `MQ-9_Reaper` | 4 | 23 | sensor_payload、navigation、data_link、fuel、avionics、mission_systems、engine、propeller、flight_control、wings | 13 | 22 | UAV/遥控链路代表样例 |
| `MH-60R_MVP` | 5 | 22 | cockpit、sensor_payload、fuel、avionics、data_link、mission_systems、engine、transmission、hydraulic、rotor、tail_rotor、flight_control | 16 | 27 | 直升机/旋翼传动代表样例 |
| `E-3_Sentry_AWACS` | 6 | 27 | cockpit、command、navigation、radar、mission_systems、data_link、fuel、avionics、双侧 engine、flight_control、wings | 17 | 31 | C2/大型机任务系统代表样例 |

这些样例共同证明当前数据面可以跨 fighter、UAV、helicopter 和 C2/large aircraft 运行；它们不代表全库飞机已经完成 authoritative 20-50 项组件建模。

## 当前 hitbox 与组件分布

`F-16C_Block50` 当前分为 nose radar/cockpit、center fuselage fuel/avionics/engine、aft engine/flight-control、wing flight-control/fuel。组件覆盖 APG-68 radar、cockpit crew station、nose avionics、IFF、center fuel cell、mission computer、data link、flight-control computer、navigation、power bus、engine core、afterburner nozzle、tail hydraulic pump、engine fuel control、rudder actuator、wing fuel cells、aileron actuators、wing spar 和 leading-edge flap actuators。

`Su-35S_Flanker-E` 当前分为 nose radar/cockpit、center fuselage fuel/avionics/data-link、left engine、right engine、wing flight-control/fuel。组件覆盖 Irbis radar、cockpit、IRST、avionics、mission computer、data link、flight-control computer、navigation、power、左右发动机 core/fuel feed/thrust-vector actuator、wing fuel cells、elevon actuators、wing spar 和 leading-edge flap actuators。

`MQ-9_Reaper` 当前分为 sensor/navigation/data-link、fuselage fuel/data-link/avionics/mission、engine/propeller、wing flight-control/fuel。组件覆盖 EO/IR turret、SAR、SATCOM、navigation、fuel cell、data-link transceiver、flight computer、mission processor、power distribution、command encryption、rear engine、engine fuel control、starter generator、pusher propeller、wing fuel cells、aileron/flap servos 和 wing spars。

`MH-60R_MVP` 当前分为 cockpit/sensor/navigation、fuel/avionics/data-link/mission、engine/transmission/hydraulic、rotor/flight-control、tail-rotor/transmission/flight-control。组件覆盖 cockpit crew station、surface-search radar、FLIR、navigation、fuel bladders、avionics rack、data link、sonar/ESM mission racks、power distribution、双 engine modules、main gearbox、hydraulic pump、main rotor hub、cyclic/collective servos、tail rotor gearbox、tail drive shaft 和 yaw servos。

`E-3_Sentry_AWACS` 当前分为 flight-deck/command/navigation、rotodome radar/data-link/mission、center fuselage fuel/avionics/data-link/mission/navigation、left engine、right engine、wing flight-control/fuel。组件覆盖 flight deck crew、command navigation suite、IFF、rotodome radar、mission processing racks、wideband data link、radar processor、mission operator consoles、fuel cells、avionics bay、navigation reference、power/APU、engine pods、engine fuel feeds、engine fire bottles、wing fuel cells、aileron/spoiler actuators 和 wing spar。

## 已具备的工程能力

- 组件可通过 hitbox 局部几何被直接命中或近炸空间投射选中。
- 组件机制载荷可记录 fragment energy、fragment areal density、penetration margin、blast pressure/impulse/scaled distance、rod cut margin 等审计量。
- 组件 `critical` 与 redundancy group 已进入合成失效概率调制。
- 组件完整性和冗余组可用性可跨多次命中累积。
- 组件 `dependencies` 已能把损伤传播到相关 aircraft systems 和 overlay。
- aircraft overlay 已能下推到 mobility、mission、sensor、survivability、fuel leak、fire 和 forced landing 等平台后果。

## 当前缺口

- 组件命名 taxonomy 尚未冻结为 schema 级约束。
- 各平台同类系统的冗余组粒度不完全一致，例如 fighter、UAV、helicopter、AWACS 的 power/data-link/mission naming 仍偏样例化。
- 依赖边只有 `system + scale`，尚无边类型、门槛、延迟、恢复/隔离状态或 load-sharing 模型。
- hydraulic、electric power、flight-control computer、actuator、surface、sensor processor、crew station 的多层依赖尚未形成完整网络。
- 当前组件失效概率和后果阈值为工程化 scaffold，不是校准数据。

