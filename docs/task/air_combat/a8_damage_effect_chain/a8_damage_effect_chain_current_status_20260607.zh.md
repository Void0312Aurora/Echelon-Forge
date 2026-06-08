# A8 损伤效果链当前状态

状态：`2026-06-08` 第三轮实现检查点。A8 已有有边界工作面，并已整合当前会话
结构发现；第一段动力消费方已作为有限 `A8-DEC-E` 运行时/测试切片落地。

## 本次变化

- 创建 A8，作为已封存 A2 research / candidate 记录之后的具体损伤效果 follow-on。
- 固定初始边界：A8 不增加直接坠毁规则、MQ-9 特例击杀规则，也不增加独立“还能不能飞”判决。
- 将工作拆成有限任务簇：结构证据、射击效果记录、部位损伤词表、消费方接入、
  MQ-9/AIM-120C 验证和验收。
- 已整合当前会话的只读 explorer 检查，分别覆盖引信/效果代码、损伤到飞行消费方、
  MQ-9/AIM-120C 验证样例。
- 已新增第一轮实现派发队列：
  [a8_damage_effect_chain_dispatch_queue_20260607.md](a8_damage_effect_chain_dispatch_queue_20260607.md)。
- 已验收第一轮 worker：
  - `A8-W1 Shot Record`：通过。它固定了
    `EffectsEvent -> DamageReport -> DiagnosticsTrace` 这条已有记录链，
    没有新增公开字段。
  - `A8-W2 Part Failure Vocabulary`：部分通过。它把机制载荷映射成内部部件故障类型，
    并通过已有飞机损伤量表现出来；公开的逐部件故障类型字段仍留给集成阶段。
  - `A8-W3 Validation Fixtures`：部分通过。它增加 MQ-9/AIM-120C 固定检查和非权威保护；
    后续飞行消费方检查仍留给 `A8-DEC-E`。
- 已验收第二轮 worker：
  - `A8-W4 Public Failure Mode Rows`：通过。它把具体模拟故障类型暴露到公开逐部件射击记录和
    Python 绑定中，同时保持 `component_failure_mode_authority=false`。
  - `A8-W5 Propulsion Fuel Mass Consumer Scout`：只读证据通过。它确认了动力/燃油/质量的最窄
    消费路径，以及发动机调参可能绕过损伤缩放的风险。
  - `A8-W6 Aero Control Consumer Scout`：只读证据通过。它确认了操纵/气动响应的最窄切口，
    同时说明真正的力和力矩变化仍需 `A8-DEC-E` 实现。
- 已验收第一段 `A8-DEC-E` 实现：
  - `A8-W7 Propulsion Tuning Consumer`：通过。显式发动机调参现在会在计算运行时推力前消费
    `AircraftDamageState.propulsion_integrity`，关闭调参绕过损伤缩放的风险，同时没有加入直接击杀规则。
    证据说明：
    [a8_w7_propulsion_tuning_consumer_20260608.md](a8_w7_propulsion_tuning_consumer_20260608.md)。

## 2026-06-07 验收检查

已运行命令：

```bash
git diff --check -- docs/task/air_combat/a8_damage_effect_chain src/components/combat/damage.h src/content/unit_definition_loader.cpp src/models/weapons/detail/default_effects_component_damage_detail.inc src/models/weapons/detail/default_effects_system_effect_detail.inc tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py tests/runtime/air_combat/test_weapon_guidance_realism_guards.py tests/runtime/air_combat/weapon_guidance_realism
cmake --build build-workshop -j 8
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
```

结果：

- diff 空白检查：通过。
- 编译：通过。
- 武器/引信/损伤链守卫：`164 passed, 1 skipped`。
- 1v1 发射链测试：`11 passed`。
- 被跳过的用例是有意保留项：它等待公开射击记录字段和公开具体损伤类型词表。

## 2026-06-07 第二轮验收检查

已运行命令：

```bash
git diff --check -- docs/task/air_combat/a8_damage_effect_chain src/runtime/contracts/engagement_contracts.h src/interfaces/python/bindings_runtime.cpp src/models/weapons/detail/default_effects_component_damage_detail.inc src/models/weapons/detail/default_effects_system_effect_detail.inc tests/runtime/air_combat/weapon_guidance_realism/a8_mq9_aim120.py tests/runtime/air_combat/weapon_guidance_realism/component_damage.py
cmake --build build-workshop -j 8
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
python -m pytest -q tests/runtime/engagement/test_engagement_contract_shape.py
```

结果：

- diff 空白检查：通过。
- 编译：通过。
- 武器/引信/损伤链守卫：`165 passed`。
- 1v1 发射链测试：`11 passed`。
- 交战记录合同形状测试：`4 passed`。

## 2026-06-08 第三轮验收检查

已运行命令：

```bash
git diff --check -- src/systems/physics/propulsion_system.h tests/runtime/air_combat/weapon_guidance_realism/a8_mq9_aim120.py docs/task/air_combat/a8_damage_effect_chain
cmake --build build-workshop --target ef_py -j2
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_a8_engine_damage_scales_actual_thrust_with_explicit_engine_tuning
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_flight_dynamics_tuning_runtime.py
python -m pytest -q tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
python -m pytest -q tests/runtime/air_combat/test_flight_dynamics_realism_guards.py
```

结果：

- diff 空白检查：通过。
- 编译：通过。
- 调参发动机动力消费方聚焦测试：`1 passed`。
- 武器/引信/损伤链守卫：`166 passed, 239 subtests passed`。
- 飞行动力学调参运行时：`3 passed`。
- 1v1 发射链测试：`11 passed, 2 subtests passed`。
- 飞行动力学真实感守卫：`4 passed`。

## 成熟度矩阵

| 区域 | Accepted | Active | Held | Deferred |
| --- | --- | --- | --- | --- |
| 引信和起爆事件路径 | 近炸静默消失问题近期已修复，并有运行时测试保护。 | A8 必须把已记录事件作为链路第一段。 | 确定性引信真值未验收。 | 真实引信校准。 |
| 结构化部件和飞机损伤状态 | 已有命中盒、部件、分组、飞机状态字段和公开逐部件故障类型行。 | A8 必须保持解释非权威，并绑定在射击记录上。 | 只有完整度/能力数字仍不够。 | 大范围目标族数据校准。 |
| 战斗部作用到部位损伤 | 当前效果代码已估算破片/爆压/切割类载荷，并公开模拟部件故障类型。 | A8 必须通过测试保持 synthetic 词表可审计。 | 当前数值不是 AIM-120C 真值。 | 发布级战斗部建模。 |
| 部位损伤到飞机行为 | 推进损伤现在即使在显式发动机调参启用时也能进入运行时推力；燃油、传感器、火灾和粗略飞行限制也消费部分损伤状态。 | A8 下一步应实现一个翼面/操纵气动或轴向控制响应。 | 气动/操纵后果在力和力矩上仍太间接。 | 完整飞机专用飞控律校准。 |
| MQ-9 / AIM-120C 验证 | 测试夹具和配置存在。 | A8 应构建尾部、翼面/操纵、燃油/火灾、传感器/数据链固定样例。 | 一次 live smoke 结果不足以验收。 | 击杀概率或真实世界杀伤声明。 |

## 已整合的只读发现

引信和效果结构：

- 当前起爆路径已经记录引信几何，并调用效果模型。最合适的第一实现切口在默认效果路径内部：
  也就是直接命中或近炸投影已经选出命中盒/部件，并且机制载荷已经存在的那一层。
- 直接代码区域是“机制载荷到部件结果”层：
  `sample_default_effects_component_failure`、`apply_component_damage_state` 和
  `apply_component_failure_impulse` 应先产生具体部件故障结果，再扩大到物理消费方。
- 当前效果已经估算破片能量、破片密度、穿透余量、爆压/冲量和切割余量。缺口不是没有机制输入，
  而是这些值大多被折叠成失效概率和完整度数字。

损伤到飞行结构：

- 当前桥接不是单个飞行判决。损伤进入 `AircraftDamageState` 后，每帧再进入
  `FlightModel`、`Propulsion`、`Mass`、`Sensor` 和 `PlatformDamageState`。
- 动力是现有最强消费方，因为推进损伤可以降低推力，再进入受力计算。`A8-W7` 已关闭窄的调参绕过风险：
  显式发动机调参会在运行时推力计算前接受同一推进损伤缩放。
- 气动和默认控制模型是主要弱点。它们还没有充分把结构破损、舵面破损、左右不对称或轴向控制能力下降
  表现成力和力矩。
- 现有 `flight_control_kill`、`propulsion_kill` 和 forced-landing 字段应保持报告/状态输出，
  不应变成绕过飞行仿真的新捷径。

MQ-9 / AIM-120C 验证结构：

- 优先验证组合是 F-16C 发射 AIM-120C-7，MQ-9 作为无武装结构化目标。MQ-9 有发动机、
  螺旋桨、燃油、数据链、航电、副翼/襟翼和翼梁等有用部件，但其脆弱性仍是 synthetic、
  non-authoritative。
- 现有测试分别覆盖发射链和许多效果细节，但还没有一个固定 live AIM-120C-to-MQ-9 测试同时验证
  发射、效果、部件损伤、下游响应和结果。
- 固定验证样例应包括：近距完整链、较远距离可审计链、右副翼/襟翼控制损伤、数据链或电源分配任务损伤、
  以及显式非权威检查。

## 初始链路设计

```text
1. 引信结果和起爆几何
2. 起爆点上的战斗部作用
3. 飞机部位暴露
4. 具体部位损伤类型
5. 功能变化
6. 已有飞机系统消费该变化
7. 观察后续飞机行为
```

通俗样例：

- 尾部命中：发动机、供油控制或螺旋桨损伤通过动力系统降低推力，并可能增加火灾或燃油风险。
- 翼面/操纵命中：翼梁、副翼、襟翼或作动器损伤通过飞行路径改变控制能力、不对称、阻力、升力或结构余量。
- 燃油命中：油箱损伤导致漏油、质量变化、火灾风险；如果供油路径受损，则影响供油。
- 机鼻或机身电子设备命中：传感器、航电或数据链损伤可以造成任务失败，不要求飞机一定坠毁。

## 证据链接

- 引信和战斗损伤更新：
  [damage_system.h](../../../../src/systems/combat/damage_system.h)
- 损伤部件/状态定义：
  [damage.h](../../../../src/components/combat/damage.h)
- 默认武器效果：
  [default_effects_model.cpp](../../../../src/models/weapons/default_effects_model.cpp)
- 气动消费方：
  [aerodynamics_system.h](../../../../src/systems/physics/aerodynamics_system.h)
- 动力消费方：
  [propulsion_system.h](../../../../src/systems/physics/propulsion_system.h)
- MQ-9 结构化损伤配置：
  [mq9_reaper.json](../../../../examples/config/database/aircraft/units/mq9_reaper.json)
- AIM-120C 武器配置：
  [aim_120c.json](../../../../examples/config/database/weapons/air_to_air/aim_120c.json)
- 当前回归入口：
  [test_weapon_guidance_realism_guards.py](../../../../tests/runtime/air_combat/test_weapon_guidance_realism_guards.py)

## 残余登记

立即：

- 继续把 `A8-DEC-E` 做成维护中的消费方工作，而不是直接击杀规则：动力调参上限已经落地；
  下一段是一个翼面/操纵气动或轴向控制响应。
- 消费方改动后必须重跑 MQ-9/AIM-120C 固定样例；当前样例证明的是可审计损伤和非权威边界，
  不是最终飞行响应保真度。

Held：

- 结构化飞机的直接坠毁或直接消失行为。
- 只因为目标是 MQ-9 就更容易杀伤的特例。
- 绕过已有飞行和动力行为的“还能不能飞”判决。

Deferred：

- 校准后的破片分布、爆压载荷和目标脆弱性。
- 真实世界击杀概率。
- 确定性引信真值。
- 完整多平台飞机损伤数据集。

## 下一步推荐顺序

1. 接入一个翼面/操纵气动或轴向控制效果。
2. 用新增消费方行为重跑 MQ-9/AIM-120C 固定验证。
3. 决定 `A8-DEC-E` accepted 或 held，再同步 A8 最终验收。

## 禁止结论

- 这些是已验收切片，不是整个 A8 完成。
- A8 不证明 AIM-120C 真实杀伤力。
- A8 不释放击杀概率或确定性引信权威。
- A8 不用直接击杀规则替代飞行模型。
