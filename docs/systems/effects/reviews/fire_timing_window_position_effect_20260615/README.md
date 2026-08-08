# Fire-Timing Window-Position Effect Review - 2026-06-15

Language: English canonical; [Chinese detailed record](README.zh.md).

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/systems/effects/reviews/fire_timing_window_position_effect_20260615/README.md`
Owner: `systems/effects/reviews`
Last verified: `2026-08-08`
Review basis: `2026-06-15` oracle legal-mask sweep and retained seed-variance artifacts.

## Scope And Independence

This review varies the legal firing-window position and inspects release
geometry, fuze/effects/damage events, component outcomes, and platform
consequences. It is a kill-chain readiness diagnosis, not a learned-policy or
reward evaluation.

## Findings

- Window position changes release geometry and the observed effects/damage
  labels.
- The small sample is non-monotonic and seed-sensitive; it does not establish a
  calibrated range-to-kill probability.
- Schema-v6 diagnostics expose component, system, and capability attribution,
  but some capability deltas still require threshold and ownership review.

Detailed evidence and limitations are in the [Chinese review record](README.zh.md).
Retained artifacts:

- [window-position sweep JSON](fire_timing_window_position_sweep_20260615.json)
- [seed-variance JSON](fire_timing_seed_variance_20260615.json)

## Verdict

Accepted as diagnostic evidence only. It grants no real-world lethality,
calibration, reward, or learned-policy authority.

## Follow-up Route

Any new calibration or learning claim must open a separate owner-local work
package and use explicit multi-seed acceptance criteria.
