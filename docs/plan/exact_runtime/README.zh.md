# `exact_runtime/`

语言版本：

- 英文主文：[README.md](README.md)
- 中文辅文：`README.zh.md`

该目录包含精确运行时 / GPU 主线的候选专项计划、检查清单以及阶段冻结记录。

并非所有历史 exact-runtime 草案都还保留在当前活跃目录中。应结合本 README 与 `../archive/exact_runtime/README.md` 判断哪些文档仍活跃、哪些已转为历史记录。

建议阅读顺序：

1. [cuda_resident_backend_program_20260729.zh.md](cuda_resident_backend_program_20260729.zh.md)
2. [cuda_resident_backend_iteration_log_20260729.zh.md](cuda_resident_backend_iteration_log_20260729.zh.md)
3. [cuda_resident_rb10_hold_decision_20260731.zh.md](cuda_resident_rb10_hold_decision_20260731.zh.md)
4. [cuda_resident_rb11_closure_20260731.zh.md](cuda_resident_rb11_closure_20260731.zh.md)
5. [cuda_resident_runtime_program_2_20260731.zh.md](cuda_resident_runtime_program_2_20260731.zh.md)
6. [cuda_resident_runtime_program_2_iteration_log_20260731.zh.md](cuda_resident_runtime_program_2_iteration_log_20260731.zh.md)
7. [cuda_resident_runtime_program_2_size_policy_20260731.json](cuda_resident_runtime_program_2_size_policy_20260731.json)
8. [cpp_exact_runtime_refactor_plan.md](cpp_exact_runtime_refactor_plan.md)
9. [gpu_execution_mainline_integration_checklist.md](gpu_execution_mainline_integration_checklist.md)
10. [gpu_execution_phase4_rollout_hot_path_freeze.md](gpu_execution_phase4_rollout_hot_path_freeze.md)
11. [../archive/exact_runtime/README.md](../archive/exact_runtime/README.md)

使用规则：

- CUDA 驻留第二后端计划是该新工作线唯一的冻结执行计划。companion 迭代账本
  记录已接受的分支证据与 RB10 hold decision/RB11 closure record，当前计划已完成
  且不晋级。之后若要继续必须建立新的显式计划。
- CR2 就是这套新的显式 continuation program，负责 full-window、规模治理、consumer、
  parity、resource 与 small-batch gates；在最终 decision row 之前不授权晋级。
- 除冻结的阶段计划外，其余文档默认作为候选专项草案或检查清单。
- 当前仓库结构已有演变，文中部分代码路径仍保留历史语义。使用时请与当前代码树交叉对照。
- 早期的 GPU 主线讨论及实验性路线已移至 `../archive/exact_runtime/`。
