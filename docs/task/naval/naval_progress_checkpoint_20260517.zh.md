# 海战推进检查点

状态：`2026-05-17` 第三波主体完成、与主线复核对齐版。

关联文档：

- [海战现实性分析](../flight_dynamics/naval/naval_realism_analysis_20260516.zh.md)
- [海战现实性分层清单与当前场景下一步计划](naval_realism_layering_and_next_step_plan_20260516.zh.md)
- [海战后续委派执行单](naval_delegated_execution_backlog_20260517.zh.md)

本文档定位：

- 本文档用于回收已完成 subagent 工作的实际产出。
- 本文档回答“已经做到了哪里、哪些风险还在、接下来继续派什么”。
- 本文档默认延续最小海战 MVP 路线，不把当前进展夸大为完整高保真海战。

## 一、已完成项

### 1.1 Wegener：舰船运动/海况

已完成：

1. `N-MOTION-01` 低速舵效与无舵速阈值
2. `N-MOTION-02` 最小 `sea_state` 输入入口
3. `N-MOTION-03` 波浪姿态代理
4. `N-MOTION-04` 波浪增阻最小耦合
5. 海况环境级抬升补丁
6. maritime state merge/fallback 规则收束

当前效果：

- 近零速时纯改航向指令不再明显转头。
- `sea_state=0` 与旧行为兼容。
- `sea_state>0` 时舰船 `roll/pitch` 不再永久为零。
- 高海况下稳态航速会低于平海面。
- 场景层 `environment.maritime` 现在可以显式注入环境 maritime 状态；未配置时会清空覆盖并回退到平台默认。
- maritime state 的当前规则已经锁定：
  - `configured=false` 时不提供环境覆盖，继续走平台默认。
  - `configured=true` 时完整覆盖 `sea_state / wave_heading_deg / wave_period_s`，即使 `sea_state=0` 也视为显式 calm override。
  - 当前 MVP 不支持部分字段 merge。

验证：

- `tests/runtime/test_naval_ship_database.py`
- `tests/runtime/test_naval_screen_scenario.py`
- `tests/scenario/test_scenario_compiler.py`
- 回执中给出的相关结果包括：
  - `38 passed, 1 failed`
  - `5 passed, 17 deselected`
  - `3 passed, 17 deselected`

保留风险：

- maritime state 规则已经清楚，但仍然是“全覆盖或不覆盖”，尚不支持只覆盖 `wave_heading` 或只覆盖 `wave_period` 这类细粒度 merge。
- `wave_heading / wave_period` 这轮主要通过编译/场景注入和现有 ship motion 用例锁定，还没有更细的姿态相位/方向性专用 runtime 断言。

### 1.2 Hilbert：多传感器/海上雷达/ESM/ASW/舰载机

已完成：

1. `N-SENS-01` 多传感器挂载
2. `N-SENS-02` 海上雷达特化字段与 ducting 扩展
3. `N-SENS-03` 舰载 ESM MVP
4. `N-ASW-01` `Submarine + Sonar` 基础类型与加载
5. `N-ASW-02` 水声 MVP runtime
6. `N-HELO-01` 舰载机协同 token MVP
7. 海面 LOS 最小海面化修补
8. maritime state 在雷达/声纳链上的一致性消费

当前效果：

- 舰艇不再受单一主传感器假设限制。
- 单位级 `esm` 配置可以进入运行时 `ESMReceiver`。
- 海上雷达可通过公开机理近似体现地平线、海况和 ducting 对探测结果的影响。
- 航迹管理可保留 `ESM / bearing-only` 被动接触来源标记。
- 潜艇和声纳已具备最小 JSON 加载与水声接触闭环。
- 舰载直升机可形成 `LaunchHelo / RecoverHelo / RelayOTHTargeting` 的 token 级最小闭环。
- 海面单位在 maritime state 已配置时拥有最小海面化 LOS 容错路径，减少近海面 `z≈0` 目标被通用地形判定误杀。
- 海上雷达和声纳都已优先消费 `EnvironmentModel` 中的全局 maritime state，未配置时才回退到平台默认海况字段。

验证：

- `tests/runtime/test_naval_ship_database.py`
- `tests/runtime/test_naval_sensor_realism_runtime.py`
- `tests/runtime/test_naval_asw_helo_runtime.py`
- `tests/runtime/test_bindings_command_surface.py`
- `tests/runtime/test_naval_screen_scenario.py`
- 回执中给出的相关结果包括：
  - `27 passed, 1 deselected`
  - `9 tests OK`

保留风险：

- 海面 LOS 仍是最小修补，不是完整海面/地形/折射统一模型。
- 当前 ESM 仍是 MVP，更接近被动方位告警，不是完整电子支援与分类系统。
- 声学模型仍是 `engineering calibration / community-derived approximation` 级近似，不是高保真声纳。
- `RecoverHelo` 目前是 token 级“回收即归舰”，不是完整飞行甲板作业。
- 这轮为稳定性把新增一致性测试更多落在 raw detection / `snr_db` 对比上，而不是强依赖“有/无探测翻转”边界。

### 1.3 Nietzsche：红方模板/数据链/C2/后勤底座

已完成：

1. `N-RED-01` 红方占位舰替换
2. `N-C2-02` 数据链去洪泛与任务群级收敛近似
3. `N-C2-01` 小范围 screen-hold 调稳补丁
4. `N-LOG-01` 最小 `UNREP` 抽象库存与闭环

当前效果：

- 红方场景不再以 `T-AKE-1` 冒充敌水面战斗舰。
- 航迹共享由“每步全量广播”收敛为“confirmed/new-significant/refresh”触发。
- `TASK_SCREEN` 在接近目标站位后采用更平滑的捕获与保持逻辑，降低末段摆动。
- `DDG-51` 与 `T-AKE-1` 已具备抽象库存、补给窗口参数和最小观测/调试面。
- `UNREP` 现在可以走通“接近窗口 -> 建立补给 -> 转移抽象库存 -> 完成/退出”的最小链路。
- “active” 观测语义已收紧到真正开始转移库存时才算激活，因此窗口外不再误判为已经在补给。

验证：

- `tests/runtime/test_naval_screen_scenario.py`
- `tests/runtime/test_naval_ship_database.py` 中与红方模板、抽象库存和补给窗口相关的定向用例
- 海军 contract 中消息语义同步到 `ReportTrack`
- 回执中给出的相关结果包括：
  - `4 passed`
  - `10 passed, 2 failed`

保留风险：

- 当前数据链仍是工程近似，不是完整舰队 C2 / Link 管理模型。
- 当前 `UNREP` 最小闭环已打通，但仍是抽象库存状态机，不是完整补给 doctrine 或细致作业流程。
- `screen-hold` 当前不再作为稳定红点保留；当前更值得关注的是海事传感器/LOS 与 `sensor/naval` 联动收口。

### 1.4 Galileo：舰载武器/毁伤

已完成：

1. `N-WEAPON-01` 舰载武器运行时结构落库
2. `N-WEAPON-02` `VLS-SAM` 最小发射链
3. `N-DAMAGE-01` 舰艇毁伤中间态
4. `N-WEAPON-03` 主炮与 `CIWS` 简化交战器
5. `N-DAMAGE-02` 持续毁伤传播
6. 舰载武器链的最小 `MissionCommand` 接入

当前效果：

- `DDG-51` 的 `VLS / gun / CIWS` 已能结构化加载。
- 舰艇可基于既有航迹走最小 `VLS-SAM` 发射链，并体现库存与冷却。
- `5in gun / CIWS` 已从纯数据库项推进到运行时结构面，但当前交战链仍未稳定收口。
- 舰艇命中后不再只有“满血或沉没”，而是可进入 `mission kill / mobility kill / sensor kill` 等中间态，并持续出现火灾、进水、破口驱动的能力退化。
- `MissionCommand -> CIWS` 的命令驱动路径已经接进主线代码，但当前工作区定向测试仍未转绿，不能描述成“已完成自动近防闭环”。

验证：

- `tests/runtime/test_naval_ship_database.py` 中与结构化武器、`VLS-SAM`、主炮、`CIWS`、中间毁伤态、持续毁伤传播相关的定向用例
- 当前工作区抽样复核结果：
  - `tests/runtime/test_naval_ship_database.py::NavalShipDatabaseTests::test_ddg_gun_can_fire_with_track_and_reduce_ammo`
  - `tests/runtime/test_naval_ship_database.py::NavalShipDatabaseTests::test_naval_mission_command_can_trigger_ciws_without_direct_weapon_api`
  - 当前结果：`2 failed`

保留风险：

- `VLS-SAM` 仍是抽象舰空导弹，不区分更细型号。
- `gun / CIWS` 现在是工程近似交战器，不是完整火控/弹道/射界/跟踪通道模拟。
- 主炮直调发射链当前未稳定通过定向回归。
- `MissionCommand -> CIWS` 命令驱动链当前未稳定通过定向回归。
- 持续毁伤传播已形成框架，但仍是标量 proxy，不是隔舱/泵/稳性/自由液面高保真模型。
- 当前接入的是最小命令驱动骨架，还不是完整 naval tasking / fire-control AI。

## 二、当前能力面判断

当前海战主线已经从“最小现实海上屏护接触场景”推进到“具备海上运动、态势感知、局部交战链和支援链雏形的战术原型”：

1. 平台层：
   - 舰船运动、低速操纵、海况代理、海况环境级入口和 maritime merge/fallback 规则已具备最小动态差异。
2. 态势层：
   - 多传感器、海上雷达、ESM、声纳、航迹共享、海面 LOS 修补和屏护闭环已经形成连续链路。
3. 支援层：
   - 舰载机 token 协同已建立最小闭环。
   - 抽象后勤库存、补给窗口和最小 `UNREP` 转移闭环已建立。
4. 交战层：
   - 已进入“最小 `VLS-SAM` + 主炮/CIWS 结构化运行时 + 中间毁伤态 + 持续毁伤传播”的可运行骨架，但主炮直调和 `MissionCommand -> CIWS` 命令链仍未稳定转绿。

但仍不能把当前状态称为完整真实海战，主要缺口仍在：

1. 海面 LOS 仍是最小修补，不是完整海面/地形/折射统一模型。
2. 舰载机仍是 token 协同，不是完整航空出动系统。
3. 武器链虽已进入命令路径，但还不是完整 naval tasking / fire-control AI。
4. 持续毁伤仍缺更真实的浮性、隔舱和稳性演化。
5. 当前海战更适合作为 `sensor/C2/runtime` 的高价值验收面，而不是独立扩功能主线。

## 三、统一数据口径

后续任务继续沿用以下规则：

1. 公开事实：
   - 可用于舰型、装备族、职责边界与平台存在性。
2. 公开专业资料：
   - 可用于海杂波、ducting、水声传播、波浪增阻、火控链等机理近似。
3. 社区/非官方资料：
   - 只用于 `engineering calibration` 或 `community-derived approximation` 级初始参数。
4. 禁止写死为硬事实：
   - 精确声纳探测距离、固定海况掉速、具体弹种真实极限性能、具体抗毁隔舱细节、真实补给 doctrine 和精确补给速率。

## 四、下一轮建议

### 4.1 当前建议

建议优先处理：

1. 海军武器命令链定向修复与守门回归
2. `DataLink / MissionCommand / naval` 共享语义的一致性补测
3. 海事传感器 / 海面 LOS / `sensor/naval` 联动守门回归

理由：

- 当前稳定复现的海军红点已经具体落在主炮直调与 `MissionCommand -> CIWS` 命令路径，而不再是泛化的 `sensor/naval` 总括。
- `screen-hold` 当前已不再适合作为独立红点继续占用主优先级。

### 4.2 次级建议

建议继续负责：

1. 如有必要，继续补一个更完整的 maritime state 联动场景
2. 复核 `pytest` 环境下偶发的观测读取 / `MemoryError` 噪声是否与当前逻辑无关

理由：

- 当前海战更需要配合主线收口传感器/联动风险，而不是继续扩大单一功能面。

### 4.3 可后置建议

建议继续负责：

1. 如有需要，可继续把主炮触发路径也接到更高层行为层
2. 继续验证 `MissionCommand` 驱动的舰载武器链在更复杂场景下的稳定性

理由：

- 当前 `CIWS` 的命令驱动路径已接入代码，但定向回归仍未转绿，下一步仍属于收口而不是纯扩展。

### 4.4 可后置建议

建议继续负责：

1. 如有必要，继续补 `wave_heading / wave_period` 的更细 runtime 断言
2. 保持 maritime state 规则文档和测试与实际实现同步

理由：

- 这条线的大结构已经完成，剩余主要是更细测试覆盖，而不是继续扩大语义。

## 五、当前优先级

建议当前按下面的顺序处理：

1. 先收口海军武器命令链的两个稳定红点。
2. 再配合主线收口 `DataLink / MissionCommand / naval` 共享语义与海事传感器联动。
3. 最后再决定是否继续扩 `MissionCommand -> gun`、更复杂 maritime 联动场景或更细 wave runtime 断言。

这样处理的好处是：

- 海战当前最值钱的角色是高价值验收面，而不是单独继续扩功能。
- 先把当前已稳定复现的海军武器命令链红点清掉，再继续扩展的收益更高。
