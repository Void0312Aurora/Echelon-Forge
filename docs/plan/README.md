# `docs/plan` 文档索引与治理说明

状态：`2026-05-10` 整理版。  
本文档用于整理 `docs/plan` 下计划、论述、契约与冻结执行记录的职责边界，避免把“架构论述”和“可执行任务单”混用。

## 一、推荐阅读顺序

1. [system_layering_and_engine_encapsulation_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/system_layering_and_engine_encapsulation_plan.zh.md)  
   架构主方案，回答“目标分层是什么、引擎边界应该如何定义”。
2. [architecture_and_performance_research_followup.zh.md](/home/void0312/Workshop/CMO/docs/plan/architecture_and_performance_research_followup.zh.md)  
   调研与论述文档，回答“为什么这样分层、性能路线如何排序、C++/CUDA/Rust 应如何取舍”。
3. [runtime_facade_contract_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade_contract_plan.zh.md)  
   接口契约方案，回答“前端应依赖什么 facade 边界、核心 DTO 和会话接口如何定义”。
4. [runtime_facade_task_bootstrap_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade_task_bootstrap_plan.zh.md)  
   第一批冻结执行记录，记录 `WP1-WP6` 的冻结范围、完成状态与验收结果。
5. [runtime_facade_layering_cleanup_freeze.zh.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade_layering_cleanup_freeze.zh.md)  
   下一批候选冻结执行计划，聚焦 facade 分层清理、主线前端解耦和依赖方向检查。
6. [src_layered_refactor_freeze.zh.md](/home/void0312/Workshop/CMO/docs/plan/src_layered_refactor_freeze.zh.md)  
   当前 `src/` 分层重构冻结执行计划，聚焦目录边界、README 护栏、大文件拆分路线和 command/tasking 归属。
7. [multi_agent_cooperative_training_foundation_and_performance_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/multi_agent_cooperative_training_foundation_and_performance_plan.zh.md)  
   多 agent 协同训练底座与性能计划，回答“如何把单 world 多实体变成真正可训练的协同底座，以及性能风险如何前置分析”。
8. [cpp_exact_runtime_refactor_plan.md](/home/void0312/Workshop/CMO/docs/plan/cpp_exact_runtime_refactor_plan.md) 与 [gpu_execution_mainline_integration_checklist.md](/home/void0312/Workshop/CMO/docs/plan/gpu_execution_mainline_integration_checklist.md)  
   后续专项方向文档；可作为下一轮计划依据，但在重新冻结前不应直接扩展实现范围。

## 二、文档分类

### A. 架构主方案

- [system_layering_and_engine_encapsulation_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/system_layering_and_engine_encapsulation_plan.zh.md)
- [system_layering_and_engine_encapsulation_plan.md](/home/void0312/Workshop/CMO/docs/plan/system_layering_and_engine_encapsulation_plan.md)

角色：

- 定义系统目标分层、引擎边界、依赖方向和迁移原则。
- 是“架构方向”的权威说明，不是单次实现任务单。

### B. 调研与论述

- [architecture_and_performance_research_followup.zh.md](/home/void0312/Workshop/CMO/docs/plan/architecture_and_performance_research_followup.zh.md)
- [gpu_execution_runtime_research_and_design.md](/home/void0312/Workshop/CMO/docs/plan/gpu_execution_runtime_research_and_design.md)

角色：

- 提供现状判断、性能分析、路线排序和设计取舍依据。
- 为主方案和后续冻结计划提供论据，但本身不授权进入实现。

### C. 接口与契约

- [runtime_facade_contract_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade_contract_plan.zh.md)

角色：

- 定义维护中的前后端边界、typed request/response 和能力协商方向。
- 是“接口设计依据”，不是自动生效的冻结任务单。

### D. 冻结执行记录

- [runtime_facade_task_bootstrap_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade_task_bootstrap_plan.zh.md)
- [runtime_facade_layering_cleanup_freeze.zh.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade_layering_cleanup_freeze.zh.md)
- [src_layered_refactor_freeze.zh.md](/home/void0312/Workshop/CMO/docs/plan/src_layered_refactor_freeze.zh.md)
- [gpu_execution_phase4_rollout_hot_path_freeze.md](/home/void0312/Workshop/CMO/docs/plan/gpu_execution_phase4_rollout_hot_path_freeze.md)

角色：

- 记录已冻结的范围、验收标准和执行结果。
- 已完成的冻结文档应视为“执行记录”，后续工作必须通过新文档重新冻结。

### E. 后续专项草案与跟踪清单

- [cpp_exact_runtime_refactor_plan.md](/home/void0312/Workshop/CMO/docs/plan/cpp_exact_runtime_refactor_plan.md)
- [gpu_execution_mainline_integration_checklist.md](/home/void0312/Workshop/CMO/docs/plan/gpu_execution_mainline_integration_checklist.md)
- [gpu_resident_state_implementation_plan.md](/home/void0312/Workshop/CMO/docs/plan/gpu_resident_state_implementation_plan.md)
- [gpu_exact_world_step_migration_plan.md](/home/void0312/Workshop/CMO/docs/plan/gpu_exact_world_step_migration_plan.md)
- [gpu_exact_world_step_performance_and_parity_plan.md](/home/void0312/Workshop/CMO/docs/plan/gpu_exact_world_step_performance_and_parity_plan.md)
- [gpu_exact_world_step_rearchitecture_plan.md](/home/void0312/Workshop/CMO/docs/plan/gpu_exact_world_step_rearchitecture_plan.md)

角色：

- 用于承接某一条专项主线的后续设计和跟踪。
- 除非文档本身已明确冻结范围并被当前任务显式采纳，否则不应直接作为扩展实现依据。

### F. 结果与产物

- [results/wp6_benchmark_world_batch_vec_env_phase4.json](/home/void0312/Workshop/CMO/docs/plan/results/wp6_benchmark_world_batch_vec_env_phase4.json)

角色：

- 存放冻结计划或调研过程产生的 benchmark、诊断或验收产物。

## 三、当前权威关系

- 架构方向以 [system_layering_and_engine_encapsulation_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/system_layering_and_engine_encapsulation_plan.zh.md) 为主。
- 性能路线与扩展取舍以 [architecture_and_performance_research_followup.zh.md](/home/void0312/Workshop/CMO/docs/plan/architecture_and_performance_research_followup.zh.md) 为主。
- runtime facade 边界定义以 [runtime_facade_contract_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade_contract_plan.zh.md) 为主。
- runtime facade 第一批实现记录以 [runtime_facade_task_bootstrap_plan.zh.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade_task_bootstrap_plan.zh.md) 为主，且 `WP1-WP6` 已完成。
- runtime facade 下一批候选执行边界以 [runtime_facade_layering_cleanup_freeze.zh.md](/home/void0312/Workshop/CMO/docs/plan/runtime_facade_layering_cleanup_freeze.zh.md) 为主；它聚焦分层清理和解耦，不授权 exact GPU、resident-state 或新训练功能扩展。
- `src/` 目录重构与大文件拆分边界以 [src_layered_refactor_freeze.zh.md](/home/void0312/Workshop/CMO/docs/plan/src_layered_refactor_freeze.zh.md) 为主；它已授权 README 护栏落地，后续代码拆分需按其中 `WP2-WP7` 分批执行。

## 四、执行规则

1. 只有明确标注“冻结执行版”且写清范围、验收标准和非目标的文档，才能直接作为实现依据。
2. “草案”“调研”“契约”“checklist”类文档默认只提供方向、论据和设计依据，不直接授权扩展实现。
3. 已完成的冻结文档自动转为执行记录，不应继续在原文档上追加未冻结的新范围。
4. 若某条后续工作跨越多个文档，必须先收敛到单一冻结任务单，再开始代码实现。
5. 新增 benchmark、测试结果或诊断结论，应优先沉淀到 `docs/plan/results/` 或对应冻结文档的验收记录中。
