<!-- Machine-translated draft generated on 2026-05-18 from docs/task/README.md. Review before treating this file as authoritative. -->

# 任务文档

本目录是面向任务的工作文档的仓库本地导航中心。

语言说明：

- 当前只有稳定任务导航面在朝着“英文规范 `.md` 为主、中文 `.zh.md` 为辅”的方向发展。
- `docs/task/**` 下高频变更的 dated task 长文默认按英文主文维护，除非某个更小切片被明确提升到持续双语维护面。
- 该策略位于 [docs/standards/governance/bilingual_documentation_policy.md](../standards/governance/bilingual_documentation_policy.md)。
- rollout 计划位于 [docs/plan/documentation_bilingual_migration_plan_20260518.md](../plan/documentation_bilingual_migration_plan_20260518.md)。

此处大部分文件是特定分析、冻结计划、任务板、检查点或收敛过程的带日期快照。如需某个领域的最新上下文，请优先从该领域的 `README.md` 开始；更深层 dated 文档应视为支撑记录，而不是稳定根入口。

如需处理本目录的生命周期收敛与封存，请参见
[任务文档封存与收敛计划](task_archive_convergence_plan_20260518.zh.md)。

## 领域导航

- [飞行动力学/](flight_dynamics/README.md)：真实度跟踪任务导航。先从局部 README 进入，再继续查看 `flight/`、`sensor_situation/`、`weapon_guidance/`、`naval/`、`c2_command_chain/` 这些子项目 README。
- [runtime 性能/](performance_runtime/README.md)：当前真实性冻结后的 runtime 性能推进线。请先从局部 README 查看当前分层规则、任务板来源和活跃入口边界。
- [可视化/](viz/README.md)：仍在推进的统一入口可视化工作线。请先从局部 README 进入；archive 中的大体量冻结/设计文档主要用于追溯，不再充当根级稳定入口。
- [海军/](naval/README.md)：仍在推进的海军真实性工作线。请先从局部 README 查看当前如何解释已归档 checkpoint 与 backlog 材料。
- [审查/](review/README.zh.md)：已归档的架构审查工作线。
- [空战/](air_combat/README.zh.md)：仍在推进的 `1v1` 空战工作线。请先从局部 README 查看当前状态，再按其中链接进入入口分析、冻结、基线进展、武器链、训练烟雾和失速跟进等历史快照。
- [通用空海军/](common_air_naval/README.md)：`common / air / naval` 拆分工作线的收敛入口。局部 README 已区分仍活跃的承接计划和 archive 中被吸收的前置分析。
- [ground/](ground/README.zh.md)：未来地面域启动规划的入口。在展开专门的
  ground 实现前，请先从这里对齐命名、范围和新增域必须补上的横向内容。
- [仿真架构/](simulation_architecture/README.md)：活跃的仿真系统架构工作线。把规范管线设计转化为武器、海军、传感器/航迹、facade 或后端工作前，应先从这里收敛任务。
- [代码冗余/](code_redundancy/README.zh.md)：已归档的代码冗余工作线。
- [诊断评估/](diagnostics_eval/README.zh.md)：已归档的诊断/评估收敛记录。
- [Python 强化学习/](python_rl/README.zh.md)：已归档的 `python/rl` 收敛记录。

## 文档类型

- `分析` / `审计`：捕捉特定片段的发现和理由。
- `计划` / `冻结`：记录该片段的范围化实现计划。
- `任务板`：记录某条工作线的分阶段工作分解。
- `当前状态` / `进度检查点`：进入此树中最新状态的最佳入口点。
- `收敛`：主要为保持可追溯性而保留的实现记录，而非默认的活跃计划。
- `归档`：已移出默认活跃路径、但仍为保持可追溯性而保留的历史快照。
