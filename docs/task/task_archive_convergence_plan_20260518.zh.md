# 任务文档封存与收敛计划

状态：`2026-06-02` 已审计生命周期更新；原始规划版为 `2026-05-18`。
范围：`docs/task/*`
参考模式：[flight_dynamics/archive](./flight_dynamics/archive/README.zh.md)

审计更新：`2026-06-02` 已完成只读 subagent 生命周期核查；后续物理归档行动已把选定的
completed evidence-package 原路径降为轻量指针。

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

## 2026-06-02 Subagent 核查更新

本轮由四个只读 diagnostics subagent 按当前 `docs/task` 子项目集合核查局部
`README`、状态、closure、acceptance 与 archive 索引文件。核查时以维护中的
`README`、可执行/验收证据优先于较早 dated 规划文本。

核查结论：

- 已在原位归档到位：`code_redundancy/`、`diagnostics_eval/`、`python_rl/`
  现在都有归档型根入口和本地 `archive/` 索引；无需继续移动。
- 已物理移动到本地 archive，并在原路径留下轻量指针：
  `air_combat/a2_high_fidelity_damage_model/`、`naval/n4_threat_roe_bridge/`、
  `naval/n5_rl_action_surface_split/`、以及已接受的 `ground/g0` 到 `g6` evidence records。
- 已完成或已接受、但应原位保留：
  `model/m1_action_interface_split/`、以及
  `issues/rl_policy_hold_baseline_drift/`。这些目录仍被父级任务入口、当前 gate
  或后续证据链引用。
- 仍处于活跃或混合态，不能整区归档：
  `air_combat/` 与 `air_combat/a1_1v1_realism_gradient/`、`common_air_naval/`、
  `flight_dynamics/` 及其仍保留活跃分析作用的子目录、`viz/`、`game/`、
  `ground/`、`model/`、`model/m1_temporal_window_hmoe/`、
  `model/m2_causal_transformer_hmoe/`、`naval/`、
  `naval/naval_domain_surface_split/`、`performance_runtime/`、
  `simulation_architecture/`、`review/` 和 `issues/`。

归档决策：

- 选定的 completed evidence 目录现在位于父级 `archive/` 目录。原路径只保留简短工作说明和
  指向完整 archived packet 的指针。
- 后续归档应沿用同一形态：先补或更新本地 archive 索引，再同步父级入口链接，最后再把
  evidence-package root 替换为轻量指针。

## 分目录判断

### 已在原位归档

- `code_redundancy/`：
  [后续冻结计划](./archive/code_redundancy/archive/code_redundancy_followup_freeze_20260516.zh.md)
  已明确 `WP-A / WP-B / WP-C` 全部收口，且不再保留活动中的实现条目。该区域现在已有根级
  `README` 和本地 `archive/` 索引；后续若继续推进，应另起新冻结文档。
- `diagnostics_eval/`：
  [diagnostics 模块化](./archive/diagnostics_eval/archive/diagnostics_modularization_20260515.zh.md)、
  [eval 入口收敛](./archive/diagnostics_eval/archive/eval_entrypoint_convergence_20260515.zh.md)、
  [benchmark CLI 收敛](./archive/diagnostics_eval/archive/diagnostics_benchmark_cli_convergence_20260515.zh.md)
  都已标记阶段完成。该区域现在已有根级 `README` 和本地 `archive/` 索引。
- `python_rl/`：
  现有文档基本都是子域迁移/收敛记录，且状态多为“已完成”“已关闭”。该区域现在已有根级
  `README` 和本地 `archive/` 索引；顶层任务索引也已说明它们更像实现追踪记录，而不是默认活跃计划。
- `air_combat/a2_high_fidelity_damage_model/`：
  完整 research/candidate package 现在位于
  [air_combat/archive/a2_high_fidelity_damage_model/](./air_combat/archive/a2_high_fidelity_damage_model/README.zh.md)，
  原路径为轻量指针。
- `naval/n4_threat_roe_bridge/` 与 `naval/n5_rl_action_surface_split/`：
  完整 evidence packet 现在位于 [naval/archive/](./naval/archive/README.zh.md)，原路径为轻量指针。
- 已接受的 ground G0-G6 evidence records：
  完整 packet 现在位于 [ground/archive/](./ground/archive/README.zh.md)，原 phase 路径为轻量工作说明。

`review/` 不再作为整区封存候选处理。它的 pre-WP
[架构审查](./review/archive/pre-wp/architecture_review_20260516.zh.md) 和
[后续冻结计划](./review/archive/pre-wp/architecture_review_followup_freeze_20260516.zh.md)
是已归档快照，但 `review/` 根入口仍是活跃治理记录。

### 先收敛，再部分封存

- `air_combat/`：
  收敛入口和 archive 分离现在已就位。根目录仍服务活跃的分阶段 `1v1` 工作线；
  `a1_1v1_realism_gradient/` 仍为 active/planning；
  `a2_high_fidelity_damage_model/` 是指向已归档 retained research/candidate record 的指针。
  不应整树归档。
- `common_air_naval/`：
  收敛入口和 archive 分离现在已就位。基础工作已完成，但更广的 runtime/tooling、
  `tests/contracts` 和后续 naval 扩展承接仍处于活跃尾项。
- `viz/`：
  本地 `README` 现在是当前入口。它有意把 `archive/` 下的一份 plan 提升为 active
  implementation boundary；除非先替换该提升入口，否则不要再次移动。

### 应保持活跃

- `naval/`：
  N4 与第一段 RL action/observation repair 已闭合或接受，并已物理归档且原路径保留指针。
  当前后续工作位于 `naval/naval_domain_surface_split/`，该包仍为 active/planning，且明确不能归档。
- `performance_runtime/`：
  截至 `2026-05-18` 仍是明确的活跃规划/执行线。
- `flight_dynamics/`：
  当前模式应保持不变。它是 reference hub，既有已归档实施包，也有仍承担 closure
  marker 与未解决真实性问题索引作用的分析子目录。
- `ground/`：
  活跃规划根入口。G0-G6 是已接受/封存证据，并已物理归档且原路径保留指针；但
  movement、sensing、terrain、fires、damage、combat 和完整 runtime release 仍 held。
- `model/`：
  活跃规划根入口。`m1_action_interface_split/` 已接受但仍保留在 M1 证据链中；
  `m1_temporal_window_hmoe/` 仍在采集证据；`m2_causal_transformer_hmoe/` 为 held。
- `simulation_architecture/`、`review/`、`issues/`：
  仍是活跃架构或治理根入口，只对已闭合快照使用本地 archive。
- `game/`：
  活跃探索性 Arma proxy 线，不可归档。

## 当前行动状态

### Wave 1：已完成

1. `code_redundancy`、`diagnostics_eval`、`python_rl` 已有根级 README 和本地
   archive 索引。
2. `review` 已有根级治理 README，并为已完成或已替代的 review 快照保留本地
   archive 索引。
3. `docs/task/README*` 已对这些区域指向局部 task-area README，而不是过期 dated 快照。

### Wave 2：选定证据包已完成

1. `air_combat`、`common_air_naval`、`viz` 已有局部 README 和 archive 分离。
2. `a2_high_fidelity_damage_model/`、naval N4/N5 evidence packets、ground G0-G6 phase
   packets 已移入本地 archive，并在原路径留下轻量指针。
3. 不要移动被提升的 `viz/archive` plan，除非已有替代 active entry。

### Wave 3：当前不动结构

1. `naval`、`ground`、`model`、`performance_runtime`、`simulation_architecture`、
   `review`、`issues`、`game` 和 `flight_dynamics` reference hub 继续保留在当前路径。
2. 后续新任务线默认采用 `README + current status + archive/` 的生命周期模式。

## 验收标准

1. `docs/task/README.md` 与 `README.zh.md` 不再把已过时的 dated 快照作为那些已收敛目录的默认入口。
2. 每个已封存子项目都保留一个根级 `README` 和一个本地 `archive/` 索引。
3. 新工作不再继续扩写已经关闭的冻结文档，而是以新的 freeze、taskboard 或 current-status 文档起新日期续篇。
4. 文件移动后，历史链接只需最小幅度调整，阅读链路仍可追踪。

## 当前建议

- 不要从本文档启动无边界的批量文件移动 wave。
- 剩余 completed retained records 继续作为 sealed evidence 保留，直到父级 README 与当前
  gate 链接可以安全改写。
- 后续逐区归档时继续沿用 `flight_dynamics/archive/` 模板。
