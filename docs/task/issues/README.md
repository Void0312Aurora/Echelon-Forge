# Issue Board

Status: active cross-cutting issue board.

This directory tracks concrete problems that are broader than one domain
folder, or that should remain visible across domain, runtime, model, training,
and evaluation worklines.

Use this area when a finding has one or more of these properties:

- it can recur outside the domain where it was first observed;
- it blocks acceptance or formal-training claims;
- it exposes a gap between runtime behavior, training evidence, and eval
  infrastructure;
- it needs follow-up work that may span multiple task areas.

Domain folders such as `naval/`, `air_combat/`, or `ground/` should still hold
domain roadmaps and scenario-specific task clusters. This board is for issues
whose evidence and repair path should be reusable by other worklines.

## Active Issues

No cross-cutting issue is currently promoted as an open blocking item from this
index. Promote a retained item back here only when a current task, review, or
acceptance gate needs active repair coordination.

## Retained Tracking Items

- [RL Policy Hold-Baseline Drift](./rl_policy_hold_baseline_drift/README.md):
  the deterministic N4 hold probe is closed, but stochastic-policy acceptance
  and off-station curricula still need this record as reusable evidence.

## Issue Record Shape

Each issue subproject should normally include:

- current status and owner thread;
- first observed context;
- evidence summary with commands or measured facts;
- impact and non-claims;
- likely causes or hypotheses;
- next action gates;
- links back to domain task clusters that depend on the issue.
