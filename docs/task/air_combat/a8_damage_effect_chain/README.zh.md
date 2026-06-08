# A8 损伤效果链

状态：`2026-06-08` active implementation。射击记录、部件故障词表、公开故障模式行、
动力消费方切片、一段翼面/操纵气动消费方切片，以及固定燃油泄漏/质量响应证据已经落地。
固定数据链命中现在会通过维护中的平台状态继续表现为任务/传感器能力下降；固定更完整火灾检查
现在覆盖油箱火势增长和尾部发动机火区播种。窄的地面接触生命周期表面现在可以区分安全着陆机体
和严重撞击残骸，不再把删除飞机作为唯一公开结果。

语言：

- 英文规范页：[README.md](README.md)
- 中文配套页：`README.zh.md`

输入：

- 父级空战任务：[../README.zh.md](../README.zh.md)
- 已封存的毁伤模型记录：
  [../a2_high_fidelity_damage_model/README.zh.md](../a2_high_fidelity_damage_model/README.zh.md)
  和 [../archive/a2_high_fidelity_damage_model/README.zh.md](../archive/a2_high_fidelity_damage_model/README.zh.md)
- 子项目创建标准：
  [../../../agent/rules/subproject_creation_standard.zh.md](../../../agent/rules/subproject_creation_standard.zh.md)
- Subagent 使用规范：
  [../../../standards/governance/subagent_usage_policy.zh.md](../../../standards/governance/subagent_usage_policy.zh.md)
- 损伤和效果代码入口：
  [damage.h](../../../../src/components/combat/damage.h)、
  [damage_system.h](../../../../src/systems/combat/damage_system.h)、
  [default_effects_model.cpp](../../../../src/models/weapons/default_effects_model.cpp)
- 飞行和动力消费入口：
  [aerodynamics_system.h](../../../../src/systems/physics/aerodynamics_system.h)、
  [propulsion_system.h](../../../../src/systems/physics/propulsion_system.h)
- MQ-9 / AIM-120C 样例：
  [mq9_reaper.json](../../../../examples/config/database/aircraft/units/mq9_reaper.json)、
  [aim_120c.json](../../../../examples/config/database/weapons/air_to_air/aim_120c.json)

## 目的

A2 已经留下了一套有用的结构化损伤运行时，但最近 AIM-120C 打 MQ-9 的检查说明：
“命中被记录了”还不等于“命中后的过程说得清楚”。本子项目要标准化这条路径：
战斗部做了什么、打到飞机哪个部位、哪个功能变差、已有的飞行、动力、燃油和传感器系统
如何随后表现出结果。

这里不增加新的“命中就击落”开关。发动机坏了，就通过动力系统降低推力；舵面或作动器坏了，
就通过飞行路径降低滚转、俯仰或偏航控制；油箱坏了，就通过漏油、燃烧风险和质量变化逐步表现。
最后是否坠毁，要让飞机仿真自己跑出来。

## 当前状态

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| 引信和起爆记录 | active input | `damage_system.h` 记录近炸/接触引信状态，并把起爆交给效果模型。 | 记录起爆不等于损伤过程完整。 |
| 部位级损伤清单 | active input | `damage.h` 和 MQ-9 JSON 已有命中盒、命名部件、分组和依赖。 | 这些名称是工程脚手架，不是已校准事实。 |
| 战斗部到部位的效果 | primary cut point | `default_effects_model.cpp` 和 detail 文件会估算作用强度、挑选受影响部件并计算当前失效概率。 | 这是第一实现切入点，但当前数值是估计，不是 AIM-120C 真实定论。 |
| 损伤到飞机状态 | active input | `AircraftDamageStateUpdate` 会把部件状态映射到推力、燃油、传感器、火灾和粗略飞行限制。 | 保留它作为下游桥接，不用直接击杀规则替代。 |
| 飞行和动力消费 | active implementation | 显式发动机调参启用时，动力系统也会消费推进损伤；气动系统现在会把结构、液压、轴向操纵能力和不对称损伤作为有限系数/控制能力变化消费。 | 当前气动响应仍是 synthetic 且偏标量化，不是飞机专用飞控律校准。 |
| 燃油和质量消费 | active evidence | 固定中心油箱命中现在会暴露燃油泄漏和火源模式，随后通过维护中的运行时路径减少燃油和质量。 | 这证明的是泄漏/质量和火灾风险，不是完整火灾蔓延或坠毁生命周期。 |
| 火灾消费 | active evidence | 固定左翼油箱命中会让火势增长并造成二次损伤；尾部发动机命中会播种发动机火区并带来后续动力下降，但不要求没有可燃暴露时火势自行增长。 | 这是确定性工程证据，不是已校准火灾真值。 |
| 传感器和数据链消费 | active evidence | 固定数据链收发机命中会暴露 `data_loss`，保持非权威，并在后续运行中通过维护中的平台损伤状态降低任务/传感器/生存能力以及航电/乘员任务/导航状态。 | 这证明的是任务/感知后果，不是 MQ-9 主动数据链报文流量，也不要求飞机坠毁。 |
| 地面接触生命周期 | active implementation | 触地现在通过调试表面暴露 `landed_airframe` 和 `crashed_wreck` 状态，并有安全跑道接触、严重撞击和低速非坠毁检查。 | 这在 A8 中作为原实体可观察性验收；一等碎片/残留对象后置。 |
| 测试证据 | active | 已有 MQ-9/AIM-120C 固定检查、公开故障模式守卫、调参发动机损伤推力检查、固定 MQ-9 右副翼短/长时程响应检查、固定中心油箱泄漏/质量响应检查、固定更完整火灾响应、固定数据链任务/传感器响应检查和地面接触生命周期检查。 | 运行时测试是工程链路证据，不是真实世界杀伤概率证据。 |

## 范围

范围内：

- 定义每次射击的标准记录：引信、起爆点、战斗部作用、受影响部位、功能变化、后续飞行/动力/传感器响应。
- 归一化损伤类型：切断、穿孔、爆压变形、漏油、液压失压、电气失效、数据链中断、火源、结构削弱。
- 把部位损伤接到已有消费方：动力、燃油和质量、传感器、火灾传播、飞行/气动力。
- 增加固定 MQ-9 / AIM-120C 测试，检查过程，而不是只检查最后活着还是消失。
- 对结构化飞机，旧的血量字段只作为兼容读数，不作为主要解释。

范围外：

- “命中即坠毁”或“AIM-120C 必然击落 MQ-9”规则。
- 绕过飞行和动力系统的独立“还能不能飞”判决。
- 真实世界击杀概率、确定性引信真值、机密武器数据，或当前 AIM-120C 数值的权威声明。
- 超出本链路所需的完整飞机数据校准。

## 阶段计划

| 阶段 | 目标 | 进入条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 建立 follow-on 工作面，不改变运行时行为。 | 用户要求标准化损伤效果链并创建子项目。 | README、当前状态、任务簇、archive 索引和父级链接存在。 | pass |
| `P1 Structure Evidence` | 确认现有命中、效果、部位和飞行消费结构。 | P0 文档存在。 | 只读发现明确代码入口、缺口和安全写入范围。 | pass for planning |
| `P2 Shot Effect Record` | 定义每次射击的解释记录。 | P1 确认字段和消费方。 | 测试能断言引信、起爆、部位效果和后果阶段。 | pass |
| `P3 Part Effect Vocabulary` | 用具体损伤类型替代单个泛化伤害值。 | P2 记录稳定。 | 部件损伤能命名泄漏、切断、火源、数据丢失、结构削弱。 | pass |
| `P4 Consumer Integration` | 把具体损伤送入动力、燃油、传感器、火灾和飞行力学。 | P3 效果存在。 | 发动机、翼面/操纵、燃油、传感器和火灾损伤能通过维护中的仿真路径表现。 | partial pass：动力、翼面/操纵气动、燃油泄漏/质量、更完整火灾和数据链任务/传感器证据通过 |
| `P5 Scenario Validation` | 用固定 MQ-9 / AIM-120C 样例证明链路。 | P4 实现通过聚焦测试。 | 测试解释尾部、翼面/操纵、燃油/火灾和传感器/数据链结果。 | partial pass：包含固定燃油泄漏/质量、更完整火灾和数据链任务/传感器样例 |
| `P6 Acceptance` | 决定 accepted 或 held 并记录残余。 | P5 证据完成。 | 父级 README 和状态文档给出诚实能力边界和剩余缺口。 | planned；第八轮 partial pass |

## 任务簇

- 任务簇计划：
  [a8_damage_effect_chain_task_clusters_20260607.md](a8_damage_effect_chain_task_clusters_20260607.md)
- 当前状态：
  [a8_damage_effect_chain_current_status_20260607.md](a8_damage_effect_chain_current_status_20260607.md)
- 派发队列：
  [a8_damage_effect_chain_dispatch_queue_20260607.md](a8_damage_effect_chain_dispatch_queue_20260607.md)
- 最新实现说明：
  [a8_w7_propulsion_tuning_consumer_20260608.md](a8_w7_propulsion_tuning_consumer_20260608.md)
  和 [a8_w8_aero_consumer_20260608.md](a8_w8_aero_consumer_20260608.md)
  以及 [a8_damage_effect_chain_dispatch_queue_20260607.md](a8_damage_effect_chain_dispatch_queue_20260607.md)
  中的第八轮验收记录。

## 产出和证据

预期产出：

- 可由测试和调试接口查看的射击效果记录。
- 能命名具体物理/功能损伤的部件记录。
- 部件损伤向动力、燃油/质量、传感器、火灾和飞行/气动力消费路径的传递。
- 覆盖尾部发动机、翼面/操纵、燃油泄漏/质量、火灾行为、传感器/数据链的
  MQ-9 / AIM-120C 回归测试。
- 持续拒绝把工程估计说成真实武器杀伤定论的文档边界。

## 验收门槛

本子项目只有在以下条件满足后才能标为 accepted：

- 结构化飞机不再把直接扣血作为导弹效果的主要解释。
- 每次有记录的射击都能解释从引信到受损部位再到后续飞机行为的链路。
- 发动机或螺旋桨损伤通过动力路径影响推力。
- 翼面、操纵或结构损伤通过维护中的飞行路径影响气动/控制行为。
- 燃油损伤通过现有燃油和火灾路径影响泄漏、质量、火灾风险或供油。
- 传感器或数据链损伤能造成任务或感知后果，而不要求飞机一定坠毁。
- MQ-9 / AIM-120C 测试同时检查即时损伤记录和后续飞机响应。
- 文档继续拒绝真实世界击杀概率、确定性引信或 AIM-120C/MQ-9 权威杀伤声明。

## 残余和下一步

- 公开射击行、具体部件故障词表、MQ-9/AIM-120C 固定检查、调参发动机动力消费方、一段
  翼面/操纵气动消费方、一个中心油箱泄漏/质量运行时检查、一组更完整火灾运行时检查、一个
  数据链任务/传感器运行时检查和一个地面接触生命周期表面已整合。
- 后续运行时工作应继续只通过已有维护系统扩大消费方覆盖，尤其要谨慎处理飞机专用飞控律校准
  和平台族扩展。
- 右副翼长时程损伤会让受损 MQ-9 在干净基线保持平飞时进入近地响应。严重触地现在可以观察为
  `crashed_wreck`，安全或低速触地保持为 `landed_airframe`。
- 碎片/残留实体后置；本 A8 切片接受原实体 `landed_airframe` / `crashed_wreck` 可观察性。
- 破片分布、爆压载荷、目标脆弱性和飞机专用失效阈值的完整校准继续 deferred。

## Archive

当前 A8 记录是 live。被替代的扫描、被拒绝的链路设计或带日期探测记录，只有在已有替代
current status 或 acceptance 表面后，才移动到 [archive/README.zh.md](archive/README.zh.md)。
