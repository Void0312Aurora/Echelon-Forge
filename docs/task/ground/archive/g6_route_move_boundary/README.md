# G6-C Route-Move Boundary

Status: `2026-05-24` accepted for route-move release-boundary guardrails.
`G2` movement scenarios remain held.

Language:

- English canonical: `README.md`
- Chinese companion: not required yet; this is a high-churn boundary slice.

Inputs:

- [G6 realism-gradient MVP scenarios](../g6_realism_gradient_mvp_scenarios/README.md)
- [Ground current progress](../ground_current_progress_20260524.md)
- [Subagent usage policy](../../../standards/governance/subagent_usage_policy.md)

## Purpose

Close the immediate follow-on risk after the first G1 ground realism fixtures:
`G2 flat route move` must not be released merely because a JSON scenario can be
shaped.

This slice accepts guardrails only:

- explicit profile hints now fail closed when unknown;
- ground runtime paths must route through the shared tasking bridge;
- current ground scenarios must declare the compatibility spawn shell and defer
  native ground runtime plus G2+ realism claims.

## Decision

`ground_platoon_flat_route_move_v1` remains held. G6-E2/E3 later accepted
native ground schema evidence, but that closes identity/load/spawn only; a
separate movement-release vote must still accept movement evidence before a
G2 route-move scenario can land. A documented movement compatibility boundary
would also need equivalent evidence and an explicit release vote.

The current accepted state is therefore:

- G0 tasking smoke: accepted;
- G1 static occupy/support relationship fixtures: accepted;
- G2 route move: not released;
- terrain, sensing, fires, damage, observation export, and combat: deferred.

## Output

- [G6-C route-move boundary cluster](g6_route_move_boundary_cluster_20260524.md)
- Runtime/profile guardrail:
  `python/rl/tasking/bridge.py`
- Focused tests:
  - `tests/leader/test_tasking_profile_contracts.py`
  - `tests/architecture/ground/test_realism_gradient_guardrails.py`

## Gate

G6-C is complete when:

- explicit unknown loader `tasking_profile` and `service_profile` hints raise a
  clear `ValueError`;
- loaders with no profile hint retain the legacy air default;
- architecture tests prove runtime code does not import private ground profile
  modules directly;
- architecture tests prove current ground scenarios stay at G0/G1 and defer
  native ground runtime plus movement, terrain, sensing, and damage claims;
- no movement scenario is added.

## Residuals

- Decide whether the first G2 route-move release will use a native ground
  platform schema or a documented compatibility boundary.
- After that decision, add `ground_platoon_flat_route_move_v1` with tests that
  prove only the accepted G2 movement boundary.
- Keep G3+ terrain, G4 contact report, and G5/G6 fire/damage deferred.
