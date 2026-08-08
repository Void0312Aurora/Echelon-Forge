# 计划归档注册表

`docs/plan/archive/` 下已归档计划文档的注册索引。

## 根级归档

| 文件 | 描述 |
|------|------|
| `documentation_bilingual_migration_plan_20260518` | 文档双语迁移计划。定义了 `docs/plan/` 从中文为主向 EN/ZH 双语体系的迁移策略与批次。已完成。 |

## 子目录归档

### `architecture/`

| 文件 | 描述 |
|------|------|
| `src_layered_refactor_freeze` | `src/` 分层重构冻结计划。C++ 源码目录从 air-first 扁平结构向 `air/naval/common` 子域拆分的冻结执行记录。已完成。 |

### `exact_runtime/`

| 文件 | 描述 |
|------|------|
| `execution_coarse_grained_route_segments` | 执行粗粒度路径分段方案。GPU exact runtime 的早期路线分段设计。 |
| `gpu_exact_world_step_migration_plan` | GPU Exact World-Step 迁移计划。将 GPU 辅助设施向 exact world-step 对齐的迁移路线。 |
| `gpu_exact_world_step_performance_and_parity_plan` | GPU Exact World-Step 性能与奇偶校验计划。GPU vs CPU 参考的性能基准与数值奇偶校验方案。 |
| `gpu_exact_world_step_rearchitecture_plan` | Exact GPU World-Step 重架构计划。GPU world-step 的架构级重构方案。 |
| `gpu_execution_runtime_research_and_design` | GPU 执行运行时调研与设计。GPU 加速执行路径的前期调研与设计文档。 |
| `gpu_resident_state_implementation_plan` | GPU Resident State 实现计划。GPU 驻留状态的同步/分片/导出方案。 |

### `runtime_facade/`

| 文件 | 描述 |
|------|------|
| `runtime_facade_layering_cleanup_freeze` | Runtime Facade 分层清理与解耦冻结执行计划。facade/bindings 层与 core/engine 的分层边界清理冻结记录。 |
| `runtime_facade_task_bootstrap_plan` | Runtime Facade 任务启动筹备方案。facade 子项目的工作包引导与任务拆分方案。 |
