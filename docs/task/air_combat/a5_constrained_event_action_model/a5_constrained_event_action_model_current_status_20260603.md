# A5 Constrained Event Action Model Current Status

Status: `2026-06-03` implementation checkpoint. Surface audit, event contract,
runtime prototype, and policy event head are accepted; reward/config cleanup,
diagnostics/evidence, and closure remain pending.

## Decision

The selected long-range solution is:

```text
explicit engagement state machine
+ C2/ROE/weapon action-support mask
+ independent event action head: hold / fire_once
+ post-launch FiredAssess no-fire state
+ explicit ReattackReady follow-on gate
```

The first implementation should use masked categorical event semantics because
it fixes the structural multi-fire path and the stochastic/deterministic eval
mismatch while remaining close to the current PPO stack. Event Q-head is the
preferred follow-on when value comparison is needed. Hazard / first-event and
full hierarchical options are deferred.

## Why A4 Is Not Enough

| Symptom | A4 evidence | A5 interpretation |
| --- | --- | --- |
| Deterministic policy does not fire | retained A4 32k routed probe remains `0 fire / 0 release` | The event head never crosses deterministic threshold because the action semantics and training data are hostile to rare fire events. |
| Stochastic policy still produces bad releases | retained stochastic probe fires/release but includes violations/invalid attempts | Per-step sampling can produce repeated or invalid event attempts unless action support removes them structurally. |
| Reward urgency trial failed | bounded opportunity penalty did not move deterministic fire and worsened release discipline | More reward pressure does not fix an incorrect event-action model. |
| Binary fire probability remains tiny | authorized-window fire probability stays near `0.22%`, max logit near `-6.11` | Fire is being learned as a rare pulse in a long sequence, not as a finite-window event decision. |

## Selected Architecture Surface

| Surface | Planned A5 treatment | Risk |
| --- | --- | --- |
| `engagement_state` | Explicit policy-visible state such as `Hold`, `AuthorizedReady`, `FiredAssess`, `ReattackReady`, `Winchester`. | Field naming must align with A3 mission observation and M1 action contract. |
| `fire_mask` | Final action-support bit derived from C2/ROE, weapon state, ammo, pending assessment, and reattack permission. | Avoid hiding useful explanatory fields behind an opaque mask only. |
| `event_action` | `hold/fire_once`, sampled only in legal support. | PPO rollout/log-prob must not include illegal action probability. |
| Post-launch behavior | Accepted `fire_once` immediately enters `FiredAssess`; fire suppressed until explicit follow-on state. | Must distinguish default suppression from intentional salvo/reattack rules. |
| Reward | Express mission result, effect, timing, ammo cost, and tracking preference. | Do not reintroduce invalid-fire penalty as the main legality mechanism. |
| Evaluation | Masked argmax or event-value comparison, not raw `sigmoid(logit)>0.5` threshold. | Deterministic behavior must remain auditable by diagnostics. |

## Immediate Work

1. Update S1 C2/ROE active entries and diagnostics.
2. Run focused diagnostics and learned-policy probes.
3. Decide accepted or held status with residual map.

## Accepted Planning Evidence

- Surface audit:
  [a5_constrained_event_action_model_surface_audit_20260603.md](a5_constrained_event_action_model_surface_audit_20260603.md)
- Event action contract:
  [a5_constrained_event_action_model_event_contract_20260603.md](a5_constrained_event_action_model_event_contract_20260603.md)
- Air action contract overlay:
  [../../../standards/air/act.md](../../../standards/air/act.md)
- Implementation evidence:
  [a5_constrained_event_action_model_implementation_evidence_20260603.md](a5_constrained_event_action_model_implementation_evidence_20260603.md)

## Open Risks

- The current loaded-model HMoE residual gate may restore to a start factor
  instead of the trained gate value. A5 should fix or account for this before
  relying on learned residual event behavior.
- If `fire_mask` is too strict, policy may never learn timing. If too loose,
  A5 reintroduces invalid samples. The contract needs component fields and
  diagnostics, not only a final bit.
- A masked categorical event head fixes structural repetition but may still need
  window-level exploration or an event Q-head if `hold` remains locally easier
  than `fire_once`.

## Forbidden Conclusions

- A5 is not accepted yet.
- A5 does not release M2.
- A5 does not alter missile physics, damage, Pk, fuze, or real-world doctrine.
- A5 does not make `2v2` or self-play in scope.
