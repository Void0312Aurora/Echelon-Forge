# Tools 脚本治理功能矩阵

Document kind: `review`
Lifecycle: `accepted`
Canonical: `docs/engineering/automation/reviews/tools_script_governance_matrix_20260611.zh.md`
Owner: `engineering/automation`
Last verified: `2026-06-11`

状态：`2026-06-11` 活跃治理表。
范围：`tools/**/*.py`、`tools/**/*.sh`、`tools/**/*.ps1`。

## 1. 治理结论

`tools/` 应按长期功能能力组织，而不是按任务编号、阶段编号、实验代号或临时过程组织。历史任务编号可以保留在文档叙述、默认配置路径、实验产物名和参数 ID 中；维护入口文件名应优先表达工具能力。

本轮已完成的低风险切片：

| 原入口类别 | 新入口 | 功能能力 | 处理 |
| --- | --- | --- | --- |
| 旧 SB3 命名 eval 入口 | `tools/eval/policy_execution_eval.py` | learned execution policy evaluation | 已重命名并删除旧入口，不保留包装壳。 |
| 旧 N4 baseline 命名 eval 入口 | `tools/eval/naval_station_policy_eval.py` | naval station policy gate | 已重命名并删除旧入口，不保留包装壳。 |
| 顶层 post-launch benchmark 入口 | `tools/diagnostics/benchmark.py --family air_combat_post_launch_assessment` | air-combat post-launch assessment benchmark family | 已迁入 `tools/diagnostics/benchmarks/` 并注册 family，删除顶层 benchmark 文件。 |
| 顶层 fire-timing learnability audit | `tools/diagnostics/fire_timing_fault_localization_probe.py --mode learnability_audit` | fire-timing learnability diagnostic mode | 已迁入 fire-timing fault-localization 命令族，删除顶层 probe 文件。 |
| 顶层 flight trajectory 任务包装入口 | `tools/diagnostics/flight_trajectory_diagnostics.py --mode takeoff_to_landing/runway_drift_sweep` | flight trajectory diagnostic modes | 已迁入 flight trajectory 命令族，删除两个任务特定 wrapper 文件。 |

同步完成：

- `tests/eval/test_evaluation_cli_contracts.py` 改为导入新模块并断言新 payload `mode`。
- README、示例配置文档、shell 调用脚本和任务归档中的活路径已迁移到新入口。
- `tools/diagnostics/ablate_visual_training_effect.py` 改为调用 `policy_execution_eval.py`。
- 旧活入口精确文件名扫描已清空；治理矩阵只保留语义描述，不保留已删除路径字符串。
- 新增 `tests/architecture/governance/test_tools_script_governance.py`，把 diagnostics 顶层入口白名单、benchmark registry 约束和旧 wrapper 路径禁复活规则固化为 architecture guard。

## 2. 通用化规则

新增或保留 `tools/` 脚本时，先问“这个工具提供哪种可复用能力”，不要先问“哪个子项目需要一个脚本”。

默认规则：

- eval 入口应覆盖一类评估能力，通过 `--mode`、配置和共享 helper 扩展，不为单个任务新增 wrapper。
- diagnostics 入口应覆盖一类定位/测量能力，通过 mode、subcommand、benchmark family 或 JSON config 扩展，不为一次实验新增脚本。
- runners 入口是稳定执行面；只有新的 suite contract 形态出现时才新增 runner。
- maintenance 入口应按治理对象或 artifact 生命周期组织，不按 A2、RES、Stage、candidate id 拆散。
- archive 中的脚本不参与活入口治理；除非被活文档或测试重新引用，否则保持归档。
- 如果一个脚本的职责只是“调用另一个工具并固定参数”，默认归档或删除。

## 3. 当前工具系统功能面

| 功能面 | 当前入口 | 判断 | 后续动作 |
| --- | --- | --- | --- |
| task metric eval | `tools/eval/eval_task.py`、`tools/eval/task_eval_driver.py` | 功能名基本稳定。 | 保留；任务指标评估已收敛到 maintained single-world WorldBatchRuntime，新增行为应扩展 driver。 |
| learned policy eval | `tools/eval/policy_execution_eval.py`、`tools/eval/sb3_eval_base.py` | 本轮已语义化。 | 保留；`sb3_eval_base.py` 是后端 helper，不作为顶层能力名。 |
| naval station policy gate | `tools/eval/naval_station_policy_eval.py` | 本轮已语义化。 | 保留；不再使用 N4 作为入口文件名。 |
| benchmark diagnostics | `tools/diagnostics/benchmark.py`、`tools/diagnostics/run_benchmark_suite.py`、`tools/diagnostics/benchmarks/*` | 已是功能族；post-launch assessment benchmark 已迁入 family。 | 保留；新增 benchmark 进 `benchmarks/` 和 registry。 |
| cooperative trajectory diagnostics | `tools/diagnostics/diagnose_cooperative_trajectory.py`、`cooperative_trajectory_base.py` | 已是功能族。 | 保留；不要恢复 takeoff/takeoff-to-cruise wrapper。 |
| flight trajectory diagnostics | `tools/diagnostics/flight_trajectory_diagnostics.py --mode takeoff_to_landing/runway_drift_sweep` | 已合并任务特定轨迹诊断入口。 | 保留统一入口；内部实现位于 `tools/diagnostics/flight_trajectory/`。 |
| runtime bridge diagnostics | `arma_proxy_backend_stub.py` | 域名清楚，非项目代号。 | 保留 stub；raw `UniversalEnv` env backend 已归档到 `tools/archive/`，不再是活入口。 |
| air-combat process tracing | `air_combat_weapon_employment_process_probe.py` | 本轮已语义化；入口表达武器使用/杀伤链诊断能力。 | 保留统一入口；运行时已迁到 batch=1 `WorldBatchVecEnv` adapter，历史 stage 配置名只留在场景/训练配置路径中。 |
| event-credit diagnostics | `event_credit_head_probe.py --mode offline_fit`、`event_credit_head_probe.py --mode online_update` | 已完成入口合并，默认路径仍可保留历史 A7 实验名。 | 保留统一入口；内部实现位于 `tools/diagnostics/event_credit_head/`。 |
| fire-timing fault localization | `fire_timing_fault_localization_probe.py --mode structural_toy/real_update/chain_breakpoint/learnability_audit` | 已完成入口合并，默认路径仍可保留历史 M3S2 实验名。 | 保留统一入口；内部实现位于 `tools/diagnostics/fire_timing_fault_localization/`。 |
| workspace cleanup/audit | `redundancy_audit.py`、`cleanup_redundancy.py`、`isolate_repro_workspace.sh` | 功能名稳定。 | 保留。 |
| docs maintenance | `translate_docs_batch.py`、`wp_doc_closure_audit.py` | 功能名稳定。 | 保留。 |
| A2 damage-model maintenance closure | 已退役；最后完整树见 `c0e4f31f` | 项目已封存，原工具、候选产物生成器、release/source governance 与自引用 hash 守卫不再服务活发布路径。 | 删除闭合维护链；唯一仍约束运行时的 authority invariant 已移入对应 runtime 测试的本地 fixture。 |
| A2 top-level legacy entries | `tools/maintenance/a2_*.py` 剩余 0 个 | 顶层历史入口已清零。 | 后续不再新增 A2/阶段命名入口；新增能力必须进入语义命令族。 |
| archived probes | `tools/archive/*` | 已不属于活入口。 | 保留在 archive；若活文档引用则迁移引用或恢复为 maintained 工具。 |

## 4. 下一轮激进清理顺序

| 批次 | 目标 | 预期结果 | 风险 |
| --- | --- | --- | --- |
| 已完成 | eval 入口语义化 | `policy_execution_eval.py`、`naval_station_policy_eval.py` 成为活入口；旧 eval 文件删除。 | 需要同步 shell、docs、tests。 |
| 已完成 | event-credit diagnostics 合并 | `event_credit_head_probe.py --mode offline_fit/online_update` 成为统一能力入口。 | 默认模型/配置路径仍包含 A7，这是历史实验定位，不是活入口命名。 |
| 已完成 | fire-timing fault localization 合并 | `fire_timing_fault_localization_probe.py --mode structural_toy/real_update/chain_breakpoint` 成为统一能力入口。 | tests/training helper import 已迁移到语义子包。 |
| 已完成 | fire-timing learnability audit 合并 | `fire_timing_fault_localization_probe.py --mode learnability_audit` 成为统一能力入口。 | 顶层 air-combat learnability audit 文件删除；活测试 import 与归档可复跑命令迁移。 |
| 已完成 | flight trajectory diagnostics 合并 | `flight_trajectory_diagnostics.py --mode takeoff_to_landing/runway_drift_sweep` 成为统一能力入口。 | 顶层 trajectory 任务包装文件删除；README 与历史引用迁移。 |
| 已完成 | tools governance guard 固化 | `tests/architecture/governance/test_tools_script_governance.py` 固化顶层入口白名单、benchmark registry 约束和旧 wrapper 禁复活扫描。 | 后续新增入口需显式更新测试与治理矩阵。 |
| 已完成 | air-combat process probe 改名 | `air_combat_weapon_employment_process_probe.py` 成为语义入口；旧过程代号入口删除。 | 已同步 runtime tests、diagnostics docs、model/archive docs。 |
| 已完成 | post-launch assessment benchmark family 化 | `benchmark.py --family air_combat_post_launch_assessment` 成为统一入口；顶层 benchmark 文件删除。 | 保留 benchmark 参数与 JSON payload，不保留兼容包装壳。 |
| 已完成 | A2 maintenance closure 退役 | 删除已封存项目的 `damage_model.py`、A2 path resolver、candidate/release/source/retained governance 模块及其 architecture contract tests。 | 历史材料保持只读；需要复核旧实现时从 `c0e4f31f` 提取，不恢复现役自维护链。 |
| P3 | archive 引用清理 | 活文档不再引用 archived scratch 脚本。 | 只改引用，不改历史证据内容。 |

## 5. A2 maintenance 的处理边界

A2 research/candidate 项目已经封存，原维护工具的消费者也只剩历史文档、配套 architecture tests
和 hash 清单。把这些消费者视为永久保留理由会形成自引用治理闭环，因此该闭环已退役。历史材料仍以
只读记录保留；如需复核生成逻辑或旧命令，使用 `git show c0e4f31f:<path>`，不得在没有新的活发布
需求时恢复该工具族。直接影响现役 runtime 行为的 authority invariant 已由 runtime 测试本地构造，
不再依赖候选产物生成器的模块级 import。

## 6. 验收规则

每个 `tools/` 清理批次必须同时满足：

- 新入口名表达功能能力，不表达 A2、A7、M3S2、N4、Stage、P0/P1 等任务/过程代号。
- 删除旧入口前，所有活调用路径、测试 import、README 和 suite 文档已迁移。
- 新增 diagnostics 顶层入口、benchmark family 或恢复旧 wrapper 路径时，必须同步更新 `test_tools_script_governance.py` 并说明功能入口理由。
- 如果旧入口被归档任务文档作为历史证据引用，迁移为新路径或明确标注历史名，不保留失效活命令。
- 合并脚本时优先保留共享 helper，再以 `--mode` 或 subcommand 区分场景。
- 不把 `tools/archive/` 的历史脚本重新纳入活入口，除非同时补 README、测试和维护责任。

最小验证命令：

```bash
source tools/maintenance/cmo_env.sh && cmo_python -m py_compile <touched-tools>
source tools/maintenance/cmo_env.sh && cmo_python -m pytest -q <touched-tests>
rg -n "<old-tool-file-name>" README.md README.zh.md tools tests docs examples scripts
git diff --check
```

如改动 smoke suite 或稳定 runner，再补跑：

```bash
source tools/maintenance/cmo_env.sh && cmo_python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
```
