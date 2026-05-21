# G3 Execution Surface Preflight Cluster

Status: `2026-05-21` ready for design preflight after accepted G1-G2 evidence.

Inputs:

- [G3 README](README.md)
- [Ground standards overview](../../../standards/ground/README.md)
- [Ground minimal task structure](../../../standards/ground/minimal_task_structure.md)
- [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)

## Purpose

Select and specify the first ground execution surface. This is a design and
preflight task; it should not implement runtime behavior.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `G3-A1` | Runtime-slice candidate | Choose one bounded G4 candidate, such as tasking-only lifecycle proof or minimal command delivery. |
| `G3-A2` | Stage map | Declare exact P0-P10 participation for the selected candidate. |
| `G3-A3` | Packet map | Name consumed, produced, and deferred packet families. |
| `G3-A4` | Observation/reporting design | Decide first reporting surface without exposing world truth. |
| `G3-A5` | Environment dependency map | Record terrain, line-of-sight, radio, and mobility assumptions as implemented, placeholder, or deferred. |
| `G3-A6` | Test plan | Name focused tests required before G4 can claim maintained behavior. |

## Write Scope

Allowed:

- `docs/task/ground/g3_execution_surface_design/**`
- updates to `docs/task/ground/README.md`
- standards follow-up only if a G3 decision changes normative ownership

Do not edit:

- runtime implementation
- profile implementation from G1 unless integration owner requests a narrow doc
  update
- fixture implementation from G2

## Suggested Validation

```bash
git diff --check
```

## Handoff

Return:

- selected G4 candidate
- stage and packet maps
- observation/reporting decision
- deferred assumptions
- test plan
- any standards update needed before G4

## Available G1-G2 Evidence

- G1 accepted a Python-profile-only ground slice with `army`, `ground`, `land`,
  and `ServiceProfile.Army` normalizing to `ground`.
- G1 accepted starter defaults for `TASK_MOVE`, `TASK_OCCUPY`, and
  `TASK_SUPPORT` through common-core fields only.
- G2 accepted a non-auto-loaded platoon-centered content seed at
  `examples/config/database/ground/units/ground_platoon_starter.seed`.
- G2 accepted runnable starter contracts under `tests/contracts/unit/ground/`.

Design preflight must not convert that evidence into runtime movement, terrain,
sensing, fires, weapon, damage, or combat claims.
