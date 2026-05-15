# CAP 任务与长机层落地计划 (Bootstrap Plan)

> ARCHIVED NOTE (2026-03-23): 该文档属于旧的 air-specific 标准化路线，现仅保留作历史参考。
> 当前标准化基线请改看 [docs/standards/README.md](/home/void0312/CMO/docs/standards/README.md)。

本文档在 [C2 任务指令与长机层标准](./task_order_leader_standard.md) 的基础上，进一步定义第一阶段的最小可实施范围，用于把当前单机连续飞行任务重构为“C2 指令 -> 长机层 -> 执行层”的拟真链路。

适用范围：
- 当前单机 `takeoff -> transit -> station -> rtb -> recover/land` 任务线。
- 第一阶段只引入脚本化 `C2`，不训练 `C2` 节点。
- 第一阶段的主要目标不是空战求解，而是先建立真实任务语义、稳定 phase 切换和可训练的长机层接口。

## 1. 第一阶段任务线程

### 1.1 任务线程定义

第一阶段采用如下军事语义任务线程：
- `TASK_SCRAMBLE`
- `TASK_CAP`
- `TASK_RTB`
- `TASK_RECOVER_LAND`

场景级包装任务可记为：
- `TASK_CAP_MISSION`

其展开顺序为：
1. `TASK_SCRAMBLE`
2. `TASK_CAP`
3. `TASK_RTB`
4. `TASK_RECOVER_LAND`

### 1.2 与现有连续任务的对应关系

当前仓内“起飞-巡航-降落”不再视为一个中性飞行流程，而解释为：
- `起飞`: 战备紧急出动
- `巡航/航路`: 转场至 CAP 空域并建立巡逻
- `返航`: 结束在站或达到退出条件后返场
- `降落`: 回收着陆

这意味着：
- 现有 `post_waypoint_transition` 不应继续充当唯一任务切换器。
- `mission_code` 只能作为执行层模式码，不能再替代完整任务语义。
- `heading / altitude / speed` 不应继续被定义为跨所有 `mission_code` 的通用长机层自由参数。

## 2. 第一阶段参数子集

第一阶段只实现能支撑单机 CAP 线程的最小参数子集，避免一开始把多机编队、武器授权和复杂空域全都耦合进来。

### 2.1 TaskOrder 最小字段

#### 通用字段
- `task_id`
- `task_type`
- `priority`
- `issuer_id`
- `assignee_id`
- `active`
- `issue_time_s`

#### CAP / 转场字段
- `anchor_x_m`
- `anchor_y_m`
- `anchor_z_m`
- `station_type`
- `station_radius_m`
- `station_leg_length_m`
- `station_heading_deg`
- `target_altitude_m`
- `target_speed_mps`
- `altitude_block_min_m`
- `altitude_block_max_m`
- `speed_min_mps`
- `speed_max_mps`
- `on_station_time_s`

#### 回收字段
- `recovery_base_id`
- `recovery_runway_id`
- `fuel_bingo_override_kg`

#### 条件字段
- `entry_condition_code`
- `exit_condition_code`

### 2.2 LeaderIntent 最小字段

- `phase_id`
- `command_code`
- `route_ref` 或 `route_points_ref`
- `recovery_base_id`
- `recovery_runway_id`
- `recovery_approach_type`
- `target_altitude_m`
- `target_speed_mps`
- `target_heading`
  仅在 `command_code = 3` 且系统将其解释为 track bug 时有效。
- `approach_armed`
- `commit_to_land`
- `abort_flag`

第一阶段暂不强制实现：
- `formation_id`
- `form_offset_x/y/z`
- `assigned_target_id`
- `authorization_to_fire`

### 2.3 PilotReport 最小字段

- `report_type`
- `sender_id`
- `task_id`
- `phase_id`
- `timestamp_s`
- `status_value`
- `location_x_m`
- `location_y_m`
- `location_z_m`

第一阶段最少支持的报告类型：
- `REP_WILCO`
- `REP_UNABLE`
- `REP_ON_STATION`
- `REP_RTB`
- `WARN_BINGO`

## 3. Phase 设计与切换责任

第一阶段的长机 phase 采用以下最小集合：
- `PHASE_IDLE`
- `PHASE_SCRAMBLE`
- `PHASE_TAKEOFF`
- `PHASE_DEPARTURE`
- `PHASE_TRANSIT_TO_STATION`
- `PHASE_ESTABLISH_CAP`
- `PHASE_ON_STATION`
- `PHASE_RTB`
- `PHASE_APPROACH_ARMED`
- `PHASE_LANDING_FINAL`
- `PHASE_ROLLOUT`
- `PHASE_ABORT`

切换责任原则：
- `C2` 只切换任务，不切换细粒度飞行 phase。
- 长机层负责 phase 展开与时机选择。
- 执行层只报告“是否达到/无法达到”，不直接决定任务线程。

关键约束：
- `PHASE_APPROACH_ARMED` 必须独立于航点完成逻辑。
- 当 `distance_to_runway_threshold_m`、`runway_heading_error_deg`、`glideslope_dev/localizer_dev` 等满足阈值时，长机层应能主动切入回收链路。
- 这一步正是为修复 OOD 中“过晚切入 landing”或“完全不切入”的失败模式。
- 主动切入回收链路的含义是“进入 recovery procedure”，不是“开放一组通用 final heading/altitude/speed 手工参数”。

## 4. 代码落点与职责划分

### 4.1 引擎组件层

建议新增或改造的位置：
- `src/components/physics/action.h`
  负责补充 `LeaderIntent`、`PendingMissionCommand`，并逐步把高层语义从 legacy `MovementCommand` 中迁出。
- `src/components/systems/comm.h`
  负责补齐 `PilotReport` 所需消息类型与载荷约定。
- `src/components/systems/data_link.h`
  继续承载网络链路能力，不直接承载任务语义。

### 4.2 系统层

建议新增或改造的位置：
- `src/systems/systems/command_link_system.h`
  增加 `MissionCommand` 延迟投递链路，避免目前只有 `MovementCommand` / `ActionCommand` 支持链路延迟。
- `src/systems/physics/instrument_system.h`
  为长机层补充 terminal / recovery 几何产品。
- `src/systems/core/operation_system.h`
  保持执行层接口兼容，不把长机 phase 直接下沉为舵面命令。

### 4.3 Kernel 与绑定层

建议新增或改造的位置：
- `src/core/engine/simulation_kernel.cpp`
- `src/core/engine/simulation_kernel.h`
- `src/interfaces/python/python_module.cpp`

第一阶段需要支持：
- 设置 `TaskOrder` 或其 Python 侧等价对象
- 设置 / 获取 `LeaderIntent`
- `MissionCommand` 的延迟投递
- 暴露完整 `CommMsgType`

### 4.4 Python 任务编排层

建议新增或改造的位置：
- `gym_envs/scenario_loader.py`
  不再将 landing 触发完全绑定到 waypoint 完成。
- `python/rl/wrappers.py`
  不再以 `mission[0] == 4` 作为唯一 landing phase 开关。
- 新增脚本式 `C2` 发布器与规则版长机 phase 管理器。

## 5. 分阶段实施计划

### 5.1 Milestone A: 数据结构先行

目标：
- 明确高层任务对象和回报对象，先把接口稳定下来。

工作项：
1. 定义 `TaskOrder`
2. 定义 `LeaderIntent`
3. 定义 `PilotReport`
4. 定义 `PendingMissionCommand`
5. 为 `CommMsgType` 与 `CommPacket` 补齐与 `rep.md` 对齐的字段说明

完成标准：
- C++ 组件可编译
- Python 可访问基础枚举和数据结构
- 不破坏现有单机训练接口

### 5.2 Milestone B: 链路与消息打通

目标：
- 让任务与长机意图能通过现有链路模型延迟投递。

工作项：
1. 在 `command_link_system.h` 中加入 `MissionCommand` 投递系统
2. 在 `simulation_kernel` 中改造 `set_mission_command`
3. 暴露完整 `CommMsgType` 到 Python
4. 明确 `PilotReport -> CommPacket` 的桥接规则

完成标准：
- Mission command 可配置延迟
- Python 能发起与读取任务相关消息
- 旧训练脚本在兼容路径下仍可运行

### 5.3 Milestone C: 脚本 C2 与规则版长机

目标：
- 用脚本和规则先替换当前脆弱的 phase 切换逻辑。

工作项：
1. 新增脚本 `C2` 发布 `TASK_SCRAMBLE/TASK_CAP/TASK_RTB/TASK_RECOVER_LAND`
2. 新增规则版 `LeaderPhaseManager`
3. 基于 terminal 几何而非单一路径完成触发 `APPROACH_ARMED`
4. 将 `LeaderIntent` 映射为当前 `MissionCommand`

完成标准：
- 连续任务不再依赖单一 `post_waypoint_transition`
- 能稳定进入 landing/recovery
- OOD 中几何和剖面扰动下的切相鲁棒性明显提升

### 5.4 Milestone D: RL 长机层接入

目标：
- 在稳定接口之上训练长机层策略。

工作项：
1. 固化长机层观测空间
2. 固化长机层动作空间
3. 冻结执行层脚本/残差控制
4. 引入 leader-only reward 与日志

完成标准：
- 训练目标聚焦于 phase 决策、返航时机、进近切入
- 不让长机层直接学习底层操纵
- 不让长机层学习跨所有 `mission_code` 共享的通用飞行参考参数

## 6. 第一阶段验收指标

第一阶段不以“战术智能极强”为验收目标，而以“接口真实、链路清晰、切相稳定”为目标。

建议验收指标：
- `TASK_CAP_MISSION` 能完整跑通 `scramble -> cap -> rtb -> recover`
- 在 OOD `wind/profile/geometry` 中不再出现大面积“永不切入 landing”
- 出现返航或进近失败时，日志中能追溯：
  - 当前 `TaskOrder`
  - 当前 `phase_id`
  - 最近一次 `PilotReport`
  - 最近一次 `MissionCommand`
- Python 侧能够独立记录和回放这些高层对象

## 7. 下一步代码工作建议

紧接着建议按如下顺序开工：
1. 在 `src/components/physics/action.h` 增补 `LeaderIntent` 与 `PendingMissionCommand`
2. 在 `src/components/systems/comm.h` 中把回报枚举与 `rep.md` 对齐，并统一命名风格
3. 在 `src/systems/systems/command_link_system.h` 中新增 `MissionCommand` 延迟投递
4. 在 `src/interfaces/python/python_module.cpp` 中暴露完整通信枚举和新增结构
5. 在 Python 侧实现脚本 `C2` 与规则版 `LeaderPhaseManager`
6. 最后替换 `scenario_loader.py` / `wrappers.py` 中对 landing phase 的脆弱硬编码

## 8. 风险与兼容性说明

主要风险：
- `MovementCommand` 仍承担 legacy 兼容职责，短期内会与新高层接口并存。
- `MissionCommand` 与 `LeaderIntent` 的职责若不明确，容易再次发生语义重叠。
- 若继续把 `target_heading / target_altitude / target_speed` 当作所有命令共享的自由参数，会再次破坏层级职责并诱发 terminal 几何漂移。
- Python 训练侧目前仍假设若干数值约定，修改 phase 触发逻辑时必须同步回归测试。

兼容策略：
- 第一阶段允许 legacy 路径继续存在。
- 新链路以“并行接入、逐步替换”为原则。
- 只有在 `LeaderPhaseManager` 与脚本 `C2` 稳定后，才逐步削弱旧的 `post_waypoint_transition` 角色。
口径约束：
- 第一阶段保留 `MissionCommand` 兼容壳，但必须按 `command_code` 解释字段。
- `Landing` 阶段不允许再把 `target_heading / target_altitude / target_speed` 当作长机层通用连续偏置。
- `Landing` 的终端参数应由 `recovery_base_id + recovery_runway_id + recovery_approach_type` 和执行层恢复逻辑共同确定。
