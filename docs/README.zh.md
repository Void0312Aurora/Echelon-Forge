# 文档索引

语言：
- 英文规范页：`README.md`
- 中文配套页：[README.zh.md](README.zh.md)

`docs/` 是 Echelon Forge 作为多域仿真与强化学习工程平台的仓库导航面。
当前文档树已经不再只是空战/飞行任务 workbench，而是同时覆盖空战与飞行
执行、协同执行与训练、海军、地面、可视化/game 代理、模型与 world-model
规划，以及由 runtime/tests/contracts 支撑的不同成熟度证据。

使用本索引时，先判断文档类别，再判断单篇文档的权威性。任务 checkpoint
可以是准确的历史记录，但不一定是当前规则；标准文档可以拥有命名权，而任务
页拥有某个范围化实现计划；手册可以说明代码边界，但不自动授权新工作。

## 维护入口面

- [plan/README.zh.md](plan/README.zh.md)
  - 架构/项目权威、runtime facade 与 exact-runtime 计划、协同计划材料、冻结
    执行范围和计划治理。
- [task/README.zh.md](task/README.zh.md)
  - 领域/任务工作线、实现包、进度 checkpoint 和 archive 索引。进入某个领域
    时先读局部 README，再继续进入带日期的深层文件。
- [standards/README.zh.md](standards/README.zh.md)
  - 联合/军种/领域建模标准、平台基线、治理规则和 bridge contract。标准文档
    拥有共享词汇和层级归属的权威。
- [manual/](manual)
  - 维护者和操作员手册：代码层映射、引擎能力、物理清单、可视化指南和任务
    说明。
- [reference_artifacts.zh.md](reference_artifacts.zh.md)
  - 对维护工作仍有意义的配置、场景和制品来源记录。
- [../tests/README.md](../tests/README.md)
  - `docs/` 之外的测试系统入口：runtime suites、JSON contracts、focused/local
    suite manifest，以及被选中 contract batch 的执行行为。

## 多域与任务导航

- 空域与执行：
  [task/air_combat/](task/air_combat/README.zh.md)、
  [task/flight_dynamics/](task/flight_dynamics/README.md)、
  [task/performance_runtime/](task/performance_runtime/README.md)、
  [plan/runtime_facade/](plan/runtime_facade/README.zh.md)，以及
  [tests/runtime/execution/](../tests/runtime/execution)。
- 协同：
  [plan/cooperative/](plan/cooperative/README.zh.md)、
  [task/simulation_architecture/](task/simulation_architecture/README.md)，以及
  [tests/runtime/multi_agent/](../tests/runtime/multi_agent)。
- 海军：
  [task/naval/](task/naval/README.md)、
  [standards/naval/](standards/naval/README.zh.md)、
  [tests/runtime/naval/](../tests/runtime/naval)，以及
  [tests/contracts/unit/naval/](../tests/contracts/unit/naval)。
- 地面：
  [task/ground/](task/ground/README.zh.md)、
  [standards/ground/](standards/ground/README.zh.md)、
  [tests/runtime/ground/](../tests/runtime/ground)，以及
  [tests/contracts/unit/ground/](../tests/contracts/unit/ground)。
- 可视化与 game 代理：
  [task/viz/](task/viz/README.zh.md)、
  [task/game/](task/game/README.zh.md)，以及
  [manual/visualization_guide.zh.md](manual/visualization_guide.zh.md)。
- 模型、策略与 world-model：
  [task/model/](task/model/README.zh.md)、
  [forward/models/hierarchical_moe_execution_policy.zh.md](forward/models/hierarchical_moe_execution_policy.zh.md)、
  [../python/world_model/](../python/world_model)，以及
  [tests/contracts/unit/world_model/](../tests/contracts/unit/world_model)。
- Runtime contracts 与架构收口：
  [task/simulation_architecture/](task/simulation_architecture/README.md)、
  [plan/architecture/](plan/architecture/README.zh.md)、
  [manual/src_layer_map.zh.md](manual/src_layer_map.zh.md)，以及
  [../tests/contracts/](../tests/contracts)。

## 文档类别

| 入口 | 用途 | 权威边界 |
|------|------|----------|
| `plan/` | 架构方向、冻结范围、contract 计划和路线治理 | 当计划仍为当前版本或被明确冻结时具备权威；已归档计划是历史 |
| `task/` | 活跃领域工作、带日期任务包、进度记录和收口证据 | 局部 README 说明当前入口；深层 dated 文件默认是支撑记录，除非被提升 |
| `standards/` | 共享词汇、军种/领域归属、公开来源准入、双语策略和治理 | 当 task 文档与标准冲突时，命名、层级归属和建模边界以 standards 为准 |
| `manual/` | 代码地图、操作说明、能力清单和实际工作流 | 描述维护行为；改实现前仍需对照当前代码和测试 |
| `forward/` | 尚未排期为实现工作的 backlog、roadmap 和设计想法 | 未提升到 `plan/` 或 `task/` 前，不是实现权威 |
| `Archive/`、嵌套 `archive/`、`temp/`、`log/`、`book/`、`results/` | 溯源、本地保留、草稿、生成/参考材料或历史快照 | 除非维护 README 明确指向，否则不是当前工作的默认权威 |

## 成熟度与权威边界

- 目录存在不等于能力已经成熟。此树同时包含稳定标准、已接受基线、活跃实现
  线、探索性原型和退役记录。
- air/execution 与 runtime-facade 材料是当前较成熟的主线入口，但其中仍包含
  历史 checkpoint 和前瞻性切片。
- cooperative、naval、ground、model/world-model、viz/game 各自处在不同成熟度。
  每次进入前都应读取局部 README，确认 accepted、active、held 或 exploratory
  状态。
- ground 目前已有 tasking/schema 证据，但更广的 movement、sensing、terrain、
  fires、damage 和完整 runtime 行为可能仍被局部任务入口保持为 held。
- game 与 visualization 工作默认是“仿真后端为权威”的代理/呈现工作，除非维护
  任务页另有说明；前端实验不会重定义仿真真值。
- tests 与 JSON contracts 提供的是所选 runner 或 suite 的可执行证据。某个
  contract 通过不自动表示整个领域成熟；被选中的 batch 失败仍按测试 runner
  策略视为执行失败。
- 当前代码与维护中的 contracts 优先于过期任务文字。需要改代码时，先读相关
  `plan/` 或 `task/` 入口，再对照当前代码树和测试验证。

## 语言与许可说明

- 严格双语维护面并不覆盖整棵文档树，而是聚焦在入口导航、标准/治理、操作手册
  和稳定计划权威面。
- 高频变更的 task 历史、dated checkpoint 和 forward 想法文档，默认按英文主文
  维护；只有被明确提升的较小切片才需要持续双语对等。
- 避免将混合语言页面作为目标稳态。
- 维护文档默认受仓库级 Apache-2.0 许可覆盖，除非具体文件或保留的第三方
  artifact 另有说明。第三方资产、数据集、来源摘录和保留输入 artifact 保留其
  自身的权利和许可证状态；见 [../LICENSE](../LICENSE) 和
  [../THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)。

## 使用规则

- 如果某个任务需要修改代码，建议先阅读相关的 `plan/` 或 `task/` 条目，再对照
  当前代码树和测试进行验证。
- 如果某个文档链接到历史制品，请在将其视为可操作入口之前，确认目标仍在工作
  空间中存在。
