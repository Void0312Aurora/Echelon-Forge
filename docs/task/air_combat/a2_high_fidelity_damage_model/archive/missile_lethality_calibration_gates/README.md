# MLF-10 Calibration Gates

Status: `2026-06-19` accepted / archived calibration-gate infrastructure;
calibration authority held. MLF-10 starts from the premise that the project
already has many calibrated or calibration-like engineering proxies, but it
does not treat them as released real-world authority until an explicit gate
admits them.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent A2 follow-on index: [../../README.md](../../README.md)
- MLF archive registry: [../../archive_registry.md](../../archive_registry.md)
- MLF-9 statistical trends:
  [../missile_lethality_pk_statistical_trends/README.md](../missile_lethality_pk_statistical_trends/README.md)
- MLF-6 structural failure:
  [../missile_lethality_structural_failure/README.md](../missile_lethality_structural_failure/README.md)
- MLF-8 debris/wreck lifecycle:
  [../missile_lethality_debris_wreck_lifecycle/README.md](../missile_lethality_debris_wreck_lifecycle/README.md)
- A2 retained calibration/residual register:
  [../../../archive/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md](../../../archive/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md)
- A2 task granularity and authority backlog:
  [../../../archive/a2_high_fidelity_damage_model/task_granularity_and_coordination_20260601.zh.md](../../../archive/a2_high_fidelity_damage_model/task_granularity_and_coordination_20260601.zh.md)
- Realism authority boundary:
  [../../../../../standards/foundation/realism_authority_boundary.zh.md](../../../../../standards/foundation/realism_authority_boundary.zh.md)

## Purpose

MLF-10 decides how the existing missile-lethality evidence may be read as
calibration evidence. It does not begin by changing damage parameters. It first
builds an admission gate that separates four different things:

1. engineering proxy tuning that is useful for simulation behavior;
2. research-retained evidence that is auditable but non-authoritative;
3. calibration candidates that have enough provenance, denominator, and
   uncertainty information to be reviewed;
4. released authority claims, which remain refused unless every required gate
   passes.

This matters because earlier A2/MLF work contains multiple calibrated-looking
values: near-field structural thresholds, cumulative wing-loss behavior,
component-failure probabilities, source-admission packets, sensitivity sweeps,
and MLF-9 trend reports. MLF-10 makes those facts reviewable without silently
turning them into real AIM-120C, F-16C, MQ-9, or Pk truth.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| MLF-1..MLF-9 chain evidence | accepted / archived | [archive registry](../../archive_registry.md) | Supplies replayable simulation facts, not released calibration authority |
| MLF-9 statistical trends | accepted / archived | [MLF-9 README](../missile_lethality_pk_statistical_trends/README.md) | Trends remain synthetic; no real Pk or weapon/target-specific lethality |
| A2 calibration residual register | retained / non-authoritative | [residual register](../../../archive/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md) | Some research blockers are closed, but authority blockers and fail-closed source gates remain |
| Source admission and rights packets | retained / mixed pass/fail-closed | retained artifacts under the A2 calibration package | Gate evidence exists; it does not automatically authorize selected outputs |
| Runtime model parameters | active engineering proxies | MLF-6/MLF-7/MLF-8 runtime and diagnostics evidence | MLF-10 must not change parameters before an admission contract exists |

## Scope

In scope:

- Inventory calibration-like evidence already present in A2, MLF-6 through
  MLF-9, proximity-fuze realism, and retained A2 calibration artifacts.
- Define a calibration-admission contract with provenance, source rights,
  denominator identity, uncertainty, independence, and authority flags.
- Build an audit/report surface that can classify evidence as rejected,
  retained-non-authoritative, calibration-candidate, or admitted.
- Keep real-world Pk, deterministic fuze reliability, and stock weapon/target
  truth fail-closed unless the gate explicitly admits them.
- Record which current model values are engineering proxies and which, if any,
  become calibration candidates.

Out of scope:

- No direct parameter retuning before the gate contract exists.
- No real AIM-120C Pk, F-16C/MQ-9 lethality, deterministic fuze, or stock
  weapon effectiveness claim.
- No reward authority, entity deletion authority, or direct crash rule.
- No reopening or editing archived MLF-1 through MLF-9 evidence packages except
  link-only maintenance.
- No source scraping or new public-data ingestion without source-rights and
  provenance review.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Open MLF-10 and freeze non-claims. | MLF-9 accepted / archived. | README, current status, dispatch queue, and task clusters exist. | complete |
| `P1 Calibration Inventory` | Map existing calibrated-looking values and retained source gates. | P0 docs exist. | Inventory separates engineering proxy, retained evidence, candidate, and authority blockers. | complete |
| `P2 Admission Contract` | Define source/provenance/uncertainty/denominator gate schema. | P1 inventory complete. | Contract can reject or admit evidence without runtime parameter changes. | complete |
| `P3 Audit Tooling` | Produce deterministic audit reports over retained evidence and MLF-9 trend artifacts. | P2 contract available. | Focused tests cover pass, fail-closed, and retained-non-authoritative cases. | complete |
| `P4 Report Integration` | Expose gate reports as retained diagnostics artifacts. | P3 tool exists. | Reports are consumable without implying stock authority. | complete |
| `P5 Validation` | Run focused validation and local link checks. | P4 reports available. | Validation records accepted/held boundaries and residuals. | complete |
| `P6 Closure` | Accept gate infrastructure or hold/re-scope calibration authority. | P5 evidence exists. | Parent indexes and archive registry are consistent with the decision. | complete |

## Task Clusters

- Task cluster plan:
  [missile_lethality_calibration_gates_task_clusters_20260619.md](missile_lethality_calibration_gates_task_clusters_20260619.md)
- Current status:
  [missile_lethality_calibration_gates_current_status_20260619.md](missile_lethality_calibration_gates_current_status_20260619.md)
- Dispatch queue:
  [missile_lethality_calibration_gates_dispatch_queue_20260619.md](missile_lethality_calibration_gates_dispatch_queue_20260619.md)
- Calibration-like evidence inventory:
  [missile_lethality_calibration_gates_inventory_20260619.md](missile_lethality_calibration_gates_inventory_20260619.md)
- Calibration admission contract:
  [missile_lethality_calibration_admission_contract_20260619.md](missile_lethality_calibration_admission_contract_20260619.md)
- Admission audit tooling:
  [missile_lethality_calibration_gates_audit_tooling_20260619.md](missile_lethality_calibration_gates_audit_tooling_20260619.md)
- Retained report integration:
  [missile_lethality_calibration_gates_report_integration_20260619.md](missile_lethality_calibration_gates_report_integration_20260619.md)
- Focused validation:
  [missile_lethality_calibration_gates_validation_20260619.md](missile_lethality_calibration_gates_validation_20260619.md)
- Acceptance record:
  [missile_lethality_calibration_gates_acceptance_20260619.md](missile_lethality_calibration_gates_acceptance_20260619.md)

## Outputs And Evidence

- MLF-10 planning surface and parent A2 archive-entry link.
- A finite task-cluster plan for calibration inventory, admission contract,
  audit tooling, report integration, validation, and closure.
- A current-status record that treats existing model tuning as audit input, not
  as already-released authority.
- A P1 inventory that classifies existing evidence without changing runtime
  behavior or admitting authority.

## Acceptance Gate

This subproject can be marked accepted only when:

- every admitted calibration claim cites a source, provenance path, denominator,
  uncertainty treatment, and authority flag;
- fail-closed source gates remain fail-closed unless a valid replacement packet
  is supplied and admitted;
- MLF-9 trend reports remain labeled as synthetic simulation trends unless a
  later gate explicitly promotes them;
- real-world Pk, weapon-specific lethality, target-specific lethality,
  deterministic fuze reliability, reward authority, and entity deletion remain
  refused unless separately admitted.

## Residuals And Next Steps

- Immediate work is complete for the current evidence set.
- Held: any actual runtime parameter retuning, selected public-output
  admission, or stock weapon/target calibration.

## Archive

MLF-10 has been physically archived under the parent A2 local archive and
registered in [../../archive_registry.md](../../archive_registry.md). The
original active path now contains only a lightweight compatibility pointer.
Future authority-promotion work should cite this accepted gate package or open
an explicitly scoped follow-on rather than extending the pointer path.
