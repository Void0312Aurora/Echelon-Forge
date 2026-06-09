# 任务归档注册表

状态：`2026-06-09` 建立。本文件注册 `docs/task/archive/` 下所有已归档子项目，供快速查阅。

每个条目记录：子项目名称、归档日期、工作描述、归档理由。

---

## 已归档子项目

### `common_air_naval/`

- **归档日期**：2026-06-09
- **描述**：Common / Air / Naval 三域 DTO 模块拆分冻结计划。将混杂的 DTO 拆分为 `联合/通用核心`（`common/`）、`空中特化`（`air/`）、`海军特化`（`naval/`），在保持兼容伞状头文件的前提下建立 Python profile dispatch seam。含 WP0–WP8 共 9 个工作包，全部已完成并验收。
- **归档理由**：基础结构（common/air/naval DTO 拆分、TaskOrder/LeaderIntent/PilotReport 通用核心提取、MissionCommand 兼容拆分、Python profile 分发接缝）已落地为主代码。后续 naval runtime 扩展和 air-first helper 迁移由独立任务单推进。
- **主要产出**：`src/components/tasking/common/`、`src/components/tasking/air/`、`src/components/command/common/`、`src/components/command/ground/` 等目录；`MissionCommandCore/Air/Naval/Ground` 投影体系。

### `code_redundancy/`

- **归档日期**：2026-06-09
- **描述**：代码冗余识别与去重工作线。记录项目中已识别的代码重复模式（DRY 违规、重复逻辑块、模板化 boilerplate）、冗余分析和去重建议。
- **归档理由**：已转为归档型工作记录。当前冗余问题由架构重构审计（`docs/task/review/architecture_refactoring_audit_20260522`）跟踪。
- **主要产出**：冗余分析文档、去重建议记录。

### `diagnostics_eval/`

- **归档日期**：2026-06-09
- **描述**：诊断工具与评估入口收敛工作线。覆盖 diagnostics benchmark CLI 收敛、diagnostics 模块化、eval 入口统一。旨在将分散的诊断脚本和评估工具收敛为一致的工具链入口。
- **归档理由**：已转入归档型工作记录。实际诊断工具代码位于 `tools/diagnostics/`，评估入口位于 `tools/eval/`，均已进入维护态。
- **主要产出**：`diagnostics_benchmark_cli_convergence`、`diagnostics_modularization`、`eval_entrypoint_convergence` 三份收敛记录。

### `game/`

- **归档日期**：2026-06-09
- **描述**：游戏前端集成探索工作线。探索在保持 Echelon Forge 后端为权威仿真真值的前提下，接入可玩的外部游戏前端（Arma 3）。核心原则：后端权威留在 Echelon，外部游戏实体只是代理体/表现壳，AI 行为来自仓库内训练策略。
- **归档理由**：探索性工作线，非活跃执行项目。实际 Arma proxy 集成代码位于 `tools/diagnostics/arma_proxy_backend_stub.py` 和 `arma_proxy_backend_echelon_env.py`。
- **主要产出**：Arma proxy backend stub、Arma proxy Echelon env backend。

### `performance_runtime/`

- **归档日期**：2026-06-09
- **描述**：Runtime 性能优化任务子项目。在真实性/保真度深化线临时冻结后，承接 runtime 性能工作：优化分层规则、计算链路分析、benchmark 导向的优化入口收拢。
- **归档理由**：优化分层与 benchmark 导向分析已冻结，旧规划链路视作参考材料。
- **主要产出**：runtime 性能规划文档、优化顺序与升级规则、热路径分析记录。

### `python_rl/`

- **归档日期**：2026-06-09
- **描述**：Python RL 框架子文件夹收敛记录。覆盖 `python/rl/` 下 control、runtime、tasking、policy_algo、planning_support 等子目录的模块化收敛工作，以及根目录 shim callsite 的去重与规范化。
- **归档理由**：已转入收敛记录归档。各子文件夹的模块化收敛已完成。
- **主要产出**：8 份子文件夹收敛记录。

---

## 归档规则

满足任一条件即可考虑归档：

1. 工作包全部完成并验收，后续工作已移交独立任务单。
2. 子项目自声明为"归档型工作记录"，且无活跃执行面。
3. 探索性工作线已冻结，实际代码产出已进入维护态。
4. 规划文档已冻结为参考材料，不再作为活跃执行入口。

---

*注册表建立于 2026-06-09。*
