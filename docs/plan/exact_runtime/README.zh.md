# `exact_runtime/`

该目录包含精确运行时 / GPU 主线的候选专项计划、检查清单以及阶段冻结记录。

建议阅读顺序：

1. [cpp_exact_runtime_refactor_plan.md](cpp_exact_runtime_refactor_plan.md)
2. [gpu_execution_mainline_integration_checklist.md](gpu_execution_mainline_integration_checklist.md)
3. [gpu_execution_phase4_rollout_hot_path_freeze.md](gpu_execution_phase4_rollout_hot_path_freeze.md)
4. [gpu_exact_world_step_performance_and_parity_plan.md](gpu_exact_world_step_performance_and_parity_plan.md)
5. [gpu_resident_state_implementation_plan.md](gpu_resident_state_implementation_plan.md)

使用规则：

- 除冻结的阶段计划外，其余文档默认作为候选专项草案或检查清单。
- 当前仓库结构已有演变，文中部分代码路径仍保留历史语义。使用时请与当前代码树交叉对照。
- 早期的 GPU 主线讨论及实验性路线已移至 `../archive/`。
