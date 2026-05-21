# G1 Contract Skeleton

Status: `2026-05-21` G1-A preflight and G1-B narrow Python-profile
implementation accepted.

Language:

- English canonical: `README.md`
- Chinese companion: not required yet; this is a high-churn task slice.

Inputs:

- [Ground standards overview](../../../standards/ground/README.md)
- [Ground minimal task structure](../../../standards/ground/minimal_task_structure.md)
- [Ground domain bootstrap plan](../ground_domain_bootstrap_plan_20260521.md)
- [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)

## Purpose

Create the smallest contract skeleton needed for the `ground` tasking profile
without adding runtime behavior.

## Output

- [G1 profile and DTO contract cluster](g1_profile_dto_contract_cluster_20260521.md)
- [G1 profile and DTO preflight](g1_profile_dto_preflight_20260521.md)

## Release State

- `G1-A`: preflight-only, returned `implementation-ready`.
- `G1-B`: accepted for Python-profile-only implementation.
- DTO shells: not needed in G1.
- Held: C++ DTOs, Python bindings, runtime behavior, scenario-loader behavior,
  and command-delivery semantics.
- Main-thread validation passed for the focused G1 suite and full
  `tests/leader`.

## Scope

In scope:

- profile resolution for `army`, `ground`, and `land`
- starter `ground_profile` / adapter shell
- default mapping for `TASK_MOVE`, `TASK_OCCUPY`, `TASK_SUPPORT`
- optional empty or minimal DTO landing points after field ownership is agreed
- focused tests for resolution, defaults, and compatibility

Out of scope:

- movement dynamics
- command delivery behavior
- observation export
- weapon/effects behavior

## Gate

G1 is mergeable when the ground profile can be resolved and normalized without
changing air/naval behavior, and focused tests prove the starter task defaults.
