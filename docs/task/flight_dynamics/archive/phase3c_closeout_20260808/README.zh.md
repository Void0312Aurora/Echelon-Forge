# Flight Dynamics Tasks

语言版本：

- 英文主文：[README.md](README.md)
- 中文辅文：`README.zh.md`

本目录是 `flight_dynamics` 真实性分析收口流的历史/参考导航入口。它记录了
flight、sensor、weapon、naval 与 C2 分析拆分如何进入当前多域任务树。当前活跃
工作应从 [../README.zh.md](../../../archive/owner_migration_20260808/README.zh.md) 以及 air combat、naval、ground、
simulation architecture 等领域入口开始。

若要判断本历史流的状态，优先看各分析文档中的 `2026-05-18` 收口标记，不要再把
`archive/program/` 或 `archive/` 当作当前参考来源。

## 历史子项目导航

- [flight 子项目](flight/README.md): 飞行动力学、推进、失速 / 高 AoA 相关分析。
- [sensor_situation 子项目](sensor_situation/README.md): 传感器、航迹、数据链态势感知分析。
- [weapon_guidance 子项目](weapon_guidance/README.md): 武器链、导引头、制导与近炸 / 毁伤分析。
- [naval 子项目](naval/README.md): 历史海战真实性分析；当前工作应转向活跃 naval task line。
- [c2_command_chain 子项目](c2_command_chain/README.md): `MissionCommand / CommandLink / DataLink / ROE / naval command-chain` 冻结分析基线。
- [program 子目录](../program/README.md): 已失效的主线状态快照入口，仅保留历史留痕。

## 跨目录关联入口

- [task 根目录](../../../archive/owner_migration_20260808/README.zh.md):
  当前多域 task-area 导航与生命周期标签。
- [air_combat 任务目录](../../../air_combat/archive/owner_migration_20260808/README.zh.md):
  当前战斗与空域工作线入口。
- [naval 任务目录](../../../naval/archive/owner_migration_20260808/README.md):
  活跃海军领域任务线。
- [ground 任务目录](../../../ground/archive/owner_migration_20260808/README.zh.md):
  早期地面 tasking/native-schema bootstrap 线。
- [simulation_architecture 任务目录](../../../simulation_architecture/archive/phase3c_closeout_20260808/README.md):
  共享 runtime、contract、facade 与架构收口线。
- [保留的 runtime 性能规划历史](../../../archive/performance_runtime/README.zh.md):
  只提供已归档的规划上下文，不是当前执行入口。

## 推荐起点

- [飞行动力学现实性分析与空战前置门槛](flight/flight_dynamics_realism_analysis_20260516.zh.md):
  以分析文档收口标记为准的飞行动力学当前口径。
- [传感器与态势感知现实性分析](sensor_situation/sensor_situation_realism_analysis_20260516.zh.md):
  以分析文档收口标记为准的传感器/数据链当前口径。
- [武器系统与制导回路现实性分析](weapon_guidance/weapon_guidance_realism_analysis_20260516.zh.md):
  以分析文档收口标记为准的武器链当前口径。
- [海战仿真现实性分析](naval/naval_realism_analysis_20260516.zh.md):
  以分析文档收口标记为准的海战当前口径。
- [指挥链与 C2 通信现实性分析](c2_command_chain/c2_command_chain_realism_analysis_20260517.zh.md):
  以补记中的收口标记为准的 C2 当前口径。

## 文档组织约定

1. 每个子方向使用一个子项目文件夹，并由该目录下的 `README.md` 作为本地导航入口。
2. `*_analysis_*` 文档中的 `2026-05-18` 收口标记是当前可信口径。
3. `archive/program/` 已失效，`archive/` 仅保留历史留痕。
4. 不在本目录下新开活跃多域实现流；新工作应通过 task 根目录和当前领域入口承接。

已归档子项目的完整清单见 [归档注册表](archive_registry.zh.md)。
