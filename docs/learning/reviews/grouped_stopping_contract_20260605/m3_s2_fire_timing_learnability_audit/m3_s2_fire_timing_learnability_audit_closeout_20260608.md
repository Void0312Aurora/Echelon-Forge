# M3-S2 Fire-Timing Learnability Audit Closeout 2026-06-08

Status: `archived as bounded firing gate accepted; robustness and timing research held`.

## Decision

Archive the M3-S2 fire-timing learnability audit as a sealed evidence package.

The release-gate question that drove the latest work is closed for the active
Stage-1 C2/ROE scenario/config pair:

- deterministic and stochastic learned-policy probes request `fire_once`;
- A5 accepts the request;
- exactly one authorized missile release is executed;
- rejected requests, violation releases, and repeat-before-assessment releases
  are all zero in the bounded batch validation.

This is not a claim that the broader fire-timing research is finished. It is a
bounded release-gate acceptance so training can continue without treating "the
model cannot fire" as the first suspected blocker.

## Retained Evidence

- Focused A5 fix evidence:
  [m3_s2_fire_closure_validation_20260608.md](m3_s2_fire_closure_validation_20260608.md)
- Batch firing-gate evidence:
  [m3_s2_fire_closure_batch_validation_20260608.md](m3_s2_fire_closure_batch_validation_20260608.md)
- Current status and historical diagnosis:
  [m3_s2_fire_timing_learnability_audit_current_status_20260605.md](m3_s2_fire_timing_learnability_audit_current_status_20260605.md)

## Held Residuals

- Timing quality is not accepted. The batch validates legal release execution,
  not whether the first-release step is tactically or statistically optimal.
- Cross-config robustness is not proven. The accepted gate is scoped to the
  active Stage-1 C2/ROE scenario/config pair and seeds recorded in the batch
  validation.
- Effects, damage, and kill-chain behavior are not accepted by this package.
  They remain separate A8/model evidence.
- Further research may still revisit event-logit calibration, support
  distribution, timing-quality labels, and sequence-memory/modeling, but that
  should start as a follow-on task rather than keeping this evidence packet live.

## Archive Action

Move this package under `docs/learning/reviews/grouped_stopping_contract_20260605/` and leave the original
`docs/learning/reviews/grouped_stopping_contract_20260605/m3_s2_fire_timing_learnability_audit/` path as a pointer README.
