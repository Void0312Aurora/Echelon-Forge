# WP17-C Multi-Rate Runtime Example

Status: `2026-05-21` implemented / focused validation passed for the selected
runtime-window cadence slice.

Inputs:

- [WP17 main plan](stage3_runtime_materialization_cleanup_wp17_20260521.md)
- [WP2.5 scheduler semantics](../wp25_scheduler_semantics/scheduler_semantics_wp25_20260519.md)
- [WP11 ActionHoldPolicy](../wp11_facade_vertical_slice_provenance/wp11_action_hold_policy_cluster_20260520.md)
- [WP16 clock-domain enforcement](../wp16_runtime_spine_consolidation/wp16_clock_domain_enforcement_cluster_20260521.md)

## Purpose

Make the architecture §8 example runnable for one maintained slice:
policy 10Hz, control 20Hz, physics 60Hz, observation sampled at the policy
boundary, and explicit hold/skip evidence.

## Scope

In scope:

- nested clock-domain trigger/skip behavior for one selected window-loop slice;
- runtime consumption of `ActionHoldPolicy.hold_last`, expiry, and optional
  interpolation evidence;
- a focused fixture proving policy/control/physics tick counts and observation
  barrier versions;
- diagnostics that distinguish skipped, held, interpolated, and expired actions.

Out of scope:

- global scheduler rewrite;
- independent wall-clock domains;
- backend/fidelity or capability composition changes;
- counterfactual rollout claims.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `C1` | Cadence planner | Selected nodes declare policy/control/physics cadence and produce trigger/skip decisions. |
| `C2` | Hold policy runtime | `hold_last` is visible between control ticks and expiry drops stale input with evidence. |
| `C3` | §8 runnable fixture | Test verifies one or more 100ms windows with 10Hz/20Hz/60Hz counts and barrier exports. |
| `C4` | Advisory flag boundary | Claimed maintained slice no longer relies on silent advisory behavior; global advisory residual remains honest. |

## Suggested Validation

```bash
git diff --check
python -m pytest -q tests/architecture/runtime_spine/test_clock_domain_enforcement.py
python -m pytest -q tests/runtime/facade/test_runtime_facade_window_loop_injection.py -k "clock or cadence or hold or barrier"
```

## Handoff

Return scheduler files touched, cadence semantics, evidence fields, commands run,
and what remains advisory outside the selected slice.
