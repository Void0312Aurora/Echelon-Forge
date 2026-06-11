# Tools 脚本治理功能矩阵

状态：`2026-06-11` 活跃治理表。
范围：`tools/**/*.py`、`tools/**/*.sh`、`tools/**/*.ps1`。

## 1. 治理结论

`tools/` 应按长期功能能力组织，而不是按任务编号、阶段编号、实验代号或临时过程组织。历史任务编号可以保留在文档叙述、默认配置路径、实验产物名和参数 ID 中；维护入口文件名应优先表达工具能力。

本轮已完成的低风险切片：

| 原入口类别 | 新入口 | 功能能力 | 处理 |
| --- | --- | --- | --- |
| 旧 SB3 命名 eval 入口 | `tools/eval/policy_execution_eval.py` | learned execution policy evaluation | 已重命名并删除旧入口，不保留包装壳。 |
| 旧 N4 baseline 命名 eval 入口 | `tools/eval/naval_station_policy_eval.py` | naval station policy gate | 已重命名并删除旧入口，不保留包装壳。 |

同步完成：

- `tests/eval/test_evaluation_cli_contracts.py` 改为导入新模块并断言新 payload `mode`。
- README、示例配置文档、shell 调用脚本和任务归档中的活路径已迁移到新入口。
- `tools/diagnostics/ablate_visual_training_effect.py` 改为调用 `policy_execution_eval.py`。
- 旧活入口精确文件名扫描已清空；治理矩阵只保留语义描述，不保留已删除路径字符串。

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
| task metric eval | `tools/eval/eval_task.py`、`tools/eval/task_eval_driver.py` | 功能名基本稳定。 | 保留；新增 raw-env/task metric 行为应扩展 driver。 |
| learned policy eval | `tools/eval/policy_execution_eval.py`、`tools/eval/sb3_eval_base.py` | 本轮已语义化。 | 保留；`sb3_eval_base.py` 是后端 helper，不作为顶层能力名。 |
| naval station policy gate | `tools/eval/naval_station_policy_eval.py` | 本轮已语义化。 | 保留；不再使用 N4 作为入口文件名。 |
| benchmark diagnostics | `tools/diagnostics/benchmark.py`、`tools/diagnostics/run_benchmark_suite.py`、`tools/diagnostics/benchmarks/*` | 已是功能族。 | 保留；新增 benchmark 进 `benchmarks/` 和 registry。 |
| cooperative trajectory diagnostics | `tools/diagnostics/diagnose_cooperative_trajectory.py`、`cooperative_trajectory_base.py` | 已是功能族。 | 保留；不要恢复 takeoff/takeoff-to-cruise wrapper。 |
| runtime bridge diagnostics | `arma_proxy_backend_stub.py`、`arma_proxy_backend_echelon_env.py` | 域名清楚，非项目代号。 | 保留。 |
| air-combat process tracing | `air_combat_weapon_employment_process_probe.py` | 本轮已语义化；入口表达武器使用/杀伤链诊断能力。 | 保留统一入口；历史 stage 配置名只留在场景/训练配置路径中。 |
| event-credit diagnostics | `event_credit_head_probe.py --mode offline_fit`、`event_credit_head_probe.py --mode online_update` | 已完成入口合并，默认路径仍可保留历史 A7 实验名。 | 保留统一入口；内部实现位于 `tools/diagnostics/event_credit_head/`。 |
| fire-timing fault localization | `fire_timing_fault_localization_probe.py --mode structural_toy/real_update/chain_breakpoint` | 已完成入口合并，默认路径仍可保留历史 M3S2 实验名。 | 保留统一入口；内部实现位于 `tools/diagnostics/fire_timing_fault_localization/`。 |
| workspace cleanup/audit | `redundancy_audit.py`、`cleanup_redundancy.py`、`isolate_repro_workspace.sh` | 功能名稳定。 | 保留。 |
| docs maintenance | `translate_docs_batch.py`、`wp_doc_closure_audit.py` | 功能名稳定。 | 保留。 |
| damage-model external evidence | `tools/maintenance/damage_model_external_evidence.py` | 本轮已合并 source-rights signoff request、external signoff intake/template/preflight。 | 保留统一入口；内部实现位于 `tools/maintenance/external_signoff_evidence/`。 |
| damage-model source governance | `tools/maintenance/damage_model_source_governance.py` | 本轮已合并 source admission audit、source payload pack、source rights output policy。 | 保留统一入口；内部实现位于 `tools/maintenance/source_governance/`。 |
| damage-model benchmark evidence | `tools/maintenance/damage_model_benchmark_evidence.py` | 本轮已合并 comparison hashes、mechanism evidence、benchmark execution、debris case、spreadsheet recalculation/replacement/lineage admission。 | 保留统一入口；内部实现位于 `tools/maintenance/benchmark_evidence/`。 |
| damage-model scope/provenance | `tools/maintenance/damage_model_scope_provenance.py` | 本轮已合并 geometry/warhead row provenance、target geometry closeout、warhead scope closeout、mechanism source closeout。 | 保留统一入口；内部实现位于 `tools/maintenance/scope_provenance/`。 |
| damage-model independent review | `tools/maintenance/damage_model_independent_review.py` | 本轮已合并 Stage B effect-scale review、RES-011/012 review closeout、scope-bucket review、uncertainty review。 | 保留统一入口；内部实现位于 `tools/maintenance/independent_review/`。 |
| damage-model release governance | `tools/maintenance/damage_model_release_governance.py` | 本轮已合并 package provenance/identity、provenance review/closeout、source release signoff、scoped release identity、Stage B release readiness/closeout。 | 保留统一入口；内部实现位于 `tools/maintenance/release_governance/`。 |
| damage-model candidate artifacts | `tools/maintenance/damage_model_candidate_artifacts.py` | 本轮已合并 validation scaffold、scope boundary probe、Stage B effect-scale snapshot/result/retained pack、runtime authority exercise、candidate package bundle、Stage C component-probability artifact/review gates。 | 保留统一入口；内部实现位于 `tools/maintenance/candidate_artifacts/`。 |
| A2 retained-artifact governance | `tools/maintenance/a2_*.py` 剩余 4 个 | 功能面重要，但文件边界仍按任务/阶段膨胀。 | 继续按 command family 合并后删除旧入口。 |
| archived probes | `tools/archive/*` | 已不属于活入口。 | 保留在 archive；若活文档引用则迁移引用或恢复为 maintained 工具。 |

## 4. 下一轮激进清理顺序

| 批次 | 目标 | 预期结果 | 风险 |
| --- | --- | --- | --- |
| 已完成 | eval 入口语义化 | `policy_execution_eval.py`、`naval_station_policy_eval.py` 成为活入口；旧 eval 文件删除。 | 需要同步 shell、docs、tests。 |
| 已完成 | event-credit diagnostics 合并 | `event_credit_head_probe.py --mode offline_fit/online_update` 成为统一能力入口。 | 默认模型/配置路径仍包含 A7，这是历史实验定位，不是活入口命名。 |
| 已完成 | fire-timing fault localization 合并 | `fire_timing_fault_localization_probe.py --mode structural_toy/real_update/chain_breakpoint` 成为统一能力入口。 | tests/training helper import 已迁移到语义子包。 |
| 已完成 | air-combat process probe 改名 | `air_combat_weapon_employment_process_probe.py` 成为语义入口；旧过程代号入口删除。 | 已同步 runtime tests、diagnostics docs、model/archive docs。 |
| 已完成 | external signoff evidence 合并 | `damage_model_external_evidence.py signoff-request/intake-contract/packet-template/admission-preflight` 成为统一维护入口。 | 旧 source-rights signoff request、signoff intake/template/preflight 顶层脚本删除；architecture tests 改用语义模块。 |
| 已完成 | source governance 合并 | `damage_model_source_governance.py admission-audit/payload-pack/rights-output-policy` 成为统一维护入口。 | 旧 source admission audit、source payload pack、source rights output policy 顶层脚本删除；architecture tests 改用语义模块。 |
| 已完成 | benchmark evidence 合并 | `damage_model_benchmark_evidence.py` 覆盖 mechanism/comparison hash、benchmark execution、debris case、spreadsheet recalculation/replacement/lineage admission。 | 旧 benchmark evidence/admission 顶层脚本删除；architecture tests 改用语义模块。 |
| 已完成 | scope/provenance closeout 合并 | `damage_model_scope_provenance.py row-provenance/target-geometry-closeout/warhead-scope-closeout/mechanism-source-closeout` 成为统一维护入口。 | 旧 scope/provenance closeout 顶层脚本删除；architecture tests 改用语义模块。 |
| 已完成 | independent review 合并 | `damage_model_independent_review.py effect-scale-review/review-closeout/scope-bucket-review/uncertainty-review` 成为统一维护入口。 | 旧 independent review 顶层脚本删除；architecture tests 改用语义模块。 |
| 已完成 | release governance 合并 | `damage_model_release_governance.py package-provenance-identity/provenance-identity-review/provenance-closeout/source-release-signoff/scoped-release-identity/effect-scale-readiness/effect-scale-closeout` 成为统一维护入口。 | 旧 release gate 顶层脚本删除；architecture tests 与活文档引用改用语义入口。 |
| 已完成 | candidate artifacts 合并 | `damage_model_candidate_artifacts.py validation-scaffold/scope-boundary-probe/effect-scale-snapshot/effect-scale-result-pack/effect-scale-retained-pack/runtime-authority-exercise/package-bundle/component-probability-*` 成为统一维护入口。 | 旧 candidate artifact 与 Stage C component-probability 顶层脚本删除；release、fragility、benchmark/scope 引用改用语义模块。 |
| P2 | A2 maintenance 命令族合并 | 剩余 4 个 `a2_*` 入口继续压缩成少数 artifact governance 命令族。 | 这是 retained-artifact 历史接口，不应只做表面重命名。 |
| P3 | archive 引用清理 | 活文档不再引用 archived scratch 脚本。 | 只改引用，不改历史证据内容。 |

## 5. A2 maintenance 的处理边界

`tools/maintenance/a2_*` 不是测试层命名问题，而是 retained-artifact 治理工具膨胀问题。直接把 47 个文件逐个改成语义名，只会制造 47 个新名字；更合理的激进清理是先合并命令族：

| 命令族 | 可承接的旧脚本类型 |
| --- | --- |
| `damage_model_external_evidence.py` | source-rights signoff request、signoff intake、external packet template、admission preflight。 |
| `damage_model_source_governance.py` | source admission audit、source payload pack、source rights output policy。 |
| `damage_model_benchmark_evidence.py` | TP-21 selected case、BEC-O recalculation/tolerance、benchmark evidence/admission。 |
| `damage_model_scope_provenance.py` | target geometry、warhead scope、row provenance、mechanism source closeout。 |
| `damage_model_independent_review.py` | Stage B independent review、scope-bucket review、uncertainty review、RES-011/012 review closeout。 |
| `damage_model_candidate_artifacts.py` | validation scaffold、scope boundary probe、effect-scale snapshot/result/retained pack、runtime authority exercise、candidate bundle、component-probability artifact/review gates。 |
| `damage_model_release_governance.py` | package provenance/identity、release readiness、release closeout、source release signoff、scoped release identity、provenance review/closeout。 |

旧入口删除前必须满足：对应命令族能覆盖旧 CLI 的输出文件、hash-only/fail-closed 行为、文档中保留物路径、以及 architecture 测试里已经固化的 contract。

## 6. 验收规则

每个 `tools/` 清理批次必须同时满足：

- 新入口名表达功能能力，不表达 A2、A7、M3S2、N4、Stage、P0/P1 等任务/过程代号。
- 删除旧入口前，所有活调用路径、测试 import、README 和 suite 文档已迁移。
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
