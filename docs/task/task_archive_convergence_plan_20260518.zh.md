# 任务文档封存与收敛计划

状态：`2026-05-18` 规划版。
范围：`docs/task/*`
参考模式：[flight_dynamics/archive](./flight_dynamics/archive/README.zh.md)

文档定位：

- 本文档用于判断 `docs/task` 下哪些子项目应继续保持活跃，哪些应先收敛为单一入口，再转入封存。
- 本文档只定义文档生命周期方案，本身不直接授权批量移动文件或改写历史结论。

## 目标

1. 降低默认导航路径上“过期 dated 快照”过多的问题。
2. 让每条仍在推进的任务线只保留一个清晰的活跃入口。
3. 保留可追溯性，通过迁移到归档位而不是删除文档来收口历史记录。

## 判定规则

- 保持活跃：该方向仍有较新的 `current status`、`progress checkpoint` 或
  `taskboard`，并且这些文档仍在驱动下一轮实现。
- 先收敛：该方向仍有后续工作，但多个 dated 文档同时充当入口。应先补
  本地 `README.md` 或单一 `current_status` 文档，再把兄弟快照移入归档。
- 立即封存：文档已经明确写出阶段完成、工作包全部收口，或后续工作必须
  另起新的冻结文档，而不是继续扩写旧文档。

## 推荐封存模式

- 优先复用 `flight_dynamics/archive/` 的做法，而不是先发明新的仓库级总归档树。
- 默认优先采用各子项目自己的 `<subproject>/archive/`，这样相对链接改动最小。
- 即便子项目大部分内容已经归档，也保留一个轻量的 `<subproject>/README.md`
  作为唯一活跃入口。
- 历史 dated 文档不改写当时结论；如需更新判断，应新增收敛文档或状态文档。

## 分目录判断

### 可立即封存

- `code_redundancy/`：
  [后续冻结计划](./code_redundancy/code_redundancy_followup_freeze_20260516.zh.md)
  已明确 `WP-A / WP-B / WP-C` 全部收口，且不再保留活动中的实现条目；后续若继续推进，应另起新冻结文档。
- `diagnostics_eval/`：
  [diagnostics 模块化](./diagnostics_eval/diagnostics_modularization_20260515.zh.md)、
  [eval 入口收敛](./diagnostics_eval/eval_entrypoint_convergence_20260515.zh.md)、
  [benchmark CLI 收敛](./diagnostics_eval/diagnostics_benchmark_cli_convergence_20260515.zh.md)
  都已标记阶段完成，当前只剩增量清理。
- `python_rl/`：
  现有文档基本都是子域迁移/收敛记录，且状态多为“已完成”“已关闭”；顶层任务索引也已说明它们更像实现追踪记录，而不是默认活跃计划。
- `review/`：
  [架构审查](./review/architecture_review_20260516.zh.md) 已完成，
  [后续冻结计划](./review/architecture_review_followup_freeze_20260516.zh.md)
  也已经把已执行内容和“后续需另起任务单”的事项区分清楚，适合转入归档入口模式。

### 先收敛，再部分封存

- `air_combat/`：
  不建议整目录立即封存。当前 `1v1` 第一阶段已落地，但奖励、eval、对手基线、失速后续和训练信号解释仍有明确缺口。建议先补
  `README.md` 或 `air_combat_1v1_current_status_20260518.md`，只保留这一份入口和最多一份活跃状态/冻结文档，再把其余 dated 快照移入 `air_combat/archive/`。
- `common_air_naval/`：
  多数工作包已经完成，但冻结计划中仍保留更广泛的 contract 迁移、naval runtime/eval 扩展等未完成尾项。建议先写一份“基础已完成 / 尾项待承接”的收敛入口文档，再封存纯分析文档以及不再作为主入口的执行记录。
- `viz/`：
  当前大文档已记录 `WP-V4 / WP-V5` 第一版可用收口，但本目录还缺少一个清晰的 `README` 或暂停状态检查点。建议先补入口文档，再决定是否把这份大型冻结设计稿移入归档。

### 应保持活跃

- `naval/`：
  [海战推进检查点](./naval/naval_progress_checkpoint_20260517.zh.md) 和
  [委派执行积压](./naval/naval_delegated_execution_backlog_20260517.zh.md)
  仍直接服务下一轮实现。
- `performance_runtime/`：
  截至 `2026-05-18` 仍是明确的活跃规划/执行线。
- `flight_dynamics/`：
  当前模式应保持不变。它已经把活跃入口与归档实施包分开，尤其是
  `program/`、`c2_command_chain/` 和 `archive/` 的分层已经可以直接作为其他目录的参考模板。

## 分波次执行建议

### Wave 1：立即封存候选

1. 为 `code_redundancy`、`diagnostics_eval`、`python_rl`、`review` 补
   `README.md` 与 `README.zh.md`。
2. 在各自目录下建立 `archive/`，将 dated 文档原名迁入，不做无谓重命名。
3. 把 `docs/task/README*` 的导航入口从“直链 dated 文档”改为“先进入该子项目 README”。

### Wave 2：混合态目录先收敛

1. `air_combat`：先写一份当前状态/收敛入口，再归档其余兄弟文档。
2. `common_air_naval`：先写承接状态文档，先归档 `analysis`，待尾项迁移或关闭后再决定是否封存 `freeze plan`。
3. `viz`：先补暂停态或当前状态入口，再决定冻结设计稿是否移入归档。

### Wave 3：当前不动结构

1. `naval`、`performance_runtime`、`flight_dynamics/program`、
   `flight_dynamics/c2_command_chain` 继续保留在活跃路径。
2. 后续新任务线默认采用 `README + current status + archive/` 的生命周期模式。

## 验收标准

1. `docs/task/README.md` 与 `README.zh.md` 不再把已过时的 dated 快照作为那些已收敛目录的默认入口。
2. 每个已封存子项目都保留一个根级 `README` 和一个本地 `archive/` 索引。
3. 新工作不再继续扩写已经关闭的冻结文档，而是以新的 freeze、taskboard 或 current-status 文档起新日期续篇。
4. 文件移动后，历史链接只需最小幅度调整，阅读链路仍可追踪。

## 当前建议

- 第一波优先从 `code_redundancy` 和 `review` 开始，风险最低。
- `air_combat` 按“先收敛、后部分封存”处理，不建议直接整目录冷封。
- 其余目录优先沿用 `flight_dynamics/archive/` 这一现成模板。
