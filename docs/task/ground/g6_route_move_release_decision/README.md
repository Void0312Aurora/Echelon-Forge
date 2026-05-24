# G6-D Route-Move Release Decision

Status: `2026-05-24` accepted for `G6-D0 Route-Move Release Decision`. No
movement scenario is released by this package.

Language:

- English canonical: `README.md`
- Chinese companion: not required yet; this is a high-churn planning slice.

Inputs:

- [G6-C route-move boundary](../g6_route_move_boundary/README.md)
- [Ground current progress](../ground_current_progress_20260524.md)
- [Ground standards overview](../../../standards/ground/README.md)
- [Ground minimal task structure](../../../standards/ground/minimal_task_structure.md)
- [Subagent usage policy](../../../standards/governance/subagent_usage_policy.md)

## Purpose

Convert the G6-C residual into a bounded decision package before any
`ground_platoon_flat_route_move_v1` scenario or movement implementation is
attempted.

G6-D exists to answer one release question:

Can the first ground route-move scenario claim `G2` movement realism through the
current compatibility spawn shell, or must it wait for a runtime-loadable native
ground platform schema?

## Decision

G6-D selects the schema-first path.

The first `G2` route-move release must wait for a runtime-loadable native ground
platform schema. The current `Aircraft` compatibility spawn shell remains valid
only for G0/G1 tasking, status-chain, static occupy, and support-relationship
fixtures.

An explicit movement compatibility boundary may still be drafted later, but it
cannot by itself release a `G2` movement-realism scenario unless it proves the
same minimum ground-movement critical points and states the shell, proof
allowed, and proof forbidden. Until then, route movement stays held.

Rationale:

- A route-move scenario needs evidence from movement state, not just route
  intent fields.
- The current compatibility shell can prove loader and tasking semantics, but
  it cannot represent ground mobility, off-route behavior, or movement cadence.
- Releasing route movement through the shell would blur the realism-gradient
  boundary between tasking evidence and movement evidence.

## Output

- [G6-D route-move release-decision cluster](g6_route_move_release_decision_cluster_20260524.md)

No scenario, runtime, binding, C++, or Python behavior file is part of this
package.

## Scope

In scope:

- selected route-move release path;
- finite follow-on cluster list;
- minimum `G2` flat-route critical points;
- future worker packets and write-scope boundaries;
- residual map for native ground platform schema work.

Out of scope:

- `ground_platoon_flat_route_move_v1`;
- runtime-loadable ground platform schema implementation;
- movement dynamics implementation;
- terrain traversal, terrain masking, line-of-sight, sensing, fires, damage,
  observation export, or combat;
- C++ DTOs, Python bindings, facade changes, and broad mission-command growth.

## Gate

G6-D0 is complete when this package records:

- schema-first as the selected route-move release posture;
- that compatibility-shell route movement is not accepted as a `G2` realism
  release path;
- the minimum critical points for later `G2` flat route movement;
- the finite cluster list, model/reasoning budget, write set, non-goals,
  validation commands, closure gate, dependency relation, and round cap.

No downstream worker may add `ground_platoon_flat_route_move_v1` until the
native ground platform schema path is accepted or a later compatibility
boundary is explicitly approved with equivalent evidence gates.

## Residuals

- Preflight the minimal runtime-loadable native ground platform schema.
- Preflight the exact state/evidence hooks needed to prove flat route movement.
- Keep G3+ terrain-aware movement, G4 contact report, G5 fires, G6 damage, and
  G7 sustainment outside this release package.
