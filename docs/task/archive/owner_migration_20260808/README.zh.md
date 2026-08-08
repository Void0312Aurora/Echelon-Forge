# 任务文档

本目录是面向任务的工作文档的仓库本地导航中心。请把这个根入口当作
task-area 选择器，而不是按时间排列的任务板，也不是单一领域路线图。

项目叙述现在是多域任务导航：air/execution 是当前成熟度最高的领域执行切片；
cooperative/common 集成是从 common/air/naval 起步的当前 shared-tasking 收敛线；
naval N4 是已闭合的 pre-fire 线；ground 是早期 tasking/runtime bootstrap，
已有 native platform-schema 证据但没有 full land runtime；viz 和 game 是探索
展示面；model 是策略/世界模型规划面；`review/` 与 `issues/` 是治理面。较早
的 `flight_dynamics/` 和 dated `air_combat/` 快照仍是有用记录，但不再是全项目
中心。

语言说明：

- 当前只有稳定任务导航面在朝着“英文规范 `.md` 为主、中文 `.zh.md` 为辅”的方向发展。
- `docs/task/**` 下高频变更的 dated task 长文默认按英文主文维护，除非某个更小切片被明确提升到持续双语维护面。
- 该策略位于
  [docs/engineering/documentation/standards/bilingual_documentation_policy.zh.md](../../../engineering/documentation/standards/bilingual_documentation_policy.zh.md)。

此处大部分文件是特定分析、冻结计划、任务板、检查点或收敛过程的带日期快照。如需某个领域的最新上下文，请优先从该领域的 `README.md` 开始；更深层 dated 文档应视为支撑记录，而不是稳定根入口。

如需处理本目录的生命周期收敛与封存，请参见
[任务文档封存与收敛计划](task_archive_convergence_plan_20260518.zh.md)。

## 生命周期标签

- `active`：有当前入口门、验收门或维护中实现面的实现、集成、审查线。
- `planning`：广泛 runtime 释放前的范围化路线图或 bootstrap 线。
- `exploratory`：展示、前端或原型探索线，不能意外变成权威仿真语义。
- `archived`：已冻结、已替代或只为追溯保留的历史材料。
- `governance`：跨领域审查、issue 或验收控制面。

## Task-Area 层级

### 执行与集成

- [空域执行 / air execution](../../air_combat/archive/owner_migration_20260808/README.zh.md)：`active` 入口，也是
  当前成熟度最高的领域执行切片。这里导航维护中的 `execution` / HMoE `1v1`
  路径、分阶段 `1v1` curriculum，以及空战 damage runtime。链接到的 archive
  快照只用于追溯；不要把旧空战快照当成全项目中心。
- [cooperative/common 集成](../common_air_naval/common_air_naval_modular_split_plan_20260515.zh.md)：`archived` —
  common/air/naval 模块拆分已完成（DTO 拆分、profile dispatch seam、MissionCommand 兼容拆分）。
  后续 naval runtime 扩展和 air-first helper 迁移由独立任务单继续推进。
- [仿真架构](../../simulation_architecture/archive/phase3c_closeout_20260808/README.zh.md)：`active` 的仿真系统架构与
  runtime lifecycle 主干。开始武器、海军、传感器/航迹、facade、backend 或跨域
  runtime 的大范围工作前，应先从这里收敛任务。已闭合的临时架构 lane 现在进入其
  `archive/` 索引，而不是作为顶层任务入口裸露。
- [海军](../../naval/archive/owner_migration_20260808/README.zh.md)：`active` 的中高成熟海军工作线。N4 已作为
  pre-fire threat/ROE bridge 和 active training-entry gate 闭合；第一段 RL
  action/observation repair 保留为已接受的 N4 证据记录，当前 surface-split 工作
  继续进入 domain-surface package。limited engagement 仍属于单独 N5 package，
  不应借此重新打开 N4。
- [runtime 性能](../performance_runtime/README.zh.md)：`archived` — 优化分层与 benchmark 导向分析已冻结，旧规划链路视作参考材料。
  用于优化排序、benchmark 边界和 hot-path 分析；已归档的旧规划链是参考材料，
  不是 active execution 入口。

### Bootstrap 与策略规划

- [ground](../../ground/archive/owner_migration_20260808/README.zh.md)：`planning` / 早期 `active` 的 ground tasking 与
  runtime bootstrap。G0-G6 已接受子项目是封存证据记录；movement、sensing、
  terrain、fires、damage 和广泛 runtime 扩展仍明确 held 在后续 gate 之后。
- [model](../../model/archive/owner_migration_20260808/README.zh.md)：`planning` 的策略/世界模型面，用于时间 HMoE 与
  sequence-policy 工作。当行为问题需要策略记忆或 world-model planning，而不是
  环境侧战术记忆板时，请从这里进入。

### 探索展示

- [viz](../../viz/archive/owner_migration_20260808/README.zh.md)：`exploratory` / `active` 的可视化统一入口面。它负责
  展示、asset registry、loader/session 流程和 runtime inspection 便利性，不是
  realism 或 world-parameter 权威入口。
- [game](../../../../game/README.md)：`exploratory` 的外部游戏前端集成线。凡是评估
  simulation-backed gameplay shell、被跟踪的 Arma proxy workspace 边界、
  本地-only 前端归档规则或 authoritative-backend proxy 实验，请先从这里进入。

### 治理

- [review](../../review/archive/phase3c_closeout_20260808/README.zh.md)：`governance` 的 review 与验收记录面。当前 review
  和路线图记录从局部 README 进入；局部 archive 保留已完成或已替代的审查快照。
- [issues](../../issues/archive/owner_migration_20260808/README.zh.md)：`governance` 的跨领域 issue board，用于保持领域、
  runtime、model、training 与 evaluation 工作线之间都应可见的问题。已闭合但仍可复用的发现
  作为 retained tracking item 保留，而不是 active issue。

### 参考与归档

- [flight_dynamics](../../flight_dynamics/archive/phase3c_closeout_20260808/README.zh.md)：`archived` / reference 的真实性
  分析导航，用于 flight、sensor/situation、weapon/guidance、naval 与 C2 closure
  记录。它适合查历史上下文和 closure marker，不是当前项目规划根入口。
- [code_redundancy](../code_redundancy/README.zh.md)：`archived` 的代码冗余工作线。
- [diagnostics_eval](../diagnostics_eval/README.zh.md)：`archived` 的诊断/评估收敛记录。
- [python_rl](../python_rl/README.zh.md)：`archived` 的 `python/rl` 收敛记录。
- [game](../game/README.zh.md)：`archived` 的游戏前端集成探索。

已归档子项目的完整清单与工作描述见 [归档注册表](archive_registry.zh.md)。

## 工作规则

1. 先从与当前工作匹配的 task-area 局部 `README` 进入。
2. 除非局部 README 明确提升，否则更深层 dated 文档应视为证据、closure 记录或
   支撑计划。
3. 跨领域任务请通过 `simulation_architecture/`、`review/`
   或 `issues/` 收敛，不要继续把旧 air-first 入口扩大成通用入口。
4. 当某个区域生命周期发生变化，先更新局部 README，再调整这个根导航。
5. 已完成子项目如果不破坏 active gate，应移入对应区域的 `archive/`；否则应在父级
   README 中降级为 sealed、retained 或 archived record，并把后续工作另开 follow-on。

## 文档类型

- `分析` / `审计`：捕捉特定片段的发现和理由。
- `计划` / `冻结`：记录该片段的范围化实现计划。
- `任务板`：记录某条工作线的分阶段工作分解。
- `当前状态` / `进度检查点`：进入此树中最新状态的最佳入口点。
- `收敛`：主要为保持可追溯性而保留的实现记录，而非默认的活跃计划。
- `归档`：已移出默认活跃路径、但仍为保持可追溯性而保留的历史快照。
