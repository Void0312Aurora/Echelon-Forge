# 杀伤链解耦诊断工具与基线结果

日期：`2026-06-21`

状态：只读诊断工具 + baseline artifact。本文记录第二个实现切片：把五段解耦视图接到
AIM-120C 8 km / 30 度偏置场景和 blast-fragmentation 近炸距离 sweep。本文不改
runtime 参数，不改默认数据库，不声明真实 AIM-120C、F-16C、Pk、deterministic fuze
或校准权威。

## 新增工具

工具：

```bash
python tools/diagnostics/kill_chain_decoupling_probe.py --mode all --seed 20260621
```

输出：

- `guidance_cases`：默认包含 16 km / ±20 度、8 km / ±30 度 AIM-120C 偏置场景。
- `proximity_sweep`：默认包含 `0.5, 2, 4, 8, 10.96, 12, 15 m` local proximity 点。
- 每个 case 均包含：
  - `effect` 扁平指标；
  - `stage_abstractions` 五段视图；
  - `decoupling_summary` 耦合 flag 汇总。

CLI 已保证 stdout 是纯 JSON；runtime 原生日志转到 stderr，便于重定向成报告文件。

## 生成的报告

命令：

```bash
python tools/diagnostics/kill_chain_decoupling_probe.py \
  --mode all \
  --seed 20260621 \
  --output docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_decoupling_probe_20260621.json
```

报告：

`docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_decoupling_probe_20260621.json`

报告随 scalar ledger、P1 factor view、P1-b per-component view、P4 runtime named
load factors、P5 response-boundary view、P2/P5 runtime facade、P3 fuze-damage
policy fields、P6 calibration admission、supplemental contract surface 和 completion audit
刷新后为 `1186180`
bytes，包含
`4` 个 guidance case 和 `7` 个 proximity case。

## 8 km / 30 度结果

| case | nearest miss distance | fuze | effects | max component failure probability |
| --- | ---: | --- | --- | ---: |
| `aim120_8km_left_30deg` | `10.963446 m` | `fuze_armed` | `damage_applied` | `0.006350` |
| `aim120_8km_right_30deg` | `10.963479 m` | `fuze_armed` | `damage_applied` | `0.006356` |

解释：

- 制导/引信段不是空白：两侧都进入近炸并触发 effects。
- 五段视图显示该 case 的主要问题落在 `warhead_load_field -> component_response`
  之后：已有 component load，但 response 概率极低。
- 两侧镜像差很小，说明该复现点适合作为后续解耦/校准 baseline。

## 近炸 sweep 关键点

| distance | spatial effect scale | max component failure probability | 观测 |
| ---: | ---: | ---: | --- |
| `0.5 m` | `0.828454` | `0.894245` | 近场强响应 |
| `8.0 m` | `0.207965` | `0.014691` | 已明显掉到弱响应 |
| `10.96 m` | `0.060000` | `0.004159` | 与 8 km / 30 度场景同量级弱响应 |
| `12.0 m` | `0.000000` | `null` | 当前投影/载荷已无有效 component response |

这比前一份手工诊断更适合后续机器比较：同一工具能把每个点分解到 approach、fuze、
load、response、consequence 五段，并保留耦合 flag。

## P6 admission 摘要

刷新后的 report 顶层包含 `calibration_admission`：

- schema：`a2.kill_chain_calibration_admission.v1`。
- `admission_granted = true`。
- `admission_mode = engineering_proxy_single_layer_guarded`。
- `prerequisites.stage_report_available = true`。
- `prerequisites.runtime_dto_authority = true`。
- `prerequisites.component_response_rows_available = true`。
- `prerequisites.legacy_fuze_quality_damage_multiplier_removed = true`。
- `prerequisites.load_rows_response_owner_clean = true`。
- `prerequisites.external_calibration_evidence_present = true`。
- `external_evidence.report_schema_version = mlf10.calibration_admission_report.v1`。
- `external_evidence.admitted_record_count = 0`。
- `external_evidence.engineering_proxy_record_count = 2`。
- `external_evidence.engineering_proxy_layer_ids = [fuze_data, warhead_data,
  target_response_data, consequence_data]`。
- `external_evidence.missing_authority_fields = [component_failure_probability_authority,
  deterministic_fuze_authority, effect_scale_authority, pk_authority]`。
- `external_evidence.evidence_unblock_queue` 包含 `4` 条 blocked evidence closeout
  项，按 open item count 排序。
- 同目录新增轻量 preflight artifact
  `kill_chain_external_evidence_preflight_20260621.json`，schema 为
  `a2.kill_chain_calibration_evidence_preflight.v1`，大小 `18822` bytes。
- 同目录新增 external evidence template artifact
  `kill_chain_external_evidence_template_20260621.json`，schema 为
  `a2.kill_chain_calibration_evidence_template.v1`，大小 `14863` bytes；
  `warhead_data` 和 `target_response_data` 有 MLF-10 v1 manifest record 模板，
  `fuze_data` 与 `consequence_data` 已挂接 supplemental evidence contract 模板。
- 同目录新增 external evidence template check artifact
  `kill_chain_external_evidence_template_check_20260621.json`，schema 为
  `a2.kill_chain_calibration_evidence_template_check.v1`，大小 `3894` bytes；
  当前 template `ready_for_mlf10_audit=false`，blockers 为
  `placeholder_values_present` 和 `population_fields_invalid`。
- 同目录新增 external evidence supplemental contract artifact
  `kill_chain_external_evidence_supplemental_contract_20260621.json`，schema 为
  `a2.kill_chain_calibration_supplemental_evidence_contract.v1`，大小 `7249`
  bytes；覆盖 `deterministic_fuze_authority` 与 `pk_authority`。
- 同目录新增 external evidence supplemental contract check artifact
  `kill_chain_external_evidence_supplemental_contract_check_20260621.json`，
  schema 为 `a2.kill_chain_calibration_supplemental_evidence_contract_check.v1`，
  大小 `3357` bytes；当前 `ready_for_authority_admission=false`，blockers 为
  `placeholder_values_present` 和 `population_fields_invalid`。
- 同目录新增 current manifest readiness check artifact
  `kill_chain_current_manifest_readiness_check_20260621.json`，大小 `6599` bytes；
  当前 MLF-10 manifest 有 `4` 条 authority candidate records，`ready_record_count=0`，
  `blocked_record_count=4`。
- 同目录新增 completion audit artifact `kill_chain_completion_audit_20260621.json`，
  schema 为 `a2.kill_chain_completion_audit.v1`，大小 `4562` bytes；当前
  `closed_item_count=7/7`，`blocked_item_ids=[]`，`goal_complete=true`，
  `contract_surface_closed=true`。
- `single_layer_calibration_plan.plan_available = true`。
- `single_layer_calibration_plan.admitted_layer_count = 4`。
- `single_layer_calibration_plan.delta_guard_schema_version =
  a2.kill_chain_calibration_delta_guard.v1`。

当前 report 已能机器化说明“可以怎样进入 P6 工程代理校准”：前置观测链路和 P5
response owner 已闭合，MLF-10 retained report 中的 engineering proxy / retained
non-authoritative 记录打开了四个 layer 的 guarded dry-run plan。真实 authority 的
`admitted_record_count=0` 仍只表示不能声明真实 Pk、deterministic fuze 或真实弹种/目标
权威。每次 proxy 校准仍必须只改变一个 layer，并由 delta guard 检查 before/after
stage report 是否只改变目标层。delta guard
也可通过 `kill_chain_decoupling_probe.py --delta-guard-before ... --delta-guard-after ...
--delta-guard-layer ...` 直接运行。

## 自动暴露的耦合 flag

8 km / 30 度 case 中出现的主要 flag：

- `fuze_stage_contains_mechanism_coverage_score`
- `component_load_uses_composite_effect_scale`
- `component_load_named_factor_available`
- `component_response_row_runtime_owner`
- `consequence_trace_contains_vulnerability_effect_scale`

这些 flag 说明当前链路还没有真正解耦：引信层仍带机制覆盖信息，load row 仍承载
复合 `effect_scale`，同时 P4 named load factors 已可读；component response 已迁移到
response-owner rows，但 consequence trace 中仍可见 vulnerability/effect scale。它们是后续
consumer 迁移和 P6 证据门的机器可读入口。

## 验证

命令：

```bash
python -m pytest tests/tools/test_kill_chain_decoupling_probe.py -q
```

结果：`8 passed`。

同时手动 smoke：

```bash
python tools/diagnostics/kill_chain_decoupling_probe.py \
  --mode proximity \
  --proximity-distances-m 0.5,10.96 \
  --seed 20260621
```

确认 stdout 可被 `json.load(...)` 直接读取。

preflight smoke：

```bash
python tools/diagnostics/kill_chain_decoupling_probe.py \
  --external-evidence-preflight \
  --external-evidence-report docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_calibration_gates/mlf10_calibration_admission_report_20260619.json \
  --output docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_external_evidence_preflight_20260621.json
```

completion audit smoke：

```bash
python tools/diagnostics/kill_chain_decoupling_probe.py \
  --completion-audit-report docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_decoupling_probe_20260621.json \
  --output docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_completion_audit_20260621.json
```

supplemental contract smoke：

```bash
python tools/diagnostics/kill_chain_decoupling_probe.py \
  --external-evidence-supplemental-contract-check docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_external_evidence_supplemental_contract_20260621.json \
  --output docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_external_evidence_supplemental_contract_check_20260621.json
```

## 下一步

当前 baseline 已包含 P0/P1/P2/P3/P4/P5/P6 的机器可读证据。下一步不应直接重调杀伤
半径或概率曲线，而应：

1. 继续让下游消费者从复合 `effect_scale` 迁移到 runtime named load factors。
2. 按 `engineering_proxy_single_layer_guarded` 约束做单层 proxy 校准；真实 authority
   flag 继续保持 false。
3. `ComponentMechanismLoadRow` 的 response 字段已物理删除；后续只处理工程代理
   数据校准和消费者对 named load factors 的迁移。
