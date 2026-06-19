# MLF-10 Calibration-Like Evidence Inventory

Status: `2026-06-19` P1 complete. This inventory classifies the evidence already
present in A2 and MLF-6 through MLF-9. It does not admit new sources, change
runtime parameters, or release any authority.

Chinese companion:
[missile_lethality_calibration_gates_inventory_20260619.zh.md](missile_lethality_calibration_gates_inventory_20260619.zh.md).

## Classification Rules

| Classification | Meaning in MLF-10 |
| --- | --- |
| `engineering_proxy` | A maintained simulation value or mechanism with tests, but without a released real-world calibration claim. |
| `retained_non_authoritative` | Auditable evidence retained for review, replay, or method development that cannot drive a released calibration claim. |
| `calibration_candidate` | A scoped package with enough provenance, population identity, uncertainty, and authority metadata to enter contract review, but not to pass it automatically. |
| `admitted` | Evidence that has passed the MLF-10 admission contract for an explicit authority field and scope. |
| `rejected` | Evidence or a claim that is not eligible for consumption because its provenance, rights, stability, or scope is unacceptable. |
| `blocked` | Potentially relevant evidence whose required gate is fail-closed or incomplete. |

These labels describe current MLF-10 handling. They do not rewrite the status
of the archived source packages.

## Evidence Inventory

| ID | Evidence family | Stable evidence | Classification | Population / denominator reading | Authority and residual reading |
| --- | --- | --- | --- | --- | --- |
| `INV-001` | MLF-6 near-field structural thresholds and cumulative wing-loss behavior | [MLF-6 README](../archive/missile_lethality_structural_failure/README.md) | `engineering_proxy` | Controlled runtime probes and regression cases; not a real weapon/target trial population | Useful for relative simulation behavior. No AIM-120C/F-16C structural-kill or Pk authority. |
| `INV-002` | MLF-7 platform consequence projection | [MLF-7 README](../archive/missile_lethality_secondary_consequence_coupling/README.md) | `retained_non_authoritative` | Consequence rows conditioned on accepted simulation breakup facts | Supports chain-outcome labels only. No target-specific mission-kill or crash authority. |
| `INV-003` | MLF-8 detached-part and terminal-wreck lifecycle facts | [MLF-8 README](../archive/missile_lethality_debris_wreck_lifecycle/README.md) | `retained_non_authoritative` | Diagnostics-only lifecycle rows over simulated chains | No calibrated debris throw, debris damage probability, reward, or entity-deletion authority. |
| `INV-004` | Proximity-fuze detection, trigger, reliability, and mechanism-coverage surrogate | [proximity-fuze realism README](../archive/missile_lethality_proximity_fuze_realism/README.md) | `engineering_proxy` | Focused surrogate matrix and live-guidance probes, not live-fuze trials | Mechanism shape is reviewable. Real thresholds, reliability, deterministic fuze truth, and Pk remain refused. |
| `INV-005` | MLF-9 trend reports and Wilson-style intervals | [MLF-9 metric contract](../archive/missile_lethality_pk_statistical_trends/missile_lethality_pk_statistical_trends_metric_contract_20260619.md) and [validation](../archive/missile_lethality_pk_statistical_trends/missile_lethality_pk_statistical_trends_validation_20260619.md) | `retained_non_authoritative` | Explicit `(episode, chain_id)` simulation populations with named denominators and interval method | Suitable as an audit-tool input. Synthetic source population prevents real-world calibration or Pk promotion. |
| `INV-006` | A2 scoped blast-fragmentation surrogate candidate package | [candidate package README](../../archive/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/README.zh.md) | `calibration_candidate` | Fixed scope: F-16C Block 50, AIM-120C-class blast-fragmentation, beam/high, near-miss 0-0.35 m; author-side benchmark populations | Reviewable research candidate only. All stock authority flags remain false. |
| `INV-007` | Stage B effect-scale snapshot, retained pack, criteria, scope, uncertainty, and review-readiness evidence | [Stage B review-readiness record](../../archive/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/validation_review_readiness_record_stage_b_effect_scale_20260530.zh.md) and [uncertainty gate](../../archive/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/validation_uncertainty_review_gate_20260531.zh.md) | `calibration_candidate` | Fixed-seed author-side benchmark cases and seed-window summaries; not operational trials | Candidate shape is sufficient for P2 contract design. Independent review, release-grade source/identity, and mechanism residuals still prevent admission. |
| `INV-008` | Stage C component-specific failure-probability surface | [Stage C review-readiness gate](../../archive/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/validation_review_readiness_gate_stage_c_component_probability_20260530.zh.md) | `blocked` | Test-local, component-specific candidate rows and fixed-seed repeatability | Blocked by independent fragility truth, uncertainty coverage, geometry/mechanism provenance, independence, and upstream Stage B release state. |
| `INV-009` | Narrow internal source-signoff and scoped surrogate-identity records (`RES-001/002`) | [residual register](../../archive/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md) | `retained_non_authoritative` | Package identity and retained payload accounting, not a lethality population | Supports traceability. It does not establish external release rights, global release identity, or calibration authority. |
| `INV-010` | TP-21 selected debris comparison outputs (`RES-005`) | [residual register](../../archive/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md) | `blocked` | Required reviewer-selected cases and selected-output preimages are incomplete | Fail-closed until locator, hashes, independent review, allowed-output signoff, and authority-boundary signoff pass. |
| `INV-011` | BEC-O recalculated selected blast outputs (`RES-006`) | [residual register](../../archive/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md) | `blocked` | Nine recalculated candidate outputs exist, but 9/9 hashes differ from cached anchors | Fail-closed pending lineage review, allowed-output signoff, tolerance policy, and replacement-anchor signoff. |
| `INV-012` | Real-world Pk claim (`RES-013`) | [residual register](../../archive/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md) | `blocked` | No independent real-world kill-chain denominator or evidence chain | MLF-9 simulation denominators cannot close this boundary. |
| `INV-013` | Deterministic fuze reliability claim (`RES-014`) | [residual register](../../archive/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md) | `blocked` | No admitted live fuze, target-signature, reliability, and miss-distance joint population | Proximity-fuze surrogate behavior cannot close this boundary. |
| `INV-014` | Restricted, leaked, unstable, untraceable, rights-unclear, or scope-mismatched source material | [public-data source admission standard](../../../../standards/foundation/public_data_source_admission.md) | `rejected` | No eligible denominator because the source cannot enter the evidence chain | Must not enter a descriptor row, generated benchmark, parameter tuning, or runtime authority path. |
| `INV-015` | Released MLF-10 calibration evidence | This inventory | `admitted` | None | No evidence is admitted at P1. Admission requires the P2 contract and a later explicit gate decision. |

## Gate-Field Coverage

| Evidence family | Source / provenance | Rights | Scope | Denominator | Uncertainty | Independence | Explicit authority state |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MLF-6 / MLF-7 / MLF-8 runtime evidence | Repository code, tests, and archived records | Repository-local | Explicit simulation scope | Controlled cases or chain rows | Limited to test/probe variation | Regression evidence, not external validation | Non-authoritative by task boundary |
| Proximity-fuze surrogate | Public mechanism references plus repository implementation evidence | Method references only | Bounded surrogate scope | Focused matrix / live probe cases | Residuals recorded | No live-fuze independent validation | Deterministic-fuze and Pk authority false |
| MLF-9 trends | Explicit replay rows and report schema | Repository-local inputs | Named synthetic scenario / fixture population | Named counts and filters | Explicit interval method and sample count | Fixture/seed provenance declared | Real-world Pk authority false |
| A2 Stage B candidate | Source ledger, pinned artifacts, manifests, hashes, and review records | Mixed retained / fail-closed | Narrow target/weapon/aspect/closure/miss-distance scope | Fixed-seed benchmark cases | Author-side seed-window review | Partial; release-grade independent review incomplete | Candidate, all stock flags false |
| A2 Stage C candidate | Retained component row chain | Inherits unresolved source gates | Single component within narrow candidate scope | Test-local component rows | Repeatability only; coverage incomplete | Independent fragility truth absent | Blocked |
| TP-21 / BEC-O selected outputs | Retained gate records | Allowed-output signoff incomplete | Narrow mechanism evidence | Selected cases incomplete or replacement-disputed | Tolerance/signoff incomplete | Independent review incomplete | Fail-closed |

## P2 Contract Inputs

The admission contract must require, at minimum:

1. stable evidence and source identifiers;
2. provenance and rights/redistribution state;
3. exact weapon, target, mechanism, geometry, aspect, closure, and miss-distance
   scope;
4. population identity, denominator name, count, filters, and independence
   assumptions;
5. uncertainty method, coverage, and residuals;
6. independent-review status;
7. field-specific authority requests and decisions;
8. explicit non-claims for Pk, deterministic fuze, reward, entity deletion, and
   out-of-scope weapon/target truth.

The contract must default to `blocked` or `retained_non_authoritative` when any
required field is missing. It must not infer admission from a passing test,
benchmark snapshot, retained artifact pack, or author-side review alone.

## P1 Decision

`MLF10-P1` is complete:

- current evidence families are classified;
- no current evidence is admitted;
- Stage B is the only evidence family ready to exercise a candidate contract;
- Stage C, TP-21, BEC-O, Pk, and deterministic fuze remain blocked;
- runtime parameters remain unchanged.

The next serial packet is `MLF10-P2`, which defines the admission contract and
report schema from this inventory.
