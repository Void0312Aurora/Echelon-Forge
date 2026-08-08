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

- [Test System Residual Governance](../../../../engineering/testing/work/issues/test_system_residual_governance/README.md):
  retained follow-on gate for test-system residuals after the scoped governance
  slice: dependency-complete airframe behavior, remaining damage-model
  literal/source-scan concentration, failing `weapon_guidance_realism`, and
  Python/C++ coverage boundary separation.
- [A6 Launch-Window Label Density Imbalance](../../../../learning/work/issues/launch_window_label_imbalance/README.md):
  deterministic `fire_once` argmax does not cross under the L contract despite
  `34.6%` open-window event probability. It remains a live symptom and
  balancing requirement, but A6 root-cause re-scope now treats the deeper
  blocker as first-event censoring plus missing counterfactual hold/fire credit;
  A7 owns the next repair path.
- [HMoE Hierarchical Computation Gap](../../../../learning/work/issues/hmoe_hierarchical_computation_gap/README.md):
  subexpert heads receive the same raw latent as family heads rather than
  family-head output; the combat C2/ROE layout collapses five families into one.
  A7 must account for this in head placement and diagnostics, but this issue is
  still not an active HMoE redesign authorization.

## Retained Tracking Items

- [Lethality Hitbox Geometry Fidelity Gap](../../../../systems/effects/work/issues/lethality_hitbox_geometry_fidelity_gap/README.md):
  the first F-16C fine-geometry engineering proxy is closed against the
  geometry-only acceptance gate; this issue remains as boundary evidence for
  later default runtime replacement, training diagnostics, other-airframe reuse,
  structural breakup, or weapon-specific conclusions.
- [Damage-To-Control Authority Coupling Gap](../../../../systems/effects/work/issues/damage_control_authority_coupling_gap/README.md):
  damage reports can mark pilot/crew, flight-control, command/navigation, or
  communication/data-link failures without necessarily disabling later control
  input, command-link delivery, or data-link behavior. Parked for follow-up; it
  is not part of the current fire-window sweep core.
- [RL Policy Hold-Baseline Drift](../../../../learning/work/issues/policy_hold_baseline_drift/README.md):
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
