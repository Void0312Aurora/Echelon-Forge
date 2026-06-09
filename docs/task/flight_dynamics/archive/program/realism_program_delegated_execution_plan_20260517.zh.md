# 真实化主线委派执行计划

状态：`2026-05-17` 主线程收敛版。

关联文档：

- [真实化主线与关联子项目当前状态](realism_program_current_status_20260517.zh.md)
- [真实化 P1 任务总表](realism_program_p1_taskboard_20260517.zh.md)
- [代码质量审查](code_quality_review_realism_wave_20260517.zh.md)
- [飞行动力学 P1 实施包](../flight/flight_dynamics_realism_p1_implementation_package_20260517.zh.md)
- [传感器/态势 P1 实施包](../sensor_situation/sensor_situation_realism_p1_implementation_package_20260517.zh.md)
- [武器/制导 P1 实施包](../weapon_guidance/weapon_guidance_realism_p1_implementation_package_20260517.zh.md)
- [C2 指挥链待解决问题分析](../c2_command_chain/c2_command_chain_unresolved_issues_20260517.zh.md)

本文档定位：

- 把 `flight / sensor_situation / weapon_guidance / c2_command_chain / naval` 当前已形成的方向性文档，收敛成一份可以继续委派执行的主线程计划。
- 明确哪些任务必须先由主线程收口，哪些任务适合交给 subagent / worker 并行推进。
- 给下一轮实现提供统一的 `lane`、依赖矩阵和阶段验收顺序，避免再次按学科各自单飞。

补充口径：

1. 当前总阶段与主阻塞判断，应优先以
   [真实化主线收束计划](realism_program_convergence_plan_20260517.zh.md)
   和
   [真实化主线与关联子项目当前状态](realism_program_current_status_20260517.zh.md)
   为准。
2. 本文更适合作为“如何分发/收束 lane”的执行文档，而不是单独承担最新总阶段说明。

---

## 零、本轮已回收成果

`2026-05-17` 这轮主线程已经按两批委派回收了第一轮 shared integration 收口，且完成了主线程重编译与集成验收。

### 0.1 第一批已落地实现

1. `Lane A / A1`：
   - `UnitDefinition / loader / factory` 已补入 `AeroTuning / EngineTuning / StallState /
     Sensor defaults / MissileTuningDefinition`
2. `Lane B / B2`：
   - `Propulsion` 已成为 `Force / Logistics / Instrument / Observation` 的统一事实源
3. `Lane C / C3`：
   - missile shared launch runtime 已进入正式发射链，不再只靠 guidance lazy init
4. `Lane D / D1`：
   - naval `screen-hold` 已补 direct-recovery -> hold handoff 收口

### 0.2 第二批已落地实现

1. `Lane D / MissionCommand contract`：
   - `bridge.py` 已收口 profile 路由
   - `naval_profile.py` 已补关键 naval/recovery/formation/helo 字段 authoring
   - runtime / batch roundtrip 测试已补齐
2. `Lane D / DataLink QoS`：
   - 已补更强的 budget scaling / fanout / churn / counter reset 回归测试
3. `Lane C / weapon launch plumbing`：
   - `definition -> default_loadout -> selected station -> fire_missile()` 最小事实链已打通
   - `debug_get_missile_runtime_state()` 已补质量、sensor、guidance 关键字段
4. `Lane B / propulsion tests`：
   - 已补 `Propulsion -> Instrument / Logistics / Observation` 同源合同测试

### 0.3 主线程已完成的验收

1. `cmake --build build-workshop --target ef_core -j4` 当前通过
2. `cmake --build build --target ef_py -j4` 与
   `cmake --build build-workshop --target ef_py -j4` 当前通过
2. 主线程统一验收当前为：
   - `80 passed, 2 subtests passed`
3. 计划制定时剩余的唯一行为红点
   - [tests/runtime/air_combat/test_air_combat_1v1_fixture.py](../../../../tests/runtime/air_combat/test_air_combat_1v1_fixture.py)
   - `test_loader_fixture_exposes_hostile_contact_and_weapon_state`
4. 上述红点已由主线程确认并收口：
   - 根因是 fixture 在第一次看到 raw contact 时就提前停止，直接把 `Tentative / Unknown`
     contact 当成 hostile confirmed track 断言
   - 当前已按 confirmed hostile track 语义修正夹具等待条件
5. 本轮 `Lane A` 小切口已回收：
   - `sensor` 默认值来源去重
   - missile `Vec3 -> Math::Vector3` 去重
6. 本轮主线程针对结构收口补充回归：
   - `tests/runtime/air_combat/test_sensor_situation_realism_p0.py`
   - `tests/runtime/core/test_kernel_observation_sanity.py`
   - `tests/runtime/air_combat/test_weapon_guidance_realism_guards.py`
   - `tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py`
   - `tests/architecture/runtime_facade/test_layering.py`
   - 当前结果：`47 passed`
7. 本轮新增 lane 收口回归：
   - `tests/architecture/runtime_facade/test_layering.py`
   - `tests/world_batch/test_world_batch_vec_env.py`
   - `tests/runtime/link/test_command_link_qos.py`
   - `tests/runtime/mission/test_mission_command_roe_fields.py`
   - `tests/runtime/air_combat/test_flight_dynamics_tuning_runtime.py`
   - 当前结果：`51 passed`
8. `Lane B/C/D` 这一轮实收增量：
   - `Lane B`: `aerodynamics_system.h` 已落地 stateful stall memory，且 tuned runtime test 已锁住
   - `Lane C`: `launch envelope enforcement` 已前置到 ammo/cooldown/VLS/munition 消耗之前
   - `Lane D`: `MissionCommand` 的 ROE/authority/assigned-target/authorization 字段
     已经由 `CommandLink QoS` 契约测试锁死

---

## 一、总判断

当前真实化主线不适合继续按“飞行动力学 / 传感器 / 武器 / 海战 / C2”五条线完全平行推进。

补充阶段判断：

1. 主线整体仍处于 `P1-A 集成收尾`。
2. `flight`、`sensor`、`naval` 与 `C2` 的关键守门面已经基本收口，当前更适合转入维护态。
3. 当前主线重点已从“修基础红点”转向“结构债减载与有限的更深建模”。
4. 因此本计划的重点应从“继续铺更多 lane”改成“先收束、再有限并行”。

原因不是这些方向不重要，而是它们已经共享三类高重叠前置面：

1. `schema -> loader -> factory` 参数注入链
2. `runtime observation / Python binding / debug view` 暴露面
3. `Detection -> Track -> Report -> MissionCommand / ROE / Weapon` 的共享语义链

如果在这些共享前置面未收口前直接把更深建模分发出去，会出现：

1. worker 同时改同一批 `unit_definition / bindings / tests/runtime`
2. 各方向各自扩口 debug/observation，合同越改越散
3. 上层 `naval / air_combat / leader` 场景继续建立在漂移的 shared semantics 上

因此，下一轮应采用：

1. `主线程先收口 shared integration`
2. `优先把 weapon 末段真实性和深层建模推进`
3. `再按 lane 有限并行推进 deeper modeling`
4. `naval` 作为高价值场景验收面并入 `C2/runtime` 维护态，而不是独立扩功能主线

---

## 二、主线程先做什么

以下任务不建议一开始就分散给多个实现 worker，而应由主线程先冻结边界、确定合同和写集。

### 2.1 Shared Schema / Loader / Factory 收口

覆盖方向：

- flight：`AeroTuning / EngineTuning / StallState`
- sensor：`Sensor` 新字段与默认值
- weapon：`MissileTuning`、导弹发射初始化参数

核心文件面：

- [unit_definition.h](../../../../src/content/unit_definition.h)
- [unit_definition_loader.cpp](../../../../src/content/unit_definition_loader.cpp)
- [default_unit_factory.h](../../../../src/models/core/default_unit_factory.h)

主线程目标：

1. 明确每条线在 `UnitDefinition` 中的最小字段集合
2. 明确缺省值回退策略
3. 冻结“哪些 tuning 进入数据库、哪些继续留在代码默认值”

### 2.2 Shared Observation / Binding / Debug Contract 收口

覆盖方向：

- flight：debug view、推进/失速运行时量
- sensor：`Detection / Track / CommPacket` 新字段
- weapon：missile runtime debug/state view

核心文件面：

- [simulation_kernel_observation_api.cpp](../../../../src/core/engine/simulation_kernel_observation_api.cpp)
- [bindings_core.cpp](../../../../src/interfaces/python/bindings_core.cpp)
- [bindings_command.cpp](../../../../src/interfaces/python/bindings_command.cpp)
- [observation.h](../../../../src/core/interfaces/observation.h)

主线程目标：

1. 冻结哪些字段进入主 observation
2. 哪些字段只进入 debug/instrument/Python surface
3. 保持各方向的 runtime guards 能用统一观测面验收

本轮补充判断：

1. `RuntimeFacade.runtime()` 暂不适合直接从 C++ binding 删除
2. 更合适的下一刀是在 Python 侧把 raw runtime/world 穿透重新收回 adapter
3. `leader_world_batch_runtime.py` 应与 `world_batch_vec_env.py` 一起作为同一批 adapter 收口任务处理

### 2.3 Shared Runtime Semantics 收口

覆盖方向：

- sensor/weapon：`Detection -> Track -> Report`
- naval/C2：`MissionCommand -> behavior_runtime -> ship runtime`
- flight：推进状态成为统一事实源

主线程需要先明确：

1. `shared track != local contact` 继续是主合同
2. `Track status / source / quality / classification / iff` 的语义主口径
3. `MissionCommand` 的 Python/C++ 双维护路径中哪些字段必须有 roundtrip contract
4. `Propulsion` 是否成为推力/油耗/仪表唯一事实源

---

## 三、推荐的执行 Lane

下一轮建议拆成 4 条 lane + 1 条 sidecar，其中主线程不再继续把 `ScenarioLoader`
作为第一优先级深拆对象。

当前冻结执行口径：

1. `ScenarioLoader` 进入兼容维护态
   - 当前只接受阻塞集成/回归的必要修补
   - 不再把继续拆 owner 当作主线程默认任务
2. 主线程转为 lane orchestration
   - 负责冻结写集、分发任务、回收结果、做集成验收
3. 并行主线改为：
   - `Lane A sidecar`: `RuntimeFacade` adapter 收尾
   - `Lane B`: Flight 建模深化
   - `Lane C`: Weapon 建模深化
   - `Lane D`: C2 / CommandLink 建模深化

### 3.1 Lane A：Shared Contract / Integration

这是全主线优先级最高的一条 lane。

范围：

1. schema / loader / factory 接线
2. observation / binding / debug 暴露
3. runtime shared semantics 与 roundtrip contract
4. realism runtime tests 的基础设施收口

推荐任务：

1. `A1 schema/factory integration`
   - `unit_definition.h`
   - `unit_definition_loader.cpp`
   - `default_unit_factory.h`
2. `A2 observation/binding integration`
   - `simulation_kernel_observation_api.cpp`
   - `bindings_core.cpp`
   - `bindings_command.cpp`
3. `A3 runtime semantic contracts`
   - `track_manager_system.h`
   - `data_link_system.h`
   - `simulation_kernel_weapon_api.cpp`
   - `mission_command_codec` / Python bridge
4. `A4 runtime test infrastructure`
   - `tests/runtime/*realism*`
   - `python/testing/runtime.py`

本轮已实收的低风险子任务：

1. `A1a sensor default source dedupe`
   - 统一为 `unit_definition` / loader 默认基线 + factory preset 覆盖
2. `A1b missile math Vec3 dedupe`
   - 去掉 `missile_guidance_math.h` 独立三维向量类型
3. `A2a runtime facade adapter tightening`
   - `world_batch_vec_env.py` / `leader_world_batch_runtime.py`
     已先收回一轮 Python 主线 raw world/runtime 业务穿透
   - `tests/architecture/runtime_facade/test_layering.py` 已补层级守卫
4. `A2b ScenarioLoader state-shell extraction`
   - `core.py` + `runtime_state.py` 已形成第一阶段状态壳
   - execution episode state 的 route/mission/reward/runtime cache 同步合同已补平
5. `A2c ScenarioLoader scripted-opponent collaborator extraction`
   - build/reset/step owner 已下沉到 `behavior_runtime/scripted_opponents.py`
   - `ScenarioLoader` 保留薄代理与兼容访问面
   - scripted-opponent 相关 runtime/world-batch 回归已补跑为绿
6. `A2c-2 ScenarioLoader command-chain owner extraction`
   - `_leader_phase_manager` 与 `_naval_screen_*` 运行态 owner
     已下沉到 `behavior_runtime/command_chain_owner.py`
   - `command_chain.py` / `loading.py` 已切换为通过 collaborator owner 管理生命周期
   - `ScenarioLoader` 仍保留旧属性代理，兼容 `leader_env` 等外部 bridge 注入路径
   - 定向与扩展回归当前为绿：`57 passed`
7. `A2c-3 ScenarioLoader behavior-phase owner extraction`
   - `post_waypoint_transition / mission_phase_name / _approach_prev_*`
     已下沉到 `behavior_runtime/behavior_phase_owner.py`
   - `runtime_state.py` 已补统一镜像视图，保持 execution episode state 的 roundtrip 合同
   - `ScenarioLoader` 继续保留旧字段代理与 `_state_shell` 兼容可见性
   - 相关回归当前为绿：`57 passed`

建议作为下一轮继续委派的 `Lane A` 子任务：

1. `A2a-1 runtime facade adapter tightening` 收尾
   - 继续压缩 `batch_runtime` / raw runtime 作为维护接口的使用面
   - 保持 `tests/architecture/runtime_facade/test_layering.py` 为守门线
2. `A2b-1 ScenarioLoader state-shell extraction` 收尾
   - 保持 `runtime_state.py` 作为 execution episode state 的单一同步面
   - 避免 mission/route/post-transition/runtime cache 再回流到 `core.py`
3. `A2c-1 ScenarioLoader collaborator extraction` 继续下沉
   - behavior-phase owner 第一阶段已落地
   - 下一刀改为 `core.py` compat facade 减载与更深协作者切面，而不是重复 scripted-opponent / command-chain / behavior-phase 第一阶段
   - 保持 `gym_envs/scenario_loader/behavior_runtime/*` 为主要写集

验收测试：

1. [test_sensor_situation_realism_p0.py](../../../../tests/runtime/air_combat/test_sensor_situation_realism_p0.py)
2. [test_kernel_observation_sanity.py](../../../../tests/runtime/core/test_kernel_observation_sanity.py)
3. [test_bindings_command_surface.py](../../../../tests/runtime/bindings/test_bindings_command_surface.py)
4. [test_weapon_guidance_realism_guards.py](../../../../tests/runtime/air_combat/test_weapon_guidance_realism_guards.py)
5. [test_flight_dynamics_realism_guards.py](../../../../tests/runtime/air_combat/test_flight_dynamics_realism_guards.py)

### 3.2 Lane B：Flight Dynamics

这条 lane 仅在 `Lane A` 冻结 schema / binding / test contract 后再正式扩。

当前冻结补充：

1. `flight` 当前更接近 `P1-A` 后半段，不再是主线程默认阻塞面。
2. `sensor/naval` 当前已进入维护态。
3. 只接受 blocker 修补、合同收口和 shared contract 相关回归。

推荐拆分：

1. `B1` 数据挂载链路
2. `B2` 推进状态统一事实源
3. `B3` Mach/compressibility 与失速语义深化
4. `B4` debug/test 收口
5. `B5` FBW/控制律与高 AoA 恢复接口

推荐文件边界：

- [flight_dynamics_tuning.h](../../../../src/components/physics/flight_dynamics_tuning.h)
- [propulsion_system.h](../../../../src/systems/physics/propulsion_system.h)
- [aero_state_system.h](../../../../src/systems/physics/aero_state_system.h)
- [aerodynamics_system.h](../../../../src/systems/physics/aerodynamics_system.h)
- [logistics_system.h](../../../../src/systems/systems/logistics_system.h)
- [instrument_system.h](../../../../src/systems/physics/instrument_system.h)
- [default_control_model.cpp](../../../../src/models/air/default_control_model.cpp)

验收测试：

1. [test_flight_dynamics_p0_runtime_guards.py](../../../../tests/runtime/air_combat/test_flight_dynamics_p0_runtime_guards.py)
2. [test_flight_dynamics_realism_guards.py](../../../../tests/runtime/air_combat/test_flight_dynamics_realism_guards.py)
3. [test_flight_dynamics_tuning_runtime.py](../../../../tests/runtime/air_combat/test_flight_dynamics_tuning_runtime.py)

### 3.3 Lane C：Sensor + Weapon Modeling

这条 lane 共享同一条 `Detection/Track/Report/Observation/Binding` 主干，因此建议放在一组 program lane 下，而不是完全拆开。

当前冻结补充：

1. `sensor` 当前已收口到维护态。
2. `weapon` 仍是本轮最值得继续推进的深层方向。
3. `Lane C` 的第一优先级是 weapon 末段真实性、truth shortcut 收紧和更深建模。

#### C1 Sensor Shared Integration 后续

范围：

1. `Sensor` 默认值与数据库接线
2. `Track status/source/quality/confidence` 收紧
3. `DataLink` shared semantics 稳定化

核心文件：

- [sensor.h](../../../../src/components/systems/sensor.h)
- [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp)
- [track_management.h](../../../../src/components/systems/track_management.h)
- [track_manager_system.h](../../../../src/systems/systems/track_manager_system.h)
- [data_link_system.h](../../../../src/systems/systems/data_link_system.h)

#### C2 Sensor Deeper Modeling

范围：

1. 更细的 `M-of-N / quality / coast-drop`
2. `Radar + DataLink` 最小融合
3. 保守环境/杂波/海杂波深化

验收测试：

1. [test_sensor_situation_realism_p0.py](../../../../tests/runtime/air_combat/test_sensor_situation_realism_p0.py)
2. [test_naval_sensor_realism_runtime.py](../../../../tests/runtime/naval/test_naval_sensor_realism_runtime.py)

#### C3 Weapon Shared Integration 后续

范围：

1. `MissileTuning` shared API
2. 发射初始化与质量语义收尾
3. missile runtime debug/state 暴露
4. guidance shared reference / observation 统一

本轮补充冻结：

1. 已完成的一刀只承诺
   `min_launch_range_m / max_launch_off_boresight_deg / lobl_required`
   的前置拒射合同。
2. 当前工作树里同时混有更大一批
   `definition-driven launch tuning / station-based launch selection / global tuning overlay`
   的扩写成果；行为回归当前为绿，但它们不再属于“最小包线拒射”。
3. 因此 `Lane C` 下一轮不应继续盲目加功能，而应把
   `launch definition resolution / tuning overlay / runtime assembly`
   拆成更清楚的子职责。

核心文件：

- [simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h)
- [simulation_kernel_weapon_api.cpp](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
- [default_effects_model.cpp](../../../../src/models/weapons/default_effects_model.cpp)

#### C4 Weapon Deeper Modeling

范围：

1. seeker type 分化
2. midcourse / datalink / activation
3. 3DoF 参数化
4. fuze / damage layering

验收测试：

1. [test_weapon_guidance_realism_guards.py](../../../../tests/runtime/air_combat/test_weapon_guidance_realism_guards.py)
2. [test_air_combat_1v1_fire_missile.py](../../../../tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py)

当前冻结建议：

1. `C4` 不作为本轮主线程默认下一刀。
2. 在 `sensor/naval` 维护态边界继续收紧前，不建议再开 `midcourse / seeker type / fuze / damage`
   的并行大展开。

### 3.4 Lane D：C2 / Runtime 收口

这条 lane 的原则是：

1. 先收 `runtime/C2` 主语义
2. 把 `naval` 作为高价值场景验收面并入
3. 暂缓更深的 naval tasking / relay / jamming / authority transfer

推荐顺序：

1. `D1 MissionCommand 字段 / codec / profile 对账`
2. `D2 DataLink QoS 压测与 budget scaling`
3. `D3 sensor/naval` 共享语义与海事守门回归联动复核（维护态）
4. `D4 CommandLink 最小 priority policy`
5. `D5 ROE / tasking 最小消息闭环原型`

补充说明：

1. `screen-hold` 当前不再作为稳定红点保留。
2. `naval` 当前更适合作为 `sensor/C2/runtime` 的高价值验收面，而不是独立扩功能入口。

核心文件：

- [naval_screen.py](../../../../gym_envs/scenario_loader/behavior_runtime/naval_screen.py)
- [command_chain.py](../../../../gym_envs/scenario_loader/behavior_runtime/command_chain.py)
- [mission_command.h](../../../../src/components/command/mission_command.h)
- [command_link_system.h](../../../../src/systems/systems/command_link_system.h)
- [data_link_system.h](../../../../src/systems/systems/data_link_system.h)
- Python `bridge/profile` 与 C++ `mission_command_codec`

验收测试：

1. [test_naval_screen_scenario.py](../../../../tests/runtime/naval/test_naval_screen_scenario.py)
2. [test_data_link_qos_runtime.py](../../../../tests/runtime/link/test_data_link_qos_runtime.py)
3. [test_command_link_qos.py](../../../../tests/runtime/link/test_command_link_qos.py)
4. [test_weapon_roe_runtime.py](../../../../tests/runtime/air_combat/test_weapon_roe_runtime.py)

---

## 四、推荐的委派方式

### 4.1 适合继续委派给 worker 的任务

以下任务写集相对清楚，适合继续通过 subagent/worker 分发：

1. `weapon` truth shortcut / seeker reject / fuze-damage 收敛
2. `MissionCommand` 字段/codec/profile 对账与缺口补测
3. `DataLink` 压测、budget scaling 与计数器补测
4. `RuntimeFacade / ScenarioLoader` compat 面减载收尾
5. `CommandLink` priority policy

### 4.2 更适合委派给 explorer/sidecar 的任务

以下任务更像对账、压力补测、合同整理，适合 explorer 或 sidecar worker：

1. `MissionCommand` 字段矩阵与 roundtrip contract
2. `DataLink` 压测设计与 budget scaling 补测
3. 现实性文档口径复核与阶段验收矩阵整理
4. `tests/runtime` 现实性守门测试的入口与 teardown 风险盘点

### 4.3 当前不建议立刻大规模并行的任务

以下任务当前写集重叠大、共享语义未钉牢，不建议同时交给多个实现 worker：

1. 同时改 `unit_definition_loader.cpp` + `default_unit_factory.h` + `bindings_core.cpp`
2. 同时改 `track_manager_system.h` + `data_link_system.h` + `simulation_kernel_observation_api.cpp`
3. 在 `shared contact/track` 合同未收稳前并行推进 relay、jamming、naval tasking doctrine
4. 在 missile shared runtime state 未收口前并行推进 seeker type + fuze + damage 全套深化
5. 在 `sensor/naval` 结构债务未继续收紧前，同时重新铺开 `flight` 与 `weapon` 深化

---

## 五、阶段顺序

推荐阶段顺序如下：

### Phase 0：主线程冻结 shared 边界

输出物：

1. schema 字段范围
2. observation/debug 暴露范围
3. shared runtime semantics 口径
4. realism runtime tests 最小入口

### Phase 1：Lane A 一轮收口

验收目标：

1. 三条线 `P0` 新字段与新状态能从配置、运行时、观测、Python 面一致访问
2. 旧测试不再依赖旧语义
3. `naval` 与 `air_combat` 这些高层场景使用的是同一 shared semantics

当前状态更新：

1. `A1a / A1b / A2a / A2b` 已完成第一阶段落地并经主线程回归验收
2. `A2c` 第一阶段也已落地并经主线程回归验收
3. `A2a` 当前剩余量主要是 adapter 使用面的继续冻结，不是重新开放 raw runtime
4. `A2b/A2c` 当前剩余量主要是 `RuntimeFacade` compat 收尾与 `core.py` compat facade 减载，不是再把状态逻辑塞回 `core.py`
5. 因此 `Phase 1` 的下一刀应集中在 `ScenarioLoader` 其余协作者下沉，而不是重新回到更早的 `A1` 类重复去重任务

### Phase 2：Lane B / C / D 平行推进

条件：

1. `Lane A` 已完成一轮 shared integration
2. `sensor/naval` 当前已收口为维护态
3. reality guards 可以稳定运行
4. DTO / observation / binding 面不再频繁漂移

### Phase 3：再评估更深建模

此时再决定是否进入：

1. 更深 Mach/compressibility / stall
2. 更深 Radar+DataLink 融合、环境效应
3. seeker type / midcourse / fuze layering
4. 更深 naval tasking / authority transfer

---

## 六、建议的首批委派单

如果下一轮继续用 subagent 分发，建议首批只开下面这些：

1. `Worker Weapon-A`
   - 任务：weapon truth shortcut / seeker reject / fuze-damage 收敛
2. `Worker C2-A`
   - 任务：`MissionCommand` 字段 / codec / profile 对账与缺口补测
3. `Worker QoS-A`
   - 任务：`DataLink` 压测与 budget scaling 补测
4. `Worker Runtime-A`
   - 任务：`RuntimeFacade / ScenarioLoader` compat 面减载收尾
5. `Explorer C2-B`
   - 任务：`MissionCommand` 字段/codec/profile 对账
6. `Explorer Docs-A`
   - 任务：现实性文档口径复核与阶段验收矩阵整理

不建议首批就开的任务：

1. `relay + jamming + doctrine` 同时推进
2. `seeker type + fuze + damage` 全套并行深化
3. `flight` 与 `weapon` 再次作为默认主线并行扩深
4. `naval` 独立扩更多功能面

---

## 七、最终建议

当前最有价值的组织方式不是“再细分更多方向”，而是：

1. 先承认这是一个 `shared integration + sensor/naval blocker` 问题
2. 用 `Lane A` 先把共用接口、观测面和合同钉牢
3. 优先清掉 `weapon` 深层真实性与 truth shortcut
4. 再把 `flight / C2-runtime` 放回较清晰的实现 lane
5. 用 `naval` 与 `air_combat` 作为高价值场景验收面，而不是新的扩功能入口

一句话总结：

下一轮应当从“按学科并行推进”切换成“先冻结 shared contract、优先清掉 weapon 深层真实性、再有限并行”的组织方式。
