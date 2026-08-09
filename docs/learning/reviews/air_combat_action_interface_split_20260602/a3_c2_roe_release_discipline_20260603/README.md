# A3 C2/ROE Release Discipline

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/learning/reviews/air_combat_action_interface_split_20260602/a3_c2_roe_release_discipline_20260603/README.md`
Owner: `learning/policy-architecture`
Last verified: `2026-08-09`
Review basis: retained C2/ROE release-discipline probes and action-interface review.

Status: retained evidence package. The bounded C2/ROE implementation and P4
probes classify release legality; learned-policy quality and M2 memory remain
held. This package is not an active training authorization.

Inputs:

- [Action-interface review](../README.md)
- [Learning owner](../../../README.md)
- [Air action contract](../../../../domains/air/standards/pilot_action_contract.md)

Evidence:

- [P4 probe](a3_c2_roe_p4_probe_evidence_20260603.md)
- [Learned-policy probe](a3_c2_roe_learned_policy_probe_20260603.md)
- [Reactive/temporal comparison](a3_c2_roe_reactive_temporal_comparison_20260603.md)

Boundary: the records distinguish release authorization, target identity, and
shot discipline from policy-memory claims. They do not claim classified C2
doctrine, real-world weapon authority, or deterministic learned firing.
