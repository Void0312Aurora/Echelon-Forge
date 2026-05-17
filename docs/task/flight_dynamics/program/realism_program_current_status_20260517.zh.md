# 真实化主线与关联子项目当前状态

状态：`2026-05-17` 当前工作区集成复核版。

关联文档：

- [真实化任务总表](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/program/realism_program_taskboard_20260516.zh.md)
- [真实化 P1 任务总表](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/program/realism_program_p1_taskboard_20260517.zh.md)
- [C2 指挥链与通信子项目](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/c2_command_chain/README.md)
- [C2 指挥链与通信推进检查点](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/c2_command_chain/c2_command_chain_progress_checkpoint_20260517.zh.md)
- [C2 指挥链与通信待解决问题分析](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/c2_command_chain/c2_command_chain_unresolved_issues_20260517.zh.md)
- [海战推进检查点](/home/void0312/Workshop/CMO/docs/task/naval/naval_progress_checkpoint_20260517.zh.md)
- [海战后续委派执行单](/home/void0312/Workshop/CMO/docs/task/naval/naval_delegated_execution_backlog_20260517.zh.md)
- [空战 1v1 F-16C 基线切换与最小对战合同进展](/home/void0312/Workshop/CMO/docs/task/air_combat/air_combat_1v1_f16c_baseline_progress_20260516.zh.md)
- [指挥链与 C2 通信现实性分析](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/c2_command_chain/c2_command_chain_realism_analysis_20260517.zh.md)

本文档定位：

- 本文档用于整理 `docs/task/flight_dynamics/` 下与当前真实化主线直接相关的文档入口。
- 本文档同时串起我当前负责的关联子项目文档：`naval/`、`air_combat/`、`C2 command-chain`。
- 本文档不重复展开每份分析细节，只回答“现在该看哪些文档、当前做到哪里、还有哪些稳定性问题”。

## 零、当前总阶段

当前总阶段建议统一表述为：

1. 主线整体仍处于 `P1-A 集成收尾`。
2. `flight`、`sensor`、`weapon`、`naval` 与 `C2` 的关键守门面已经收口，当前更适合转入维护态。
3. 本轮抽样复核里，`sensor / DataLink / track`、海军武器命令链与 weapon 守门面都已转绿；
   当前不再把它们写成稳定红点，剩余重点转向 shared contract 收口与结构债减载。
4. `C2` 已进入“最小工程闭环接入主线”，但仍不是完整 tasking / network / authority 系统。

这意味着当前最重要的工作不是继续多线扩深，而是先把 shared contract
与结构债务收束，再按需做有限的 deeper modeling。

## 一、文档整理口径

### 1.1 `flight_dynamics/` 的当前定位

`docs/task/flight_dynamics/` 现在承载两类文档：

1. 真实化主线核心文档
   - 飞行动力学
   - 传感器/态势感知
   - 武器/制导
   - 真实化总任务板
2. 跨域分析输入文档
   - [海战仿真现实性分析](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/naval/naval_realism_analysis_20260516.zh.md)
   - [指挥链与 C2 通信现实性分析](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/c2_command_chain/c2_command_chain_realism_analysis_20260517.zh.md)
3. 当前活跃子项目入口
   - [C2 指挥链与通信子项目](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/c2_command_chain/README.md)

第 2 类文档保留在这里是为了历史追踪和跨域分析完整性，但当前执行状态已经不应只看冻结分析。

### 1.2 当前活动文档应该怎么看

建议按下面顺序看：

1. 先看本文件：
   - 确认当前活跃方向和真实稳定性状态
2. 再看 `flight_dynamics/` 下的总任务板与分包：
   - [真实化任务总表](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/program/realism_program_taskboard_20260516.zh.md)
   - [真实化 P1 任务总表](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/program/realism_program_p1_taskboard_20260517.zh.md)
3. `C2` 方向不要只看冻结分析：
   - 当前应先看 [C2 指挥链与通信子项目](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/c2_command_chain/README.md)、[推进检查点](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/c2_command_chain/c2_command_chain_progress_checkpoint_20260517.zh.md) 和 [待解决问题分析](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/c2_command_chain/c2_command_chain_unresolved_issues_20260517.zh.md)
4. 海战执行状态不要停留在旧分析：
   - 当前应以 [海战推进检查点](/home/void0312/Workshop/CMO/docs/task/naval/naval_progress_checkpoint_20260517.zh.md) 和 [海战后续委派执行单](/home/void0312/Workshop/CMO/docs/task/naval/naval_delegated_execution_backlog_20260517.zh.md) 为准
5. 空战 1v1 运行状态不要只看冻结计划：
   - 当前应结合 [空战 1v1 F-16C 基线切换与最小对战合同进展](/home/void0312/Workshop/CMO/docs/task/air_combat/air_combat_1v1_f16c_baseline_progress_20260516.zh.md) 和现行运行测试判断

## 二、当前进展摘要

### 2.1 飞行动力学主线

当前判断：

- `Propulsion` 已经收口成 `Force / Logistics / Instrument / Observation` 的统一事实源。
- `StallState` 已从“只记账”升级为参与气动行为的有记忆失速状态：
  `effective_stall_progress` 当前已驱动 `stall_drag / damp_scale / pitch_break_active / debug stall_progress`。
- `test_flight_dynamics_realism_guards.py`、`test_flight_dynamics_tuning_runtime.py`、
  `test_flight_dynamics_p0_runtime_guards.py`、`test_kernel_observation_sanity.py`
  当前在本工作区为绿。
- 这条线当前更接近 `P1-A` 后半段，而不是仍停留在 `P0` 或即将进入 `P1-B`。
- 本轮重点不再是“守门测试持续发红”，而是“更深建模尚未继续推进、结构债务仍在”。

含义：

- 这条线的行为合同已经进入可继续深化的状态。
- 当前更推荐把 `flight` 转入维护态：
  先保 shared contract 与回归绿线，不把它作为主线程默认扩写入口。
- 下一步更值得投入的是 `Mach/compressibility / stall / FBW` 深化，以及
  `default_unit_factory / unit_definition` 的边界收口，而不是继续救火式修基础运行时。

### 2.2 传感器/态势主线

当前判断：

- `shared track != local contact`、`coasted track usability`、`local + datalink -> fused`
  这批 `P0` 主合同在当前工作区为绿。
- `test_sensor_situation_realism_p0.py` 与 `test_data_link_qos_runtime.py`
  当前均为绿，说明 `track/report` 与 QoS contract 已经收口到可维持状态。
- 海事传感器主链本轮复核也已转绿；
  当前更需要关注的是后续更深建模与结构收口，而不是继续救火基础合同。
- 当前更接近 `P1-A` 后半段，已可以转入维护态。
- 旧冻结分析里关于“DataLink 直接复制 contact”的表述已不再适合作为当前状态描述；
  `DataLink -> track/report` 的边界条件已经收紧到当前合同。

含义：

- 本轮已经把“共享航迹可见但不伪造本地 contact”这条主语义重新锁住。
- 这条线当前不再是主阻塞之一，而是进入维护态验收面。
- 需要注意的是，这里有一部分旧测试场景口径也做了收紧：
  某些接收方平台如果本地就具备远距空情探测能力，不再适合作为
  “只能靠 datalink 可见”的场景载体。

### 2.3 武器/制导主线

当前判断：

- shared launch runtime 已经接入 `fire_missile()` 正式发射链。
- `UnitDefinition / default_loadout / weapon_select_id` 到发射实体初始化的最小事实链已打通。
- `debug_get_missile_runtime_state()` 已补齐质量、sensor、推进与 guidance 关键字段，
  便于 runtime 验证。
- `launch envelope` 当前已补入发射前门槛：
  `min_launch_range_m / max_launch_off_boresight_deg / lobl_required`
  会在 ammo/cooldown/VLS/munition 消耗之前拒射。
- `midcourse_datalink_supported`、`seeker_activation_range_m`、
  `terminal_seeker_active` 已进入运行时，并有专门守门测试锁定中制导与末制导切换语义。
- 当前更接近 `P1-A` 后半段，而不是仍停留在旧冻结分析所描述的 `P0` workaround 阶段。

含义：

- `test_weapon_guidance_realism_guards.py` 与
  `test_air_combat_1v1_fire_missile.py` 当前为绿。
- 现在可以明确验证：不同挂点选择会得到不同 definition 驱动的导弹 runtime，
  同时全局 `set_missile_tuning()` 仍能作为显式 override 覆盖 definition baseline。
- 但也要明确一条新的结构风险：
  weapon 线当前已经不只是“补包线拒射”，而是开始把
  `definition-driven launch tuning`、`global tuning overlay`、`station-based launch selection`
  一并并入 `simulation_kernel_weapon_api.cpp`；
  行为上当前为绿，结构上则意味着 `Lane C` 后续需要继续拆分 launch resolution、
  tuning overlay 与 runtime assembly 的职责边界。
- 因此当前更推荐把 `weapon` 转入维护态：
  先冻结 shared contract，不把 `midcourse / seeker type / damage layering`
  作为主线程默认下一刀。

### 2.4 海战子项目

当前判断：

- `screen-hold` 的 direct-recovery -> hold handoff 已完成最小收口。
- `test_naval_screen_scenario.py` 当前为绿。
- `UNREP / abstract stores / maritime override / multi-sensor+ESM` 这批海战底座仍然保持绿态。
- `test_naval_ship_database.py` 与 `test_ship_mission_command_authority.py`
  这组海军武器命令链/authority 定向用例本轮复核里均为绿。
- 海战当前最重要的工作不再是 `screen-hold`，而是把海军武器命令链收口后的
  `naval` shared semantics 纳入 `C2/runtime` 维护态。

含义：

- 海战当前不再以 `screen-hold` 回归为主要阻塞点。
- 当前抽样复核没有再复现海军武器命令链红点，它更适合作为维护态验收面。
- 因此海战也不适合作为新的扩功能主线，而应作为 `C2/runtime` 高价值验收面进入维护态。
- 下一步应把海战继续放在 `C2/runtime` 高价值验收面，但不再把它当独立救火线。

### 2.5 空战 1v1 子项目

当前判断：

- `fire_missile` 直连路径与 `PilotAction.fire_weapon` 桥接路径都已纳入 definition-driven
  导弹运行时验证。
- `ScenarioLoader` 入口上的 `air_combat_1v1_fixture` 语义对齐问题已经收口；
  [tests/runtime/test_air_combat_1v1_fixture.py](/home/void0312/Workshop/CMO/tests/runtime/test_air_combat_1v1_fixture.py)
  当前为绿。

本次主线程确认的关键事实：

- 第 1 帧即可看到 `Red_Fighter` 的 raw contact，但它仍可能是 `Tentative / Unknown`。
- 到第 2 帧左右会升级为 hostile confirmed track，`classification=2`。
- 之前失败的原因不是内核把 hostile classification 丢失，而是 fixture 在“第一次看到 contact”
  时就提前停止，随后直接拿 raw contact 去断言 hostile track 语义。

含义：

- `ScenarioLoader / fixture` 当前已经与 `shared track != raw contact` 的主语义保持一致。
- 空战 1v1 当前不再有稳定复现的行为红点，主要剩余量回到 reward / termination /
  eval 合同深化，以及更深的建模工作。

### 2.6 C2 / 指挥链分析线

当前判断：

- `bridge.py` 的 profile 路由已收口：显式 `tasking_profile` 优先，
  缺省时允许按 `service_profile` 推断 `naval / air`。
- `naval_profile.build_kernel_mission_command()` 已补齐一批关键字段 authoring：
  `embarked_helo_entity_id / launch_helo / recover_helo / relay_oth_targeting /
  recovery_* / formation_*`。
- `MissionCommand` 的 Python builder、runtime roundtrip、world-batch roundtrip
  都已有显式测试锁定。
- `CommandLink` 已从“只有最小 FIFO”推进到“排队 backlog 可按最小优先级重排”，
  backlog debug surface 也已有显式测试锁定。
- `RuntimeFacade` 的 Python 主线访问面已收回显式 adapter，
  `RuntimeFacade.runtime()` 当前只保留 compatibility / diagnostics 逃逸口定位。

含义：

- `test_naval_mission_command_mapping.py`、`test_mission_command_roe_fields.py`、
  `tests/world_batch/test_world_batch_runtime.py`、`test_mission_command_air_fields_roundtrip.py`
  中相关 roundtrip 用例当前为绿。
- `tests/runtime/test_command_link_qos.py`、`tests/architecture/test_runtime_facade_layering.py`
  与 `test_world_setup_compat.py` 当前把 queue / adapter / compat 口径锁成守门线。
- 当前 `C2` 方向的主要剩余量已经从“字段漂移”转向
  `CommandLink priority / jitter / retry`、`relay / jamming / doctrine`、
  `RuntimeFacade / ScenarioLoader compat` 减载，以及更深的 tasking 闭环。

## 三、当前复核到的稳定性问题

### 3.1 当前未复现新的稳定失败

当前主线程抽样复核里未再复现稳定失败；与本节对应的定向回归已转绿：

1. [tests/runtime/test_sensor_situation_realism_p0.py](/home/void0312/Workshop/CMO/tests/runtime/test_sensor_situation_realism_p0.py)
2. [tests/runtime/test_data_link_qos_runtime.py](/home/void0312/Workshop/CMO/tests/runtime/test_data_link_qos_runtime.py)
3. [tests/runtime/test_naval_ship_database.py](/home/void0312/Workshop/CMO/tests/runtime/test_naval_ship_database.py)
4. [tests/runtime/test_ship_mission_command_authority.py](/home/void0312/Workshop/CMO/tests/runtime/test_ship_mission_command_authority.py)
5. [tests/runtime/test_mission_command_air_fields_roundtrip.py](/home/void0312/Workshop/CMO/tests/runtime/test_mission_command_air_fields_roundtrip.py)
6. [tests/runtime/test_world_setup_compat.py](/home/void0312/Workshop/CMO/tests/runtime/test_world_setup_compat.py)
7. [tests/runtime/test_command_link_qos.py](/home/void0312/Workshop/CMO/tests/runtime/test_command_link_qos.py)
8. [tests/runtime/test_weapon_guidance_realism_guards.py](/home/void0312/Workshop/CMO/tests/runtime/test_weapon_guidance_realism_guards.py)

当前结果：本轮定向回归已转绿，未复现稳定失败。

补充说明：

1. 当前更合适的总口径是“关键守门面基本为绿”。
2. 这不等于所有子方向都可以宣称完全签收。
3. 当前主线重点已经从泛化的 `flight / weapon` 收缩成结构债减载与有限深化，
   而不是 `flight / weapon / screen-hold` 这些此前更容易被视为首要风险的方向。

### 3.2 当前已验证为绿色的关键面

1. 主线程已完成 `build-workshop` 重编译，`ef_core` 当前可成功构建。
2. 主线程集成验收：
   - `test_flight_dynamics_realism_guards.py`
   - `test_flight_dynamics_tuning_runtime.py`
   - `test_flight_dynamics_p0_runtime_guards.py`
   - `test_kernel_observation_sanity.py`
   - `test_weapon_guidance_realism_guards.py`
   - `test_air_combat_1v1_fire_missile.py`
   - `test_naval_screen_scenario.py`
   - `test_sensor_situation_realism_p0.py`
   - `test_data_link_qos_runtime.py`
   - `test_naval_mission_command_mapping.py`
   - `test_mission_command_roe_fields.py`
   - `tests/world_batch/test_world_batch_runtime.py::WorldBatchRuntimeTests::test_world_batch_runtime_mission_command_roundtrip_preserves_naval_extension_fields`
   - 当前结果：`82 passed`
3. 本轮新增的聚焦验收当前为绿：
   - `tests/architecture/test_runtime_facade_layering.py`
   - `tests/world_batch/test_world_batch_vec_env.py`
   - `tests/runtime/test_command_link_qos.py`
   - `tests/runtime/test_mission_command_roe_fields.py`
   - `tests/runtime/test_flight_dynamics_tuning_runtime.py`
   - 当前结果：`51 passed`
4. `Weapon` 专项在显式指定新构建产物后当前为绿：
   - `CMO_BUILD_DIR=build pytest -q tests/runtime/test_weapon_guidance_realism_guards.py tests/runtime/test_air_combat_1v1_fire_missile.py`
   - 当前结果：`29 passed`
5. `MissionCommand` Python/C++ 收口相关定向验证为绿：`11 passed`
6. `DataLink QoS` 扩展守门线为绿：`8 passed, 2 subtests passed`
7. 海战 `screen-hold` 全量场景验证为绿：`8 passed`
8. `RuntimeFacade / MissionCommand` adapter 与 air/naval roundtrip 守门线当前为绿：
   - `tests/architecture/test_runtime_facade_layering.py`
   - `tests/runtime/test_mission_command_air_fields_roundtrip.py`
   - `tests/runtime/test_world_setup_compat.py`

### 3.3 当前仍成立的结构性风险

这些不是本轮行为红灯，但仍然是当前最重要的架构债务：

1. `default_unit_factory.h` 的 God Factory 倾向
2. `content/unit_definition.h` 的内容层污染
3. `Weapon launch resolution + tuning overlay + runtime assembly`
   当前开始在 `simulation_kernel_weapon_api.cpp` 汇聚
4. `RuntimeFacade.runtime()` 兼容逃逸口仍然存在
5. `ScenarioLoader` 仍然是 Python 侧 God Object
6. `SimulationKernel` 公共 API 持续膨胀

它们的详细分析仍以
[code_quality_review_realism_wave_20260517.zh.md](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/program/code_quality_review_realism_wave_20260517.zh.md)
为准。

### 3.4 本轮已收的结构性小切口

虽然大项结构债务还在，但本轮 `Lane A` 已经先收了两条低风险小切口：

1. `sensor` 默认值来源去重
   - `default_unit_factory.h` 不再自带一份独立的 sensor 默认值实现
   - 当前改为复用 `unit_definition` / loader 侧的默认 sensor 基线，再叠加 factory preset 覆盖
2. missile 三维向量类型去重
   - `missile_guidance_math.h` 不再维护一份独立 `Vec3` 结构体
   - 当前改为 `using Vec3 = Math::Vector3`

含义：

- 这两条改动还不足以消灭 `default_unit_factory` 与 `weapon guidance` 的大结构债务，
  但已经把“重复默认值来源”和“平行基础类型”这两类低成本退化先止住。
- 下一轮可以继续沿这个方向做更深拆分，而不需要回头先清这些基础噪声。

### 3.5 本轮已完成的 `RuntimeFacade / ScenarioLoader` 收口

除了上述两条小切口，本轮 `Lane A` 还完成了 `RuntimeFacade / ScenarioLoader`
的一轮主线程收口：

1. Python 侧 `RuntimeFacade` 访问面已先收回显式 adapter
   - `world_batch_vec_env.py` 里更多 world/time-step/visual 访问改为走 `_RuntimeFacadeAdapter`
   - `leader_world_batch_runtime.py` 已减少对 `batch_runtime.world(...)` 的业务级直接穿透
   - `tests/architecture/test_runtime_facade_layering.py` 已补层级守卫，锁住这条收口方向
2. `ScenarioLoader` 已完成第一阶段状态壳抽离
   - mission/route/reward/termination 等运行态字段已集中到 `runtime_state.py`
   - `core.py` 当前通过 `_state_shell` 保持旧属性访问兼容
3. execution episode controller 与 loader state 的同步合同已补平
   - 本轮主线程修复了 `mission_command / route cache / post-waypoint / mission phase`
     的回写遗漏
   - 同时补平了 `cached_route_ref_id=0` 这类“字段存在但值为零”的镜像语义
4. `ScenarioLoader` 的 scripted-opponent owner 已完成第一阶段抽离
   - build/reset/step 生命周期已下沉到 `behavior_runtime/scripted_opponents.py`
   - `core.py` 当前只保留薄代理与兼容访问面
   - `loader.scripted_opponents` / `loader.scripted_opponent_reports` 兼容读取仍保留
5. `ScenarioLoader` 的 command-chain owner 已完成第一阶段抽离
   - `_leader_phase_manager` 与 naval-screen 运行态缓存
     已下沉到 `behavior_runtime/command_chain_owner.py`
   - `command_chain.py` 当前改为经由 collaborator owner 托管生命周期与 kernel sync
   - `ScenarioLoader` 仍保留 `_leader_phase_manager` /
     `_naval_screen_*` 的兼容代理入口，外部注入 bridge 的旧路径未中断
   - 定向回归已覆盖 `execution_episode_state / naval_screen / common_core / world_batch / air_combat fixture`
6. `ScenarioLoader` 的 behavior-phase owner 已完成第一阶段抽离
   - `post_waypoint_transition / mission_phase_name / _approach_prev_*`
     已下沉到 `behavior_runtime/behavior_phase_owner.py`
   - `runtime_state.py` 当前通过统一镜像视图继续维护 execution episode state 的导入/导出合同
   - `ScenarioLoader` 仍保留旧字段名与私有方法入口，`_state_shell` 的兼容断言也继续成立
   - 相关扩展回归当前为绿：`57 passed`

额外含义：

- 这说明 `RuntimeFacade.runtime()` 的风险仍在，但已经从“主线散落穿透”
  收窄到了“兼容逃逸口仍然存在”。
- `ScenarioLoader` 的问题也已经从“状态与编排全挤在一个 owner”
  收窄到“compat facade 收尾与更深 owner 减载仍待继续推进，主 owner 仍偏大”。

### 3.6 低置信度噪声

目前只作为备注保留，不计入当前已复现失败：

1. subagent 回执曾提到 `pytest` 环境下偶发 `MemoryError / nanobind` 观测读取噪声
2. 本轮主线程没有稳定复现这一条，因此先不把它上升为主稳定性问题

## 四、建议的后续处理顺序

建议按下面顺序继续推进，而不是重新把所有线同时铺开：

1. 先回收 `Lane A` 的结构性收口
   - `default_unit_factory`
   - `unit_definition`
   - `RuntimeFacade / ScenarioLoader`
   - 这些问题当前不红，但已经成为下一轮继续扩功能前最该清掉的边界债务
2. 再推进更深建模
   - `flight`: Mach/compressibility / stall / FBW
   - `sensor`: relay / jamming / 更深融合
   - `weapon`: seeker type / fuze / damage layering
   - `C2/naval`: deeper tasking / authority / message loop

本轮之后，`Lane A` 的建议切入顺序可以进一步收窄为：

1. 先完成 `RuntimeFacade` Python 主线收口的余量
   - 不急着删 C++ binding
   - 继续冻结 `batch_runtime` / raw runtime 只作为兼容逃逸口而非维护接口
2. 再继续拆 `ScenarioLoader`
   - 状态壳、scripted-opponent owner、command-chain owner、behavior-phase owner 第一阶段已完成
   - 下一刀优先是 `core.py` 兼容入口减载与更深 behavior owner 切面，而不是重新扩 `core.py`

## 五、当前最推荐的文档入口

如果下一轮要继续推进，建议优先看：

1. [真实化 P1 任务总表](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/program/realism_program_p1_taskboard_20260517.zh.md)
2. [真实化主线收束计划](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/program/realism_program_convergence_plan_20260517.zh.md)
2. [海战推进检查点](/home/void0312/Workshop/CMO/docs/task/naval/naval_progress_checkpoint_20260517.zh.md)
3. [空战 1v1 F-16C 基线切换与最小对战合同进展](/home/void0312/Workshop/CMO/docs/task/air_combat/air_combat_1v1_f16c_baseline_progress_20260516.zh.md)
4. [C2 指挥链与通信子项目](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/c2_command_chain/README.md)
5. 本文档

这样看的好处是：

- 不会把 `flight_dynamics/` 下的冻结分析误当成当前执行状态
- 能直接看到“主线规划”和“当前稳定性现实”之间的差距
- 能先对齐“当前总阶段、主阻塞和冻结范围”，再决定是否值得分发更多并行实现
