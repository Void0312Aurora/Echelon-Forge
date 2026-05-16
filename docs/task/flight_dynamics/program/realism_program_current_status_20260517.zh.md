# 真实化主线与关联子项目当前状态

状态：`2026-05-17` 当前工作区复核版。

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

- `P0` / `P1` 文档仍然有效，作为实现方向和分层规划没有失效。
- 但当前工作区复核显示，这条线还没有完全稳定。
- 目前最明确的红点是：
  - [tests/runtime/test_flight_dynamics_realism_guards.py](/home/void0312/Workshop/CMO/tests/runtime/test_flight_dynamics_realism_guards.py) 中 `test_full_throttle_improves_specific_energy_relative_to_idle`

含义：

- 全油门相对怠速的比能改善趋势当前没有满足守门合同。
- 说明推进、阻力或相关共享状态语义仍有回归或漂移。

### 2.2 传感器/态势主线

当前判断：

- `SNR/Pd`、`M-of-N`、`alpha-beta`、`track/report` 语义的大方向仍然是对的。
- 但当前工作区复核显示，`P0` 合同里仍有 3 条失败：
  - [tests/runtime/test_sensor_situation_realism_p0.py](/home/void0312/Workshop/CMO/tests/runtime/test_sensor_situation_realism_p0.py)
    - `test_confirmed_and_coasted_tracks_expose_different_usability_semantics`
    - `test_datalink_report_becomes_visible_track_without_fabricating_local_contact`
    - `test_datalink_track_report_does_not_create_local_contact`

含义：

- `coasted track` 的可见性/可用性语义还没有完全守住。
- `datalink report` 不应伪造成本地 contact 的旧合同当前再次被打破。
- 这会直接影响空战和海战上层对“本地探测 vs 共享航迹”的区分。

### 2.3 武器/制导主线

当前判断：

- 本轮复核里，武器/制导守门测试没有暴露新的红点。
- 导弹 `truth cut`、最小 `3DoF`、`PN accel surrogate` 主线目前仍可视为成立。
- 但它仍依赖飞行动力学和传感器链的共享语义稳定；一旦上游漂移，武器链的解释也会跟着变。

### 2.4 海战子项目

当前判断：

- 海战已经从最小屏护接触样例推进到了战术原型：
  - 海况/运动
  - 多传感器/ESM/声纳/helo token
  - 红方模板 / datalink / screen
  - `UNREP`
  - `VLS-SAM / gun / CIWS / 持续毁伤`
- 但当前最明确的稳定性红点就在海战 `screen-hold`：
  - [tests/runtime/test_naval_screen_scenario.py](/home/void0312/Workshop/CMO/tests/runtime/test_naval_screen_scenario.py)
    - `test_screen_station_hold_recovers_after_heading_disturbance`
    - `test_screen_station_hold_settles_without_large_late_oscillation`

当前工作区实际复核结果：

- [tests/runtime/test_naval_ship_database.py](/home/void0312/Workshop/CMO/tests/runtime/test_naval_ship_database.py) 中 `UNREP / abstract_naval_stores / maritime_state_environment_override / multi_sensor_and_passive_esm_suite` 定向子集为绿
- [tests/runtime/test_naval_screen_scenario.py](/home/void0312/Workshop/CMO/tests/runtime/test_naval_screen_scenario.py) 当前是 `2 failed, 6 passed`

含义：

- `UNREP` 这条线已经比之前稳定得多。
- 现在真正需要优先复核的是 `screen-hold` 恢复逻辑，而不是继续把海战范围铺得更大。

### 2.5 空战 1v1 子项目

当前判断：

- `F-16C vs F-16C` 的 canonical 基线、最小导弹释放桥、红方脚本基线仍然成立。
- 但当前工作区复核显示 1 条 fixture 语义失败：
  - [tests/runtime/test_air_combat_1v1_fixture.py](/home/void0312/Workshop/CMO/tests/runtime/test_air_combat_1v1_fixture.py)
    - `test_loader_fixture_exposes_hostile_contact_and_weapon_state`

失败现象：

- hostile track 的 `classification` 当前为 `0`，而测试预期是 `2`

含义：

- 当前敌我/分类/IFF 相关语义仍存在漂移。
- 这条问题更像传感器/态势合同漂移对空战 fixture 的投影，而不是 1v1 场景自身单独坏掉。

### 2.6 C2 / 指挥链分析线

当前判断：

- 当前 `C2` 方向已经从单篇冻结分析扩展成独立子项目入口：
  - [C2 指挥链与通信子项目](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/c2_command_chain/README.md)
  - [C2 指挥链与通信推进检查点](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/c2_command_chain/c2_command_chain_progress_checkpoint_20260517.zh.md)
  - [C2 指挥链与通信待解决问题分析](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/c2_command_chain/c2_command_chain_unresolved_issues_20260517.zh.md)
- 这意味着原 [指挥链与 C2 通信现实性分析](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/c2_command_chain/c2_command_chain_realism_analysis_20260517.zh.md) 仍然是基线，但已经不能再被当成“当前完全未动”的状态。
- 当前已明确落地的最小收口包括：
  - `PilotAction` 与 `MissionCommand` 的 deadband 接管边界
  - 海军 `MissionCommand` 最小站位字段与 `Ship` authority 主写统一
  - `ROE / engagement authority` 最小字段与 runtime gate
  - `CommandLink` 的最小 FIFO 语义澄清
  - `DataLink` 的消息/报告双预算与 drop 可观测性
- 当前仍待解决的重点则转向：
  - `CommandLink` priority / jitter / retry
  - `DataLink` relay / jamming / tasking doctrine
  - 更深的 naval tasking 语义
  - `ROE / authority` 尚未进入完整任务与通信闭环

## 三、当前复核到的稳定性问题

### 3.1 已复现失败

1. 飞行动力学：
   - [tests/runtime/test_flight_dynamics_realism_guards.py](/home/void0312/Workshop/CMO/tests/runtime/test_flight_dynamics_realism_guards.py)
   - `test_full_throttle_improves_specific_energy_relative_to_idle`
2. 传感器/态势：
   - [tests/runtime/test_sensor_situation_realism_p0.py](/home/void0312/Workshop/CMO/tests/runtime/test_sensor_situation_realism_p0.py)
   - `coasted track` 语义失败 1 条
   - `datalink report 不伪造本地 contact` 语义失败 2 条
3. 海战：
   - [tests/runtime/test_naval_screen_scenario.py](/home/void0312/Workshop/CMO/tests/runtime/test_naval_screen_scenario.py)
   - `screen-hold` 恢复/收敛失败 2 条
4. 空战 1v1：
   - [tests/runtime/test_air_combat_1v1_fixture.py](/home/void0312/Workshop/CMO/tests/runtime/test_air_combat_1v1_fixture.py)
   - hostile track `classification` 语义失败 1 条

### 3.2 当前已验证为绿色的关键面

1. 海战 `UNREP / abstract stores / maritime override / multi-sensor+ESM` 定向子集通过
2. 海战 `sensor + ASW + helo` 定向子集由 subagent 回执为绿，本轮未复现新红点
3. 武器/制导守门线本轮没有出现新的失败

### 3.3 低置信度噪声

目前只作为备注保留，不计入当前已复现失败：

1. subagent 回执曾提到 `pytest` 环境下偶发 `MemoryError / nanobind` 观测读取噪声
2. 本轮我没有在当前工作区直接复现这一条，因此先不把它上升为主稳定性问题

## 四、建议的后续处理顺序

建议按下面顺序收问题，而不是继续把实现面铺得更大：

1. 先修海战 `screen-hold`
   - 这是当前最明确、最稳定可复现的行为回归
   - 且它直接影响海战“护航/屏护是否成立”的主语义
2. 再收传感器/态势合同漂移
   - `coasted track`
   - `datalink report != local contact`
   - hostile `classification`
3. 再回头收飞行动力学全油门比能测试
   - 避免继续在能量语义漂移的状态上谈更深物理
4. 最后再考虑继续扩功能
   - 更复杂 maritime 联动
   - 更深 naval tasking / fire-control
   - 更完整空战训练入口

## 五、当前最推荐的文档入口

如果下一轮要继续推进，建议优先看：

1. [真实化 P1 任务总表](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/program/realism_program_p1_taskboard_20260517.zh.md)
2. [海战推进检查点](/home/void0312/Workshop/CMO/docs/task/naval/naval_progress_checkpoint_20260517.zh.md)
3. [空战 1v1 F-16C 基线切换与最小对战合同进展](/home/void0312/Workshop/CMO/docs/task/air_combat/air_combat_1v1_f16c_baseline_progress_20260516.zh.md)
4. [C2 指挥链与通信子项目](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/c2_command_chain/README.md)
5. 本文档

这样看的好处是：

- 不会把 `flight_dynamics/` 下的冻结分析误当成当前执行状态
- 能直接看到“主线规划”和“当前稳定性现实”之间的差距
