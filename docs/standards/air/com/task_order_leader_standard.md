# C2 任务指令与长机层标准 (Task Order & Leader Layer Standard)

> ARCHIVED NOTE (2026-03-23): 该文档属于旧的 air-specific 标准化路线，现仅保留作历史参考。
> 当前标准化基线请改看 [docs/standards/README.md](/home/void0312/CMO/docs/standards/README.md)。

本文档定义空中单位分层控制中的任务发布层、长机层、执行层之间的标准接口，用于把“强军事语义任务”稳定地映射为可训练、可执行、可回放的控制链路。

本标准服务于以下目标：
- 保持任务语义的真实性，不把军事任务退化为纯民航式航点串。
- 在“指挥层目标”和“执行层动作”之间建立清晰防火墙。
- 为后续长机层 RL 训练提供稳定的观测空间、动作空间和消息接口。
- 与当前仓库已经存在的 `MissionCommand` / `PilotAction` / `CommandLink` / `DataLink` 兼容。

## 1. 层级定义

### 1.1 C2 层
- 职责：发布任务、调整任务优先级、下达进入/退出条件。
- 输出：`TaskOrder`
- 不负责：舵面、油门、起落架、瞬时转弯率。
- 当前路线：先脚本化，不训练。

### 1.2 长机层
- 职责：将 `TaskOrder` 展开为可执行阶段；根据任务、进度、链路和本机状态决定当前意图、任务阶段、航路方案与回收方案。
- 输入：`TaskOrder`、执行层回报、导航/仪表/任务进度状态。
- 输出：`LeaderIntent`，并进一步映射到 `MissionCommand`。
- 当前路线：作为下一阶段主要 RL 训练对象。

### 1.3 执行层 / 飞行员层
- 职责：接收长机层下达的任务目标，完成“怎么飞”。
- 输入：`MissionCommand` + 仪表/导航观测。
- 输出：`PilotAction`
- 当前路线：继续复用现有脚本基线或残差控制。

### 1.5 参数归属总原则

必须区分“任务语义”与“飞行程序参数”：
- `TaskOrder` 承载 `C2 -> 长机层` 的任务、约束与回收要求。
- `LeaderIntent` 承载长机层的阶段判断、意图选择、回报与任务级决策。
- `MissionCommand` 承载 `长机层 -> 执行层` 的可执行命令，但其参数槽位必须与 `command_code` 绑定。

严格约束：
- `heading / altitude / speed` 不是长机层对所有任务通用可写的自由参数。
- 当 `command_code = 3 (Route / LNAV)` 时，`target_heading` 解释为当前航段的轨迹/航迹参考，`target_altitude / target_speed` 解释为航路/阶段参考。
- 当 `command_code = 4 (Landing / Final)` 时，终端参数应来自回收机场、跑道、进近程序与执行层终端跟踪逻辑，不应被长机层当作通用连续偏置反复改写。
- 长机层的真实职责是“选命令、选航路、选回收、选切换时机”，不是在 terminal 阶段持续手动拧 final heading。

### 1.4 操作层 / 控制层
- 职责：将 `PilotAction` 或 `ActionCommand` 映射为受物理约束的控制命令。
- 输出：底层控制模型可消费的命令状态。
- 当前状态：仓库内已具备 `ActionMapping -> CommandLag -> ControlModel` 主链路。

标准数据流：

`C2 -> TaskOrder -> Leader -> LeaderIntent -> MissionCommand -> Pilot -> PilotAction -> OperationLayer -> Physics`

回报链路：

`Pilot -> PilotReport -> Leader -> TaskStatus -> C2`

## 2. 任务对象标准

### 2.1 顶层任务类型

第一阶段必须直接采用军事语义任务，而不是中性飞行任务名。

建议最小任务集合：
- `TASK_IDLE`
- `TASK_SCRAMBLE`
- `TASK_CAP`
- `TASK_RTB`
- `TASK_RECOVER_LAND`

可选复合任务：
- `TASK_CAP_MISSION`
  语义：起飞、转场、建立 CAP、在站、返航、回收着陆。

说明：
- `TASK_CAP_MISSION` 可作为场景级任务线程包装。
- 长机层内部仍应拆解为多个 phase，而不是把整个任务当成单阶段处理。

### 2.2 TaskOrder 标准字段

`TaskOrder` 是 `C2 -> 长机层` 的任务发布对象。

必选字段：
- `task_id`: 唯一任务 ID
- `task_type`: 任务类型枚举
- `priority`: 优先级
- `issuer_id`: 发布者实体 ID
- `assignee_id`: 接收长机实体 ID 或编队 ID
- `active`: 是否生效
- `issue_time_s`: 发布时间

导航/空域字段：
- `anchor_x_m`
- `anchor_y_m`
- `anchor_z_m`
- `station_type`
  取值建议：`orbit`, `racetrack`, `route_cap`
- `station_radius_m`
- `station_leg_length_m`
- `station_heading_deg`
- `route_waypoint_ids` 或 `route_points`

飞行约束字段：
- `altitude_block_min_m`
- `altitude_block_max_m`
- `target_altitude_m`
- `speed_min_mps`
- `speed_max_mps`
- `target_speed_mps`

任务进出条件：
- `entry_condition_code`
- `exit_condition_code`
- `on_station_time_s`
- `fuel_bingo_override_kg`
- `recovery_base_id`
- `recovery_runway_id`
- `recovery_approach_type`

战术与编队字段：
- `formation_template_id`
- `formation_role_id`
- `assigned_sector_id`
- `assigned_target_id`
- `emcon_state`
- `sensor_posture`
- `weapon_posture`
- `fire_authorization_state`

## 3. CAP 任务语义

### 3.1 CAP 任务定义

`TASK_CAP` 表示在指定区域、指定高度层和速度窗口内建立并维持战斗空中巡逻态势。

对当前仓库的连续起飞-巡航-降落任务，建议用以下方式表达：
- 场景开始：脚本 C2 下发 `TASK_SCRAMBLE`
- 离场后：脚本 C2 下发 `TASK_CAP`
- 达到退出条件后：脚本 C2 下发 `TASK_RTB`
- 进入返场窗口后：脚本 C2 下发 `TASK_RECOVER_LAND`

如果一个场景只允许单任务入口，也可由脚本 C2 直接下发 `TASK_CAP_MISSION`，其内部子阶段仍按上述阶段展开。

### 3.2 CAP 任务参数

CAP 最小参数集合：
- `station_type`
- `station_anchor` 或 `station_points`
- `station_radius_m` / `station_leg_length_m`
- `station_heading_deg`
- `altitude_block_min_m`
- `altitude_block_max_m`
- `target_speed_mps`
- `on_station_time_s`
- `formation_template_id`
- `recovery_base_id`
- `recovery_runway_id`
- `recovery_approach_type`

说明：
- `TASK_CAP` 的真实语义是“在指定空域与约束下建立并维持巡逻态势”。
- 因此 `CAP` 任务对执行层的主要下游载荷应是航路/站位几何与高度速度约束，而不是抽象成任何阶段都能自由覆盖的 `heading/altitude/speed` 三元组。

## 4. 长机层内部阶段

长机层必须维护内部 phase，而不是把 `mission_code` 当成唯一任务状态。

建议标准 phase：
- `PHASE_IDLE`
- `PHASE_SCRAMBLE`
- `PHASE_TAKEOFF`
- `PHASE_DEPARTURE`
- `PHASE_TRANSIT_TO_STATION`
- `PHASE_ESTABLISH_CAP`
- `PHASE_ON_STATION`
- `PHASE_REPOSITION`
- `PHASE_RTB`
- `PHASE_APPROACH_ARMED`
- `PHASE_LANDING_FINAL`
- `PHASE_ROLLOUT`
- `PHASE_ABORT`

其中：
- `PHASE_APPROACH_ARMED` 必须独立存在。
- 其职责是允许长机层在“满足进近几何”时提前进入 terminal/recovery，而不是被动等待航点链或 `post_waypoint_transition`。

## 5. 长机层观测空间

长机层观测应采用结构化状态，不使用视觉图像。

### 5.1 自机状态
- `ias_mps`
- `ground_speed_mps`
- `altitude_agl_m`
- `altitude_baro_m`
- `vvi_mps`
- `heading_deg`
- `ground_track_deg`
- `roll_deg`
- `pitch_deg`
- `beta_deg`
- `yaw_rate_deg_s`
- `fuel_internal_kg`
- `fuel_external_kg`
- `gear_pos`

### 5.2 任务状态
- `task_type`
- `task_priority`
- `phase_id`
- `phase_time_s`
- `task_time_s`
- `landing_required`
- `fire_authorization_state`
- `formation_template_id`

### 5.3 航路 / CAP 进度

优先复用现有 `nav_v2` 产物：
- `command_code`
- `selected_steerpoint_idx`
- `steerpoint_mode`
- `distance_to_go_m`
- `bearing_rel_deg`
- `altitude_delta_m`
- `cdi_m`
- `track_error_deg`
- `leg_distance_remaining_m`
- `next_turn_angle_deg`
- `distance_to_turn_m`

再补充：
- `remaining_waypoint_count`
- `on_station_progress`
- `time_on_station_remaining_s`
- `distance_to_station_anchor_m`
- `station_radial_error_deg`

### 5.4 回收 / 进近几何
- `distance_to_runway_threshold_m`
- `runway_along_m`
- `runway_cross_m`
- `runway_heading_error_deg`
- `dme_m`
- `localizer_dev`
- `glideslope_dev`
- `terminal_feasible_flag`
- `approach_commit_flag`

### 5.5 链路与回报
- 最近一次任务更新时间
- 指令链路可用性
- 最近一次 `PilotReport` 类型
- 最近一次 `PilotReport` 时间
- `rep_wilco_flag`
- `rep_unable_flag`
- `rep_on_station_flag`
- `rep_rtb_flag`

## 6. 长机层动作空间

长机层动作不直接输出舵面。

推荐使用“命令选择 + 命令绑定参数”的混合动作，而不是“离散阶段动作 + 通用连续参考参数”。

### 6.1 离散动作头
- `ACT_KEEP_CURRENT`
- `ACT_SELECT_ROUTE_CAP`
- `ACT_SELECT_RTB`
- `ACT_ARM_APPROACH`
- `ACT_COMMIT_LAND`
- `ACT_ABORT_TO_HOLD`
- `ACT_UPDATE_REPORT`

### 6.2 命令绑定参数头

不同 `command_code` 仅开放与其语义一致的参数槽位。

`command_code = 1` (`Takeoff / Departure`)
- 不开放通用 `heading / altitude / speed` 自由参数。
- 允许选择：`departure_profile_id`、`departure_runway_id`、`formation_template_id`

`command_code = 3` (`Route / LNAV`)
- 开放：`route_ref` 或 `route_points`
- 开放：`target_altitude_m`
- 开放：`target_speed_mps`
- 条件开放：`target_heading`
  仅当实现明确将其定义为当前航段 track bug 时有效。

`command_code = 4` (`Landing / Final`)
- 开放：`recovery_base_id`
- 开放：`recovery_runway_id`
- 开放：`recovery_approach_type`
- 开放：`commit_to_land`
- 不开放通用 `target_heading / target_altitude / target_speed` 连续偏置
  这些量应由已选 recovery procedure 与执行层终端逻辑生成。

通用附加参数：
- `formation_offset_x_m`
- `formation_offset_y_m`
- `formation_offset_z_m`
- `report_type`
- `report_status_value`

说明：
- 长机层可以决定“走哪条 route”“回哪条跑道”“何时切回收”。
- 长机层不应在所有命令下都直接生成一组裸 `cmd_heading / cmd_altitude / cmd_speed`，否则会再次把任务层和执行层混在一起。

## 7. LeaderIntent 与 MissionCommand 映射

`LeaderIntent` 是长机层内部输出对象，随后映射为当前引擎可消费的 `MissionCommand`。

### 7.1 LeaderIntent 字段
- `phase_id`
- `command_code`
- `route_ref` 或 `route_points_ref`
- `recovery_base_id`
- `recovery_runway_id`
- `recovery_approach_type`
- `target_altitude_m`
- `target_speed_mps`
- `target_heading`
  仅在 `command_code = 3` 且系统明确定义为航段 track bug 时有效。
- `formation_id`
- `form_offset_x`
- `form_offset_y`
- `form_offset_z`
- `assigned_target_id`
- `authorization_to_fire`
- `approach_armed`
- `commit_to_land`
- `abort_flag`

### 7.2 当前 MissionCommand 数值约定

与当前仓库保持兼容：
- `0 = Idle`
- `1 = Takeoff / Departure`
- `2 = Vector / Cruise`
- `3 = Route / LNAV`
- `4 = Landing / Final`

未来可扩展保留：
- `5 = Tactical Intercept / Attack`
- `6 = RTB / Recovery Transit`

### 7.3 映射规则
- `PHASE_TAKEOFF / PHASE_DEPARTURE` -> `command_code = 1`
- `PHASE_TRANSIT_TO_STATION / PHASE_ESTABLISH_CAP / PHASE_ON_STATION / PHASE_REPOSITION / PHASE_RTB` -> `command_code = 2 or 3`
- `PHASE_APPROACH_ARMED / PHASE_LANDING_FINAL / PHASE_ROLLOUT` -> `command_code = 4`

重要约束：
- 长机层必须有权在满足终端几何条件时提前切入 `command_code = 4`
- 不应再把 `ScenarioLoader.post_waypoint_transition` 作为唯一切相源
- `MissionCommand` 的参数解释必须随 `command_code` 切换，不允许把 `heading / altitude / speed` 视为全命令共享的自由变量

### 7.4 参数归属矩阵

`C2 -> TaskOrder`
- 负责：任务类型、任务区、进出条件、altitude/speed block、在站要求、回收基地/跑道/进近类型
- 不负责：瞬时操纵、terminal final 的逐拍调节

`Leader -> LeaderIntent`
- 负责：阶段选择、命令选择、route 选择、recovery 选择、报告与提交时机
- 不负责：把 terminal final 当成通用 heading 偏置控制问题

`Execution -> PilotAction`
- 负责：轨迹跟踪、能量管理、着陆控制、终端程序跟踪
- 不负责：改变任务线程本身

## 8. 执行层与飞行员回报

### 8.1 PilotReport

执行层回报应对齐 [rep.md](../rep.md)。

最小回报集合：
- `REP_WILCO`
- `REP_UNABLE`
- `REP_ON_STATION`
- `REP_RTB`
- `WARN_BINGO`

回报字段：
- `report_type`
- `sender_id`
- `task_id`
- `phase_id`
- `timestamp_s`
- `status_value`
- `entity_ref`
- `location_x_m`
- `location_y_m`
- `location_z_m`

### 8.2 设计原则
- `PilotReport` 由执行层或脚本/规则桥接逻辑发出
- 长机层根据回报修正 phase，而不是只依赖隐式状态推断

## 9. RL 架构建议

### 9.1 第一阶段
- `C2`：脚本化
- `长机层`：规则实现
- `执行层`：现有脚本/残差控制

目标：先建立稳定接口与链路，不引入训练不稳定因素。

### 9.2 第二阶段
- `C2`：脚本化
- `长机层`：RL 训练
- `执行层`：冻结

训练目标：
- 学会 CAP 子阶段展开
- 学会返航与回收时机
- 学会提前 arm terminal / landing
- 学会 route / recovery 选择
- 不让长机层学习所有命令共享的一组通用飞控参数

### 9.3 第三阶段
- `C2`：可选 RL 或规则增强
- `长机层`：RL
- `执行层`：冻结或小步联合微调

## 10. 与当前引擎的对接要求

仓库内已有以下可直接复用能力：
- `MissionCommand`
- `PilotAction`
- `CommandLink`
- `DataLink`
- `CommQueue`
- `ActionMapping`
- `InstrumentState` 中的 command bugs

下一步新增/改造要求：
- 新增 `TaskOrder` 组件或 Python 侧对象
- 新增 `LeaderIntent`
- 新增 `PilotReport`
- 为 `MissionCommand` 增加链路延迟投递能力
- 将消息字段从 `ActionCommand` 中逐步迁出
- 将 `CommMsgType` 的完整枚举暴露到 Python

## 11. 实施顺序

建议按以下顺序实施：

1. 定义数据结构
- `TaskOrder`
- `LeaderIntent`
- `PilotReport`

2. 实现脚本 C2
- 支持 `TASK_SCRAMBLE`
- 支持 `TASK_CAP`
- 支持 `TASK_RTB`
- 支持 `TASK_RECOVER_LAND`

3. 实现规则版长机层
- 先解决任务展开与 phase 切换
- 先替代当前被动 `mission_code` 切换

4. 接入 RL 长机层
- 固定执行层
- 使用上述标准观测和动作空间训练

5. 逐步扩展多机/编队/通信损伤
