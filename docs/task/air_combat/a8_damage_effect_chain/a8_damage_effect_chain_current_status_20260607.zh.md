# A8 损伤效果链当前状态

状态：`2026-06-08` 第七轮实现检查点。A8 已有有边界工作面，并已整合当前会话
结构发现；有限动力消费方、翼面/操纵气动消费方、固定燃油泄漏/质量响应证据、固定数据链
任务/传感器后果证据，以及窄的地面接触生命周期表面已经落地。

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
- 已验收第二段 `A8-DEC-E` 实现：
  - `A8-W8 Wing/Control Aero Consumer`：通过。结构、液压、滚转/俯仰/偏航操纵能力和操纵不对称
    现在会影响维护中的气动系数和力矩；没有加入直接坠毁规则，也没有加入独立飞行判决。
    主线程验收时也根据 `A8-W9` 侦察建议补了一条固定 MQ-9/AIM-120C 右副翼响应检查。
    证据说明：
    [a8_w8_aero_consumer_20260608.md](a8_w8_aero_consumer_20260608.md)。
- 已验收第五轮工作：
  - `A8-W11 Fuel/Fire/Mass Consumer Evidence`：通过。它增加固定中心油箱
    MQ-9/AIM-120C-like 命中，记录燃油泄漏和火源模式，保持即时损伤报告非权威，
    并证明后续燃油和质量会通过维护中的运行时系统下降。
  - `A8-W12 Ground-Impact Lifecycle Scout`：部分通过，只作为只读证据验收。它确认当前
    触地路径可以发现地面接触，但可观察的坠毁/残骸/碎片生命周期还不是维护中的公开表面，
    不能用直接删除替代。
- 已验收第一段 `A8-DEC-H` 实现：
  - `A8-W13 Ground-Impact Lifecycle Writer`：通过。既有 subagent 没有返回可用的新包，
    所以主线程接手实现了窄 writer 切片。地面接触现在通过公开调试状态区分无接触、已着陆机体
    和坠毁残骸。严重撞击不再把 `Health.current_hp = 0.0` 当成唯一可见结果，测试也保护
    安全/低速接触不会变成坠毁残骸。
  - `A8-W14 Sensor/Data-Link/Fire Consequence Scout`：第六轮没有可验收侦察包被整合；
    下方第七轮 W15/W16 已接替这个传感器/数据链和火灾后果缺口。
- 已验收第七轮工作：
  - `A8-W15 Sensor/Data-Link Consequence Writer`：通过。它增加固定
    MQ-9/AIM-120C-like 数据链收发机命中，记录 `data_loss`，保持即时损伤报告非权威，
    并证明后续任务/传感器/生存能力以及航电/乘员任务/导航状态会通过维护中的平台状态下降。
  - `A8-W16 Broader Fire Consequence Scout`：只读证据通过。它给出下一段 test-only
    writer 路径：左翼油箱火势增长和尾部发动机火区播种；同时提醒，不应在没有可燃暴露时
    断言纯发动机火区会自行增长。

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

## 2026-06-08 第四轮验收检查

已运行命令：

```bash
clang-format --dry-run -Werror src/systems/physics/aerodynamics_system.h
./.venv/bin/python -m ruff check tests/runtime/air_combat/weapon_guidance_realism/a8_aero_consumer.py tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
cmake --build build-workshop --target ef_py -j2
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k 'a8_mq9_aim120_right_aileron_damage_changes_roll_response_through_aero_path or wing_control_damage_reaches_neutral_aero_response'
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k 'right_aileron_damage_long_run_reaches_ground_response or right_aileron_damage_changes_roll_response_through_aero_path'
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_flight_dynamics_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_flight_dynamics_tuning_runtime.py
python -m pytest -q tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
```

结果：

- 触碰 C++ 文件 clang-format 门：通过。
- 聚焦 Python lint：通过。
- 编译：通过。
- W8 气动/MQ-9 短时响应聚焦检查：`2 passed, 166 deselected`。
- W8 MQ-9 长时程响应聚焦检查：`2 passed, 167 deselected`。
- 武器/引信/损伤链守卫：`169 passed`。
- 飞行动力学真实感守卫：`4 passed`。
- 飞行动力学调参运行时：`3 passed`。
- 1v1 发射链测试：`11 passed`。

## 2026-06-08 第五轮验收检查

已运行命令：

```bash
git diff --check -- docs/task/air_combat/a8_damage_effect_chain/a8_damage_effect_chain_dispatch_queue_20260607.md tests/runtime/air_combat/weapon_guidance_realism/a8_mq9_aim120.py
./.venv/bin/python -m ruff check tests/runtime/air_combat/weapon_guidance_realism/a8_mq9_aim120.py
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k 'center_fuel_hit_continues_into_leak_and_mass_runtime_path'
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
```

结果：

- diff 空白检查：通过。
- 聚焦 Python lint：通过。
- 固定中心油箱泄漏/质量运行时检查：`1 passed, 169 deselected`。
- 武器/引信/损伤链守卫：`170 passed`。
- `A8-W12` 是只读包，没有文件改动；它的验收只代表下一轮实现包的证据成立，不代表实现已验收。

## 2026-06-08 第六轮验收检查

已运行命令：

```bash
git diff --check -- src/components/systems/logistics.h src/systems/physics/ground_contact_system.h src/core/engine/simulation_kernel.h src/core/engine/simulation_kernel_observation_api.cpp src/interfaces/python/bindings_core.cpp tests/runtime/air_combat/weapon_guidance_realism/a8_mq9_aim120.py
./.venv/bin/python -m ruff check tests/runtime/air_combat/weapon_guidance_realism/a8_mq9_aim120.py
cmake --build build-workshop --target ef_py -j2
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k 'ground_contact_lifecycle'
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
```

结果：

- diff 空白检查：通过。
- 聚焦 Python lint：通过。
- `ef_py` 编译：通过。
- 地面接触生命周期聚焦检查：`3 passed, 170 deselected`。
- 武器/引信/损伤链守卫：`173 passed`。

## 2026-06-08 第七轮验收检查

已运行命令：

```bash
git diff --check -- docs/task/air_combat tests/runtime/air_combat/weapon_guidance_realism/a8_sensor_datalink_consumer.py tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
./.venv/bin/python -m ruff check tests/runtime/air_combat/weapon_guidance_realism/a8_sensor_datalink_consumer.py tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -k 'data_link_hit_continues_into_platform_mission_sensor_runtime_path'
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
```

结果：

- 文档/测试 diff 空白检查：通过。
- 聚焦 Python lint：通过。
- 数据链任务/传感器后果检查：`1 passed, 173 deselected`。
- 武器/引信/损伤链守卫：`174 passed`。

## 成熟度矩阵

| 区域 | Accepted | Active | Held | Deferred |
| --- | --- | --- | --- | --- |
| 引信和起爆事件路径 | 近炸静默消失问题近期已修复，并有运行时测试保护。 | A8 必须把已记录事件作为链路第一段。 | 确定性引信真值未验收。 | 真实引信校准。 |
| 结构化部件和飞机损伤状态 | 已有命中盒、部件、分组、飞机状态字段和公开逐部件故障类型行。 | A8 必须保持解释非权威，并绑定在射击记录上。 | 只有完整度/能力数字仍不够。 | 大范围目标族数据校准。 |
| 战斗部作用到部位损伤 | 当前效果代码已估算破片/爆压/切割类载荷，并公开模拟部件故障类型。 | A8 必须通过测试保持 synthetic 词表可审计。 | 当前数值不是 AIM-120C 真值。 | 发布级战斗部建模。 |
| 部位损伤到飞机行为 | 推进损伤即使在显式发动机调参启用时也能进入运行时推力；翼面/操纵损伤现在能进入有限气动系数、力矩和轴向控制能力；固定油箱损伤能进入泄漏/质量运行时响应；固定数据链损伤能进入任务/传感器运行时响应。 | A8 后续只能通过维护中的系统继续扩大消费方覆盖。 | 当前气动响应仍是 synthetic 且偏标量化；燃油样例证明的是泄漏/质量和火源标记，不是完整火灾蔓延；数据链样例证明的是平台状态后果，不是主动报文流量；左右符号保真和飞机专用飞控律未验收。 | 完整飞机专用飞控律校准和完整火灾生命周期校准。 |
| 地面接触生命周期 | 安全接触和严重接触现在有公开调试生命周期状态；构造的严重撞击可以观察为 `crashed_wreck`，实体仍保持 active。 | A8 后续应决定是否还需要 debris/residue 实体，而不只是调试生命周期状态。 | 该生命周期不会让武器命中更早坠毁，也不生成物理碎片。 | 完整残骸/残留对象模型。 |
| MQ-9 / AIM-120C 验证 | 已有测试夹具、固定部件样例、非权威检查、固定右副翼气动响应检查、300 秒右副翼长时程检查、固定中心油箱泄漏/质量检查、固定数据链任务/传感器后果检查和地面接触生命周期检查。 | A8 应继续补尾部动力和更完整火灾覆盖。 | 一次 live smoke 结果不足以验收；燃油泄漏、数据链后果或坠毁残骸生命周期测试也不是真实击杀证明。 | 击杀概率或真实世界杀伤声明。 |

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
- 气动系统现在会把有限结构破损、操纵通路破损和不对称字段消费成升力/阻力缩放以及滚转/俯仰/偏航力矩。
  这是工程响应路径，不是已校准的飞机专用飞控律。
- 现有 `flight_control_kill`、`propulsion_kill` 和 forced-landing 字段应保持报告/状态输出，
  不应变成绕过飞行仿真的新捷径。
- 当前触地系统会记录地形高度和触地状态。`A8-W13` 已改变越野/严重撞击路径，让起落架坍塌和
  严重撞击发布地面接触生命周期状态，而不是把 `Health=0` 当成唯一可观察路径。
- 目前还没有公开残留对象类型来表示碎片。把武器损伤报告直接复用于地面撞击，会把“武器效果”
  和“后续坠毁”混在同一类事件里。

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
- 燃油命中：油箱损伤导致漏油、质量变化，并标记火源；更完整的火灾蔓延和供油中断样例仍需单独证据。
- 机鼻或机身电子设备命中：传感器、航电或数据链损伤可以降低任务完成能力，不要求飞机一定坠毁。
  固定 W15 样例现在通过平台任务/传感器状态证明这点，而不是通过主动报文流量证明。

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

- 继续把 `A8-DEC-E` 做成维护中的消费方工作，而不是直接击杀规则：动力调参、一段翼面/操纵气动响应、
  一个固定燃油泄漏/质量响应和一个固定数据链任务/传感器响应已经落地。
- 每新增一个消费方切片后，继续扩展 MQ-9/AIM-120C 固定下游检查，尤其是尾部动力和更完整火灾生命周期。
- 保持新的地面接触生命周期路径足够窄：它覆盖已着陆机体和坠毁残骸可观察性，不覆盖碎片或完整残骸对象模型。

Held：

- 结构化飞机的直接坠毁或直接消失行为。
- 只因为目标是 MQ-9 就更容易杀伤的特例。
- 绕过已有飞行和动力行为的“还能不能飞”判决。
- 绕过维护中撞击/坠毁路径的直接触地击杀逻辑。

Deferred：

- 校准后的破片分布、爆压载荷和目标脆弱性。
- 真实世界击杀概率。
- 确定性引信真值。
- 完整多平台飞机损伤数据集。

## 下一步推荐顺序

1. 补充更完整火灾行为的下游响应检查，优先使用 W16 给出的左翼油箱和尾部发动机火区证据。
2. 决定 debris/residue 是否需要一等对象模型，或当前 `landed_airframe/crashed_wreck` 生命周期状态
   对本 A8 切片是否足够。
3. 决定当前有限 `A8-DEC-E` 消费方集合是 accepted 还是仍需继续 held 等待更多维护消费方。
4. 只有在残余明确 hold 或 closed 后，才同步 A8 最终验收。

## 禁止结论

- 这些是已验收切片，不是整个 A8 完成。
- A8 不证明 AIM-120C 真实杀伤力。
- A8 不释放击杀概率或确定性引信权威。
- A8 不用直接击杀规则替代飞行模型。
