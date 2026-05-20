# WP11-A ActionHoldPolicy Contract

Status: `2026-05-20` planned WP11 dispatch sheet.

Language:

- English canonical: `wp11_action_hold_policy_cluster_20260520.md`
- Chinese companion:
  [wp11_action_hold_policy_cluster_20260520.zh.md](wp11_action_hold_policy_cluster_20260520.zh.md)

Inputs:

- [WP11 facade vertical slice and provenance](facade_vertical_slice_provenance_wp11_20260520.md)
- [Post-WP9 gap analysis](../../review/post_wp9_gap_analysis_20260520.md)
- [WP9 policy contracts](../wp9_contract_infrastructure_closure/wp9_dto_promotion_batch2_cluster_20260520.md)

## 1. Purpose

`WP11-A` adds the missing `ActionHoldPolicy` contract required by the
architecture before any policy/control/physics cadence claim can be made.

This stream creates the typed contract and tests only. Runtime cadence execution
is explicitly out of scope.

## 2. Scope

In scope:

- define a typed `ActionHoldPolicy` DTO/contract;
- encode hold modes for hold-last, interpolate, expire, and drop behavior;
- include validity duration, refresh cadence, expiry behavior, and
  credit-assignment latency assumptions;
- expose the DTO through Python bindings if adjacent policy DTOs are already
  binding-visible;
- add contract-shape and binding smoke tests.

Out of scope:

- enforcing multi-rate policy/control/physics cadence;
- changing the scheduler;
- applying interpolation to real control commands;
- claiming maintained runtime cadence support.

## 3. Contract Shape

Minimum field families:

| Field family | Required meaning |
|--------------|------------------|
| Identity | stable policy id or action family label when available. |
| Hold mode | one of `hold_last`, `interpolate`, `expire`, or `drop`. |
| Validity | validity duration, optional valid-until time, and expiry action. |
| Cadence | policy refresh cadence and target control cadence declarations. |
| Interpolation | interpolation mode or explicit `none`. |
| Credit | credit-assignment latency / attribution note. |
| Diagnostics | reason when a policy is diagnostics-only or unsupported. |

## 4. Acceptance Tests

Minimum tests:

- C++/header contract contains the required field families;
- default policy is deterministic and conservative;
- invalid hold mode is rejected by helper or validation test if a validator is
  added;
- Python binding smoke exposes the DTO fields when bindings are touched;
- tests assert that WP11-A does not claim runtime cadence execution.

## 5. Handoff Contract

Return:

- contract file paths and public fields;
- binding paths if touched;
- tests added or updated;
- commands run and outcomes;
- any fields intentionally left declarative rather than enforced;
- integration notes for `WP11-B/C/E`.
