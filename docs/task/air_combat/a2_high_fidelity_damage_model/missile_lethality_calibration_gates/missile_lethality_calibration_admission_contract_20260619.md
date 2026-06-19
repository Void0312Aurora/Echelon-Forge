# MLF-10 Calibration Admission Contract

Status: `2026-06-19` P2 complete. This contract defines the v1 evidence record,
field-specific authority decision, and retained audit-report schema for MLF-10.
It does not change runtime parameters or admit any current repository evidence.

Chinese companion:
[missile_lethality_calibration_admission_contract_20260619.zh.md](missile_lethality_calibration_admission_contract_20260619.zh.md).

## Contract Versions

| Surface | Schema version |
| --- | --- |
| Evidence manifest | `mlf10.calibration_evidence_manifest.v1` |
| Evidence record | `mlf10.calibration_evidence.v1` |
| Audit report | `mlf10.calibration_admission_report.v1` |

## Evidence Record

Each record must contain:

| Field | Requirement |
| --- | --- |
| `evidence_id` | Stable identifier unique within the manifest. |
| `evidence_class` | One of `engineering_proxy`, `retained_non_authoritative`, `calibration_candidate`, `admitted`, `rejected`, or `blocked`. Input `admitted` is never trusted without re-evaluation. |
| `source_kind` | Source category. Authority-eligible v1 kinds are `external_calibration_dataset` and `validated_physics_surrogate`. |
| `source_ref` | Stable URL, report/catalog identifier, repository artifact path, or manifest reference. |
| `provenance` | Non-empty acquisition, generation, retention, and transformation summary. |
| `rights_status` | Explicit rights/redistribution state. Authority requires `release_grade_admitted`. |
| `source_gate_status` | `passed`, `blocked`, `fail_closed`, `pending`, or `rejected`. |
| `validation_status` | `passed`, `candidate`, `not_run`, `blocked`, or `rejected`. |
| `scope` | Exact target, weapon, mechanism, aspect, closure, and miss-distance axes. |
| `population` | Population identity, denominator name, sample count, filters, and independence assumption. |
| `uncertainty` | Method, coverage statement, and residual list. |
| `independent_review` | Status and stable reviewer/signoff reference. |
| `authority_requests` | Boolean requests for each authority field. Omitted fields default to false. |
| `non_claims` | Explicitly refused claims carried by the evidence. |
| `residuals` | Remaining evidence, scope, rights, validation, or authority blockers. |

## Required Scope

An authority request must name all six axes:

- `target_type`
- `weapon_family`
- `mechanism_family`
- `aspect_bucket`
- `closure_bucket`
- `miss_distance_bucket`

Empty, wildcard, global, all-platform, or all-weapon scope does not pass v1.

## Population And Uncertainty

Authority review requires:

- a non-empty population identity;
- a named denominator;
- `sample_count > 0`;
- explicit filters;
- an independence assumption;
- a named uncertainty method;
- a coverage statement;
- no blocking uncertainty residual.

A passing regression, fixed-seed snapshot, retained pack, or deterministic
simulation report is not an operational calibration population by itself.

## Authority Matrix

| Authority field | MLF-10 v1 handling |
| --- | --- |
| `effect_scale_authority` | Eligible only for an admitted external calibration dataset or validated physics surrogate after every gate passes. |
| `component_failure_probability_authority` | Eligible under the same gates, with component/fragility scope represented in provenance and residual review. |
| `pk_authority` | Always blocked in v1. Requires a separate real-world kill-chain evidence contract. |
| `deterministic_fuze_authority` | Always blocked in v1. Requires admitted live fuze, signature, reliability, and joint miss-distance evidence. |
| `reward_authority` | Always blocked. Calibration evidence cannot define reward authority. |
| `entity_deletion_authority` | Always blocked. Calibration evidence cannot define entity lifecycle deletion. |

Authority is granted per field. Passing one field never promotes another field.

## Decision Order

The audit applies this order:

1. `rejected`: source kind, rights, or source gate explicitly rejects the
   evidence.
2. `blocked`: an authority request exists but any required field or gate is
   missing, pending, blocked, or fail-closed; v1-forbidden authority requests
   are also blocked.
3. `admitted`: every requested authority is v1-eligible and every gate passes.
4. `engineering_proxy`: no authority is requested and the record is explicitly
   an engineering proxy.
5. `calibration_candidate`: no authority is granted, but the record has a
   reviewable candidate shape and no explicit rejection.
6. `retained_non_authoritative`: evidence is useful for audit or method
   development but is not an authority candidate.

The output must never trust an input `admitted` label without recalculating the
decision.

## Mandatory Non-Claims

Every manifest must preserve these non-claims unless a later, separate contract
explicitly replaces one:

- `real_world_pk`
- `deterministic_fuze_reliability`
- `reward_authority`
- `entity_deletion_authority`
- `out_of_scope_weapon_truth`
- `out_of_scope_target_truth`

## Audit Report

The report contains:

- manifest and report schema versions;
- source manifest reference;
- deterministic record ordering;
- one decision per evidence record;
- decision counts;
- admitted authority fields and scopes, if any;
- blocking reasons and residuals;
- report-surface identity;
- top-level non-claims and current authority boundary.

The current repository report must show zero admitted records unless a later
review supplies complete release-grade evidence. A positive test fixture may
exercise the admitted branch without changing repository authority.

## P3 Implementation Gate

P3 may proceed because:

- required fields and decision precedence are explicit;
- authority eligibility is field-specific;
- fail-closed behavior is defined;
- current evidence does not need runtime parameter changes;
- test fixtures can cover admitted, retained, candidate, rejected, and blocked
  decisions.
