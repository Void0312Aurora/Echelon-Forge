# `docs/plan` 文档索引与治理说明

状态：`2026-06-01` 计划权威与归档边界索引。
本文档只描述当前仓库里真实存在的 `docs/plan/` 结构，以及这些文档
在当前主线中的使用方式，避免把历史论述、调研草案和冻结执行依据混用。

语言迁移说明：

- 当前 `docs/plan/` 已迁移到”英文 `.md` 为主、中文 `.zh.md` 为辅”的双语体系。
- 迁移记录见 [archive/documentation_bilingual_migration_plan_20260518.zh.md](archive/documentation_bilingual_migration_plan_20260518.zh.md)。
- 严格双语维护面聚焦在稳定计划权威层，而不是 `docs/plan/**` 下的每一份历史冻结或候选草案。

## 一、当前目录结构

`docs/plan/` 当前包含四条维护中的主线子目录：

- [architecture/README.md](architecture/README.md)
  - 架构主方案、性能调研，以及已归档的 `src/` 分层记录。
- [runtime_facade/README.md](runtime_facade/README.md)
  - runtime facade 契约与仍在推进的清理后续；已完成执行记录已移至 `archive/`。
- [cooperative/README.md](cooperative/README.md)
  - 协同训练与协同执行管线主线文档。
- [exact_runtime/README.md](exact_runtime/README.md)
  - exact runtime / GPU 主线的候选专项计划、检查清单与阶段冻结记录。
- [repository_consolidation/README.zh.md](repository_consolidation/README.zh.md)
  - 活跃整合工作线：迭代协议、候选路由与单一迭代台账。
- [unified_architecture_program/README.zh.md](unified_architecture_program/README.zh.md)
  - 活跃的架构统一路线图（DTO 单源化、运行时基座、C++ 边界、声明式配置）；迭代落入整合台账。
- [archive/](archive/README.md)
  - 已关闭路线、历史溯源材料与双语迁移记录。

更早期的归档设计材料仍保留在旧路径 `docs/Archive/` 下；该目录只用于历史追溯，
不是当前 plan 入口。

## 二、推荐阅读顺序

1. [architecture/simulation_system_architecture_design.zh.md](architecture/simulation_system_architecture_design.zh.md)
   - 严格仿真系统基线，回答“规范生命周期是什么、领域扩展应如何接入”。
2. [architecture/system_layering_and_engine_encapsulation_plan.zh.md](architecture/system_layering_and_engine_encapsulation_plan.zh.md)
   - 架构主方案，回答“目标分层是什么、引擎边界应如何定义”。
3. [architecture/architecture_and_performance_research_followup.zh.md](architecture/architecture_and_performance_research_followup.zh.md)
   - 路线调研与性能取舍说明，回答“为什么这样分层、后续路线怎样排序”。
4. [runtime_facade/runtime_facade_contract_plan.zh.md](runtime_facade/runtime_facade_contract_plan.zh.md)
   - facade 契约依据，回答“上层长期应依赖什么 C++ 应用 contract”。
5. [archive/runtime_facade/README.md](archive/runtime_facade/README.md)
   - runtime_facade 已归档 bootstrap / cleanup 记录的索引入口，仅作历史参考。
6. [cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.zh.md](cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.zh.md)
   - 协同训练底座与性能分析主文。
7. [cooperative/p8_cooperative_execution_pipeline_findings_and_plan.zh.md](cooperative/p8_cooperative_execution_pipeline_findings_and_plan.zh.md)
   - P8 协同执行管线的设施盘点与下一步方向。
8. `exact_runtime/` 下的专项文档
   - 仅当任务明确进入 GPU / exact runtime 主线时再继续深入，并应先从 `exact_runtime/README.md` 看当前仍存在的候选草案。

## 三、历史冻结记录

这些文档已经从活跃子目录移出，仅保留执行历史：

- [archive/runtime_facade/README.md](archive/runtime_facade/README.md)
- [archive/architecture/README.md](archive/architecture/README.md)
- [archive/exact_runtime/README.md](archive/exact_runtime/README.md)

## 四、当前权威关系

### A. 方向与契约依据

| 文档 | 当前角色 | 使用规则 |
|------|-----------|----------|
| [architecture/simulation_system_architecture_design.zh.md](architecture/simulation_system_architecture_design.zh.md) | 严格仿真架构基线 | 当前规范生命周期、扩展模型与架构门槛权威；不是直接任务单 |
| [architecture/system_layering_and_engine_encapsulation_plan.zh.md](architecture/system_layering_and_engine_encapsulation_plan.zh.md) | 架构主方案 | 分层方向背景依据；不是直接任务单 |
| [architecture/architecture_and_performance_research_followup.zh.md](architecture/architecture_and_performance_research_followup.zh.md) | 路线调研主文 | 提供路线排序与性能判断；不直接授权实现 |
| [runtime_facade/runtime_facade_contract_plan.zh.md](runtime_facade/runtime_facade_contract_plan.zh.md) | facade 契约依据 | 定义接口边界与 DTO；不直接授权扩展实现 |
| [cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.zh.md](cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.zh.md) | 协同训练方向依据 | 提供设施底座、风险与路线分析 |
| [cooperative/p8_cooperative_execution_pipeline_findings_and_plan.zh.md](cooperative/p8_cooperative_execution_pipeline_findings_and_plan.zh.md) | 协同执行方向依据 | 提供当前协同执行主线的设施盘点与下一步方向 |

### B. 已归档或阶段性冻结记录

| 文档 | 当前状态 | 说明 |
|------|-----------|------|
| [archive/runtime_facade/README.md](archive/runtime_facade/README.md) | runtime_facade 归档索引 | 通过归档索引进入已完成的 bootstrap 和 cleanup freeze |
| [archive/architecture/README.md](archive/architecture/README.md) | 架构归档索引 | 通过归档索引进入已完成的 `src/` 分层冻结记录 |
| [exact_runtime/gpu_execution_phase4_rollout_hot_path_freeze.md](exact_runtime/gpu_execution_phase4_rollout_hot_path_freeze.md) | 已冻结的阶段性执行计划 | 作为 GPU 主线的历史阶段记录使用 |

### C. 仍可推进的专项草案 / 清单

| 文档 | 当前状态 | 说明 |
|------|-----------|------|
| [exact_runtime/cpp_exact_runtime_refactor_plan.md](exact_runtime/cpp_exact_runtime_refactor_plan.md) | Draft follow-on implementation plan | 后续 C++ exact runtime 候选计划 |
| [exact_runtime/gpu_execution_mainline_integration_checklist.md](exact_runtime/gpu_execution_mainline_integration_checklist.md) | Open | GPU execution 主线一致性检查清单 |
| [exact_runtime/README.md](exact_runtime/README.md) | 候选专项索引 | 通过局部 README 确认当前仍存在的 exact-runtime 草案 |

### D. 归档材料位置

- 更早的性能重构和路线演化说明见 [docs/Archive/rearchitecture/README.md](../Archive/rearchitecture/README.md)。
- 更早的 speed rearchitecture 总结见 [docs/Archive/speed_rearchitecture/README.md](../Archive/speed_rearchitecture/README.md)。
- 这些材料保留溯源价值，但不应被当作当前实现权威。

## 五、执行规则

1. 只有明确写清范围、验收标准和非目标的冻结执行文档，才能直接作为实现依据。
2. “草案”“调研”“契约”“checklist”“评估记录”默认只提供方向、论据、契约或结果，不直接授权扩展实现。
3. 已完成的冻结文档自动转为执行记录，不应继续在原文档上追加未冻结的新范围。
4. 历史保留或实验归档材料只用于溯源、解释路线演化或回看已放弃方案。
5. 如果一项新工作同时依赖多份调研、契约或历史计划，应先收敛为新的单一冻结任务单，再进入实现。

已归档计划的完整清单见 [归档注册表](archive_registry.zh.md)。
