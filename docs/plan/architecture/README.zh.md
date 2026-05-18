# `architecture/`

语言版本：

- 英文主文：[README.md](README.md)
- 中文辅文：`README.zh.md`

本目录存放严格仿真系统架构基线、架构主方案、性能路线调研与已归档的 `src/` 分层记录。

推荐阅读顺序：

1. [simulation_system_architecture_design.md](simulation_system_architecture_design.md)
2. [simulation_system_architecture_design.zh.md](simulation_system_architecture_design.zh.md)
3. [system_layering_and_engine_encapsulation_plan.md](system_layering_and_engine_encapsulation_plan.md)
4. [system_layering_and_engine_encapsulation_plan.zh.md](system_layering_and_engine_encapsulation_plan.zh.md)
5. [architecture_and_performance_research_followup.md](architecture_and_performance_research_followup.md)
6. [architecture_and_performance_research_followup.zh.md](architecture_and_performance_research_followup.zh.md)
7. [archive/src_layered_refactor_freeze.zh.md](../archive/architecture/src_layered_refactor_freeze.zh.md)

使用规则：

- 本目录的目标稳态是“英文 `.md` 为主、中文 `.zh.md` 为辅”。
- 在迁移完成前，部分长文仍只有 `.zh.md`，它们可作为过渡输入使用，但应在后续批次中补齐英文 peer。
- 调研文档提供论据与路线排序，不直接授权实现。
- 冻结计划已完成部分视为执行记录；新增范围需另行冻结。
- 仿真系统设计是当前严格架构基线。大范围实现工作应先收敛为
  [docs/task/simulation_architecture/](../../task/simulation_architecture/README.zh.md)
  下的有边界任务单。
