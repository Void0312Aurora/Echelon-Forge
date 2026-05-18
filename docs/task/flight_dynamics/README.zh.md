# Flight Dynamics Tasks

语言版本：

- 英文主文：[README.md](README.md)
- 中文辅文：`README.zh.md`

本目录是 `flight_dynamics` 真实性主线的导航入口。各子目录下的 dated
文档是针对某一轮分析、实施包、任务板或检查点的工作快照；需要了解当前上下文时，优先从子项目
`README.md` 或最新的状态 / 任务板 / 检查点文档开始，而不是把单篇分析文档当作全局现状。

## 子项目导航

- [program 子项目](./program/README.md): 主线状态、总任务板、阶段排期入口。
- [flight 子项目](./flight/README.md): 飞行动力学、推进、失速 / 高 AoA 相关分析与实施包。
- [sensor_situation 子项目](./sensor_situation/README.md): 传感器、航迹、数据链态势感知方向文档。
- [weapon_guidance 子项目](./weapon_guidance/README.md): 武器链、导引头、制导与近炸 / 毁伤真实化文档。
- [naval 子项目](./naval/README.md): 海战真实性冻结分析与主线关联说明。
- [c2_command_chain 子项目](./c2_command_chain/README.md): `MissionCommand / CommandLink / DataLink / ROE / naval command-chain` 推进线。

## 推荐起点

- [真实化主线与关联子项目当前状态](./program/realism_program_current_status_20260517.zh.md):
  program 主线当前状态总览。
- [真实化 P1 任务总表](./program/realism_program_p1_taskboard_20260517.zh.md):
  当前拆分后的 `P1` 任务板。
- [C2 指挥链与通信推进检查点](./c2_command_chain/c2_command_chain_progress_checkpoint_20260517.zh.md):
  C2 / 数据链方向最新检查点。
- [海战推进检查点](../naval/naval_progress_checkpoint_20260517.zh.md): 位于
  `docs/task/naval/` 的跨目录海战推进检查点，和本主线仍然联动。

## 文档组织约定

1. 每个子方向使用一个子项目文件夹，并由该目录下的 `README.md` 作为本地导航入口。
2. `*_analysis_*` 文档保留冻结分析口径，不应单独视为最新实现状态。
3. `*_implementation_package_*`、`*_taskboard_*`、`current_status`、`progress checkpoint`
   和 `unresolved issues` 文档分别承载实施范围、排期或最新跟踪状态。
4. 新方向若继续拆分，应先建新子文件夹和入口页，再补充分析或实施文档。
