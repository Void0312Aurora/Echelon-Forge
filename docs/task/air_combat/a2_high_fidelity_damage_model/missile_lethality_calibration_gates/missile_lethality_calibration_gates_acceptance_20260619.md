# MLF-10 Acceptance Record

Status: `2026-06-19` accepted / retained gate infrastructure; calibration
authority held.

Chinese companion:
[missile_lethality_calibration_gates_acceptance_20260619.zh.md](missile_lethality_calibration_gates_acceptance_20260619.zh.md).

## Accepted

MLF-10 accepts the following infrastructure:

- a cited inventory of current calibration-like evidence;
- a versioned evidence-manifest, evidence-record, and audit-report contract;
- field-specific, fail-closed authority decisions;
- deterministic audit tooling and focused tests;
- a retained current-repository manifest and generated report;
- explicit separation of engineering proxy, retained evidence, blocked
  candidate, rejected source, and admitted evidence;
- validation showing deterministic report regeneration and compatibility with
  MLF-9 trend and A2 source-admission guardrails.

## Held

The following remain held:

- `effect_scale_authority` for current Stage B evidence;
- `component_failure_probability_authority` for current Stage C evidence;
- TP-21 selected debris output admission;
- BEC-O recalculated blast output admission;
- real-world Pk;
- deterministic fuze reliability;
- stock weapon/target lethality;
- reward authority;
- entity-deletion authority;
- runtime parameter retuning based on the current evidence.

## Evidence

- [Inventory](missile_lethality_calibration_gates_inventory_20260619.md)
- [Admission contract](missile_lethality_calibration_admission_contract_20260619.md)
- [Audit tooling](missile_lethality_calibration_gates_audit_tooling_20260619.md)
- [Report integration](missile_lethality_calibration_gates_report_integration_20260619.md)
- [Validation](missile_lethality_calibration_gates_validation_20260619.md)
- [Current retained report](mlf10_calibration_admission_report_20260619.json)

## Closure Decision

The gate infrastructure is accepted and retained at the live A2 follow-on root.
It is intentionally not physically archived because future authority-promotion
work should reuse the same contract, tool, and current-evidence manifest
surface.

The A2 archive registry remains a registry of physically archived evidence
packages. MLF-10 is therefore not added as an archived calibration result.

Reopening MLF-10 requires new evidence, a replacement signoff packet, or an
explicit authority-promotion request. A new report must be generated before any
authority decision changes.
