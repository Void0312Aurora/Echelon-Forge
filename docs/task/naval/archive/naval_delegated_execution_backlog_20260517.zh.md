# 海战后续委派执行单

状态：`2026-05-17` 执行准备版。

关联文档：

- [海战现实性分析](../flight_dynamics/naval/naval_realism_analysis_20260516.zh.md)
- [海战现实性分层清单与当前场景下一步计划](./naval_realism_layering_and_next_step_plan_20260516.zh.md)

本文档定位：

- 本文档把已完成的核验结论转成可直接委派给 subagent / worker 的执行任务。
- 本文档不重复论证“问题是否存在”，只回答“下一步先做什么、谁来做、验收什么”。
- 本文档默认延续当前最小海战 MVP 思路，不直接跳入完整舰队级高保真海战。

## 一、当前建议

下一步不建议我自己铺开做大而全主线，而是直接按领域复用现有 subagent 分发任务。

推荐执行顺序：

1. 先开 `P0/P1` 的三条并行线：
   - `海上态势感知 MVP`
   - `舰船运动/海况 MVP`
   - `红方占位替换 + 数据链/C2 收敛`
2. 第二波再开：
   - `舰载武器链 MVP`
   - `舰艇毁伤状态机 MVP`
3. 第三波再开：
   - `声纳/ASW MVP`
   - `舰载机协同 MVP`
   - `UNREP/后勤 MVP`

原因：

- 第一波都能在现有结构上增量推进，文件写集相对容易拆开。
- 第二波要依赖第一波提供更可信的目标、态势和任务链。
- 第三波价值高，但涉及更多新系统与跨模块耦合，放在前两波后面更稳。

## 二、委派映射

### 2.1 Wegener

负责：`舰船运动/海况`

建议任务：

1. `N-MOTION-01` 低速舵效与无舵速阈值补完
2. `N-MOTION-02` 最小海况输入入口
3. `N-MOTION-03` 波浪姿态代理
4. `N-MOTION-04` 波浪增阻最小耦合

主要文件：

- [src/systems/naval/ship_motion_system.h](../../../src/systems/naval/ship_motion_system.h)
- [src/components/naval/ship_platform.h](../../../src/components/naval/ship_platform.h)
- [src/content/unit_definition_loader.cpp](../../../src/content/unit_definition_loader.cpp)
- [examples/config/database/ships/units/ddg51_flight_i_uss_arleigh_burke.json](../../../examples/config/database/ships/units/ddg51_flight_i_uss_arleigh_burke.json)
- [examples/config/database/ships/units/take1_usns_lewis_and_clark.json](../../../examples/config/database/ships/units/take1_usns_lewis_and_clark.json)
- [tests/runtime/naval/test_naval_ship_database.py](../../../tests/runtime/naval/test_naval_ship_database.py)

验收要点：

- 近零速时纯改航向指令不应明显转头。
- `sea_state=0` 时行为与现状一致。
- `sea_state>0` 时 `roll/pitch` 不再永久为零且有界。
- 高海况下稳态航速低于平海面。

### 2.2 Hilbert

负责：`舰载雷达/ESM、声纳/ASW、舰载机协同`

建议任务：

1. `N-SENS-01` 多传感器挂载
2. `N-SENS-02` 海上雷达特化字段与探测损失
3. `N-SENS-03` 舰载 ESM MVP
4. `N-ASW-01` `Submarine + Sonar` 基础类型与加载
5. `N-ASW-02` 水声 MVP runtime
6. `N-HELO-01` 舰载机协同 token MVP

主要文件：

- [src/content/unit_definition.h](../../../src/content/unit_definition.h)
- [src/content/unit_definition_loader.cpp](../../../src/content/unit_definition_loader.cpp)
- [src/models/core/default_unit_factory.h](../../../src/models/core/default_unit_factory.h)
- [src/components/systems/sensor.h](../../../src/components/systems/sensor.h)
- [src/models/systems/default_sensor_model.cpp](../../../src/models/systems/default_sensor_model.cpp)
- [src/components/systems/ew.h](../../../src/components/systems/ew.h)
- [src/core/engine/simulation_kernel_observation_api.cpp](../../../src/core/engine/simulation_kernel_observation_api.cpp)
- 新增建议：
  - [src/components/systems/sonar.h](../../../src/components/systems/sonar.h)
  - [src/core/interfaces/acoustic_model.h](../../../src/core/interfaces/acoustic_model.h)
  - [src/models/systems/default_acoustic_model.cpp](../../../src/models/systems/default_acoustic_model.cpp)
  - [src/systems/systems/sonar_system.h](../../../src/systems/systems/sonar_system.h)
  - [src/components/naval/embarked_air_ops.h](../../../src/components/naval/embarked_air_ops.h)

验收要点：

- DDG 能同时挂多传感器与被动侦察组件。
- 海况/地平线/可选 ducting 能改变水面雷达探测结果。
- 敌方辐射源可触发 bearing-only ESM 告警。
- 潜艇与声纳 JSON 可加载，声学接触能进入观测。
- `LaunchHelo / RecoverHelo / RelayOTHTargeting` 至少有 token 级闭环。

### 2.3 Galileo

负责：`舰载武器链、舰艇毁伤`

建议任务：

1. `N-WEAPON-01` 舰载武器运行时结构落库
2. `N-WEAPON-02` `VLS-SAM` 最小发射链
3. `N-WEAPON-03` 主炮与 `CIWS` 简化交战器
4. `N-DAMAGE-01` 舰艇毁伤状态机
5. `N-DAMAGE-02` 持续毁伤传播

主要文件：

- [src/components/combat/weapon.h](../../../src/components/combat/weapon.h)
- [src/content/unit_definition.h](../../../src/content/unit_definition.h)
- [src/content/unit_definition_loader.cpp](../../../src/content/unit_definition_loader.cpp)
- [src/models/core/default_unit_factory.h](../../../src/models/core/default_unit_factory.h)
- [src/core/engine/simulation_kernel_weapon_api.cpp](../../../src/core/engine/simulation_kernel_weapon_api.cpp)
- [src/components/combat/damage.h](../../../src/components/combat/damage.h)
- [src/components/combat/health.h](../../../src/components/combat/health.h)
- [src/models/weapons/default_effects_model.cpp](../../../src/models/weapons/default_effects_model.cpp)
- [src/systems/combat/damage_system.h](../../../src/systems/combat/damage_system.h)

验收要点：

- DDG 的 `VLS / gun / CIWS` 能以结构化数据加载。
- 有航迹时才能发射 `VLS-SAM`，库存与冷却生效。
- 舰船命中后能出现 `mission kill / mobility kill / sensor kill` 等中间态。
- 轻伤不会立刻沉没，重伤可在持续传播后进入丧失状态。

### 2.4 Nietzsche

负责：`红方占位替换、屏护/编队控制、数据链/C2、后勤`

建议任务：

1. `N-RED-01` 红方占位舰替换为最小敌水面战斗舰模板
2. `N-C2-01` 屏护/编队最小闭环调稳
3. `N-C2-02` 数据链去洪泛与任务群级共享
4. `N-LOG-01` UNREP/后勤抽象库存版

主要文件：

- 新增建议：[examples/config/database/ships/units/red_surface_combatant_minimal.json](../../../examples/config/database/ships/units/red_surface_combatant_minimal.json)
- [scenarios/naval/ddg51_take1_screen_contact_report_v1.json](../../../scenarios/naval/ddg51_take1_screen_contact_report_v1.json)
- [scenarios/naval/ddg51_take1_screen_closing_contact_v1.json](../../../scenarios/naval/ddg51_take1_screen_closing_contact_v1.json)
- [gym_envs/scenario_loader/behavior_runtime/naval_screen.py](../../../gym_envs/scenario_loader/behavior_runtime/naval_screen.py)
- [gym_envs/scenario_loader/behavior_runtime/command_chain.py](../../../gym_envs/scenario_loader/behavior_runtime/command_chain.py)
- [src/systems/systems/data_link_system.h](../../../src/systems/systems/data_link_system.h)
- [src/systems/systems/track_manager_system.h](../../../src/systems/systems/track_manager_system.h)
- [src/components/command/common/comm_message.h](../../../src/components/command/common/comm_message.h)
- [src/components/systems/logistics.h](../../../src/components/systems/logistics.h)
- [src/systems/systems/logistics_system.h](../../../src/systems/systems/logistics_system.h)

验收要点：

- 红方不再复用 `T-AKE-1`。
- `TASK_SCREEN` 在受扰后能稳定朝目标站位恢复。
- 航迹共享消息不再每步洪泛。
- `T-AKE` 与 `DDG` 至少有抽象库存与补给窗口状态机。

## 三、推荐并行波次

### 3.1 第一波

建议立即并行开三条：

1. `Hilbert`：`N-SENS-01 / N-SENS-02 / N-SENS-03`
2. `Wegener`：`N-MOTION-01 / N-MOTION-02 / N-MOTION-03`
3. `Nietzsche`：`N-RED-01 / N-C2-02`

理由：

- 写集大体可分离。
- 这三条会直接改善“看得见、动得像、目标不再是错舰型”这三个最显眼缺口。

### 3.2 第二波

第一波合入后再开：

1. `Galileo`：`N-WEAPON-01 / N-WEAPON-02 / N-DAMAGE-01`
2. `Nietzsche`：`N-C2-01`

理由：

- 武器链和毁伤链需要建立在更可信的目标、态势和站位控制之上。
- 屏护闭环调稳要利用第一波的新目标与共享语义来校正行为。

### 3.3 第三波

第二波稳定后再开：

1. `Hilbert`：`N-ASW-01 / N-ASW-02`
2. `Hilbert` 或新 worker：`N-HELO-01`
3. `Nietzsche`：`N-LOG-01`
4. `Galileo`：`N-WEAPON-03 / N-DAMAGE-02`

理由：

- ASW、舰载机与后勤都跨系统更深。
- 这时基础平台、目标、武器和消息语义都更稳，返工风险更低。

## 四、数据使用口径

所有后续任务统一采用下面的注记规则：

1. `官方/半官方公开事实`
   - 可用于：舰型、装备族、系统用途、任务分工、平台边界。
   - 例：DDG-51 装备族、`SQQ-89`/`SLQ-32`/`MH-60R` 是否存在及用途。

2. `专业公开资料`
   - 可用于：海杂波、波导、汇聚区、水声传播、波浪增阻、火控链机理。
   - 需要在文档或 JSON 里标成“公开机理/工程近似依据”。

3. `社区/非官方资料`
   - 只用于：初始工程量级、经验参数、保守校准起点。
   - 必须显式标成 `engineering calibration` 或 `community-derived approximation`。

4. `禁止当硬事实写死`
   - DDG-51 精确战术直径、固定海况掉速、Harpoon 特定批次公开射程、具体隔舱数、穿透舱段数、精确声纳探测距离。

## 五、直接可发出的主任务

如果下一轮直接开工，我建议先发这三个主任务，而不是我亲自继续铺：

1. 给 `Hilbert`：多传感器 + 海上雷达特化 + 舰载 ESM MVP
2. 给 `Wegener`：海况输入 + 波浪姿态代理 + 低速舵效补完
3. 给 `Nietzsche`：红方最小敌舰模板 + 数据链去洪泛 + 屏护闭环调稳

这三条完成后，再决定是否让 `Galileo` 开 `VLS-SAM + damage state`。
