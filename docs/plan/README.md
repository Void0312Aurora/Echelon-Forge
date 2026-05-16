# `docs/plan` 文档索引与治理说明

状态：`2026-05-16` 目录分组整理版。
本文档用于说明 `docs/plan` 的目录结构、权威关系与保留策略，避免把“现行实现依据”和“历史论述/实验记录”混用。

## 一、当前整理结论

- `docs/plan` 已完成按主线的物理分组，根目录只保留总入口 [README.md](/home/void0312/Workshop/CMO/docs/plan/README.md)。
- 当前子目录为：
  `architecture/`、`runtime_facade/`、`cooperative/`、`exact_runtime/`、`archive/`、`results/`。
- 暂不直接删除仍有溯源价值或仍被交叉引用的文档；这类材料优先转入 `archive/`，而不是继续留在根目录扁平堆放。
- `results/` 只存放 benchmark、评估记录和验收产物，不再和计划文档混放。
- 只有明确写出冻结范围、验收标准和非目标的“冻结执行版”文档，才能直接作为代码实现依据。
- 如果某项新工作同时依赖多份调研、契约或历史计划，必须先收敛为新的单一冻结任务单，再进入实现。

## 二、目录结构

- [architecture/README.md](/home/void0312/Workshop/CMO/docs/plan/architecture/README.md)
  架构主方案、性能调研、`src/` 分层重构冻结记录。
- [runtime_facade/README.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade/README.md)
  runtime facade 契约、已完成的第一批执行记录、后续分层清理冻结计划。
- [cooperative/README.md](/home/void0312/Workshop/CMO/docs/plan/cooperative/README.md)
  协同训练与协同执行管线主线文档。
- [exact_runtime/README.md](/home/void0312/Workshop/CMO/docs/plan/exact_runtime/README.md)
  exact runtime / GPU 主线的候选专项计划与清单。
- [archive/README.md](/home/void0312/Workshop/CMO/docs/plan/archive/README.md)
  已关闭、实验归档或仅保留溯源价值的历史文档。
- [results/README.md](/home/void0312/Workshop/CMO/docs/plan/results/README.md)
  benchmark、评估说明与验收产物。

## 三、推荐阅读顺序

1. [system_layering_and_engine_encapsulation_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/architecture/system_layering_and_engine_encapsulation_plan.zh.md)
   架构主方案，回答“目标分层是什么、引擎边界应如何定义”。
2. [architecture_and_performance_research_followup.zh.md](/home/void0312/Workshop/CMO/docs/plan/architecture/architecture_and_performance_research_followup.zh.md)
   调研与论述文档，回答“为什么这样分层、性能路线如何排序、C++/CUDA 路线如何取舍”。
3. [runtime_facade_contract_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade/runtime_facade_contract_plan.zh.md)
   接口契约方案，回答“前端应依赖什么 facade 边界、核心 DTO 与会话接口如何定义”。
4. [runtime_facade_layering_cleanup_freeze.zh.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade/runtime_facade_layering_cleanup_freeze.zh.md)
   当前仍可继续使用的候选冻结执行计划，聚焦 facade 分层清理、主线前端解耦与依赖方向检查。
5. [src_layered_refactor_freeze.zh.md](/home/void0312/Workshop/CMO/docs/plan/architecture/src_layered_refactor_freeze.zh.md)
   当前 `src/` 分层重构冻结计划，记录 `WP1-WP7` 的完成状态与后续边界。
6. [multi_agent_cooperative_training_foundation_and_performance_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.zh.md)
   协同训练底座与性能计划，回答“多 agent 协同训练的设施底座与风险前置分析如何展开”。
7. [p8_cooperative_execution_pipeline_findings_and_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/cooperative/p8_cooperative_execution_pipeline_findings_and_plan.zh.md)
   P8 协同执行管线发现与计划，聚焦执行输入链路、设施盘点与下一批补齐切口。
8. GPU / exact runtime 相关计划
   仅在当前任务明确进入 GPU/exact runtime 主线时，再继续阅读 [cpp_exact_runtime_refactor_plan.md](/home/void0312/Workshop/CMO/docs/plan/exact_runtime/cpp_exact_runtime_refactor_plan.md)、[gpu_execution_mainline_integration_checklist.md](/home/void0312/Workshop/CMO/docs/plan/exact_runtime/gpu_execution_mainline_integration_checklist.md) 与其他专项文档。

## 四、状态索引

### A. 当前权威依据

| 文档 | 当前角色 | 使用规则 |
|------|-----------|----------|
| [system_layering_and_engine_encapsulation_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/architecture/system_layering_and_engine_encapsulation_plan.zh.md) | 架构主方案 | 架构方向权威说明；不是直接任务单 |
| [architecture_and_performance_research_followup.zh.md](/home/void0312/Workshop/CMO/docs/plan/architecture/architecture_and_performance_research_followup.zh.md) | 路线调研主文 | 提供路线排序与性能判断；不直接授权实现 |
| [runtime_facade_contract_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade/runtime_facade_contract_plan.zh.md) | runtime facade 契约依据 | 定义接口边界与 DTO；不直接授权扩展实现 |
| [runtime_facade_layering_cleanup_freeze.zh.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade/runtime_facade_layering_cleanup_freeze.zh.md) | 候选冻结执行计划 | 仅限 facade 分层清理与解耦范围 |
| [src_layered_refactor_freeze.zh.md](/home/void0312/Workshop/CMO/docs/plan/architecture/src_layered_refactor_freeze.zh.md) | `src/` 分层重构冻结记录/边界文档 | 已完成部分视为执行记录；新增范围需重新冻结 |
| [multi_agent_cooperative_training_foundation_and_performance_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.zh.md) | 协同训练主线调研计划 | 当前协同训练主线的重要方向依据 |
| [p8_cooperative_execution_pipeline_findings_and_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/cooperative/p8_cooperative_execution_pipeline_findings_and_plan.zh.md) | P8 设施盘点与下一步计划 | 当前协同执行管线主线的重要方向依据 |

### B. 冻结执行记录

| 文档 | 当前状态 | 说明 |
|------|-----------|------|
| [runtime_facade_task_bootstrap_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade/runtime_facade_task_bootstrap_plan.zh.md) | 第一批 `WP1-WP6` 已完成 | 现为执行记录，不应继续向其中追加新范围 |
| [src_layered_refactor_freeze.zh.md](/home/void0312/Workshop/CMO/docs/plan/architecture/src_layered_refactor_freeze.zh.md) | `WP1-WP7` 已完成 | 已完成工作视为记录；后续拆分需新冻结 |
| [gpu_execution_phase4_rollout_hot_path_freeze.md](/home/void0312/Workshop/CMO/docs/plan/exact_runtime/gpu_execution_phase4_rollout_hot_path_freeze.md) | 已冻结的阶段性执行计划 | 作为 GPU 主线的历史阶段记录使用 |

### C. 仍可推进的专项草案 / 跟踪清单

| 文档 | 当前状态 | 说明 |
|------|-----------|------|
| [cpp_exact_runtime_refactor_plan.md](/home/void0312/Workshop/CMO/docs/plan/exact_runtime/cpp_exact_runtime_refactor_plan.md) | Draft follow-on implementation plan | 后续 C++ exact runtime 专项候选计划 |
| [gpu_execution_mainline_integration_checklist.md](/home/void0312/Workshop/CMO/docs/plan/exact_runtime/gpu_execution_mainline_integration_checklist.md) | Open | GPU execution 主线一致性检查清单 |
| [gpu_resident_state_implementation_plan.md](/home/void0312/Workshop/CMO/docs/plan/exact_runtime/gpu_resident_state_implementation_plan.md) | 实施草案 | 设备常驻状态方向的专项实施草案 |
| [gpu_exact_world_step_performance_and_parity_plan.md](/home/void0312/Workshop/CMO/docs/plan/exact_runtime/gpu_exact_world_step_performance_and_parity_plan.md) | 实施计划草案 | GPU 精确步进性能/语义对等专项草案 |

### D. 历史保留 / 已关闭 / 实验归档

| 文档 | 当前状态 | 说明 |
|------|-----------|------|
| [execution_coarse_grained_route_segments.md](/home/void0312/Workshop/CMO/docs/plan/archive/execution_coarse_grained_route_segments.md) | Closed on `2026-03-24` | 历史阶段性切口，不是当前主线依据 |
| [gpu_execution_runtime_research_and_design.md](/home/void0312/Workshop/CMO/docs/plan/archive/gpu_execution_runtime_research_and_design.md) | Closed on `2026-03-24` | 早期 GPU runtime 调研记录 |
| [gpu_exact_world_step_migration_plan.md](/home/void0312/Workshop/CMO/docs/plan/archive/gpu_exact_world_step_migration_plan.md) | experimental archive retained | 保留迁移路径论证，用于溯源 |
| [gpu_exact_world_step_rearchitecture_plan.md](/home/void0312/Workshop/CMO/docs/plan/archive/gpu_exact_world_step_rearchitecture_plan.md) | experimental archive retained | 保留重构路径论证，用于溯源 |

### E. 翻译镜像 / 配套版本

| 文档 | 当前状态 | 说明 |
|------|-----------|------|
| [system_layering_and_engine_encapsulation_plan.md](/home/void0312/Workshop/CMO/docs/plan/architecture/system_layering_and_engine_encapsulation_plan.md) | 英文镜像 | 默认以中文主文为权威版本，英文版用于对照 |

### F. 结果与评估记录

| 文档 | 当前状态 | 说明 |
|------|-----------|------|
| [results/wp6_benchmark_world_batch_vec_env_phase4.json](/home/void0312/Workshop/CMO/docs/plan/results/wp6_benchmark_world_batch_vec_env_phase4.json) | benchmark 产物 | `WP6` 相关基准结果产物 |
| [hmoe_strict_terminal_eval_20260515.md](/home/void0312/Workshop/CMO/docs/plan/results/hmoe_strict_terminal_eval_20260515.md) | 评估记录 | HMoE 严格终局对比结果说明，不是计划文档 |

## 五、当前权威关系

- 架构方向以 [system_layering_and_engine_encapsulation_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/architecture/system_layering_and_engine_encapsulation_plan.zh.md) 为主。
- 性能路线与扩展取舍以 [architecture_and_performance_research_followup.zh.md](/home/void0312/Workshop/CMO/docs/plan/architecture/architecture_and_performance_research_followup.zh.md) 为主。
- runtime facade 边界定义以 [runtime_facade_contract_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade/runtime_facade_contract_plan.zh.md) 为主。
- runtime facade 第一批实现记录以 [runtime_facade_task_bootstrap_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade/runtime_facade_task_bootstrap_plan.zh.md) 为主，但其 `WP1-WP6` 已完成，后续不得在原文档直接扩范围。
- runtime facade 下一批候选边界以 [runtime_facade_layering_cleanup_freeze.zh.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade/runtime_facade_layering_cleanup_freeze.zh.md) 为主；它只覆盖分层清理与解耦，不自动授权 GPU/exact runtime 或训练功能扩张。
- `src/` 目录重构与大文件拆分边界以 [src_layered_refactor_freeze.zh.md](/home/void0312/Workshop/CMO/docs/plan/architecture/src_layered_refactor_freeze.zh.md) 为主；已完成内容视为记录，新增拆分范围需另行冻结。
- 协同训练主线以 [multi_agent_cooperative_training_foundation_and_performance_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.zh.md) 与 [p8_cooperative_execution_pipeline_findings_and_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/cooperative/p8_cooperative_execution_pipeline_findings_and_plan.zh.md) 共同提供方向依据；具体实现前仍应收敛为新的冻结任务单。

## 六、执行规则

1. 只有明确标注“冻结执行版”且写清范围、验收标准与非目标的文档，才能直接作为实现依据。
2. “草案”“调研”“契约”“checklist”“评估记录”默认只提供方向、论据、契约或结果，不直接授权扩展实现。
3. 已完成的冻结文档自动转为执行记录，不应继续在原文档上追加未冻结的新范围。
4. 历史保留、已关闭或实验归档文档仅用于溯源、解释路线演化或回看已放弃方案，不应被当作当前实现权威。
5. 新增 benchmark、实验结果或评估说明，应优先沉淀到 `docs/plan/results/` 或独立结果文档，而不是混入冻结任务单主体。
6. 若后续继续细分目录，应优先在现有主线子目录内扩展，而不是重新回到根目录扁平堆放。
