# MLF-10 校准准入契约

状态：`2026-06-19` P2 complete。本契约定义 MLF-10 v1 evidence record、
逐字段 authority decision 和 retained audit-report schema。它不修改 runtime 参数，
也不接纳当前仓库中的任何证据。

英文主文：
[missile_lethality_calibration_admission_contract_20260619.md](missile_lethality_calibration_admission_contract_20260619.md)。

## 契约版本

| Surface | Schema version |
| --- | --- |
| Evidence manifest | `mlf10.calibration_evidence_manifest.v1` |
| Evidence record | `mlf10.calibration_evidence.v1` |
| Audit report | `mlf10.calibration_admission_report.v1` |

## Evidence Record

每条 record 必须包含：

| Field | Requirement |
| --- | --- |
| `evidence_id` | Manifest 内唯一的稳定标识。 |
| `evidence_class` | `engineering_proxy`、`retained_non_authoritative`、`calibration_candidate`、`admitted`、`rejected` 或 `blocked`。输入中的 `admitted` 必须重新计算，不能直接信任。 |
| `source_kind` | 来源类别。v1 可申请 authority 的类别只有 `external_calibration_dataset` 和 `validated_physics_surrogate`。 |
| `source_ref` | 稳定 URL、报告/目录标识、仓库 artifact 路径或 manifest 引用。 |
| `provenance` | 非空的获取、生成、保留和转换摘要。 |
| `rights_status` | 显式权利/再分发状态。Authority 要求 `release_grade_admitted`。 |
| `source_gate_status` | `passed`、`blocked`、`fail_closed`、`pending` 或 `rejected`。 |
| `validation_status` | `passed`、`candidate`、`not_run`、`blocked` 或 `rejected`。 |
| `scope` | 精确 target、weapon、mechanism、aspect、closure 和 miss-distance 轴。 |
| `population` | Population identity、denominator name、sample count、filters 和 independence assumption。 |
| `uncertainty` | Method、coverage statement 和 residual list。 |
| `independent_review` | Status 和稳定 reviewer/signoff reference。 |
| `authority_requests` | 每个 authority 字段的布尔申请；缺失字段默认为 false。 |
| `non_claims` | 该证据显式拒绝的声明。 |
| `residuals` | 仍存在的 evidence、scope、rights、validation 或 authority blocker。 |

## 必需 Scope

Authority request 必须命名以下六个轴：

- `target_type`
- `weapon_family`
- `mechanism_family`
- `aspect_bucket`
- `closure_bucket`
- `miss_distance_bucket`

空值、wildcard、global、all-platform 或 all-weapon scope 均不能通过 v1。

## Population 与 Uncertainty

Authority review 要求：

- 非空 population identity；
- 命名 denominator；
- `sample_count > 0`；
- 显式 filters；
- independence assumption；
- 命名 uncertainty method；
- coverage statement；
- 没有 blocking uncertainty residual。

Passing regression、fixed-seed snapshot、retained pack 或 deterministic simulation
report 本身都不是 operational calibration population。

## Authority Matrix

| Authority field | MLF-10 v1 handling |
| --- | --- |
| `effect_scale_authority` | 只有 admitted external calibration dataset 或 validated physics surrogate 在全部 gate 通过后才可放行。 |
| `component_failure_probability_authority` | 适用同一 gate，同时 provenance 和 residual review 必须表示 component/fragility scope。 |
| `pk_authority` | v1 固定 blocked；需要独立 real-world kill-chain evidence contract。 |
| `deterministic_fuze_authority` | v1 固定 blocked；需要 admitted live fuze、signature、reliability 和 joint miss-distance evidence。 |
| `reward_authority` | 固定 blocked；calibration evidence 不能定义 reward authority。 |
| `entity_deletion_authority` | 固定 blocked；calibration evidence 不能定义 entity lifecycle deletion。 |

Authority 逐字段授予。一个字段通过不能提升其他字段。

## 判定顺序

Audit 按以下顺序执行：

1. `rejected`：source kind、rights 或 source gate 显式拒绝证据。
2. `blocked`：存在 authority request，但任一必填字段或 gate 缺失、pending、
   blocked 或 fail-closed；v1 禁止的 authority request 也属于 blocked。
3. `admitted`：所有 requested authority 都属于 v1 eligible，且全部 gate 通过。
4. `engineering_proxy`：未申请 authority，且 record 明确是 engineering proxy。
5. `calibration_candidate`：没有 authority 被授予，但 record 具备可审阅 candidate
   shape，且没有显式 rejection。
6. `retained_non_authoritative`：证据可用于 audit 或方法开发，但不是 authority candidate。

输出不得直接信任输入中的 `admitted`，必须重新计算。

## Mandatory Non-Claims

每个 manifest 都必须保留下列 non-claims，除非后续独立 contract 明确替换其中某项：

- `real_world_pk`
- `deterministic_fuze_reliability`
- `reward_authority`
- `entity_deletion_authority`
- `out_of_scope_weapon_truth`
- `out_of_scope_target_truth`

## Audit Report

报告包含：

- manifest 和 report schema versions；
- source manifest reference；
- 确定性 record ordering；
- 每条 evidence record 的 decision；
- decision counts；
- 如有则列出 admitted authority fields 和 scopes；
- blocking reasons 和 residuals；
- report-surface identity；
- 顶层 non-claims 和当前 authority boundary。

当前仓库报告必须显示零 admitted records，除非后续 review 提供完整 release-grade
evidence。正向测试 fixture 可以演练 admitted branch，但不改变仓库 authority。

## P3 实现门

P3 可以开始，因为：

- 必填字段和判定优先级明确；
- authority eligibility 是逐字段的；
- fail-closed 行为已定义；
- 当前证据不需要修改 runtime 参数；
- 测试 fixture 可以覆盖 admitted、retained、candidate、rejected 和 blocked decisions。
