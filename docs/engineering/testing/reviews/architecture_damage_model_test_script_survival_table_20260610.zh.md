# Architecture Damage-Model 测试功能矩阵

Document kind: `review`
Lifecycle: `accepted`
Canonical: `docs/engineering/testing/reviews/architecture_damage_model_test_script_survival_table_20260610.zh.md`
Owner: `engineering/testing`
Last verified: `2026-06-10`

状态：`2026-06-10` 活跃治理表。
范围：`tests/architecture/damage_model/*.py`。
说明：本文件名保留为既有 review 链接兼容路径；正文口径已从“脚本生存表”改为“功能矩阵”。后续清理不再问“这个历史脚本要不要活”，而是问“这个测试系统必须提供哪些功能能力，以及哪些脚本只是历史过程残留”。

## 1. 治理结论

`damage_model` 测试系统应面向功能能力组织，而不是面向 A2、blastfrag、RES、Stage B/C 等内部过程名组织。历史任务可以解释某个断言为什么出现，但不应继续决定测试文件边界。

当前已经执行的收敛：

| 指标 | 当前值 |
| --- | ---: |
| damage_model 测试脚本数 | 14 |
| damage_model 测试函数数 | 173 |
| 已替代的 release 历史文件名 | 5 |
| 已替代的 independent review 历史文件名 | 4 |
| 已替代的 scope provenance 历史文件名 | 2 |
| 已替代的 source evidence 历史文件名 | 2 |
| 已替代的 candidate artifact 历史文件名 | 4 |
| 已替代的 benchmark evidence 历史文件名 | 2 |
| 新 release 能力文件 | `test_release_authority_guardrails.py` |
| 新 independent review 能力文件 | `test_independent_review_closeout_gates.py` |
| 新 scope provenance 能力文件 | `test_scope_provenance_closeout_gates.py` |
| 新 source evidence 能力文件 | `test_source_evidence_governance.py` |
| 新 candidate artifact 能力文件 | `test_candidate_artifact_contracts.py` |
| 新 benchmark evidence 能力文件 | `test_benchmark_evidence_admission.py` |
| architecture collect-only 基线 | 461 collected |
| 最近 smoke suite 基线 | 321 passed, 38 subtests passed |

本轮已把 release provenance、release signoff、scoped release identity、effect-scale release readiness、effect-scale release closeout 五个历史文件名并入 `test_release_authority_guardrails.py`。

同时把 effect-scale independent review、bounded review closeout、scope bucket review、uncertainty review 四个历史文件名并入 `test_independent_review_closeout_gates.py`。

同时把 target/warhead scope closeout 与 geometry/warhead row provenance 两个历史文件名并入 `test_scope_provenance_closeout_gates.py`。

同时把 source payload/output policy 与 source-rights signoff request 两个历史文件名并入 `test_source_evidence_governance.py`。

同时把 candidate bundle、effect-scale candidate artifacts、retained artifact pack、runtime-aligned authority exercise 四个历史文件名并入 `test_candidate_artifact_contracts.py`。

同时把 external benchmark output admission 与 RES005/006 benchmark execution admission 两个历史文件名并入 `test_benchmark_evidence_admission.py`。

维护工具名中的 `a2_blastfrag_*` 暂不改名。它们是生产/保留物历史接口；本轮只重建测试层的语义边界。

## 2. 通用化规则

本表不只是 `damage_model` 的存量清单，也作为 `tests/architecture` 的能力文件整理样例：测试脚本应面向长期稳定的功能能力，而不是面向 A2、blastfrag、RES、Stage B/C、候选包或某次评审流程。

后续新增场景默认追加到既有能力文件中，通过测试函数、参数化、fixture 或 shared helper 扩展覆盖面。只有出现新的能力边界、不同的执行模型、独立的 artifact 生命周期、独立 failure policy，或既有文件已经变成不相关 setup 混合体时，才允许新增文件。

小于三到五个测试且只因历史任务标签存在的文件，默认列为合并候选。若能力文件继续膨胀，拆分方向必须是能力子面，例如 `release authority`、`benchmark admission`、`source evidence governance`，而不是工程代号、任务编号或阶段名。

历史标识仍可保留在测试函数名、参数 ID、注释和任务文档中用于追溯；文件名必须优先表达能力语义。维护工具名中的 `a2_blastfrag_*` 属于生产/保留物接口历史，不纳入本轮测试脚本语义重建。

## 3. 测试系统应提供的功能

| 功能能力 | 系统责任 | 当前覆盖文件 | 冗余/命名问题 | 治理动作 |
| --- | --- | --- | --- | --- |
| retained artifact integrity | 校验 retained manifest、hash、authority guard、fix 行为，作为所有保留物链的基础约束。 | `test_retained_manifest_integrity.py` | 文件名已是功能名。 | 保留为基础能力，不并入 release/source 语义。 |
| source and provenance admission | 阻止未准入 source、未固定 payload、raw output 或伪 release evidence 进入候选/发布链。 | `test_source_admission_audit.py`、`test_source_evidence_governance.py`、`test_mechanism_source_evidence_closeout.py` | source admission audit 与 mechanism closeout 仍是独立治理锚点。 | 当前 source payload/output 与 source-rights request 合并完成。 |
| external evidence intake | 定义外部 signoff/reviewer packet 的 hash-only shape、template、fixture、admission preflight，确保默认 fail-closed。 | `test_external_signoff_intake_contracts.py`、`test_external_signoff_admission_preflight.py` | intake/template 与 admission preflight 职责不同。 | 当前命名语义化完成；不把 admission gate 混入 intake contract。 |
| benchmark evidence admission | 准入外部 benchmark output、selected case、recalculation、lineage/tolerance 和 execution evidence，保证 hash-only、fail-closed。 | `test_benchmark_evidence_admission.py`、`test_benchmark_recalculation_admission.py` | recalculation admission 仍可独立承接 BEC-O tolerance 细节。 | 当前 external/output 与 execution gate 合并完成。 |
| release authority guardrails | 防止任何 author-side retained pack、hard-gate pass、scoped identity 或 signoff 被误解为 release authority。 | `test_release_authority_guardrails.py` | 已从过程脚本合并为能力文件。 | 当前切片已完成；后续只做内部测试函数语义微调。 |
| independent review closeout | 验证 independent review、uncertainty、scope bucket、review closeout 只能关闭对应 review 面，不能授予 release。 | `test_independent_review_closeout_gates.py` | 已从四个 residual/stage 历史脚本合并为能力文件。 | 当前切片已完成。 |
| scope provenance closeout | 固定 target geometry、warhead family、geometry/warhead row provenance 的 scope closeout 边界。 | `test_scope_provenance_closeout_gates.py` | 已从 scope closeout 与 row provenance 历史脚本合并为能力文件。 | 当前切片已完成。 |
| candidate artifact contracts | 固定 candidate bundle、effect-scale artifact、retained artifact pack、runtime-aligned authority exercise 的 non-authoritative 边界。 | `test_candidate_artifact_contracts.py` | 已从 candidate/vps/stage/artifact 历史脚本合并为能力文件。 | 当前切片已完成，test-local authority exercise 断言保留。 |
| component probability validation | 固定 component probability artifacts、fragility validation、review readiness、benchmark gate。 | `test_component_probability_artifacts.py`、`test_component_fragility_validation.py` | 已去掉 `chain` 过程标题。 | 保持双文件，不继续压成巨型文件。 |

## 4. 当前脚本到功能的映射

| 当前脚本 | 功能能力 | 处理判断 |
| --- | --- | --- |
| `test_retained_manifest_integrity.py` | retained artifact integrity | 保留。 |
| `test_source_admission_audit.py` | source and provenance admission | 保留。 |
| `test_source_evidence_governance.py` | source and provenance admission | 已完成能力合并。 |
| `test_mechanism_source_evidence_closeout.py` | source and provenance admission | 保持为 mechanism/source closeout 锚点。 |
| `test_external_signoff_intake_contracts.py` | external evidence intake | 保留。 |
| `test_external_signoff_admission_preflight.py` | external evidence intake | 已完成语义重命名。 |
| `test_benchmark_evidence_admission.py` | benchmark evidence admission | 已完成能力合并。 |
| `test_benchmark_recalculation_admission.py` | benchmark evidence admission | 已完成语义重命名。 |
| `test_release_authority_guardrails.py` | release authority guardrails | 已完成能力合并。 |
| `test_independent_review_closeout_gates.py` | independent review closeout | 已完成能力合并。 |
| `test_scope_provenance_closeout_gates.py` | scope provenance closeout | 已完成能力合并。 |
| `test_candidate_artifact_contracts.py` | candidate artifact contracts | 已完成能力合并。 |
| `test_component_probability_artifacts.py` | component probability validation | 保留。 |
| `test_component_fragility_validation.py` | component probability validation | 保留。 |

## 5. 激进清理顺序

| 批次 | 功能目标 | 替代旧文件名数 | 目标结果 | 风险 |
| --- | --- | ---: | --- | --- |
| 已完成 | release authority guardrails | 5 | `test_release_authority_guardrails.py` 承接 release signoff、scoped identity、provenance identity、release readiness/closeout。 | 单文件较大，但功能边界清楚。 |
| 已完成 | independent review closeout | 4 | `test_independent_review_closeout_gates.py` 承接 review pass、RES-011/012 closeout、scope bucket review、uncertainty review。 | 不能把 review pass 写成 release pass。 |
| 已完成 | scope provenance closeout | 2 | `test_scope_provenance_closeout_gates.py` 承接 scope closeout 与 row provenance。 | 文档引用需同步。 |
| 已完成 | source evidence governance | 2 | `test_source_evidence_governance.py` 承接 source payload pack、source rights output policy、source-rights signoff request。 | 不把外部 signoff intake 混进 source payload policy。 |
| 已完成 | candidate artifact contracts | 4 | `test_candidate_artifact_contracts.py` 承接 candidate bundle、effect-scale artifacts、retained pack、runtime-aligned authority exercise。 | test-local authority exercise 不能被淡化。 |
| 已完成 | benchmark evidence admission | 2 | `test_benchmark_evidence_admission.py` 承接 TP-21 selected output/case/candidate packet 与 RES005/006 execution admission。 | BEC-O recalculation tolerance 保持独立能力文件。 |

## 6. 验收规则

每个清理批次必须同时满足：

- 旧测试函数断言已经搬入能力文件，不能直接删除行为覆盖。
- 文件名表达功能能力，不表达内部工程代号、任务编号或临时阶段。
- 文档引用只指向新能力文件；历史文档可以保留业务叙述，但不能保留失效测试路径。
- maintenance 工具名不因测试层重命名而变更。
- 验证命令至少包含：

```bash
source tools/maintenance/cmo_env.sh && cmo_python -m pytest -q <new-or-touched-test-file>
source tools/maintenance/cmo_env.sh && cmo_python -m pytest --collect-only -q tests/architecture
rg -n "<old-test-file-name>" docs tests
git diff --check -- docs tests
```

如修改 smoke suite manifest，再补跑：

```bash
source tools/maintenance/cmo_env.sh && cmo_python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
```
