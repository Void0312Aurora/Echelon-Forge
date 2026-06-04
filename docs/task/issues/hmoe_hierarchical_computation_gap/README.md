# HMoE Hierarchical Computation Gap

Status: `2026-06-04` open; subexpert heads do not receive family-head output,
and the combat-weapons C2/ROE observation layout collapses the five-family
hierarchy into a single-family flat structure.

First observed: `2026-06-04`, during A6 air-combat deep-dive code review.

Issue class: architecture design gap — the parameter organization and training
schedule are hierarchical, but the forward computation graph is not.

## Summary

`HierarchicalMoEExecutionPolicy` is the primary execution-layer policy for
air-combat and naval tasks. It organizes computation into three tiers:

- shared backbone (`action_net`) — baseline policy mean;
- `_HMoEHeadBank` — five family heads × (1–3) subexpert heads per family,
  added as a residual on top of the shared mean;
- `hybrid_event_head` (A6-EVT-K) — dedicated event-logit deltas for the
  masked `hold/fire_once` decision.

The architecture name and docstring describe "explicit hierarchical semantic
routing", and the parameter organization (separate LR scales, warmup schedule,
residual initialization) is genuinely hierarchical. However, two structural
gaps limit how much the hierarchy is realized in the forward computation:

1. Subexpert heads receive the same raw `latent_pi` as family heads — they
   have no access to what the family head already computed.
2. The air-combat C2/ROE layout (`mission_dim=20`) hard-routes every step to
   `FAMILY_COMBAT_WEAPONS`, so 4 of 5 families and 9 of 12 subexperts never
   activate during S1 air-combat training.

## Current Evidence

### Gap 1: Flat Subexpert Input

From `_HMoEHeadBank.forward` in [policies.py:86-110](../../../../python/rl/policy_algo/policies.py#L86-L110):

```python
family_out = family_head(family_latent)              # family uses latent_pi
residual[sub_mask] = sub_head(family_latent[sub_mask])  # subexpert also uses latent_pi
family_out = family_out + residual                   # simple addition
```

Both family heads and subexpert heads receive the **identical** `latent_pi`
tensor. A truly hierarchical computation would feed the family head's output
(or a transformation of it) into the subexpert, so the subexpert can
specialize based on what the family already decided:

```python
# What a hierarchical forward would look like:
family_out = family_head(latent_pi)
sub_input = concat([latent_pi, family_out.detach()])  # subexpert sees family output
residual = sub_head(sub_input)
```

Consequence: the subexpert cannot learn "the family wants to hold — I should
reinforce that" vs "the family wants to fire — I should moderate that".
It must infer the tactical context from raw latent alone, duplicating work
the family head already did.

### Gap 2: Combat-Mode Hierarchy Collapse

From `route_from_mission_observation` in [hmoe_routing.py:133-167](../../../../python/rl/policy_algo/hmoe_routing.py#L133-L167):

```python
if _air_combat_c2_roe_layout(dim):       # dim == 20 → True
    family = FAMILY_COMBAT_WEAPONS        # always 4
    # ... subexpert routing ...
    return HMoERouteBatch(...)            # returns early; all other families skipped
```

When the mission observation has 20 dimensions (the air-combat C2/ROE
layout), the router **immediately** sets `family = COMBAT_WEAPONS` and
returns. None of the other four family routing branches (takeoff, nav,
formation, landing) are ever evaluated.

In the current S1 air-combat training:

| Family | Heads | Subexperts | Activated in S1? |
| --- | --- | --- | --- |
| `takeoff_ground` (0) | 1 | 3 (single / interval / wing) | Never |
| `departure_nav` (1) | 1 | 2 (vector / route) | Never |
| `formation_cooperative` (2) | 1 | 3 (generic / lead / wingman) | Never |
| `recovery_landing` (3) | 1 | 1 (generic) | Never |
| `combat_weapons` (4) | 1 | 3 (hold / first_shot / assess) | Always |

Effective architecture in air-combat training: **1 family × 3 subexperts** —
a flat 3-expert structure, not a 5×n hierarchical MoE.

This is not a routing bug — the C2/ROE layout genuinely describes a combat
phase. But it means the HMoE's "hierarchical" property is not exercised in
the scenario where it matters most (air combat), and the parameters for the
other four families receive no gradient during combat training.

### Gap 3: Deterministic Non-Learned Routing

Routing uses hard assignment via hand-written rules on the mission observation
vector. There is no learned gating network and no soft mixing of experts:

```python
subexpert = th.where(authorized_first_shot, 1, subexpert)
subexpert = th.where(post_launch_assess, 2, subexpert)
```

While deterministic routing is stable and interpretable, it cannot adapt to
regime boundaries. At the transition from `weapons_hold` to
`authorized_first_shot`, the active subexpert switches abruptly from index 0
to index 1. There is no overlap, no gradual handoff, and the
`authorized_first_shot` expert must learn its policy from scratch without
any information from the `weapons_hold` expert's computation.

### What IS Hierarchical (for fairness)

The design is not without hierarchy — it is hierarchical in three important
dimensions:

1. **Parameter organization**: family heads and subexpert heads are separate
   `nn.ModuleList` structures with clear semantic grouping.
2. **Optimizer LR scales**: three-tier learning rates (shared `1.0`, HMoE
   `0.35`, event-head `10.0`) create a training-speed hierarchy.
3. **Residual warmup**: `hmoe_residual_warmup_fraction=0.3` and
   `hmoe_residual_start_factor=0.25` schedule the HMoE contribution to ramp
   from 25% to 100% over the first 30% of training, keeping the shared
   backbone dominant early.

These are genuine architectural decisions that improve training stability.
The gap is that the **forward computation** does not match this hierarchical
structure.

## Impact

- **Air-combat training wastes HMoE capacity**: 80% of family heads and 75%
  of subexpert heads never activate.
- **Subexpert specialization is limited**: without access to family-head
  output, subexperts cannot learn complementary or moderating behaviors.
- **Hard routing at authorization boundaries**: the abrupt switch from
  `weapons_hold` to `authorized_first_shot` may contribute to the difficulty
  of learning stable fire timing. The `authorized_first_shot` expert starts
  from zero knowledge every time the mask opens.
- **Not a direct blocker for A6**: the event-head optimization lane (K)
  proved deterministic fire is trainable despite these gaps. But the gaps
  may limit how robustly the policy can learn nuanced timing behavior.

## A7 Relationship

A7
([air-combat A7](../../air_combat/a7_event_value_advantage_credit_head/README.md))
uses this issue as a placement and diagnostics constraint:

- the event-value / advantage-credit head should be a policy-level sibling of
  `hybrid_event_head`, not a signal hidden inside one hard-routed combat
  subexpert;
- diagnostics should report both event-credit signs and HMoE route stats so
  failures can be separated into credit-learning failure versus routing/capacity
  failure;
- HMoE repair should be promoted only if A7 learns correct event-credit signs
  but policy coupling still fails in a way attributable to the hierarchy gap.

This issue does not authorize an HMoE redesign inside A7.

## Non-Claims

- This is not a claim that the HMoE architecture is broken — it works and
  produces valid policies.
- This is not a claim that learned routing would solve the A6 label-imbalance
  problem.
- This is not a call to redesign HMoE from scratch — the residual warmup and
  LR hierarchy are well-designed and should be preserved.
- This is not a vote for M2 release.

## Hypotheses

1. **Primary**: feeding family-head output into subexpert heads would create
   a genuine information hierarchy, letting subexperts specialize relative
   to the family's baseline decision.
2. **Secondary**: the combat-mode hierarchy collapse is intentional (the
   scenario is combat-only) but could be mitigated by allowing soft mixing
   of combat subexperts rather than hard routing at authorization
   boundaries.
3. **Secondary**: a small learned routing residual on top of the
   deterministic base route would improve boundary-region behavior without
   sacrificing stability.
4. **Tertiary**: the current design is adequate for single-phase scenarios
   (like S1 combat-only). The hierarchy would become more important in
   multi-phase scenarios (takeoff → nav → combat → landing).

## Related Domain Context

- HMoE routing:
  [python/rl/policy_algo/hmoe_routing.py](../../../../python/rl/policy_algo/hmoe_routing.py)
- Policy implementation:
  [python/rl/policy_algo/policies.py](../../../../python/rl/policy_algo/policies.py)
- A6 subproject:
  [docs/task/air_combat/a6_event_value_first_event_timing/README.md](../../air_combat/a6_event_value_first_event_timing/README.md)
- M1 temporal-window HMoE:
  [docs/task/model/m1_temporal_window_hmoe/README.zh.md](../../model/m1_temporal_window_hmoe/README.zh.md)
- M2 causal Transformer HMoE:
  [docs/task/model/m2_causal_transformer_hmoe/README.zh.md](../../model/m2_causal_transformer_hmoe/README.zh.md)

## Next Gates

This issue is a design observation, not an active implementation blocker.
Recommended actions, ordered by impact-to-effort ratio:

1. **P0 (low effort, high impact)**: feed family-head output into subexpert
   heads. Change subexpert input from `[latent_pi]` to
   `[latent_pi, family_out.detach()]`. This requires increasing subexpert
   `in_features` from `latent_dim` to `latent_dim + action_dim`. The
   zero-initialization of HMoE heads means this change is backward-compatible
   — existing checkpoints would need the subexpert input layer expanded
   (pad with zeros), but new training would use the hierarchical input
   immediately.
2. **P1 (medium effort, medium impact)**: add soft gating for combat-weapons
   subexperts. Instead of hard-routing to one subexpert, compute a learned
   softmax gate over all three combat subexperts and mix their outputs.
   Keep the deterministic route as a gate bias or prior.
3. **P2 (medium effort, situational impact)**: add a learned routing residual
   on top of the deterministic base route. This becomes important when
   multi-phase scenarios (takeoff → nav → combat → landing) are trained.
4. **P3 (observation only)**: track HMoE family/subexpert activation
   statistics during training to quantify how much capacity is utilized.
   The route-stats infrastructure already exists in
   `_update_route_stats`.

## Acceptance For Closure

This issue can be closed when at least one of these holds:

- Subexpert heads receive family-head output (Gap 1 addressed).
- A documented decision explains why the current flat-subexpert design is
  intentional and sufficient for the planned scenario surface.
- Multi-phase scenario training demonstrates that the five-family hierarchy
  is exercised and useful.

The issue does not need to block any air-combat acceptance gate — the A6
label-imbalance issue ([../a6_launch_window_label_imbalance/README.md](../a6_launch_window_label_imbalance/README.md))
is the active blocker.
