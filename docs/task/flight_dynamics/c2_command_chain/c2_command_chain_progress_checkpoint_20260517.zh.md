# C2 指挥链与通信推进检查点

状态：`2026-05-17` 主线持续推进后收敛版。

关联文档：

- [冻结分析基线](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/c2_command_chain/c2_command_chain_realism_analysis_20260517.zh.md)
- [待解决问题分析](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/c2_command_chain/c2_command_chain_unresolved_issues_20260517.zh.md)
- [海战推进检查点](/home/void0312/Workshop/CMO/docs/task/naval/naval_progress_checkpoint_20260517.zh.md)
- [传感器/态势真实化 P1 实施包](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/sensor_situation/sensor_situation_realism_p1_implementation_package_20260517.zh.md)
- [武器/制导真实化 P1 实施包](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/weapon_guidance/weapon_guidance_realism_p1_implementation_package_20260517.zh.md)

本文档定位：

- 用于回答“当前 C2 指挥链 / CommandLink / DataLink 已经推进到了哪里”。
- 记录当前主线已落地的最小闭环，不把这些进展夸大为完整战术数据链或完整联合作战 C2。
- 给后续继续实现、补测或再委派 sidecar agent 提供统一现状入口。

## 零、当前阶段口径

当前更准确的口径应统一为：

1. `C2` 方向已经进入“最小工程闭环接入主线”，不是冻结分析阶段。
2. 但它仍处于 `P1-A 集成收尾` 的一部分，而不是完整 `tasking / network / authority` 系统。
3. 当前更适合把它视为：
   - `MissionCommand` 字段、profile、codec、runtime、world-batch roundtrip 已基本接通
   - `RuntimeFacade / adapter / ScenarioLoader compat` 仍有收尾余量
   - `CommandLink / DataLink / authority transfer` 仍停留在最小工程近似

这意味着当前不应再把 `C2` 表述成“完全未动”，也不应把它表述成“已经完成高保真 C2”。

## 一、已完成项

### 1.1 控制权竞争最小收束

已完成：

1. `PilotAction.active=true` 不再无条件抢占 `MissionCommand`。
2. 仅在 `stick_roll / stick_pitch / rudder` 超过最小 deadband 时才判为手动接管。

当前效果：

- 自动驾驶仪不会因为微小或无意的 pilot 输入被静默脱开。
- `MissionCommand` 与 pilot override 之间已经具备最小的“需明显接管动作才切换”语义。

关键文件：

- [DefaultControlModel](/home/void0312/Workshop/CMO/src/models/air/default_control_model.cpp)
- [控制权测试](/home/void0312/Workshop/CMO/tests/runtime/test_control_authority_arbitration.py)

### 1.2 海军 `MissionCommand` 最小语义接入

已完成：

1. 海军 `MissionCommand` 已补入 `reference_entity_id / station_radius_m / station_bearing_deg`。
2. 这些字段已能完成 `binding / profile / runtime-state roundtrip`。
3. `set_unit_command()` 对 `Ship` 已统一朝 `MissionCommand` 侧写入，不再把舰船主 authority 放在 `MovementCommand`。

当前效果：

- 海军命令不再只能退化成“硬编码 `command_code=3` 的绝对航向/航速”。
- 舰船最小站位控制现在有了 `MissionCommand` 侧可传递的结构入口。
- `Ship` 的命令 authority 已经从“写 movement 兼容层”推进到“主写 mission command”。

关键文件：

- [MissionCommand umbrella](/home/void0312/Workshop/CMO/src/components/command/mission_command.h)
- [MissionCommand naval fields](/home/void0312/Workshop/CMO/src/components/command/naval/mission_command_naval.h)
- [SimulationKernel command API](/home/void0312/Workshop/CMO/src/core/engine/simulation_kernel_command_api.cpp)
- [CommandLinkSystem](/home/void0312/Workshop/CMO/src/systems/systems/command_link_system.h)
- [海军命令映射测试](/home/void0312/Workshop/CMO/tests/runtime/test_naval_mission_command_mapping.py)
- [舰船 authority 测试](/home/void0312/Workshop/CMO/tests/runtime/test_ship_mission_command_authority.py)
- [mission state roundtrip 测试](/home/void0312/Workshop/CMO/tests/runtime/test_mission_command_naval_fields_roundtrip.py)
- [air mission roundtrip 测试](/home/void0312/Workshop/CMO/tests/runtime/test_mission_command_air_fields_roundtrip.py)

### 1.3 ROE / authority 最小字段与 runtime gate

已完成：

1. `roe_state / engagement_authority_holder_id / engagement_authority_grantor_id` 已进入 `LeaderIntent / MissionCommand / codec / binding / profile`。
2. 武器释放已具备最小 ROE gate：
   - `HOLD` 阻止隐式开火
   - `TIGHT` 要求 target、authorization 和 authority holder 匹配

当前效果：

- `authorization_to_fire` 不再是唯一的交战控制位。
- 运行时至少可以区分 `HOLD / TIGHT / legacy fallback` 三种最小交战约束。

关键文件：

- [LeaderIntent core](/home/void0312/Workshop/CMO/src/components/tasking/common/leader_intent_core.h)
- [MissionCommand core](/home/void0312/Workshop/CMO/src/components/command/common/mission_command_core.h)
- [weapon runtime gate](/home/void0312/Workshop/CMO/src/core/engine/simulation_kernel_weapon_api.cpp)
- [ROE 字段测试](/home/void0312/Workshop/CMO/tests/runtime/test_mission_command_roe_fields.py)
- [ROE runtime 测试](/home/void0312/Workshop/CMO/tests/runtime/test_weapon_roe_runtime.py)

### 1.4 `CommandLink` 队列语义澄清与测试收口

已完成：

1. `MissionCommand` pending queue 已具备最小 FIFO 语义。
2. backlog 当前已补入最小优先级重排与满队列替换低优先级尾项的策略。
3. 之前把正常顺序投递误判为覆盖的 QoS 测试已经改正。

当前效果：

- 当前主线可以稳定验证“先提交的 mission command 先送达、后提交的后送达”。
- 当 backlog 拥塞时，高优先级交战命令现在可以前插或替换低优先级尾项。
- queue / backlog 状态当前也已有 debug surface，可直接观测 pending 与 queued 条目。
- 但当前仍不应把它描述成“完整 command-link queue policy 已完成”。

关键文件：

- [Mission queue helper](/home/void0312/Workshop/CMO/src/components/command/command_link_qos.h)
- [CommandLink QoS 测试](/home/void0312/Workshop/CMO/tests/runtime/test_command_link_qos.py)

### 1.5 `DataLink` 从“无限广播”推进到“有预算、可观测拥塞”

已完成：

1. `DataLink` 已具备独立的 `max_reports_per_update` 与 `max_messages_per_update`。
2. 显式消息与轨迹报告不再共享一个总预算。
3. `DataLink` 已记录每帧与累计的：
   - reports sent
   - messages sent
   - reports dropped
   - messages dropped
4. Python / runtime 侧已可通过 `debug_get_data_link_state()` 读取这些状态。

当前效果：

- 现在已经不能再把当前 `DataLink` 描述为“单帧无限广播”。
- 最小消息优先和最小吞吐上限已经进入运行时。
- 拥塞不再只是隐式行为，而是有调试与测试可见的状态面。

关键文件：

- [DataLink component](/home/void0312/Workshop/CMO/src/components/systems/data_link.h)
- [DataLinkSystem](/home/void0312/Workshop/CMO/src/systems/systems/data_link_system.h)
- [debug_get_data_link_state binding](/home/void0312/Workshop/CMO/src/interfaces/python/bindings_core.cpp)
- [DataLink QoS runtime 测试](/home/void0312/Workshop/CMO/tests/runtime/test_data_link_qos_runtime.py)

### 1.6 `RuntimeFacade` / world-batch adapter 收口进入守门态

已完成：

1. `RuntimeFacade.runtime()` 已被明确降级为 compatibility / diagnostics 逃逸口。
2. 维护中的 Python 主线改为通过显式 adapter 暴露 facade-shaped 方法。
3. `world_batch_vec_env.py` 与 `leader_world_batch_runtime.py` 的 raw runtime/world 穿透
   已被集中收回 adapter，并由架构测试守门。
4. world-setup 兼容入口已显式收敛为 compat helper，而不是在业务主链里散落分叉。

当前效果：

1. 当前不再适合把 `RuntimeFacade` 描述成“主类可任意直穿 raw runtime”。
2. 但也还不能说这条线已经完全签收；compat 面仍存在，adapter 减载仍有余量。

关键文件：

- [RuntimeFacade README](/home/void0312/Workshop/CMO/src/runtime/facade/README.md)
- [RuntimeFacade header](/home/void0312/Workshop/CMO/src/runtime/facade/runtime_facade.h)
- [adapter.py](/home/void0312/Workshop/CMO/python/rl/runtime/world_batch/adapter.py)
- [runtime facade layering tests](/home/void0312/Workshop/CMO/tests/architecture/test_runtime_facade_layering.py)
- [world setup compat tests](/home/void0312/Workshop/CMO/tests/runtime/test_world_setup_compat.py)

### 1.7 空战武器桥接测试补强

已完成：

1. `fire_weapon_from_pilot_action()` 的 smoke 覆盖已补上“尊重 `assigned_target_id`，而不是只会发射”的断言。

当前效果：

- `MissionCommand -> pilot-triggered weapon release` 这条桥不再只验证“能打”，而是开始验证“朝对的目标打”。

关键文件：

- [空战 1v1 missile tests](/home/void0312/Workshop/CMO/tests/runtime/test_air_combat_1v1_fire_missile.py)

## 二、当前能力面判断

当前 C2 指挥链主线已经从“冻结分析里列出一组缺陷”推进到“数条最小闭环已进入运行时主线”：

1. 控制权层：
   - `PilotAction` 与 `MissionCommand` 已有最小接管阈值语义。
2. 执行命令层：
   - 海军 `MissionCommand` 已不再完全空壳。
   - `Ship` authority 已主写向 `MissionCommand`。
3. 交战层：
   - `ROE / authority holder` 已开始进入 runtime gate。
4. 命令投递层：
   - `MissionCommand` queue 已有稳定的最小 FIFO 验证。
5. 通信层：
   - `DataLink` 已从“无限广播”推进到“分预算 + 可观测拥塞”。
6. runtime adapter 层：
   - `RuntimeFacade` 的主线使用面已被收回显式 adapter + 守门测试。

但当前仍不能把这条线称为完整的“联合作战 C2 / tactical datalink simulation”，因为：

1. `CommandLink` 仍无 ACK / retransmission / multi-hop / true jitter。
2. `DataLink` 仍无 relay / jamming / NPG / tasking message doctrine。
3. 海军 tasking 与 fire-control AI 仍是最小工程近似。
4. `MissionCommand` 的 common / air / naval 语义边界仍未彻底收束。
5. `RuntimeFacade / ScenarioLoader` compat 面仍未完全减载。

## 三、当前建议

如果继续推进，建议按下面顺序处理：

1. 先做 `DataLink` 的小型压力/规模补测，确认预算与 drop 计数在更复杂 fanout 下的稳定性。
2. 再回到 `CommandLink`，决定是否要引入最小 priority queue 或 jitter 近似。
3. 同时继续压缩 `RuntimeFacade / ScenarioLoader` compat 面，避免 raw runtime 重新回流主线。
4. 然后再评估是否开启更深的 naval tasking / engage-on-remote / relay 方向。

当前最重要的结论是：

- 这条线已经不再只有分析文档。
- 但它仍处在“最小工程闭环逐步接入主线”的阶段，而不是“高保真 C2 已完成”的阶段。
