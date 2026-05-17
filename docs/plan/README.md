# `docs/plan` 文档索引与治理说明

状态：`2026-05-18` 入口校正版。
本文档只描述当前仓库里真实存在的 `docs/plan/` 结构，以及这些文档
在当前主线中的使用方式，避免把历史论述、调研草案和冻结执行依据混用。

## 一、当前目录结构

`docs/plan/` 当前只包含四条维护中的主线子目录：

- [architecture/README.md](architecture/README.md)
  - 架构主方案、性能调研、`src/` 分层重构边界。
- [runtime_facade/README.md](runtime_facade/README.md)
  - runtime facade 契约、已完成执行记录、后续清理冻结计划。
- [cooperative/README.md](cooperative/README.md)
  - 协同训练与协同执行管线主线文档。
- [exact_runtime/README.md](exact_runtime/README.md)
  - exact runtime / GPU 主线的候选专项计划、检查清单与阶段冻结记录。

说明：

- 当前仓库中不存在 `docs/plan/archive/` 或 `docs/plan/results/` 子目录。
- 更早期的归档设计材料位于 [docs/Archive/](../Archive)，不再挂在
  `docs/plan/` 目录下。
- benchmark、评估结果与历史产物如仍需保留，应在具体文档中说明其
  保留位置，而不是假设 `docs/plan/results/` 已经存在。

## 二、推荐阅读顺序

1. [architecture/system_layering_and_engine_encapsulation_plan.zh.md](architecture/system_layering_and_engine_encapsulation_plan.zh.md)
   - 架构主方案，回答“目标分层是什么、引擎边界应如何定义”。
2. [architecture/architecture_and_performance_research_followup.zh.md](architecture/architecture_and_performance_research_followup.zh.md)
   - 路线调研与性能取舍说明，回答“为什么这样分层、后续路线怎样排序”。
3. [runtime_facade/runtime_facade_contract_plan.zh.md](runtime_facade/runtime_facade_contract_plan.zh.md)
   - facade 契约依据，回答“上层长期应依赖什么 C++ 应用 contract”。
4. [runtime_facade/runtime_facade_layering_cleanup_freeze.zh.md](runtime_facade/runtime_facade_layering_cleanup_freeze.zh.md)
   - 当前仍可继续使用的候选冻结执行计划，聚焦 facade 分层清理与解耦。
5. [architecture/src_layered_refactor_freeze.zh.md](architecture/src_layered_refactor_freeze.zh.md)
   - `src/` 分层重构边界和已完成工作记录。
6. [cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.zh.md](cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.zh.md)
   - 协同训练底座与性能分析主文。
7. [cooperative/p8_cooperative_execution_pipeline_findings_and_plan.zh.md](cooperative/p8_cooperative_execution_pipeline_findings_and_plan.zh.md)
   - P8 协同执行管线的设施盘点与下一步方向。
8. `exact_runtime/` 下的专项文档
   - 仅当任务明确进入 GPU / exact runtime 主线时再继续深入。

## 三、当前权威关系

### A. 方向与契约依据

| 文档 | 当前角色 | 使用规则 |
|------|-----------|----------|
| [architecture/system_layering_and_engine_encapsulation_plan.zh.md](architecture/system_layering_and_engine_encapsulation_plan.zh.md) | 架构主方案 | 架构方向权威说明；不是直接任务单 |
| [architecture/architecture_and_performance_research_followup.zh.md](architecture/architecture_and_performance_research_followup.zh.md) | 路线调研主文 | 提供路线排序与性能判断；不直接授权实现 |
| [runtime_facade/runtime_facade_contract_plan.zh.md](runtime_facade/runtime_facade_contract_plan.zh.md) | facade 契约依据 | 定义接口边界与 DTO；不直接授权扩展实现 |
| [cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.zh.md](cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.zh.md) | 协同训练方向依据 | 提供设施底座、风险与路线分析 |
| [cooperative/p8_cooperative_execution_pipeline_findings_and_plan.zh.md](cooperative/p8_cooperative_execution_pipeline_findings_and_plan.zh.md) | 协同执行方向依据 | 提供当前协同执行主线的设施盘点与下一步方向 |

### B. 已完成或阶段性冻结记录

| 文档 | 当前状态 | 说明 |
|------|-----------|------|
| [runtime_facade/runtime_facade_task_bootstrap_plan.zh.md](runtime_facade/runtime_facade_task_bootstrap_plan.zh.md) | 第一批 `WP1-WP6` 已完成 | 现为执行记录，不应继续向其中追加新范围 |
| [architecture/src_layered_refactor_freeze.zh.md](architecture/src_layered_refactor_freeze.zh.md) | `WP1-WP7` 已完成 | 已完成工作视为记录；新增拆分需新冻结 |
| [exact_runtime/gpu_execution_phase4_rollout_hot_path_freeze.md](exact_runtime/gpu_execution_phase4_rollout_hot_path_freeze.md) | 已冻结的阶段性执行计划 | 作为 GPU 主线的历史阶段记录使用 |

### C. 仍可推进的专项草案 / 清单

| 文档 | 当前状态 | 说明 |
|------|-----------|------|
| [exact_runtime/cpp_exact_runtime_refactor_plan.md](exact_runtime/cpp_exact_runtime_refactor_plan.md) | Draft follow-on implementation plan | 后续 C++ exact runtime 候选计划 |
| [exact_runtime/gpu_execution_mainline_integration_checklist.md](exact_runtime/gpu_execution_mainline_integration_checklist.md) | Open | GPU execution 主线一致性检查清单 |
| [exact_runtime/gpu_resident_state_implementation_plan.md](exact_runtime/gpu_resident_state_implementation_plan.md) | 实施草案 | 设备常驻状态方向草案 |
| [exact_runtime/gpu_exact_world_step_performance_and_parity_plan.md](exact_runtime/gpu_exact_world_step_performance_and_parity_plan.md) | 实施计划草案 | GPU 精确步进性能/语义对等专项草案 |

### D. 归档材料位置

- 更早的性能重构和路线演化说明见 [docs/Archive/rearchitecture/README.md](../Archive/rearchitecture/README.md)。
- 更早的 speed rearchitecture 总结见 [docs/Archive/speed_rearchitecture/README.md](../Archive/speed_rearchitecture/README.md)。
- 这些材料保留溯源价值，但不应被当作当前实现权威。

## 四、执行规则

1. 只有明确写清范围、验收标准和非目标的冻结执行文档，才能直接作为实现依据。
2. “草案”“调研”“契约”“checklist”“评估记录”默认只提供方向、论据、契约或结果，不直接授权扩展实现。
3. 已完成的冻结文档自动转为执行记录，不应继续在原文档上追加未冻结的新范围。
4. 历史保留或实验归档材料只用于溯源、解释路线演化或回看已放弃方案。
5. 如果一项新工作同时依赖多份调研、契约或历史计划，应先收敛为新的单一冻结任务单，再进入实现。
