# Flight Dynamics Tasks

本目录承载 `flight_dynamics` 主线下的真实性工作文档。当前已按子方向拆成独立子项目文件夹，避免把冻结分析、实施包、进展检查点和总任务板继续平铺在同一层。

## 子项目导航

- [program 子项目](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/program/README.md)
  主线状态、总任务板、阶段排期入口。
- [flight 子项目](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/flight/README.md)
  飞行动力学、推进、失速/高 AoA 相关分析与实施包。
- [sensor_situation 子项目](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/sensor_situation/README.md)
  传感器、航迹、数据链态势感知方向文档。
- [weapon_guidance 子项目](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/weapon_guidance/README.md)
  武器链、导引头、制导与近炸/毁伤真实化文档。
- [naval 子项目](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/naval/README.md)
  海战真实性冻结分析与主线关联说明。
- [c2_command_chain 子项目](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/c2_command_chain/README.md)
  `MissionCommand / CommandLink / DataLink / ROE / naval command-chain` 推进线。

## 当前优先入口

- [真实化主线与关联子项目当前状态](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/program/realism_program_current_status_20260517.zh.md)
- [真实化 P1 任务总表](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/program/realism_program_p1_taskboard_20260517.zh.md)
- [C2 指挥链与通信推进检查点](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/c2_command_chain/c2_command_chain_progress_checkpoint_20260517.zh.md)
- [海战推进检查点](/home/void0312/Workshop/CMO/docs/task/naval/naval_progress_checkpoint_20260517.zh.md)

## 文档组织约定

1. 每个子方向使用一个子项目文件夹，并由该目录下的 `README.md` 作为入口。
2. `*_analysis_*` 文档保留冻结分析口径，不直接回填后续实现进展。
3. `*_implementation_package_*`、`*_taskboard_*`、`progress checkpoint`、`unresolved issues` 分别承载实施范围、排期和当前状态。
4. 新方向若继续拆分，应先建新子文件夹和入口页，再补充分析或实施文档。
