# WP1 管线盘点

状态：`2026-05-19` inventory 草案。

语言版本：

- 英文主文：[pipeline_inventory_wp1_20260519.md](pipeline_inventory_wp1_20260519.md)
- 中文辅文：`pipeline_inventory_wp1_20260519.zh.md`

架构基线：

- [仿真系统架构设计](../../plan/architecture/simulation_system_architecture_design.zh.md)
- [仿真架构任务入口](README.zh.md)

本文档把当前代码库映射到规范 `P0-P10` 语义生命周期，并识别当前实现中已经接近 temporal DAG 的位置。它是只读盘点和 gap 分析，不直接授权实现；它为后续 `WP2 Contract Freeze` 准备证据。

## 一、摘要

当前仓库已经在完整 `P0-P10` 语义生命周期上拥有真实资产。当前所有权最强的阶段是：

- `P1 WorldSetup`，
- `P2 TaskingIntent`，
- `P5 PhysicsStep`，
- `P6 SenseTrackLink`，
- `P10 ObservationExport`。

当前契约面最弱的阶段是：

- `P4 PlatformControl` 作为 facade 可见阶段，
- `P7 FireControlLaunch` 作为 typed launch request/event 边界，
- `P8 MunitionLifecycle` 作为生命周期 packet，
- `P9 EffectsDamage` 作为 damage report contract。

主要结构风险不是行为缺失。行为已经存在。风险在于多个阶段仍在宽运行时 owner 中交汇，尤其是 `SimulationKernel`、`WorldBatchRuntime`、`ExecutionEpisodeController` 和 `simulation_kernel_weapon_api.cpp`。因此 WP2 应冻结 stage-node contract，而不只是冻结 packet 名称。

第二个结构风险是跨层耦合。仿真层是项目保真度中心，但当前策略层和编排层也在组装 observation、塑造 reward、请求 action、协调多智能体 intent，并 mirror episode state。因此 WP2 不仅要冻结仿真内部契约，也要冻结触达这些契约的策略/编排契约。

## 二、阶段盘点

| 阶段 | 成熟度 | 当前资产 | 证据 | 缺口 / 风险 |
|------|--------|----------|------|-------------|
| `P0 ContentCompile` | partial | unit/content preset 与 setup-facing DTO 已存在。 | [default_unit_factory.h](../../../src/models/core/default_unit_factory.h:71), [world_batch_contracts.h](../../../src/runtime/contracts/world_batch_contracts.h:19), [world_batch_runtime.cpp](../../../src/core/engine/world_batch_runtime.cpp:396) | content compile 与 world setup 仍在 runtime setup 路径中交汇；spawn-time combat override 模糊了 content 与 setup 边界。 |
| `P1 WorldSetup` | strong but coupled | batch reset、terrain/wind/zone setup、spawn、time-step setup 与 facade setup 调用已存在。 | [runtime_facade.h](../../../src/runtime/facade/runtime_facade.h:41), [runtime_facade.cpp](../../../src/runtime/facade/runtime_facade.cpp:107), [world_batch_runtime.cpp](../../../src/core/engine/world_batch_runtime.cpp:234) | facade 访问较完整，但 setup 仍依赖具体 `WorldBatchRuntime` 行为。 |
| `P2 TaskingIntent` | strong but compatibility-heavy | `TaskOrder`、`LeaderIntent`、`PilotReport`、mission command、episode state 与 batch assignment 路径已存在。 | [world_batch_contracts.h](../../../src/runtime/contracts/world_batch_contracts.h:77), [runtime_facade.cpp](../../../src/runtime/facade/runtime_facade.cpp:146), [execution_episode_controller.cpp](../../../src/core/mission/episode/execution_episode_controller.cpp:124) | `MissionCommand` 仍是 flat 兼容性聚合点；tasking 与 execution intent 在 consumer 中仍有重叠。 |
| `P3 CommandDelivery` | present but not narrow | command-link systems 会实体化 pending movement/action/mission command；facade 可 batch 设置 mission command。 | [command_link_system.h](../../../src/systems/systems/command_link_system.h:19), [simulation_kernel_systems.cpp](../../../src/core/engine/simulation_kernel_systems.cpp:169), [runtime_facade.cpp](../../../src/runtime/facade/runtime_facade.cpp:142) | command packet ownership 仍较宽；`MissionCommand` 同时携带 tasking、execution 和 engagement 字段。 |
| `P4 PlatformControl` | partial | pilot/action DTO、air control model 与 control system stage 已存在。 | [bindings_command.cpp](../../../src/interfaces/python/bindings_command.cpp:260), [default_control_model.cpp](../../../src/models/air/default_control_model.cpp:101), [control_system.h](../../../src/systems/physics/control_system.h:12) | control 行为真实存在，但看不到专门的 facade-level platform-control packet 或 stage contract。 |
| `P5 PhysicsStep` | strong internally | force clear、aero state、propulsion、force accumulation、aerodynamics、contact、rotational integration、leapfrog、naval kinematics 已注册。 | [simulation_kernel_systems.cpp](../../../src/core/engine/simulation_kernel_systems.cpp:172), [force_system.h](../../../src/systems/physics/force_system.h:60), [leapfrog_system.h](../../../src/systems/physics/leapfrog_system.h:44) | physics chain 已调度，但类似 `IPhysicsBackend` 的可替换物理后端边界还不是公开契约。 |
| `P6 SenseTrackLink` | strong internally, partial contract | sensor、sonar、track fusion、data link、EW 与 observation fallback 逻辑已存在。 | [default_sensor_model.cpp](../../../src/models/systems/default_sensor_model.cpp:312), [track_manager_system.h](../../../src/systems/systems/track_manager_system.h:240), [data_link_system.h](../../../src/systems/systems/data_link_system.h:76) | facade/contracts 中还没有独立的 `TrackPacket` ownership 边界。 |
| `P7 FireControlLaunch` | behavior-rich, contract-weak | missile launch、naval launch、target selection、envelope、ammo/cooldown、pilot-triggered firing 与 naval auto-fire 已存在。 | [simulation_kernel_weapon_api.cpp](../../../src/core/engine/simulation_kernel_weapon_api.cpp:353), [simulation_kernel.cpp](../../../src/core/engine/simulation_kernel.cpp:147), [simulation_kernel_systems.cpp](../../../src/core/engine/simulation_kernel_systems.cpp:191) | launch selection、envelope check、ammo、spawning 与 naval variants 集中在一个 kernel API；看不到 typed launch request/event contract。 |
| `P8 MunitionLifecycle` | behavior present, contract-weak | missile runtime 初始化、guidance model 与 guidance system 已存在。 | [default_unit_factory.h](../../../src/models/core/default_unit_factory.h:579), [default_guidance_model.cpp](../../../src/models/weapons/default_guidance_model.cpp:410), [guidance_system.h](../../../src/systems/combat/guidance_system.h:8) | munition lifecycle state 还没有形成清晰 packet family 或 facade contract。 |
| `P9 EffectsDamage` | behavior present, report contract missing | effects model、damage system 与 debug hit API 已存在。 | [default_effects_model.cpp](../../../src/models/weapons/default_effects_model.cpp:129), [damage_system.h](../../../src/systems/combat/damage_system.h:42), [simulation_kernel_damage_debug_api.cpp](../../../src/core/engine/simulation_kernel_damage_debug_api.cpp:9) | damage 行为已存在，但没有专门的 `DamageReport` 或 event-diagnostic contract 来替代临时 health/debug surface。 |
| `P10 ObservationExport` | strong | observation packet、instrument state、mission runtime observation 与 facade export 已存在。 | [runtime_facade_types.h](../../../src/runtime/facade/runtime_facade_types.h:49), [runtime_facade.cpp](../../../src/runtime/facade/runtime_facade.cpp:251), [simulation_kernel_observation_api.cpp](../../../src/core/engine/simulation_kernel_observation_api.cpp:318) | observation export 较强，但 launch/damage event diagnostics 还没有汇入同一条可解释 trace。 |

## 三、跨阶段耦合热点

这些文件不是错误；它们是当前多个架构阶段交汇的位置。它们应指导 WP2/WP3 边界设计。

| 热点 | 当前角色 | 管线关注点 |
|------|----------|------------|
| [simulation_kernel_systems.cpp](../../../src/core/engine/simulation_kernel_systems.cpp:54) | 注册 command-link、control、physics、sensor/track/data-link、embarked-air ops、weapon release、instrument、damage、EW 与 logistics。 | 一个注册主线串起 `P3-P10`；当前有用，但容易隐藏 stage ownership。 |
| [simulation_kernel.cpp](../../../src/core/engine/simulation_kernel.cpp:147) | 推进 world state，并在同一 step 路径中执行 naval weapon auto-fire。 | `P5` world advance 与 `P7` fire-control 行为处于同一个 owner 内。 |
| [world_batch_runtime.cpp](../../../src/core/engine/world_batch_runtime.cpp:521) | 应用 batch world setup 与 spawn-time override。 | `P0` content、`P1` setup 与 combat default 可能在 setup 中混合。 |
| [execution_episode_controller.cpp](../../../src/core/mission/episode/execution_episode_controller.cpp:196) | 拥有 execution episode flow、reward、termination、transition 与 observation aggregation。 | `P2`、`P10`、reward 与 termination 被打包在一个 mission runtime flow。 |
| [simulation_kernel_weapon_api.cpp](../../../src/core/engine/simulation_kernel_weapon_api.cpp:422) | 拥有 launch selection、envelope check、ammo/cooldown、munition spawning 与 naval launch variants。 | 主要 `P7-P8` 契约风险；行为已存在但 packet 边界还不够窄。 |

## 四、Facade 与契约覆盖

当前 facade 覆盖不均衡：

- 较强：setup/reset (`P1`)、tasking assignment/export (`P2`)、execution batch stepping 与 observation export (`P10`)。
- 部分：通过 mission command assignment 覆盖 command delivery (`P3`)。
- 较弱：platform control (`P4`)、launch/fire-control (`P7`)、munition lifecycle (`P8`) 与 damage reporting (`P9`) 作为 typed request/result family。

重要风险：

1. `RuntimeFacade::runtime()` 仍是 compatibility 与 diagnostics 逃逸口。它被有意记录，但仍是绕行路径。
2. Python bindings 仍为兼容性直接暴露 `WorldBatchRuntime`。
3. `world_batch_contracts.h` 在一个宽头文件中混合 setup、command、tasking 与 observation 结构。
4. `MissionCommand` 仍是兼容性聚合点，而不是窄 command packet。

## 五、Temporal DAG 发现

当前实现已经更接近带时钟域的图，而不是线性等步长管线：

| 发现 | 证据 | WP2 含义 |
|------|------|----------|
| physics 内部是多阶段链，频率很可能高于 command/tasking。 | [simulation_kernel_systems.cpp](../../../src/core/engine/simulation_kernel_systems.cpp:172), [leapfrog_system.h](../../../src/systems/physics/leapfrog_system.h:44) | `P5` 应声明 physics clock domain 与 substep/sync policy。 |
| command delivery 有 latency/drop state 与 pending queue。 | [command_link_system.h](../../../src/systems/systems/command_link_system.h:19) | `P3` 应按 event/latency 驱动，而不是默认 same-window。 |
| sensor/track/data-link 不天然与 physics 等频。 | [default_sensor_model.cpp](../../../src/models/systems/default_sensor_model.cpp:312), [data_link_system.h](../../../src/systems/systems/data_link_system.h:76) | `P6` 需要 sensor scan 与 fusion clock domain，以及 track snapshot 规则。 |
| fire-control 与 launch 使用 ammo/cooldown/envelope 等状态。 | [simulation_kernel_weapon_api.cpp](../../../src/core/engine/simulation_kernel_weapon_api.cpp:353) | `P7` 应产出 timestamped launch event，而不是暗示立即线性传递。 |
| guidance 与 fuze 行为可能与 launch decision 不同频。 | [default_guidance_model.cpp](../../../src/models/weapons/default_guidance_model.cpp:410), [guidance_system.h](../../../src/systems/combat/guidance_system.h:8) | `P8` 需要 guidance-rate、seeker-rate 与 fuze/event-driven node contract。 |
| damage 天然是 event-driven，并反馈到未来 platform/sensor/weapon capability。 | [damage_system.h](../../../src/systems/combat/damage_system.h:42) | `P9` 应跨越 event/state barrier 后，再让后续 capability change 被读取。 |
| observation export 是 snapshot/export surface，不一定是每阶段 mutation point。 | [runtime_facade.cpp](../../../src/runtime/facade/runtime_facade.cpp:251) | `P10` 应声明 snapshot version 与 sync policy。 |

WP2 应把 `P0-P10` 视作语义阶段词汇，并用 stage-node contract 定义真实执行约束：

1. `semantic_stage`，
2. `read_set`，
3. `write_set`，
4. `clock_domain`，
5. `latency_policy`，
6. `sync_policy`，
7. data-derived same-window edge，
8. state-store shard versioning，
9. deterministic event ordering，
10. nested 或 explicitly merged clock-domain scheduling。

## 六、验证盘点

现有测试已经覆盖若干重要边界：

| 验证区域 | 证据 | 说明 |
|----------|------|------|
| Facade layering | [test_runtime_facade_layering.py](../../../tests/architecture/test_runtime_facade_layering.py:41) | 阻止 adapter 外部 raw runtime 逃逸，并检查 contract header hygiene。 |
| Build layering | [test_cmake_target_readiness.py](../../../tests/architecture/test_cmake_target_readiness.py:25) | 保护未来 target split 所需的 grouped source readiness。 |
| Facade behavior | [test_runtime_facade.py](../../../tests/runtime/facade/test_runtime_facade.py:213) | 覆盖 setup、observation export、execution batch stepping 与 state advancement。 |
| Mission/runtime bridge | [test_mission_runtime.py](../../../tests/runtime/mission/test_mission_runtime.py:86) | 对 mission observation、route guidance、live track、datalink 有较强 `P2/P6/P10` 覆盖。 |
| Sensor/track realism | [test_sensor_situation_realism_p0.py](../../../tests/runtime/air_combat/test_sensor_situation_realism_p0.py:62) | 对 `P6` 有较强覆盖。 |
| Air weapon realism | [test_weapon_guidance_realism_guards.py](../../../tests/runtime/air_combat/test_weapon_guidance_realism_guards.py:167) | 对 air-side `P7-P9` 行为有较强覆盖。 |
| ROE gating | [test_weapon_roe_runtime.py](../../../tests/runtime/air_combat/test_weapon_roe_runtime.py:53) | 与 `P2/P3/P7` 授权边界相关。 |
| Naval engagement | [test_naval_ship_database.py](../../../tests/runtime/naval/test_naval_ship_database.py:30) | 覆盖 naval-side sensor、mount、launch、CIWS 与 damage。 |
| Batch runtime | [test_world_batch_runtime.py](../../../tests/world_batch/test_world_batch_runtime.py:184) | 验证 batch runtime 的 setup、stepping、observation 与 timing。 |
| Local smoke | [ci_smoke_suite.json](../../../tests/smoke/ci_smoke_suite.json:1) | 维护中的 smoke set 已包含 architecture、facade、env config 与 world batch tests。 |

缺失验证：

1. 单一跨领域交战管线测试，用来证明 air 与 naval 的 launch/damage 行为共享同一生命周期。
2. facade-only engagement path 测试，用来证明 launch、damage 与 observation 可通过 facade-shaped API 或显式 compatibility adapter 访问。
3. diagnostics trace，把 launch、munition lifecycle、effects、damage 与 observation export 绑定成一条可解释链路。
4. stage-aligned local non-RL smoke test，显式验证新的 `P0-P10` 架构词汇。

## 七、跨层耦合发现

当前 inventory 识别了五个系统级耦合点。WP2 应把它们当作架构契约输入，而不是偶然的 Python/C++ 实现细节。

| 耦合点 | 当前证据 | WP2 含义 |
|--------|----------|----------|
| Observation assembly 横跨仿真与策略关注点。 | [mission_obs_taxonomy.py](../../../python/mission_obs_taxonomy.py:127), [mission_observation.py](../../../gym_envs/scenario_loader/mission_observation.py:209), [runtime_facade_types.h](../../../src/runtime/facade/runtime_facade_types.h:49) | 冻结 `ObservationViewSpec`：策略/测试拥有 schema、encoding、normalization；仿真/facade 拥有可查询 snapshot 与 packet export。 |
| Reward 与 termination 分裂在 compiled mission runtime 和 Python step assembly 之间。 | [execution_episode_controller.cpp](../../../src/core/mission/episode/execution_episode_controller.cpp:143), [mainline.py](../../../gym_envs/scenario_loader/execution_runtime/mainline.py:309), [reward_runtime/](../../../gym_envs/scenario_loader/reward_runtime/) | 冻结 `RewardSpec`、`RewardReport`、`TerminationSpec` 与 reason-source attribution。语义 termination 应能从 compiled/facade 恢复；shaping 可以保持实验可配置。 |
| Coordination intent 在 simulation DAG 外部产生，但写入 tasking/command DTO。 | [cooperative_director.py](../../../python/rl/runtime/world_batch/cooperative_director.py:141), [cooperative_world_batch_vec_env.py](../../../python/rl/runtime/cooperative_world_batch_vec_env.py:617), [world_batch_runtime.cpp](../../../src/core/engine/world_batch_runtime.cpp:619) | 冻结 `CoordinationIntentPacket`，以及 scripted、learned、human director 的 facade assignment path。 |
| Policy inference cadence 与 simulation cadence 不是同一时钟。 | [wrappers.py](../../../python/rl/control/wrappers.py:30), [operation_layer.md](../../forward/operation_layer.md:12), [runtime_facade.cpp](../../../src/runtime/facade/runtime_facade.cpp:195) | 冻结 `ActionIntentPacket` 与 `ActionHoldPolicy`：effective time、validity window、hold/interpolation/expiry，以及 P3/P4/P5 consumption boundary。 |
| Episode lifecycle 在 compiled runtime 与 Gymnasium adapter 之间 mirror。 | [execution_episode_controller.h](../../../src/core/mission/episode/execution_episode_controller.h:20), [runtime_facade_types.h](../../../src/runtime/facade/runtime_facade_types.h:79), [universal_env.py](../../../gym_envs/universal_env.py:229), [core.py](../../../gym_envs/scenario_loader/core.py:1140) | 冻结 `EpisodeLifecycleContract`：compiled/facade 拥有权威 phase 与语义 termination；adapter mirror status 并请求 reset/truncation。 |

这些发现不会降低仿真保真度的优先级。它们澄清了哪些外部 producer 与 consumer 必须被建模，从而让仿真层在 RL、batch evaluation 和 service deployment 扩展时继续保持权威。

## 八、WP2 Contract Freeze 输入

WP2 不应从字段级重写开始。它应先冻结最薄弱阶段的 packet ownership、facade exposure、stage-node read/write set 与 timing policy。

建议 WP2 主题：

1. `TrackPacket` ownership：决定 track export 属于 `components`、`runtime/contracts`，还是 facade-only observation packet。
2. `LaunchRequest` / `LaunchEvent`：拆分 fire-control intent、munition spawning 与 naval/air launcher variants。
3. `MunitionLifecyclePacket`：定义哪些状态值得进入契约，哪些继续留在 component 内部。
4. `EffectsEvent` / `DamageReport`：定义能覆盖 HP、subsystem damage、soft-kill、mission kill 与 diagnostics 的 report surface。
5. `MissionCommand` containment：冻结哪些字段继续作为 compatibility-only，哪些应迁入更窄 tasking/command/engagement packet。
6. Facade escape policy：保留 `RuntimeFacade::runtime()` 用于 diagnostics，但阻止新的维护中 engagement 工作依赖它。
7. Stage-node timing policy：冻结 command、sensor、launch、guidance、fuze、damage 与 export node 的 clock domain、latency rule 与 feedback barrier。
8. DAG composition rule：冻结从 `read_set` 与 `write_set` 推导 edge 的规则，并标记通过 `StateStore` 或 `EventQueue` 发生的跨窗口反馈。
9. Event ordering rule：为 launch、fuze、damage、report 与 observation event 冻结确定性 `(timestamp, priority, event_id)` 排序。
10. Clock-domain rule：默认使用嵌套触发，独立 clock 需要显式 merge policy。
11. `ObservationViewSpec`：冻结 field selection、encoding、normalization、schema version 与 snapshot source 分别由哪一侧拥有。
12. `ActionIntentPacket` / `ActionHoldPolicy`：冻结 policy action 的 effective time、validity window、hold/interpolation/expiry 与 `P3/P4/P5` 边界。
13. `RewardSpec` / `RewardReport`：冻结仿真事实与实验 shaping 的拆分，包括 Python 计算 reward 时的 mirror snapshot version 与 latency。
14. `TerminationSpec` / `EpisodeStatus`：冻结语义 termination 与训练/测试 truncation 的边界，并要求 reason-source attribution。
15. `EpisodeLifecycleContract`：冻结 compiled/facade 对 episode phase、transition 与 reset 的 authority，同时允许 Gymnasium/batch mirror。
16. `CoordinationIntentPacket`：冻结 scripted、learned 与 human director 如何通过 facade-compatible path 写入 tasking 或 command intent。

## 九、WP3 Engagement Pilot 输入

交战试点应在 WP2 命名 packet 边界后开始。最有价值的试点应证明：

1. 航空挂架发射与舰载挂载发射使用同一套 stage 词汇，
2. fire-control 产出 typed launch event，
3. 必要时允许 clock domain 不同，但不创建私有纵向栈，
4. munition lifecycle 使用共享状态概念，即使 guidance 不同，
5. effects 与 damage 产出 observation/diagnostics 可见 report，
6. 本地 smoke path 不需要 RL 依赖。

## 十、当前状态

WP1 已经具备进入 `WP2 Contract Freeze` 的证据基础。

当前实现最适合描述为：

- 行为丰富，
- 内部已经有 stage 形状，
- 已经呈现 temporal DAG 倾向，
- 部分对齐 facade，
- 在 engagement 与 damage 上尚未 contract-narrow。

这对下一步而言是不错的位置。代码已经有足够真实行为可盘点；下一项任务是在不假装兼容面不存在的前提下，把契约收窄。
