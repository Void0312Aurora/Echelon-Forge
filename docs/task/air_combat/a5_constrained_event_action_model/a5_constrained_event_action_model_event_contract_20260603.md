# A5 Event Action Contract

Status: `2026-06-03` contract draft frozen for A5 implementation. This document
defines the S1 C2/ROE constrained event-action semantics before runtime or
policy edits start.

Parent: [README.md](README.md). Input:
[surface audit](a5_constrained_event_action_model_surface_audit_20260603.md).

## Boundary

This contract does not change missile physics, release kinematics, damage, Pk,
fuze behavior, or true BVR doctrine. It changes the policy-facing release
semantics for accepted S1 C2/ROE training/eval entries.

The core split is:

- legality and availability belong to event state and action support;
- policy learns timing inside valid support;
- reward expresses outcome, timing, ammo, and tracking preferences.

## Event State

`engagement_state` is the policy-visible finite state for weapon-release event
support. The first A5 implementation should use these values:

| Value | Meaning | Fire support |
| --- | --- | --- |
| `Hold` | C2/ROE, target, weapon, or mission state does not allow release. | `hold` only |
| `AuthorizedReady` | First-shot release is authorized and the event is available. | `hold`, `fire_once` |
| `FiredAssess` | A release was accepted and the episode is waiting for missile outcome or assessment. | `hold` only |
| `ReattackReady` | Assessment or mission state explicitly allows a follow-on shot. | `hold`, `fire_once` |
| `Winchester` | No valid weapon remains or the release path is no longer available. | `hold` only |

Future implementations may add a terminal/disengage value, but A5 must not
require it for the first event-action gate.

## Mask Components

`fire_mask` is the final action-support bit for `fire_once`. It must be derived
from named components so diagnostics can explain why an event is unavailable.

Recommended component names:

| Component | Meaning |
| --- | --- |
| `fire_mask_c2_authorized` | C2/ROE authorization allows release. |
| `fire_mask_target_present` | A valid assigned/primary target track is present. |
| `fire_mask_shot_budget_available` | Shot budget remains for the current event cycle. |
| `fire_mask_not_pending_assessment` | No no-fire assessment state blocks first shot or salvo. |
| `fire_mask_weapon_ready` | Master arm, selected weapon, and runtime weapon readiness permit release. |
| `fire_mask_ammo_available` | Ammunition remains for the selected weapon. |
| `fire_mask_reattack_allowed` | Follow-on release is explicitly authorized after assessment. |

The final support rule is:

```text
fire_mask =
  engagement_state in {AuthorizedReady, ReattackReady}
  and fire_mask_c2_authorized
  and fire_mask_target_present
  and fire_mask_shot_budget_available
  and fire_mask_weapon_ready
  and fire_mask_ammo_available
  and (
    engagement_state == AuthorizedReady
    or fire_mask_reattack_allowed
  )
  and fire_mask_not_pending_assessment
```

If a future salvo state is added, it must be an explicit state or explicit mask
component. It must not be represented by weakening `FiredAssess` suppression.

## Event Action

The policy-facing event action is:

```text
event_action in {hold, fire_once}
event_action_mask = [1, fire_mask]
```

Rules:

- `hold` is always available.
- `fire_once` is unavailable when `fire_mask == 0`.
- Sampling and deterministic evaluation must use the same mask.
- The accepted S1 C2/ROE training entry must not use raw
  `sigmoid(fire_weapon_logit) > 0.5` or a continuous threshold as the event
  semantics.

## State Transitions

Minimum transition contract:

| From | Condition | To | Notes |
| --- | --- | --- | --- |
| `Hold` | all first-shot support components true | `AuthorizedReady` | Fire becomes available. |
| `AuthorizedReady` | `event_action=hold` and support remains true | `AuthorizedReady` | Policy may continue waiting. |
| `AuthorizedReady` | support closes before release | `Hold` | No penalty is implied by this transition alone. |
| `AuthorizedReady` | `event_action=fire_once` and `fire_mask=1` | `FiredAssess` | Release event is accepted and consumed. |
| `FiredAssess` | mission success or terminal condition | terminal/end state | Out of first implementation if terminal is already elsewhere. |
| `FiredAssess` | assessment complete, no ammo | `Winchester` | Fire remains unavailable. |
| `FiredAssess` | assessment complete and reattack allowed | `ReattackReady` | Follow-on fire becomes explicit. |
| `FiredAssess` | assessment complete and no reattack support | `Hold` | Default no-fire after assessment. |
| `ReattackReady` | `event_action=fire_once` and `fire_mask=1` | `FiredAssess` | Follow-on event is accepted and consumed. |
| `ReattackReady` | support closes before release | `Hold` | No implicit repeated fire. |

## Runtime Info Fields

Runtime and diagnostics should converge on these fields:

| Field | Meaning |
| --- | --- |
| `fire_once_requested` | Policy requested `fire_once` in this step. |
| `fire_once_accepted` | Runtime accepted and consumed the event. |
| `fire_once_rejected_reason` | Stable reason string when requested fire is unavailable. |
| `release_executed` | A missile release actually occurred. |
| `post_launch_suppressed` | A fire request was suppressed because assessment/no-fire state was active. |
| `reattack_ready` | Explicit follow-on release support is available. |
| `engagement_state` | Current event state value. |
| `fire_mask` | Final event action support bit. |

Recommended initial `fire_once_rejected_reason` values:

- `masked_hold_only`
- `hold_state`
- `no_c2_authorization`
- `no_target`
- `shot_budget_empty`
- `pending_assessment`
- `weapon_not_ready`
- `ammo_empty`
- `reattack_not_authorized`

## Policy Semantics

First implementation:

```text
event_dist = MaskedCategorical(logits=[logit_hold, logit_fire], mask=[1, fire_mask])
```

Training:

```text
event_action ~ event_dist
```

Deterministic evaluation:

```text
event_action = argmax_masked(event_dist)
```

Log-prob and entropy must be computed on the masked distribution. Illegal
`fire_once` must not contribute probability mass. If the transport remains flat
for SB3 compatibility, the event head still owns policy log-prob and evaluation
semantics.

## Reward Boundary

Reward may score:

- mission success or failure;
- missile effect;
- timing and opportunity cost;
- ammo usage;
- tracking and weapon-chain preparation.

Reward must not be the primary mechanism for:

- teaching unauthorized fire is illegal;
- preventing immediate repeated fire after release;
- enforcing shot budget;
- suppressing fire during assessment.

Those are event-state and action-support responsibilities.

## Contract Test Requirements

Implementation clusters must add or update tests that prove:

- `fire_mask=0` forces event action support to `hold` only.
- `AuthorizedReady + fire_once` consumes one event and enters `FiredAssess`.
- `FiredAssess` suppresses immediate repeat fire even if policy requests it.
- `ReattackReady` is the only initial follow-on state that can reopen `fire_once`.
- Policy stochastic sampling, deterministic eval, log-prob, and entropy use the
  same mask.
- Diagnostics distinguish requested, accepted, rejected, executed, and
  post-launch-suppressed fire.

## Acceptance Result

`A5-EAM-C Event Contract` is accepted as a contract draft. It unlocks runtime
and policy implementation packets, but those packets must still prove the
contract with focused tests.
