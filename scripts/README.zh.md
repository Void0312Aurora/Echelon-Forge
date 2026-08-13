# Scripts README

`scripts/` 现在只保留一小部分面向操作人员的工作流脚本，这些脚本在维护的 Python 入口点（位于 `tools/`）之外仍能提供价值。
当前保留脚本是 air/execution 或 cooperative/HMoE workflow shell，不是通用多域产品入口。

当前保留的脚本：

- [benchmark_cuda_resident_rb9.py](benchmark_cuda_resident_rb9.py)
  - 将分别构建的 RB9 CPU/CUDA 诊断证据报告合并为一份临时对比，且不越界成为
    maintained-backend 的结论。
  - 被 `tests/architecture/runtime_profiles/test_cuda_resident_performance.py` 直接导入，
    因此它是受测试覆盖的模块，而不仅是操作人员 shell。
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
- 新的 naval 或 ground workflow 应先落为 maintained `tools/` 入口，再考虑在这里增加 convenience shell。
- 保留的 shell 工作流应引用 [tools/maintenance/cmo_env.sh](../tools/maintenance/cmo_env.sh)，
  以使 `.venv` 和构建目录检测保持一致。
- 如果某个脚本变得过时或特定于某台机器，请直接删除并在 `tools/README.md` 的退役登记中留一行（git 历史即归档）。
- 工作区清理辅助程序归属于 `tools/maintenance/`，而不是此处。
