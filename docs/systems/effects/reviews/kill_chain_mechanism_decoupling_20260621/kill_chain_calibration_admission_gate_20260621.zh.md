# P6 校准 admission 机器门切片

日期：`2026-06-21`

状态：P6 admission gate 已进入 `kill_chain_decoupling_probe.py` 顶层报告；当前
`admission_granted=true`，模式为 `engineering_proxy_single_layer_guarded`。本文允许
repository engineering proxy 范围内的单层校准计划，不声明真实 Pk、真实弹种/目标
权威或 deterministic fuze authority。

## 当前实现

新增 probe 顶层字段：

```text
calibration_admission
```

schema：

```text
a2.kill_chain_calibration_admission.v1
```

该字段把 P6 校准拆成四个互不混用的 layer admission：

- `fuze_data` -> `fuze_decision`
- `warhead_data` -> `warhead_load_field`
- `target_response_data` -> `component_response`
- `consequence_data` -> `consequence_projection`

每个 layer 都记录：

- `allowed_parameter_scope`
- `required_evidence`
- `single_layer_mutation_required`
- `stage_report_required`
- `blocked_by`

## 当前 admission 结果

刷新后的 review packet：

`docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_decoupling_probe_20260621.json`

关键事实：

- artifact size：`1186180` bytes。
- `calibration_admission.schema_version = a2.kill_chain_calibration_admission.v1`。
- `admission_granted = true`。
- `admission_mode = engineering_proxy_single_layer_guarded`。
- `prerequisites.stage_report_available = true`。
- `prerequisites.runtime_dto_authority = true`。
- scalar/probe evidence 已包含 `component_load_named_factor_available=63`。
- `prerequisites.component_response_rows_available = true`。
- `prerequisites.legacy_fuze_quality_damage_multiplier_removed = true`。
- `prerequisites.load_rows_response_owner_clean = true`。
- `prerequisites.external_calibration_evidence_present = true`。
- `external_evidence.source_ref =
  docs/task/air_combat/a2_high_fidelity_damage_model/archive/missile_lethality_calibration_gates/mlf10_calibration_admission_report_20260619.json`。
- `external_evidence.admitted_record_count = 0`。
- `external_evidence.engineering_proxy_record_count = 2`。
- `external_evidence.engineering_proxy_record_ids =
  [MLF10-CURRENT-MLF6-STRUCTURAL-PROXY, MLF10-CURRENT-MLF9-SYNTHETIC-TRENDS]`。
- `external_evidence.engineering_proxy_layer_ids =
  [fuze_data, warhead_data, target_response_data, consequence_data]`。
- `external_evidence.missing_authority_fields =
  [component_failure_probability_authority, deterministic_fuze_authority,
  effect_scale_authority, pk_authority]`。
- `external_evidence.blocked_by = []`。
- `external_evidence.real_world_authority_blocked_by =
  [no_admitted_external_calibration_evidence]`。
- `external_evidence.layer_gap_summary` 已按 layer 输出缺失 authority、相关 evidence id
  和 blocking reason counts；当前 `warhead_data` 缺 `effect_scale_authority`，相关
  evidence 为 `MLF10-CURRENT-BECO-RECALCULATED-BLAST` 与
  `MLF10-CURRENT-STAGE-B-EFFECT-SCALE`，但仍被 validation、rights、source gate、
  uncertainty residual 和 independent review blockers 挡住。
- `external_evidence.evidence_unblock_queue` 当前有 `4` 条记录，分别对应
  `MLF10-CURRENT-BECO-RECALCULATED-BLAST`、
  `MLF10-CURRENT-STAGE-B-EFFECT-SCALE`、
  `MLF10-CURRENT-STAGE-C-COMPONENT-PROBABILITY` 和
  `MLF10-CURRENT-TP21-SELECTED-DEBRIS`；每条记录列出 requested authority、
  target layer、blocking reasons、residuals 和 required closeout actions。
- `single_layer_calibration_plan.schema_version =
  a2.kill_chain_single_layer_calibration_plan.v1`。
- `single_layer_calibration_plan.delta_guard_schema_version =
  a2.kill_chain_calibration_delta_guard.v1`。
- `single_layer_calibration_plan.delta_guard_required = true`。
- `single_layer_calibration_plan.plan_available = true`。
- `single_layer_calibration_plan.dry_run_only = true`。
- `single_layer_calibration_plan.admitted_layer_count = 4`。
- `single_layer_calibration_plan.blocked_by = []`。

当前顶层 blockers：无。真实世界 authority 仍由
`real_world_authority_blocked_by=[no_admitted_external_calibration_evidence]` 单独记录。

轻量 external evidence preflight artifact：

`docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_external_evidence_preflight_20260621.json`

- schema：`a2.kill_chain_calibration_evidence_preflight.v1`。
- artifact size：`18822` bytes。
- `status = admitted_evidence_available`。
- `evidence_unblock_queue_count = 4`。
- `simulation_run_required_for_final_admission = true`。

external evidence template artifact：

`docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_external_evidence_template_20260621.json`

- schema：`a2.kill_chain_calibration_evidence_template.v1`。
- artifact size：`14863` bytes。
- `status = template_only_not_evidence`。
- MLF-10 v1 eligible authority fields：
  `[component_failure_probability_authority, effect_scale_authority]`。
- `deterministic_fuze_authority` 和 `pk_authority` 已挂接 supplemental evidence
  contract 模板。

external evidence template check artifact：

`docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_external_evidence_template_check_20260621.json`

- schema：`a2.kill_chain_calibration_evidence_template_check.v1`。
- artifact size：`3894` bytes。
- `ready_for_mlf10_audit = false`。
- `record_count = 2`，`blocked_record_count = 2`。
- `blocked_by = [placeholder_values_present, population_fields_invalid]`。

external evidence supplemental contract artifact：

`docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_external_evidence_supplemental_contract_20260621.json`

- schema：`a2.kill_chain_calibration_supplemental_evidence_contract.v1`。
- artifact size：`7249` bytes。
- `status = template_only_not_evidence`。
- `contract_record_count = 2`。
- 覆盖 `deterministic_fuze_authority` 与 `pk_authority` 两个 MLF-10 v1 外的
  authority 字段。

external evidence supplemental contract check artifact：

`docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_external_evidence_supplemental_contract_check_20260621.json`

- schema：`a2.kill_chain_calibration_supplemental_evidence_contract_check.v1`。
- artifact size：`3357` bytes。
- `ready_for_authority_admission = false`。
- `record_count = 2`，`blocked_record_count = 2`。
- `blocked_by = [placeholder_values_present, population_fields_invalid]`。

current manifest readiness check artifact：

`docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_current_manifest_readiness_check_20260621.json`

- schema：`a2.kill_chain_calibration_evidence_template_check.v1`。
- artifact size：`6599` bytes。
- `record_count = 7`，`authority_candidate_record_count = 4`。
- `ready_record_count = 0`，`blocked_record_count = 4`。
- 非 authority-requested records 只保留 warning，不计入 P6 authority readiness
  blockers。

当前 layer 缺口摘要：

| layer | missing authority | related blocked evidence |
| --- | --- | --- |
| `fuze_data` | `deterministic_fuze_authority` | 无 admitted/blocked record |
| `warhead_data` | `effect_scale_authority` | `MLF10-CURRENT-BECO-RECALCULATED-BLAST`, `MLF10-CURRENT-STAGE-B-EFFECT-SCALE` |
| `target_response_data` | `component_failure_probability_authority` | `MLF10-CURRENT-STAGE-C-COMPONENT-PROBABILITY`, `MLF10-CURRENT-TP21-SELECTED-DEBRIS` |
| `consequence_data` | `pk_authority` | 无 admitted/blocked record |

## 防跨层泄漏条件

admission gate 要求后续每次校准：

1. 只改变一个 layer 的参数。
2. 必须带 before/after stage report。
3. 若非目标 layer 的 stage delta 改变，则该次 admission 失败。
4. 不授予 `runtime_parameter_retuning`、`real_world_pk`、
   `deterministic_fuze_authority` 或 `calibration_authority`。

当前 probe 还输出 `single_layer_calibration_plan`。该字段不是调参执行器，而是 P6
dry-run 合同：某个 layer 拿到 admitted authority field，或由当前 repository
engineering-proxy evidence 以 `admission_source=engineering_proxy` 受控准入后，会为
该 layer 生成单层计划，并列出 `frozen_stage_ids` / `reject_if_changed_stage_ids`。计划还绑定
`a2.kill_chain_calibration_delta_guard.v1`；后续 before/after report 必须通过 delta
guard，即目标 stage 有变化、冻结 stage 无变化。当前真实 authority 的 admitted
record 仍为零，但 engineering-proxy evidence 已生成四个 dry-run plans；这些计划的
`admitted_authority_fields=[]`，且不允许默认数据库修改或 runtime parameter retuning。

delta guard 可通过 CLI 直接运行，不需要重新跑仿真：

```bash
./.venv/bin/python tools/diagnostics/kill_chain_decoupling_probe.py \
  --delta-guard-before before_report.json \
  --delta-guard-after after_report.json \
  --delta-guard-layer warhead_data \
  --output delta_guard.json
```

输出为 `a2.kill_chain_calibration_delta_guard.v1`。`guard_passed=true` 只表示 before/after
report 满足单层变化约束，不授予真实 Pk、deterministic fuze 或 runtime retuning 权威。

external evidence preflight 也可通过 CLI 直接运行，不需要重新跑仿真：

```bash
./.venv/bin/python tools/diagnostics/kill_chain_decoupling_probe.py \
  --external-evidence-preflight \
  --external-evidence-report docs/task/air_combat/a2_high_fidelity_damage_model/archive/missile_lethality_calibration_gates/mlf10_calibration_admission_report_20260619.json \
  --output docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_external_evidence_preflight_20260621.json
```

输出为 `a2.kill_chain_calibration_evidence_preflight.v1`。它只做校准输入预检、
engineering-proxy admission 展开和 closeout queue 展开；最终 proxy calibration 仍需要
完整 kill-chain report 和 delta guard。

external evidence template 可通过 CLI 生成，不需要重新跑仿真：

```bash
./.venv/bin/python tools/diagnostics/kill_chain_decoupling_probe.py \
  --external-evidence-template \
  --output docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_external_evidence_template_20260621.json
```

输出为 `a2.kill_chain_calibration_evidence_template.v1`。该文件只是后续外部证据的
输入模板，不是 admitted evidence，也不会改变 admission gate。

external evidence template check 也可通过 CLI 运行：

```bash
./.venv/bin/python tools/diagnostics/kill_chain_decoupling_probe.py \
  --external-evidence-template-check docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_external_evidence_template_20260621.json \
  --output docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_external_evidence_template_check_20260621.json
```

输出为 `a2.kill_chain_calibration_evidence_template_check.v1`。它只检查模板或
manifest draft 是否可进入 MLF-10 audit，不授予 evidence authority。

supplemental evidence contract 可通过 CLI 生成：

```bash
./.venv/bin/python tools/diagnostics/kill_chain_decoupling_probe.py \
  --external-evidence-supplemental-contract \
  --output docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_external_evidence_supplemental_contract_20260621.json
```

输出为 `a2.kill_chain_calibration_supplemental_evidence_contract.v1`。它覆盖
`deterministic_fuze_authority` 与 `pk_authority`，并要求对应 layer 的 before/after
stage report 继续受 delta guard 约束。

supplemental evidence contract check 可通过 CLI 运行：

```bash
./.venv/bin/python tools/diagnostics/kill_chain_decoupling_probe.py \
  --external-evidence-supplemental-contract-check docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_external_evidence_supplemental_contract_20260621.json \
  --output docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_external_evidence_supplemental_contract_check_20260621.json
```

输出为 `a2.kill_chain_calibration_supplemental_evidence_contract_check.v1`。它只检查
非 MLF-10 v1 authority contract 是否具备 admission-ready 形状，不授予 evidence
authority。

当前 retained MLF-10 manifest readiness check：

```bash
./.venv/bin/python tools/diagnostics/kill_chain_decoupling_probe.py \
  --external-evidence-template-check docs/task/air_combat/a2_high_fidelity_damage_model/archive/missile_lethality_calibration_gates/mlf10_calibration_evidence_manifest_20260619.json \
  --output docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_current_manifest_readiness_check_20260621.json
```

## 验收含义

本切片完成的是 P6 的工程代理 admission、dry-run plan surface、before/after delta
guard 和 supplemental contract/check。它把“现在可以按什么边界校准”和“真实权威仍
不能声明什么”变成可测试输出：

- P3 已删除旧引信质量伤害倍率入口。
- P2/P4/P5 的 runtime DTO、component-load named factors 和 event-level response owner rows 已满足。
- P5 load-row response owner 已清理：load row response 字段已从 ABI 删除，probe 中
  `rows_with_response_fields_on_load_row = 0`。
- MLF-10 retained admission report 中真实 authority 的 `admitted_record_count=0`；
  这只阻止真实 Pk / deterministic fuze / stock weapon-target authority 声明，不阻止
  repository engineering proxy 范围内的校准。
- `engineering_proxy_record_count=2` 已打开四个 layer 的 guarded dry-run plan；
  每次仍必须只改变一个 layer，并提供 before/after stage report 证明没有跨层泄漏。
- 非 MLF-10 v1 的 `deterministic_fuze_authority` / `pk_authority` 仍有
  contract/check artifact，但这是为了记录真实权威边界，不是工程代理校准的阻塞条件。

## 验证

```bash
./.venv/bin/python -m pytest -q tests/tools/test_kill_chain_decoupling_probe.py
```

结果：`8 passed`。
