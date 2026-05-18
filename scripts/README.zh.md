<!-- Machine-translated draft generated on 2026-05-18 from scripts/README.md. Review before treating this file as authoritative. -->

# Scripts README

`scripts/` 现在只保留一小部分面向操作人员的工作流脚本，这些脚本在维护的 Python 入口点（位于 `tools/`）之外仍能提供价值。

当前保留的脚本：

- [benchmark_multi_agent.py](benchmark_multi_agent.py)
  - 用于 `python.rl.support.multi_agent_benchmark.main` 的轻量兼容启动器。
  - 保留原因：现有性能规划文档中引用了它。
- [eval_hmoe_strict_terminal.sh](eval_hmoe_strict_terminal.sh)
  - 用于严格端点 HMoE 与共享协作评估运行的便捷 shell 脚本。
- [run_hmoe_cooperative_takeoff_to_cruise_control.sh](run_hmoe_cooperative_takeoff_to_cruise_control.sh)
  - 用于维护的 HMoE 公平性流程的组合训练/评估控制脚本。
- [train_cruise_waypoints_pipeline.sh](train_cruise_waypoints_pipeline.sh)
  - 遗留但仍可使用的世界模型航点训练管道。

维护指南：

- 新维护的工作流应优先使用 `tools/` 入口点加配置文件，而不是在 `scripts/` 中创建新的 shell 包装脚本。
- 保留的 shell 工作流应引用 [tools/maintenance/cmo_env.sh](../tools/maintenance/cmo_env.sh)，
  以使 `.venv` 和构建目录检测保持一致。
- 如果某个脚本变得过时或特定于某台机器，请将其归档到 `tools/archive/legacy_scripts/`。
- 工作区清理辅助程序归属于 `tools/maintenance/`，而不是此处。
